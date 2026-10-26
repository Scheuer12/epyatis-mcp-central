"""
Entidades relacionais do Epyatis MCP Central (SQLAlchemy 2.0).
"""

from datetime import datetime, timezone
import json
import uuid
from typing import Any
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from central.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class UserEntity(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=True)
    role = Column(String(32), default="standard", nullable=False)  # epy_root | standard
    password_hash = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    connections = relationship("ConnectionEntity", back_populates="user", cascade="all, delete-orphan")
    instances = relationship("InstanceEntity", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSessionEntity", back_populates="user", cascade="all, delete-orphan")


class UserSessionEntity(Base):
    __tablename__ = "user_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("UserEntity", back_populates="sessions")


class ConnectionEntity(Base):
    __tablename__ = "connections"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False, default="stdio")
    prefix = Column(String(32), nullable=False, index=True)
    visibility = Column(String(32), default="shared", nullable=False, index=True)  # private | shared | public
    command = Column(String(256), nullable=True)  # ex: npx
    args_json = Column(Text, nullable=True, default="[]")  # lista de argumentos JSON
    env_json = Column(Text, nullable=True, default="{}")  # variaveis de ambiente JSON
    url = Column(String(512), nullable=True)  # url para remote_mcp
    auth_config_json = Column(Text, nullable=True, default="{}")
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(32), default="healthy", nullable=False)  # healthy | error | unconfigured
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("UserEntity", back_populates="connections")
    tools = relationship("ToolEntity", back_populates="connection", cascade="all, delete-orphan")
    instance_associations = relationship("InstanceConnectionEntity", back_populates="connection", cascade="all, delete-orphan")

    @property
    def args(self) -> list[str]:
        try:
            return json.loads(self.args_json or "[]")
        except Exception:
            return []

    @args.setter
    def args(self, val: list[str]) -> None:
        self.args_json = json.dumps(val or [])

    @property
    def env(self) -> dict[str, str]:
        from central.security.crypto import decrypt_json_dict
        return decrypt_json_dict(self.env_json)

    @env.setter
    def env(self, val: dict[str, str]) -> None:
        from central.security.crypto import encrypt_json_dict
        self.env_json = encrypt_json_dict(val or {})

    @property
    def auth_config(self) -> dict[str, Any]:
        from central.security.crypto import decrypt_json_dict
        return decrypt_json_dict(self.auth_config_json)

    @auth_config.setter
    def auth_config(self, val: dict[str, Any]) -> None:
        from central.security.crypto import encrypt_json_dict
        self.auth_config_json = encrypt_json_dict(val or {})



class ToolEntity(Base):
    __tablename__ = "tools"

    id = Column(String(128), primary_key=True)  # ex: conn_gdrive__read_file
    connection_id = Column(String(64), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(128), nullable=False)  # ex: read_file
    namespaced_name = Column(String(128), nullable=False, index=True)  # ex: gdrive__read_file
    title = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    input_schema_json = Column(Text, nullable=True, default="{}")
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    connection = relationship("ConnectionEntity", back_populates="tools")
    instance_tools = relationship("InstanceToolEntity", back_populates="tool", cascade="all, delete-orphan")

    @property
    def input_schema(self) -> dict[str, Any]:
        try:
            return json.loads(self.input_schema_json or "{}")
        except Exception:
            return {"type": "object", "properties": {}}

    @input_schema.setter
    def input_schema(self, val: dict[str, Any]) -> None:
        self.input_schema_json = json.dumps(val or {})


class InstanceEntity(Base):
    __tablename__ = "instances"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    visibility = Column(String(32), default="shared", nullable=False, index=True)  # private | shared | public
    is_active = Column(Boolean, default=True, nullable=False)
    data_sources_map_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("UserEntity", back_populates="instances")
    tokens = relationship("InstanceTokenEntity", back_populates="instance", cascade="all, delete-orphan")
    connection_associations = relationship("InstanceConnectionEntity", back_populates="instance", cascade="all, delete-orphan")
    tool_associations = relationship("InstanceToolEntity", back_populates="instance", cascade="all, delete-orphan")

    @property
    def data_sources_map(self) -> dict[str, Any] | None:
        if not self.data_sources_map_json:
            return None
        try:
            return json.loads(self.data_sources_map_json)
        except Exception:
            return None

    @data_sources_map.setter
    def data_sources_map(self, val: dict[str, Any] | None) -> None:
        self.data_sources_map_json = json.dumps(val) if val else "{}"


class InstanceConnectionEntity(Base):
    __tablename__ = "instance_connections"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    instance_id = Column(String(64), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(String(64), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)

    instance = relationship("InstanceEntity", back_populates="connection_associations")
    connection = relationship("ConnectionEntity", back_populates="instance_associations")


class InstanceToolEntity(Base):
    __tablename__ = "instance_tools"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    instance_id = Column(String(64), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(String(128), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)

    instance = relationship("InstanceEntity", back_populates="tool_associations")
    tool = relationship("ToolEntity", back_populates="instance_tools")


class InstanceTokenEntity(Base):
    __tablename__ = "instance_tokens"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    instance_id = Column(String(64), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(128), nullable=False, index=True)
    label = Column(String(128), nullable=False, default="Connector Token")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    instance = relationship("InstanceEntity", back_populates="tokens")


class AuditLogEntity(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    instance_slug = Column(String(64), nullable=False, index=True)
    client_ip = Column(String(64), nullable=True)
    tool_name = Column(String(128), nullable=False, index=True)
    arguments_summary = Column(Text, nullable=True)
    status = Column(String(32), default="success", nullable=False)  # success | error
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)


class ConnectionTemplateEntity(Base):
    __tablename__ = "connection_templates"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True, default="")
    type = Column(String(32), default="stdio", nullable=False)  # stdio | remote_mcp | openapi | internal
    prefix = Column(String(32), nullable=False)
    command = Column(String(256), nullable=True)
    args_json = Column(Text, nullable=True, default="[]")
    env_json = Column(Text, nullable=True, default="{}")
    auth_config_json = Column(Text, nullable=True, default="{}")
    visibility = Column(String(32), default="shared", nullable=False, index=True)  # private | shared | public
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("UserEntity")

    @property
    def args(self) -> list[str]:
        try:
            return json.loads(self.args_json or "[]")
        except Exception:
            return []

    @args.setter
    def args(self, val: list[str]) -> None:
        self.args_json = json.dumps(val or [])

    @property
    def env(self) -> dict[str, str]:
        from central.security.crypto import decrypt_json_dict
        return decrypt_json_dict(self.env_json)

    @env.setter
    def env(self, val: dict[str, str]) -> None:
        from central.security.crypto import encrypt_json_dict
        self.env_json = encrypt_json_dict(val or {})

    @property
    def auth_config(self) -> dict[str, Any]:
        from central.security.crypto import decrypt_json_dict
        return decrypt_json_dict(self.auth_config_json)

    @auth_config.setter
    def auth_config(self, val: dict[str, Any]) -> None:
        from central.security.crypto import encrypt_json_dict
        self.auth_config_json = encrypt_json_dict(val or {})


class DataSourceKitEntity(Base):
    __tablename__ = "data_source_kits"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True, default="")
    category = Column(String(64), default="Geral", nullable=False)
    sources_json = Column(Text, nullable=False, default="[]")
    visibility = Column(String(32), default="shared", nullable=False, index=True)  # private | shared | public
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("UserEntity")

    @property
    def sources(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.sources_json or "[]")
        except Exception:
            return []

    @sources.setter
    def sources(self, val: list[dict[str, Any]]) -> None:
        self.sources_json = json.dumps(val or [], ensure_ascii=False)
