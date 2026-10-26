"""
Servidor FastAPI e rotas do Epyatis MCP Central (Fase 1: MVP Estruturado & UI).
"""

from contextlib import asynccontextmanager
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from central.api.routes import api_router, auth_router
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
    version="0.3.0",
    description="Centralized MCP gateway and management platform",
    lifespan=lifespan,
)

# Hardening de Cabeçalhos e CORS (SEC-06)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=getattr(settings, "ALLOWED_HOSTS", ["*"]),
)

# Registra rotas de autenticação e API administrativa (v1)
app.include_router(auth_router)
app.include_router(api_router)



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
        "version": "0.2.0",
        "instances": instances_status,
    }


@app.get("/mcp/{slug}/sse")
async def handle_instance_sse(slug: str, request: Request) -> Response:
    gateway = gateway_manager.get_instance(slug)
    if not gateway:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada.")

    # Dual-auth: Query param (?token=...) ou Header (Authorization: Bearer ...)
    token = request.query_params.get("token")
    auth_header = request.headers.get("authorization")
    if not token and auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

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

    # Dual-auth: Query param (?token=...) ou Header (Authorization: Bearer ...)
    token = request.query_params.get("token")
    auth_header = request.headers.get("authorization")
    if not token and auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not gateway.validate_token(token):
        logger.warning(f"[Security] Tentativa de conexão não autorizada na instância '{slug}'.")
        raise HTTPException(status_code=401, detail="Token de instância ausente ou inválido.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corpo da requisição deve ser um JSON válido.")

    method = body.get("method")
    req_id = body.get("id")

    # Handshake de inicialização
    if method == "initialize":
        client_version = body.get("params", {}).get("protocolVersion", "2024-11-05")
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
                        "version": "0.2.0"
                    }
                }
            },
            headers={"mcp-session-id": "central-session-1"}
        )

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

    await gateway.sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
    return Response()


@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def dashboard_view() -> str:
    """Renderiza a interface administrativa web do Central."""
    return DASHBOARD_HTML
