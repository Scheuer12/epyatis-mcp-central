"""
Ferramentas nativas internas do Epyatis MCP Central.
"""

from datetime import datetime, timezone
from typing import Any
import json
import mcp.types as types

from central.models import DataSourcesMap
from central.upstreams.base import BaseUpstream


class InternalUpstream(BaseUpstream):
    def __init__(self, connection_id: str, prefix: str, data_sources_map: DataSourcesMap | None = None):
        super().__init__(connection_id, prefix)
        self.data_sources_map = data_sources_map

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def is_healthy(self) -> bool:
        return True

    async def list_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="ping",
                description="Testa a conectividade com o Epyatis MCP Central e retorna o status do gateway.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="get_data_sources_map",
                description=(
                    "Retorna o Mapa de Fontes de Dados Operacionais da organização. "
                    "Use esta ferramenta para descobrir em qual sistema (Google Drive, Periskope, etc.) "
                    "e em quais ferramentas determinadas informações corporativas estão armazenadas."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Filtro opcional por categoria (ex: 'financeiro', 'whatsapp', 'documentos')."
                        }
                    },
                    "required": []
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        if name == "ping":
            now_iso = datetime.now(timezone.utc).isoformat()
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Pong! Epyatis MCP Central ativo e operacional. Timestamp: {now_iso}"
                    )
                ]
            )

        if name == "get_data_sources_map":
            if not self.data_sources_map:
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="Nenhum Mapa de Fontes de Dados configurado para esta instância."
                        )
                    ]
                )

            category = (arguments or {}).get("category", "").lower()
            sources = self.data_sources_map.sources
            if category:
                sources = [
                    s for s in sources
                    if category in s.name.lower()
                    or any(category in ct.lower() for ct in s.content_types)
                ]

            result_dict = {
                "organization": self.data_sources_map.organization,
                "sources": [s.model_dump() for s in sources]
            }

            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(result_dict, ensure_ascii=False, indent=2)
                    )
                ]
            )

        return types.CallToolResult(
            is_error=True,
            content=[
                types.TextContent(
                    type="text",
                    text=f"Ferramenta interna '{name}' não encontrada."
                )
            ]
        )
