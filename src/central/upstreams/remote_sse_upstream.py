"""
Cliente upstream para servidores MCP remotos via SSE/HTTP (ex: Periskope).
"""

import asyncio
import logging
import os
from typing import Any
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from central.models import UpstreamAuthConfig
from central.upstreams.base import BaseUpstream

logger = logging.getLogger(__name__)


class RemoteSseUpstream(BaseUpstream):
    def __init__(
        self,
        connection_id: str,
        prefix: str,
        url: str,
        auth: UpstreamAuthConfig | None = None,
    ):
        super().__init__(connection_id, prefix)
        self.url = url
        self.auth = auth
        self._cached_tools: list[types.Tool] = []
        self._is_healthy = False
        self._lock = asyncio.Lock()

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth and self.auth.type == "header":
            header_name = self.auth.header_name or "Authorization"
            env_var = self.auth.header_value_env
            val = os.environ.get(env_var, "") if env_var else ""
            if val:
                if header_name.lower() == "authorization" and not val.lower().startswith("bearer "):
                    headers[header_name] = f"Bearer {val}"
                else:
                    headers[header_name] = val
        return headers

    async def start(self) -> None:
        """Tenta conectar e descobrir as ferramentas do MCP remoto."""
        logger.info(f"[{self.connection_id}] Conectando ao upstream remoto SSE: {self.url}")
        try:
            tools = await self._discover_tools()
            self._cached_tools = tools
            self._is_healthy = True
            logger.info(f"[{self.connection_id}] Conectado com sucesso. Ferramentas descobertas: {len(tools)}")
        except Exception as e:
            self._is_healthy = False
            logger.warning(
                f"[{self.connection_id}] Não foi possível conectar ao upstream remoto ({e}). "
                f"Verifique se o endpoint e as credenciais ({self.auth.header_value_env if self.auth else 'N/A'}) estão ativos."
            )

    async def stop(self) -> None:
        self._is_healthy = False

    async def is_healthy(self) -> bool:
        return self._is_healthy

    async def _discover_tools(self) -> list[types.Tool]:
        headers = self._get_headers()
        async with sse_client(self.url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools

    async def list_tools(self) -> list[types.Tool]:
        if not self._cached_tools:
            try:
                self._cached_tools = await self._discover_tools()
                self._is_healthy = True
            except Exception as e:
                logger.error(f"[{self.connection_id}] Erro ao listar ferramentas remotas: {e}")
                self._is_healthy = False
                return []
        return self._cached_tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        async with self._lock:
            headers = self._get_headers()
            try:
                async with sse_client(self.url, headers=headers) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(name=name, arguments=arguments or {})
                        return result
            except Exception as e:
                logger.error(f"[{self.connection_id}] Erro ao executar ferramenta remota '{name}': {e}")
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Erro na execução da ferramenta remota ({self.connection_id}): {str(e)}"
                        )
                    ]
                )
