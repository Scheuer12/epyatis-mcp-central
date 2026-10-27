"""
Modelos de dados para instâncias, conexões e ferramentas no Epyatis MCP Central.
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class UpstreamAuthConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "none"
    header_name: str | None = None
    header_value_env: str | None = None
    query_param_name: str | None = None
    query_param_value_env: str | None = None



class UpstreamConnectionConfig(BaseModel):
    id: str
    enabled: bool = True
    type: Literal["internal", "stdio", "remote_mcp", "openapi"] = "internal"
    prefix: str
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    auth: UpstreamAuthConfig | None = None


class DataSourceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str
    description: str = ""
    purpose: str = ""
    system: str
    tags: list[str] = Field(default_factory=list)
    authority: str = "official"  # official | candidate | deprecated | external
    status: str = "active"  # active | deprecated | maintenance | archived
    resource_type: str = "unspecified"  # whatsapp_group | spreadsheet | folder | database_table | document | api | other
    native_resource_id: str | None = None
    primary_tools: list[str] = Field(default_factory=list)
    default_query_params: dict[str, Any] = Field(default_factory=dict)
    historical_or_alternative_sources: list[str] = Field(default_factory=list)
    version: str = "1.0"
    last_updated: str | None = None
    content_types: list[str] = Field(default_factory=list)
    guidance: str = ""

    def ensure_id(self) -> str:
        """Garante que a fonte possua um ID estável se estiver vazio."""
        if not self.id:
            import re
            clean_name = re.sub(r'[^a-z0-9]+', '.', self.name.lower()).strip('.')
            clean_sys = re.sub(r'[^a-z0-9]+', '.', self.system.lower()).strip('.')
            self.id = f"{clean_sys}.{clean_name}" if clean_sys else clean_name
        return self.id


class DataSourcesMap(BaseModel):
    model_config = ConfigDict(extra="allow")

    organization: str
    sources: list[DataSourceItem] = Field(default_factory=list)
    version: str = "1.0"
    last_updated: str | None = None

    def get_source(self, source_id: str) -> DataSourceItem | None:
        for s in self.sources:
            if s.ensure_id() == source_id or s.id == source_id:
                return s
        return None

    def search_sources(
        self,
        purpose: str | None = None,
        tags: list[str] | None = None,
        system: str | None = None,
        authority: str | None = None,
        status: str | None = None,
    ) -> list[DataSourceItem]:
        results: list[DataSourceItem] = []
        for s in self.sources:
            s.ensure_id()

            if purpose and purpose.strip():
                p_query = purpose.strip().lower()
                p_val = (s.purpose or "").lower()
                if p_query not in p_val and p_query != p_val:
                    continue

            if tags:
                s_tags_lower = [t.lower() for t in s.tags]
                if not all(t.strip().lower() in s_tags_lower for t in tags if t.strip()):
                    continue

            if system and system.strip():
                if s.system.lower() != system.strip().lower():
                    continue

            if authority and authority.strip():
                if s.authority.lower() != authority.strip().lower():
                    continue

            if status and status.strip():
                if s.status.lower() != status.strip().lower():
                    continue

            results.append(s)
        return results


class InstanceToken(BaseModel):
    token: str
    label: str


class InstanceConfig(BaseModel):
    id: str
    name: str
    slug: str
    description: str = ""
    tokens: list[InstanceToken] = Field(default_factory=list)
    data_sources_map: DataSourcesMap | None = None
    connections: list[UpstreamConnectionConfig] = Field(default_factory=list)


class CentralBootstrapConfig(BaseModel):
    instances: list[InstanceConfig] = Field(default_factory=list)
