"""
Gateway de Instância: agrega conexões upstreams e expõe um servidor MCP SSE independente.
Suporta Stdio, Remote SSE, OpenAPI e filtragem granular de ferramentas por instância.
"""

import json
import logging
import time
from typing import Any
import mcp.types as types
from mcp.server.lowlevel.server import Server, ServerRequestContext
from mcp.server.sse import SseServerTransport
from mcp.server.transport_security import TransportSecuritySettings

from central.db.entities import InstanceEntity, InstanceToolEntity
from central.db.repository import CentralRepository
from central.db.session import get_db_context
from central.models import InstanceConfig
from central.upstreams.base import BaseUpstream
from central.upstreams.internal import InternalUpstream
from central.upstreams.openapi_upstream import OpenApiUpstream
from central.upstreams.remote_sse_upstream import RemoteSseUpstream
from central.upstreams.stdio_upstream import StdioUpstream

logger = logging.getLogger(__name__)


class InstanceGateway:
    def __init__(self, config: InstanceConfig):
        self.config = config
        self.slug = config.slug
        self.valid_tokens = {t.token for t in config.tokens}
        self.upstreams: dict[str, BaseUpstream] = {}
        self.tool_prefix_map: dict[str, str] = {}  # "gdrive" -> connection_id

        # Configura as conexões upstream definidas para esta instância
        self._init_upstreams()

        # Cria o servidor MCP nativo da instância
        self.mcp_server = Server(
            name=self.config.name,
            version="0.2.0",
            description=self.config.description,
            on_list_tools=self._handle_list_tools,
            on_call_tool=self._handle_call_tool,
        )

        # Transport SSE com proteção DNS permissiva para conexões locais/Paperclip
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"],
        )
        self.sse_transport = SseServerTransport(
            endpoint=f"/mcp/{self.slug}/messages",
            security_settings=security,
        )

    def _init_upstreams(self) -> None:
        for conn in self.config.connections:
            if not conn.enabled:
                continue

            prefix = conn.prefix
            self.tool_prefix_map[prefix] = conn.id

            if conn.type == "internal":
                self.upstreams[conn.id] = InternalUpstream(
                    connection_id=conn.id,
                    prefix=prefix,
                    data_sources_map=self.config.data_sources_map,
                )
            elif conn.type == "stdio":
                if conn.command:
                    self.upstreams[conn.id] = StdioUpstream(
                        connection_id=conn.id,
                        prefix=prefix,
                        command=conn.command,
                        args=conn.args,
                        env=conn.env,
                    )
            elif conn.type == "remote_mcp":
                if conn.url:
                    self.upstreams[conn.id] = RemoteSseUpstream(
                        connection_id=conn.id,
                        prefix=prefix,
                        url=conn.url,
                        auth=conn.auth,
                    )
            elif conn.type == "openapi":
                spec = conn.url or ""
                base_url = conn.url
                headers = {}
                if conn.auth:
                    auth_dict = conn.auth.model_dump() if hasattr(conn.auth, "model_dump") else conn.auth
                    if isinstance(auth_dict, dict):
                        spec = auth_dict.get("spec", conn.url or "")
                        base_url = auth_dict.get("base_url", conn.url)
                        headers = auth_dict.get("headers", {})
                self.upstreams[conn.id] = OpenApiUpstream(
                    connection_id=conn.id,
                    prefix=prefix,
                    spec=spec,
                    base_url=base_url,
                    auth_headers=headers,
                )

    async def start(self) -> None:
        logger.info(f"[Instance:{self.slug}] Iniciando upstreams...")
        for conn_id, upstream in self.upstreams.items():
            try:
                await upstream.start()
            except Exception as e:
                logger.error(f"[Instance:{self.slug}] Erro ao inicializar upstream {conn_id}: {e}")

    async def stop(self) -> None:
        for upstream in self.upstreams.values():
            await upstream.stop()

    def validate_token(self, token: str | None) -> bool:
        if not self.valid_tokens:
            logger.warning(f"[Instance:{self.slug}] Acesso negado: nenhum token configurado para esta instância (Fail-Closed).")
            return False
        return bool(token and token in self.valid_tokens)


    async def _handle_list_tools(
        self,
        ctx: ServerRequestContext[Any],
        params: types.PaginatedRequestParams | None = None,
    ) -> types.ListToolsResult:
        aggregated_tools: list[types.Tool] = []

        for conn_id, upstream in self.upstreams.items():
            try:
                tools = await upstream.list_tools()
                raw_tools_for_db: list[dict[str, Any]] = []

                for tool in tools:
                    # Aplica namespace de prefixo na ferramenta
                    prefixed_name = f"{upstream.prefix}__{tool.name}"
                    aggregated_tools.append(
                        types.Tool(
                            name=prefixed_name,
                            title=tool.title or prefixed_name,
                            description=f"[{upstream.prefix.upper()}] {tool.description or ''}",
                            input_schema=tool.input_schema,
                        )
                    )
                    raw_tools_for_db.append({
                        "name": tool.name,
                        "title": tool.title or prefixed_name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    })

                # Sincroniza ferramentas descobertas no banco de dados SQLite
                if raw_tools_for_db:
                    try:
                        with get_db_context() as db:
                            CentralRepository.sync_discovered_tools(db, conn_id, raw_tools_for_db)
                    except Exception as db_err:
                        logger.warning(f"[Instance:{self.slug}] Falha ao persistir tools de {conn_id} no DB: {db_err}")

            except Exception as e:
                logger.error(f"[Instance:{self.slug}] Falha ao agregar tools de {conn_id}: {e}")

        # Filtragem granular de ferramentas por instância (Allowlist / Toggles)
        disabled_identifiers: set[str] = set()
        try:
            with get_db_context() as db:
                inst_entity = db.query(InstanceEntity).filter(InstanceEntity.slug == self.slug).first()
                if inst_entity:
                    disabled_records = (
                        db.query(InstanceToolEntity)
                        .filter(
                            InstanceToolEntity.instance_id == inst_entity.id,
                            InstanceToolEntity.is_enabled == False,
                        )
                        .all()
                    )
                    for d in disabled_records:
                        disabled_identifiers.add(d.tool_id)
        except Exception as check_err:
            logger.warning(f"[Instance:{self.slug}] Falha ao consultar tools desabilitadas: {check_err}")

        filtered_tools: list[types.Tool] = []
        for tool in aggregated_tools:
            parts = tool.name.split("__", 1)
            prefix = parts[0]
            orig_name = parts[1] if len(parts) > 1 else ""
            conn_id = self.tool_prefix_map.get(prefix, prefix)
            tool_db_id = f"tool_{conn_id}_{orig_name}"

            if tool.name in disabled_identifiers or tool_db_id in disabled_identifiers:
                logger.debug(f"[Instance:{self.slug}] Omitindo ferramenta desabilitada: {tool.name}")
                continue

            filtered_tools.append(tool)

        logger.info(f"[Instance:{self.slug}] Total de ferramentas expostas ao cliente: {len(filtered_tools)} (agregadas: {len(aggregated_tools)})")
        return types.ListToolsResult(tools=filtered_tools)

    async def _handle_call_tool(
        self,
        ctx: ServerRequestContext[Any],
        params: types.CallToolRequestParams,
    ) -> types.CallToolResult:
        full_tool_name = params.name
        arguments = params.arguments or {}
        start_time = time.time()
        status = "success"
        error_msg: str | None = None

        logger.info(f"[Instance:{self.slug}] Invocação de ferramenta: {full_tool_name}")

        try:
            # Identifica o prefixo (ex: gdrive__read_file -> prefix="gdrive", original_name="read_file")
            if "__" not in full_tool_name:
                status = "error"
                error_msg = "Formato inválido: esperado 'prefixo__nome_da_tool'."
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Formato de ferramenta inválido '{full_tool_name}'. Esperado: 'prefixo__nome_da_tool'.",
                        )
                    ],
                )

            prefix, original_name = full_tool_name.split("__", 1)
            conn_id = self.tool_prefix_map.get(prefix)

            if not conn_id or conn_id not in self.upstreams:
                status = "error"
                error_msg = f"Nenhuma conexão configurada para o prefixo '{prefix}'."
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Nenhuma conexão configurada para o prefixo '{prefix}'.",
                        )
                    ],
                )

            # Verifica se a ferramenta está desabilitada para esta instância
            try:
                with get_db_context() as db:
                    inst_entity = db.query(InstanceEntity).filter(InstanceEntity.slug == self.slug).first()
                    if inst_entity:
                        tool_db_id = f"tool_{conn_id}_{original_name}"
                        disabled = (
                            db.query(InstanceToolEntity)
                            .filter(
                                InstanceToolEntity.instance_id == inst_entity.id,
                                InstanceToolEntity.tool_id.in_([full_tool_name, tool_db_id]),
                                InstanceToolEntity.is_enabled == False,
                            )
                            .first()
                        )
                        if disabled:
                            status = "error"
                            error_msg = f"A ferramenta '{full_tool_name}' está desabilitada para a instância '{self.slug}'."
                            return types.CallToolResult(
                                is_error=True,
                                content=[types.TextContent(type="text", text=error_msg)],
                            )
            except Exception as perm_err:
                logger.warning(f"[Instance:{self.slug}] Erro ao verificar permissão da tool: {perm_err}")

            upstream = self.upstreams[conn_id]
            res = await upstream.call_tool(original_name, arguments)
            if res.is_error:
                status = "error"
                error_parts = [c.text for c in res.content if hasattr(c, "text")]
                error_msg = "\n".join(error_parts) if error_parts else "Erro retornado pelo upstream."
            return res

        except Exception as exc:
            status = "error"
            error_msg = str(exc)
            logger.error(f"[Instance:{self.slug}] Exceção ao executar tool {full_tool_name}: {exc}", exc_info=True)
            return types.CallToolResult(
                is_error=True,
                content=[types.TextContent(type="text", text=f"Erro interno de execução: {exc}")],
            )

        finally:
            elapsed_ms = int((time.time() - start_time) * 1000)
            try:
                with get_db_context() as db:
                    args_summary = json.dumps(arguments, ensure_ascii=False)
                    if len(args_summary) > 500:
                        args_summary = args_summary[:497] + "..."

                    CentralRepository.log_audit_event(
                        db=db,
                        instance_slug=self.slug,
                        tool_name=full_tool_name,
                        status=status,
                        execution_time_ms=elapsed_ms,
                        arguments_summary=args_summary,
                        error_message=error_msg,
                    )
            except Exception as audit_err:
                logger.warning(f"[Instance:{self.slug}] Erro ao registrar log de auditoria: {audit_err}")
