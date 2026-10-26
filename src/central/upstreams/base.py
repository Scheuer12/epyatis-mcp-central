"""
Interface base para Upstreams MCP (locais via Stdio, remotos via SSE/HTTP ou internos).
"""

from abc import ABC, abstractmethod
from typing import Any
import mcp.types as types


class BaseUpstream(ABC):
    def __init__(self, connection_id: str, prefix: str):
        self.connection_id = connection_id
        self.prefix = prefix

    @abstractmethod
    async def start(self) -> None:
        """Inicializa e conecta ao upstream."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Encerra a conexão com o upstream."""
        pass

    @abstractmethod
    async def list_tools(self) -> list[types.Tool]:
        """Retorna as ferramentas oferecidas pelo upstream (sem prefixo)."""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        """Executa a ferramenta original (com o nome original sem prefixo)."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Verifica a saúde da conexão."""
        pass
