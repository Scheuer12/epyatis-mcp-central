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
    name: str
    system: str
    content_types: list[str] = Field(default_factory=list)
    primary_tools: list[str] = Field(default_factory=list)
    guidance: str


class DataSourcesMap(BaseModel):
    organization: str
    sources: list[DataSourceItem] = Field(default_factory=list)


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
