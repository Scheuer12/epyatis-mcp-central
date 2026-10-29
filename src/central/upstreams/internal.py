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
    def __init__(
        self,
        connection_id: str,
        prefix: str,
        data_sources_map: DataSourcesMap | None = None,
        instance_slug: str | None = None,
    ):
        super().__init__(connection_id, prefix)
        self.data_sources_map = data_sources_map
        self.instance_slug = instance_slug

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
                    "Retorna o Mapa de Fontes de Dados Operacionais completo da organização. "
                    "Use esta ferramenta para descobrir em qual sistema externo "
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
            ),
            types.Tool(
                name="search_data_sources",
                description=(
                    "Descobre nós de fontes de dados operacionais autorizadas através de metadados leves "
                    "(propósito de negócio, tags, sistema, autoridade e status). "
                    "Permite localizar fontes autorizadas (grupos de WhatsApp, planilhas, pastas) sem carregar definições completas no contexto."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "purpose": {
                            "type": "string",
                            "description": "Filtro opcional por propósito de negócio da fonte (ex: 'procurement_communications', 'procurement_tracking')."
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista opcional de tags. Múltiplas tags utilizam semântica AND (todas devem estar presentes na fonte)."
                        },
                        "system": {
                            "type": "string",
                            "description": "Filtro opcional pelo sistema upstream (ex: 'periskope', 'gdrive', 'postgres')."
                        },
                        "authority": {
                            "type": "string",
                            "description": "Filtro opcional pelo nível de autoridade (ex: 'official', 'candidate', 'deprecated', 'external')."
                        },
                        "status": {
                            "type": "string",
                            "description": "Filtro opcional pelo status operacional (ex: 'active', 'deprecated', 'maintenance', 'archived')."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="get_data_source",
                description=(
                    "Recupera a definição operacional completa de uma fonte de dados específica pelo seu ID estável "
                    "(inclui identificador nativo verificado, ferramentas primárias, parâmetros padrão de consulta, tipo de recurso e diretrizes)."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "source_id": {
                            "type": "string",
                            "description": "Identificador estável e único da fonte de dados (ex: 'example.procurement.messages.primary')."
                        }
                    },
                    "required": ["source_id"]
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        # Normaliza o nome da ferramenta caso venha com o prefixo
        clean_name = name
        if clean_name.startswith(f"{self.prefix}__"):
            clean_name = clean_name[len(f"{self.prefix}__"):]

        if clean_name == "ping":
            now_iso = datetime.now(timezone.utc).isoformat()
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Pong! Epyatis MCP Central ativo e operacional. Timestamp: {now_iso}"
                    )
                ]
            )

        if clean_name == "get_data_sources_map":
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

        if clean_name == "search_data_sources":
            if not self.data_sources_map:
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=json.dumps({"sources": [], "count": 0}, ensure_ascii=False, indent=2)
                        )
                    ]
                )

            args = arguments or {}
            purpose = args.get("purpose")
            tags = args.get("tags")
            # Tolerância se tags vier como string única ou separada por vírgula
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]

            system = args.get("system")
            authority = args.get("authority")
            status = args.get("status")

            matched = self.data_sources_map.search_sources(
                purpose=purpose,
                tags=tags,
                system=system,
                authority=authority,
                status=status,
            )

            # Retorna apenas descritores leves para economia de contexto
            lightweight = [
                {
                    "id": s.ensure_id(),
                    "name": s.name,
                    "purpose": s.purpose,
                    "system": s.system,
                    "tags": s.tags,
                    "authority": s.authority,
                    "status": s.status,
                }
                for s in matched
            ]

            result = {
                "sources": lightweight,
                "count": len(lightweight),
            }

            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2)
                    )
                ]
            )

        if clean_name == "get_data_source":
            if not self.data_sources_map:
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=json.dumps({
                                "found": False,
                                "error": "not_found",
                                "message": "Nenhum Mapa de Fontes de Dados configurado para esta instância."
                            }, ensure_ascii=False, indent=2)
                        )
                    ]
                )

            args = arguments or {}
            source_id = (args.get("source_id") or "").strip()
            if not source_id:
                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=json.dumps({
                                "found": False,
                                "error": "missing_parameter",
                                "message": "O parâmetro 'source_id' é obrigatório para recuperar os detalhes da fonte."
                            }, ensure_ascii=False, indent=2)
                        )
                    ]
                )

            src = self.data_sources_map.get_source(source_id)
            if not src:
                # Verifica correspondência ambígua caso tenha sido passado identificador parcial
                partial_matches = [
                    s.ensure_id() for s in self.data_sources_map.sources
                    if source_id.lower() in s.ensure_id().lower() or source_id.lower() in s.name.lower()
                ]
                if len(partial_matches) > 1:
                    return types.CallToolResult(
                        is_error=True,
                        content=[
                            types.TextContent(
                                type="text",
                                text=json.dumps({
                                    "found": False,
                                    "error": "ambiguous_source_id",
                                    "message": f"Identificador '{source_id}' é ambíguo. Várias fontes correspondem.",
                                    "candidate_ids": partial_matches
                                }, ensure_ascii=False, indent=2)
                            )
                        ]
                    )

                return types.CallToolResult(
                    is_error=True,
                    content=[
                        types.TextContent(
                            type="text",
                            text=json.dumps({
                                "found": False,
                                "error": "not_found",
                                "source_id": source_id,
                                "message": f"Fonte de dados com ID '{source_id}' não foi encontrada no registro operacional desta instância."
                            }, ensure_ascii=False, indent=2)
                        )
                    ]
                )

            # Definição operacional completa da fonte selecionada
            detail = {
                "found": True,
                "id": src.ensure_id(),
                "name": src.name,
                "description": src.description,
                "purpose": src.purpose,
                "system": src.system,
                "tags": src.tags,
                "authority": src.authority,
                "status": src.status,
                "resource_type": src.resource_type,
                "native_resource_id": src.native_resource_id,
                "primary_tools": src.primary_tools,
                "default_query_params": src.default_query_params,
                "historical_or_alternative_sources": src.historical_or_alternative_sources,
                "version": src.version,
                "last_updated": src.last_updated,
                "guidance": src.guidance,
                "content_types": src.content_types,
            }
            # Fornece tanto campos na raiz quanto chave 'source' para compatibilidade total
            result_payload = {**detail, "source": detail}

            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(result_payload, ensure_ascii=False, indent=2)
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
