"""
Servidor FastAPI e rotas do Epyatis MCP Central (Fase 1: MVP Estruturado & UI).
"""

from contextlib import asynccontextmanager
import hashlib
import json
import logging
import secrets
import time
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from central.api.routes import api_router, auth_router
from central import __version__
from central.config import settings
from central.db.seeder import init_database
from central.gateway.manager import gateway_manager
from central.ui.dashboard import DASHBOARD_HTML

logging.basicConfig(
    level=logging.INFO if settings.CENTRAL_DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("central")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicializa o banco SQLite e migra bootstrap se necessário
    logger.info("Inicializando banco de dados SQLite do Epyatis MCP Central...")
    init_database(settings.CONFIG_PATH)

    # 2. Carrega instâncias a partir do SQLite
    logger.info("Carregando instâncias ativas do banco de dados...")
    gateway_manager.load_from_db()

    # Fallback para YAML se o banco estiver vazio
    if not gateway_manager.instances:
        logger.warning("Nenhuma instância no banco; carregando fallback do YAML...")
        gateway_manager.load_config(settings.CONFIG_PATH)

    # 3. Inicia conexões upstream
    await gateway_manager.start_all()

    # 4. Proactive discovery: descobre e persiste tools de todos os upstreams no DB
    for slug, gw in gateway_manager.instances.items():
        try:
            logger.info(f"Sincronizando catálogo de ferramentas para instância '{slug}'...")
            await gw._handle_list_tools(None)
        except Exception as e:
            logger.warning(f"Aviso durante sincronização inicial de tools da instância '{slug}': {e}")

    yield

    # Encerramento: Finaliza subprocessos e conexões remotas
    logger.info("Encerrando Epyatis MCP Central...")
    await gateway_manager.stop_all()


from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="Epyatis MCP Central",
    version=__version__,
    description="Centralized MCP gateway and management platform",
    lifespan=lifespan,
)

# Hardening de Cabeçalhos e CORS (SEC-06)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Mcp-Session-Id",
        "X-Central-Admin-Key",
        "X-Central-Session-Token",
    ],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Registra rotas de autenticação e API administrativa (v1)
app.include_router(auth_router)
app.include_router(api_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or secrets.token_urlsafe(12)
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith(("/api/", "/admin")):
        response.headers["Cache-Control"] = "no-store"
    if settings.CENTRAL_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


MCP_MAX_BODY_BYTES = 1_048_576
MCP_SESSION_TTL_SECONDS = 3_600
_mcp_http_sessions: dict[str, tuple[str, str, float]] = {}


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _jsonrpc_error(request_id: Any, code: int, message: str, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        },
    )


def _validate_mcp_session(request: Request, slug: str, token: str) -> bool:
    session_id = request.headers.get("mcp-session-id", "").strip()
    session = _mcp_http_sessions.get(session_id)
    if not session:
        return False
    session_slug, session_digest, expires_at = session
    if expires_at <= time.monotonic():
        _mcp_http_sessions.pop(session_id, None)
        return False
    return session_slug == slug and secrets.compare_digest(session_digest, _token_digest(token))



@app.get("/health")
async def health_check() -> dict[str, Any]:
    instances_status = {}
    for slug, gw in gateway_manager.instances.items():
        upstreams_health = {}
        for conn_id, up in gw.upstreams.items():
            upstreams_health[conn_id] = await up.is_healthy()
        instances_status[slug] = {
            "name": gw.config.name,
            "upstreams": upstreams_health,
        }

    return {
        "status": "healthy",
        "service": "Epyatis MCP Central",
        "version": __version__,
        "instances": instances_status,
    }


@app.get("/mcp/{slug}/sse")
async def handle_instance_sse(slug: str, request: Request) -> Response:
    gateway = gateway_manager.get_instance(slug)
    if not gateway:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada.")

    token = _bearer_token(request)

    if not gateway.validate_token(token):
        logger.warning(f"[Security] Tentativa de conexão não autorizada na instância '{slug}'.")
        raise HTTPException(status_code=401, detail="Token de instância ausente ou inválido.")

    # Conecta o transport SSE do SDK oficial
    async with gateway.sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await gateway.mcp_server.run(
            read_stream,
            write_stream,
            gateway.mcp_server.create_initialization_options(),
        )

    return Response()


@app.post("/mcp/{slug}/sse")
@app.post("/mcp/{slug}")
async def handle_instance_post(slug: str, request: Request) -> Response:
    """Suporte a Streamable HTTP / Direct JSON-RPC POST usado pelo Paperclip."""
    gateway = gateway_manager.get_instance(slug)
    if not gateway:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada.")

    token = _bearer_token(request)

    if not gateway.validate_token(token):
        logger.warning(f"[Security] Tentativa de conexão não autorizada na instância '{slug}'.")
        raise HTTPException(status_code=401, detail="Token de instância ausente ou inválido.")

    try:
        raw_body = await request.body()
        if len(raw_body) > MCP_MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="Payload MCP excede o limite permitido.")
        body = json.loads(raw_body)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Corpo da requisição deve ser um JSON válido.")

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or not isinstance(body.get("method"), str):
        return _jsonrpc_error(body.get("id") if isinstance(body, dict) else None, -32600, "Requisição JSON-RPC inválida.", 400)

    method = body.get("method")
    req_id = body.get("id")

    # Handshake de inicialização
    if method == "initialize":
        client_version = body.get("params", {}).get("protocolVersion", "2024-11-05")
        session_id = secrets.token_urlsafe(32)
        _mcp_http_sessions[session_id] = (
            slug,
            _token_digest(token),
            time.monotonic() + MCP_SESSION_TTL_SECONDS,
        )
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": client_version,
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": gateway.config.name,
                        "version": __version__
                    }
                }
            },
            headers={"mcp-session-id": session_id}
        )

    if not _validate_mcp_session(request, slug, token):
        return _jsonrpc_error(req_id, -32001, "Sessão MCP ausente, expirada ou inválida.", 401)

    if method == "notifications/initialized":
        return Response(status_code=204)

    # Descoberta de ferramentas
    if method == "tools/list":
        tools_res = await gateway._handle_list_tools(None)
        serialized_tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.input_schema or {"type": "object", "properties": {}},
            }
            for t in tools_res.tools
        ]
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": serialized_tools
                }
            }
        )

    # Execução de ferramentas
    if method == "tools/call":
        params = body.get("params", {})
        import mcp.types as types
        call_params = types.CallToolRequestParams(
            name=params.get("name", ""),
            arguments=params.get("arguments", {})
        )
        call_res = await gateway._handle_call_tool(None, call_params)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": c.text} for c in call_res.content if hasattr(c, "text")
                    ],
                    "isError": call_res.is_error
                }
            }
        )

    if method == "ping":
        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {}})

    return JSONResponse(
        status_code=404,
        content={
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Método '{method}' não suportado pelo gateway."
            }
        }
    )


@app.post("/mcp/{slug}/messages")
async def handle_instance_messages(slug: str, request: Request) -> Response:
    gateway = gateway_manager.get_instance(slug)
    if not gateway:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada.")

    token = _bearer_token(request)
    if not gateway.validate_token(token):
        raise HTTPException(status_code=401, detail="Token de instância ausente ou inválido.")

    await gateway.sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
    return Response()


@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def dashboard_view() -> str:
    """Renderiza a interface administrativa web do Central."""
    return DASHBOARD_HTML
