"""
Cliente upstream para servidores MCP locais executados via subprocesso Stdio (ex: Google Drive).
"""

import asyncio
import logging
import os
import shutil
from typing import Any
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from central.security.validation import validate_stdio_command
from central.upstreams.base import BaseUpstream

logger = logging.getLogger(__name__)


class StdioUpstream(BaseUpstream):
    def __init__(
        self,
        connection_id: str,
        prefix: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ):
        super().__init__(connection_id, prefix)
        validate_stdio_command(command, args)
        self.command = command
        self.args = args or []
        self.custom_env = env or {}
        self._cached_tools: list[types.Tool] = []
        self._is_healthy = False
        self._lock = asyncio.Lock()


    def _resolve_command(self) -> str:
        """Resolve o executável no Windows (ex: npx -> npx.cmd)."""
        resolved = shutil.which(self.command)
        if resolved:
            return resolved
        if os.name == "nt" and not self.command.endswith((".cmd", ".exe", ".bat")):
            for ext in (".cmd", ".exe", ".bat"):
                candidate = shutil.which(f"{self.command}{ext}")
                if candidate:
                    return candidate
        return self.command

    def _get_server_params(self) -> StdioServerParameters:
        merged_env = os.environ.copy()
        merged_env.update(self.custom_env)
        cmd = self._resolve_command()
        return StdioServerParameters(
            command=cmd,
            args=self.args,
            env=merged_env,
        )

    async def start(self) -> None:
        """Inicializa e descobre as ferramentas iniciais do servidor MCP local."""
        logger.info(f"[{self.connection_id}] Iniciando upstream Stdio: {self.command} {' '.join(self.args)}")
        try:
            tools = await self._discover_tools()
            self._cached_tools = tools
            self._is_healthy = True
            logger.info(f"[{self.connection_id}] Conectado com sucesso. Ferramentas descobertas: {len(tools)}")
        except Exception as e:
            self._is_healthy = False
            logger.warning(
                f"[{self.connection_id}] Falha ao conectar ao upstream Stdio ({e}). "
                f"Verifique se as credenciais e dependências locais estão configuradas."
            )

    async def stop(self) -> None:
        self._is_healthy = False

    async def is_healthy(self) -> bool:
        return self._is_healthy

    async def _discover_tools(self) -> list[types.Tool]:
        server_params = self._get_server_params()
        async with stdio_client(server_params) as (read, write):
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
                logger.error(f"[{self.connection_id}] Erro ao listar ferramentas: {e}")
                self._is_healthy = False
                return []
        return self._cached_tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        async with self._lock:
            server_params = self._get_server_params()
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(name=name, arguments=arguments or {})
                        return result
            except Exception as e:
                logger.error(f"[{self.connection_id}] Erro ao executar ferramenta '{name}': {e}")
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Erro na execução da ferramenta upstream ({self.connection_id}): {str(e)}"
                        )
                    ]
                )
