"""
Cliente upstream para servidores MCP locais executados via subprocesso Stdio (ex: Google Drive).
Aplica isolamento de variáveis de ambiente e timeout de execução.
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

# Variáveis do sistema permitidas para execução de processos filhos
SAFE_ENV_ALLOWLIST = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "COMMONPROGRAMFILES",
    "HOME",
    "USER",
    "LANG",
    "LC_ALL",
}

BLOCKED_ENV_PREFIXES = ("CENTRAL_", "EPY_")
BLOCKED_ENV_EXACT = {"DATABASE_URL", "DB_PATH"}


class StdioUpstream(BaseUpstream):
    def __init__(
        self,
        connection_id: str,
        prefix: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 60.0,
    ):
        super().__init__(connection_id, prefix)
        validate_stdio_command(command, args)
        self.command = command
        self.args = args or []
        self.custom_env = env or {}
        self.timeout_seconds = timeout_seconds
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
        """
        Gera parâmetros de subprocesso com ambiente sanitizado.
        Bloqueia a herança inadvertida de segredos mestres (CENTRAL_*, DATABASE_URL)
        """
        sanitized_env: dict[str, str] = {}

        # 1. Copia apenas variáveis seguras de sistema do host
        for key, val in os.environ.items():
            if key.upper() in SAFE_ENV_ALLOWLIST:
                sanitized_env[key] = val

        # 2. Injeta variáveis explicitamente configuradas para a conexão
        for k, v in self.custom_env.items():
            # Bloqueia qualquer tentativa de sobrescrever segredos internos do Central
            if any(k.upper().startswith(p) for p in BLOCKED_ENV_PREFIXES) or k.upper() in BLOCKED_ENV_EXACT:
                logger.warning(f"[{self.connection_id}] Tentativa de injetar variável de ambiente proibida bloqueada: {k}")
                continue
            sanitized_env[k] = str(v)

        cmd = self._resolve_command()
        return StdioServerParameters(
            command=cmd,
            args=self.args,
            env=sanitized_env,
        )

    async def start(self) -> None:
        """Inicializa e descobre as ferramentas iniciais do servidor MCP local."""
        logger.info(f"[{self.connection_id}] Iniciando upstream Stdio: {self.command} {' '.join(self.args)}")
        try:
            tools = await asyncio.wait_for(self._discover_tools(), timeout=self.timeout_seconds)
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
                self._cached_tools = await asyncio.wait_for(self._discover_tools(), timeout=self.timeout_seconds)
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
                async def _invoke() -> types.CallToolResult:
                    async with stdio_client(server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(name=name, arguments=arguments or {})
                            return result

                return await asyncio.wait_for(_invoke(), timeout=self.timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"[{self.connection_id}] Timeout ({self.timeout_seconds}s) ao executar ferramenta '{name}'")
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Timeout na execução da ferramenta upstream ({self.connection_id}): excedeu {self.timeout_seconds}s"
                        )
                    ]
                )
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
