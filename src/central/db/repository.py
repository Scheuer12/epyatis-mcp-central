"""
Repositório de dados para entidades do Epyatis MCP Central.
"""

from datetime import datetime, timezone
import json
import logging
import secrets
from typing import Any
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from central.db.entities import (
    AuditLogEntity,
    ConnectionEntity,
    ConnectionShareEntity,
    ConnectionTemplateEntity,
    DataSourceKitEntity,
    InstanceConnectionEntity,
    InstanceEntity,
    InstanceShareEntity,
    InstanceTokenEntity,
    InstanceToolEntity,
    ToolEntity,
    UserEntity,
    UserInviteEntity,
    UserSessionEntity,
)
from central.models import (
    DataSourceItem,
    DataSourcesMap,
    InstanceConfig,
    InstanceToken,
    UpstreamAuthConfig,
    UpstreamConnectionConfig,
)

logger = logging.getLogger(__name__)


class CentralRepository:
    """Acesso e mutação a instâncias, conexões, ferramentas e logs."""

    @staticmethod
    def get_all_instances(
        db: Session,
        active_only: bool = False,
        current_user: UserEntity | None = None,
        visibility: str | None = None,
    ) -> list[InstanceEntity]:
        query = db.query(InstanceEntity)
        if active_only:
            query = query.filter(InstanceEntity.is_active == True)  # noqa: E712

        if visibility:
            query = query.filter(InstanceEntity.visibility == visibility)

        if current_user and current_user.role != "epy_root":
            shared_instance_ids = db.query(InstanceShareEntity.instance_id).filter(
                InstanceShareEntity.user_id == current_user.id
            )
            query = query.filter(
                or_(
                    InstanceEntity.visibility == "public",
                    InstanceEntity.user_id == current_user.id,
                    (InstanceEntity.visibility == "shared") & InstanceEntity.id.in_(shared_instance_ids),
                )
            )

        return query.order_by(InstanceEntity.name).all()

    @staticmethod
    def get_instance_by_slug(db: Session, slug: str) -> InstanceEntity | None:
        return db.query(InstanceEntity).filter(InstanceEntity.slug == slug).first()

    @staticmethod
    def get_instance_by_id(db: Session, instance_id: str) -> InstanceEntity | None:
        return db.query(InstanceEntity).filter(InstanceEntity.id == instance_id).first()

    @staticmethod
    def create_instance(
        db: Session,
        name: str,
        slug: str,
        description: str = "",
        user_id: str | None = None,
        visibility: str = "shared",
        data_sources_map: dict[str, Any] | None = None,
    ) -> InstanceEntity:
        instance = InstanceEntity(
            id=slug,
            user_id=user_id,
            name=name,
            slug=slug,
            description=description,
            visibility=visibility,
            is_active=True,
            data_sources_map_json=json.dumps(data_sources_map) if data_sources_map else None,
        )
        db.add(instance)
        db.flush()

        # Adiciona um token inicial por padrão
        token_str = f"epy_{slug}_{secrets.token_hex(4)}"
        token = InstanceTokenEntity(
            instance_id=instance.id,
            token=token_str,
            label="Default Token",
        )
        db.add(token)
        db.commit()
        db.refresh(instance)
        return instance

    @staticmethod
    def update_instance(
        db: Session,
        instance: InstanceEntity,
        name: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
    ) -> InstanceEntity:
        if name is not None:
            instance.name = name
        if description is not None:
            instance.description = description
        if visibility is not None:
            instance.visibility = visibility
        db.commit()
        db.refresh(instance)
        return instance

    @staticmethod
    def delete_instance(db: Session, instance: InstanceEntity) -> None:
        db.query(InstanceTokenEntity).filter(InstanceTokenEntity.instance_id == instance.id).delete()
        db.query(InstanceConnectionEntity).filter(InstanceConnectionEntity.instance_id == instance.id).delete()
        db.delete(instance)
        db.commit()

    @staticmethod
    def attach_connection_to_instance(db: Session, instance_id: str, connection_id: str) -> InstanceConnectionEntity:
        assoc = (
            db.query(InstanceConnectionEntity)
            .filter(
                InstanceConnectionEntity.instance_id == instance_id,
                InstanceConnectionEntity.connection_id == connection_id,
            )
            .first()
        )
        if not assoc:
            assoc = InstanceConnectionEntity(
                instance_id=instance_id,
                connection_id=connection_id,
                is_enabled=True,
            )
            db.add(assoc)
        else:
            assoc.is_enabled = True
        db.commit()
        db.refresh(assoc)
        return assoc

    @staticmethod
    def detach_connection_from_instance(db: Session, instance_id: str, connection_id: str) -> None:
        db.query(InstanceConnectionEntity).filter(
            InstanceConnectionEntity.instance_id == instance_id,
            InstanceConnectionEntity.connection_id == connection_id,
        ).delete()
        db.commit()

    @staticmethod
    def update_connection_visibility(db: Session, connection: ConnectionEntity, visibility: str) -> ConnectionEntity:
        connection.visibility = visibility
        db.commit()
        db.refresh(connection)
        return connection

    @staticmethod
    def get_connection_shared_user_ids(db: Session, connection_id: str) -> list[str]:
        rows = db.query(ConnectionShareEntity.user_id).filter(ConnectionShareEntity.connection_id == connection_id).all()
        return [r[0] for r in rows]

    @staticmethod
    def set_connection_shares(db: Session, connection_id: str, user_ids: list[str]) -> list[str]:
        db.query(ConnectionShareEntity).filter(ConnectionShareEntity.connection_id == connection_id).delete()
        for uid in set(user_ids):
            if uid:
                db.add(ConnectionShareEntity(connection_id=connection_id, user_id=uid))
        db.commit()
        return list(set(user_ids))

    @staticmethod
    def get_instance_shared_user_ids(db: Session, instance_id: str) -> list[str]:
        rows = db.query(InstanceShareEntity.user_id).filter(InstanceShareEntity.instance_id == instance_id).all()
        return [r[0] for r in rows]

    @staticmethod
    def set_instance_shares(db: Session, instance_id: str, user_ids: list[str]) -> list[str]:
        db.query(InstanceShareEntity).filter(InstanceShareEntity.instance_id == instance_id).delete()
        for uid in set(user_ids):
            if uid:
                db.add(InstanceShareEntity(instance_id=instance_id, user_id=uid))
        db.commit()
        return list(set(user_ids))

    @staticmethod
    def delete_connection(db: Session, connection: ConnectionEntity) -> None:
        db.query(ToolEntity).filter(ToolEntity.connection_id == connection.id).delete()
        db.query(InstanceConnectionEntity).filter(InstanceConnectionEntity.connection_id == connection.id).delete()
        db.delete(connection)
        db.commit()

    @staticmethod
    def get_all_connections(
        db: Session,
        active_only: bool = False,
        current_user: UserEntity | None = None,
        visibility: str | None = None,
    ) -> list[ConnectionEntity]:
        query = db.query(ConnectionEntity)
        if active_only:
            query = query.filter(ConnectionEntity.is_active == True)  # noqa: E712

        if visibility:
            query = query.filter(ConnectionEntity.visibility == visibility)

        if current_user and current_user.role != "epy_root":
            shared_conn_ids = db.query(ConnectionShareEntity.connection_id).filter(
                ConnectionShareEntity.user_id == current_user.id
            )
            query = query.filter(
                or_(
                    ConnectionEntity.visibility == "public",
                    ConnectionEntity.user_id == current_user.id,
                    (ConnectionEntity.visibility == "shared") & ConnectionEntity.id.in_(shared_conn_ids),
                )
            )

        return query.order_by(ConnectionEntity.name).all()

    @staticmethod
    def get_connection_by_id(db: Session, connection_id: str) -> ConnectionEntity | None:
        return db.query(ConnectionEntity).filter(ConnectionEntity.id == connection_id).first()

    @staticmethod
    def create_or_update_connection(
        db: Session,
        connection_id: str,
        name: str,
        conn_type: str,
        prefix: str,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str | None = None,
        auth_config: dict[str, Any] | None = None,
        visibility: str = "shared",
        user_id: str | None = None,
    ) -> ConnectionEntity:
        conn = db.query(ConnectionEntity).filter(ConnectionEntity.id == connection_id).first()
        if not conn:
            conn = ConnectionEntity(
                id=connection_id,
                user_id=user_id,
                name=name,
                type=conn_type,
                prefix=prefix,
                command=command,
                args=args or [],
                env=env or {},
                url=url,
                auth_config=auth_config or {},
                visibility=visibility,
                is_active=True,
                health_status="healthy",
            )
            db.add(conn)
        else:
            conn.name = name
            conn.type = conn_type
            conn.prefix = prefix
            conn.command = command
            conn.args = args or []
            conn.env = env or {}
            conn.url = url
            conn.auth_config = auth_config or {}
            if visibility:
                conn.visibility = visibility
            if user_id:
                conn.user_id = user_id

        db.commit()
        db.refresh(conn)
        return conn

    @staticmethod
    def sync_discovered_tools(db: Session, connection_id: str, tools_data: list[dict[str, Any]]) -> int:
        """Sincroniza ferramentas descobertas de um upstream no banco de dados."""
        conn = db.query(ConnectionEntity).filter(ConnectionEntity.id == connection_id).first()
        if not conn:
            return 0

        synced_count = 0
        for t in tools_data:
            orig_name = t.get("name", "")
            namespaced = f"{conn.prefix}__{orig_name}"
            tool_id = f"tool_{conn.id}_{orig_name}"

            tool = db.query(ToolEntity).filter(ToolEntity.id == tool_id).first()
            if not tool:
                tool = ToolEntity(
                    id=tool_id,
                    connection_id=conn.id,
                    original_name=orig_name,
                    namespaced_name=namespaced,
                    title=t.get("title") or namespaced,
                    description=t.get("description", ""),
                    input_schema_json=json.dumps(t.get("inputSchema") or t.get("input_schema") or {}),
                    is_active=True,
                )
                db.add(tool)
            else:
                tool.title = t.get("title") or namespaced
                tool.description = t.get("description", "")
                tool.input_schema_json = json.dumps(t.get("inputSchema") or t.get("input_schema") or {})
                tool.is_active = True

            synced_count += 1

        db.commit()
        return synced_count

    @staticmethod
    def get_all_tools(
        db: Session,
        connection_id: str | None = None,
        query: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[ToolEntity], int]:
        q = db.query(ToolEntity)
        if connection_id:
            q = q.filter(ToolEntity.connection_id == connection_id)
        if query:
            pattern = f"%{query.lower()}%"
            q = q.filter(
                (func.lower(ToolEntity.namespaced_name).like(pattern))
                | (func.lower(ToolEntity.description).like(pattern))
            )

        total = q.count()
        tools = q.order_by(ToolEntity.namespaced_name).offset(offset).limit(limit).all()
        return tools, total

    @staticmethod
    def load_instance_configs_from_db(db: Session) -> list[InstanceConfig]:
        """Converte as entidades do SQLite em modelos InstanceConfig para o Gateway."""
        instances = db.query(InstanceEntity).filter(InstanceEntity.is_active == True).all()  # noqa: E712
        configs: list[InstanceConfig] = []

        for inst in instances:
            # Tokens
            tokens = [
                InstanceToken(token=t.token, label=t.label)
                for t in inst.tokens
            ]

            # Data Sources Map
            ds_map = None
            if inst.data_sources_map:
                try:
                    ds_dict = inst.data_sources_map
                    sources = [
                        DataSourceItem(
                            name=s.get("name", ""),
                            system=s.get("system", ""),
                            content_types=s.get("content_types", []),
                            primary_tools=s.get("primary_tools", []),
                            guidance=s.get("guidance", ""),
                        )
                        for s in ds_dict.get("sources", [])
                    ]
                    ds_map = DataSourcesMap(
                        organization=ds_dict.get("organization", inst.name),
                        sources=sources,
                    )
                except Exception as e:
                    logger.warning(f"Erro ao converter data sources map da instância {inst.slug}: {e}")

            # Conexões associadas
            connections: list[UpstreamConnectionConfig] = []
            for inst_conn in inst.connection_associations:
                if not inst_conn.is_enabled:
                    continue
                c = inst_conn.connection
                if not c or not c.is_active:
                    continue

                auth_cfg = None
                if c.auth_config:
                    auth_cfg = UpstreamAuthConfig(**c.auth_config)

                conn_cfg = UpstreamConnectionConfig(
                    id=c.id,
                    enabled=c.is_active,
                    type=c.type,  # type: ignore
                    prefix=c.prefix,
                    command=c.command,
                    args=c.args,
                    env=c.env,
                    url=c.url,
                    auth=auth_cfg,
                )
                connections.append(conn_cfg)

            config = InstanceConfig(
                id=inst.id,
                name=inst.name,
                slug=inst.slug,
                description=inst.description or "",
                tokens=tokens,
                data_sources_map=ds_map,
                connections=connections,
            )
            configs.append(config)

        return configs

    @staticmethod
    def log_audit_event(
        db: Session,
        instance_slug: str,
        tool_name: str,
        status: str,
        execution_time_ms: int,
        arguments_summary: str | None = None,
        error_message: str | None = None,
        client_ip: str | None = None,
    ) -> AuditLogEntity:
        log = AuditLogEntity(
            instance_slug=instance_slug,
            client_ip=client_ip,
            tool_name=tool_name,
            arguments_summary=arguments_summary,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def get_recent_audit_logs(db: Session, limit: int = 50) -> list[AuditLogEntity]:
        return (
            db.query(AuditLogEntity)
            .order_by(AuditLogEntity.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_system_overview(db: Session) -> dict[str, Any]:
        total_instances = db.query(InstanceEntity).count()
        active_instances = db.query(InstanceEntity).filter(InstanceEntity.is_active == True).count()  # noqa: E712
        total_connections = db.query(ConnectionEntity).count()
        total_tools = db.query(ToolEntity).count()
        total_calls = db.query(AuditLogEntity).count()
        error_calls = db.query(AuditLogEntity).filter(AuditLogEntity.status == "error").count()

        success_rate = 100.0 if total_calls == 0 else round(((total_calls - error_calls) / total_calls) * 100, 1)

        return {
            "total_instances": total_instances,
            "active_instances": active_instances,
            "total_connections": total_connections,
            "total_tools": total_tools,
            "total_calls": total_calls,
            "success_rate": success_rate,
        }

    @staticmethod
    def toggle_instance_tool(
        db: Session,
        instance_id: str,
        tool_id: str,
        is_enabled: bool,
    ) -> InstanceToolEntity:
        """Define se uma ferramenta está explicitamente habilitada ou desabilitada para uma instância."""
        assoc = (
            db.query(InstanceToolEntity)
            .filter(
                InstanceToolEntity.instance_id == instance_id,
                InstanceToolEntity.tool_id == tool_id,
            )
            .first()
        )
        if not assoc:
            assoc = InstanceToolEntity(
                instance_id=instance_id,
                tool_id=tool_id,
                is_enabled=is_enabled,
            )
            db.add(assoc)
        else:
            assoc.is_enabled = is_enabled

        db.commit()
        db.refresh(assoc)
        return assoc

    @staticmethod
    def update_instance_data_sources_map(
        db: Session,
        slug: str,
        data_sources_map: dict[str, Any],
    ) -> InstanceEntity | None:
        """Atualiza as diretrizes do Mapa de Fontes de Dados de uma instância."""
        instance = db.query(InstanceEntity).filter(InstanceEntity.slug == slug).first()
        if not instance:
            return None

        instance.data_sources_map_json = json.dumps(data_sources_map, ensure_ascii=False)
        db.commit()
        db.refresh(instance)
        return instance

    # --- Gestão de Usuários e Sessões ---

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> UserEntity | None:
        return db.query(UserEntity).filter(UserEntity.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> UserEntity | None:
        return db.query(UserEntity).filter(UserEntity.username == username).first()

    @staticmethod
    def get_all_users(db: Session) -> list[UserEntity]:
        return db.query(UserEntity).order_by(UserEntity.username).all()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        role: str = "standard",
        display_name: str | None = None,
        password_hash: str | None = None,
        status: str = "approved",
    ) -> UserEntity:
        is_active = (status == "approved")
        user = UserEntity(
            username=username,
            role=role,
            display_name=display_name or username,
            password_hash=password_hash,
            status=status,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_user_with_password(
        db: Session,
        username: str,
        password: str,
        role: str = "standard",
        display_name: str | None = None,
        status: str = "approved",
    ) -> UserEntity:
        from central.security.crypto import hash_password
        p_hash = hash_password(password) if password else None
        return CentralRepository.create_user(
            db=db,
            username=username,
            role=role,
            display_name=display_name,
            password_hash=p_hash,
            status=status,
        )

    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
    ) -> tuple[UserEntity | None, str | None]:
        from central.security.crypto import verify_password
        from central.config import settings

        user = db.query(UserEntity).filter(UserEntity.username == username).first()
        if not user:
            return None, "Usuário ou senha incorretos."

        if user.username == "epy_root" and not user.password_hash and settings.CENTRAL_ADMIN_KEY:
            if secrets.compare_digest(password, settings.CENTRAL_ADMIN_KEY):
                return user, None

        if not user.password_hash:
            return None, "Conta sem senha configurada. Utilize a chave administrativa."

        if not verify_password(password, user.password_hash):
            return None, "Usuário ou senha incorretos."

        if getattr(user, "status", "approved") == "pending_approval":
            return None, "Sua conta está aguardando aprovação pelo Master Admin."

        if getattr(user, "status", "approved") == "rejected":
            return None, "Sua solicitação de acesso foi rejeitada pelo administrador."

        if not user.is_active:
            return None, "Conta desativada."

        return user, None

    @staticmethod
    def create_invite(
        db: Session,
        created_by_user_id: str | None,
        expires_hours: int = 24,
        role: str = "standard",
    ) -> UserInviteEntity:
        from datetime import timedelta
        code = secrets.token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        invite = UserInviteEntity(
            code=code,
            created_by_user_id=created_by_user_id,
            role=role,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    @staticmethod
    def get_invite_by_code(db: Session, code: str) -> UserInviteEntity | None:
        return db.query(UserInviteEntity).filter(UserInviteEntity.code == code).first()

    @staticmethod
    def get_all_invites(db: Session, active_only: bool = False) -> list[UserInviteEntity]:
        q = db.query(UserInviteEntity)
        if active_only:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            q = q.filter(UserInviteEntity.is_used == False, UserInviteEntity.expires_at > now)
        return q.order_by(UserInviteEntity.created_at.desc()).all()

    @staticmethod
    def delete_invite(db: Session, code: str) -> bool:
        inv = db.query(UserInviteEntity).filter(UserInviteEntity.code == code).first()
        if inv:
            db.delete(inv)
            db.commit()
            return True
        return False

    @staticmethod
    def get_pending_users(db: Session) -> list[UserEntity]:
        return db.query(UserEntity).filter(UserEntity.status == "pending_approval").order_by(UserEntity.created_at.desc()).all()

    @staticmethod
    def approve_user(db: Session, user_id: str) -> UserEntity | None:
        user = db.query(UserEntity).filter(UserEntity.id == user_id).first()
        if user:
            user.status = "approved"
            user.is_active = True
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def reject_user(db: Session, user_id: str) -> UserEntity | None:
        user = db.query(UserEntity).filter(UserEntity.id == user_id).first()
        if user:
            user.status = "rejected"
            user.is_active = False
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def create_session(db: Session, user_id: str, token: str, expires_at: datetime | None = None) -> UserSessionEntity:
        session = UserSessionEntity(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session_by_token(db: Session, token: str) -> UserSessionEntity | None:
        return db.query(UserSessionEntity).filter(UserSessionEntity.token == token).first()

    @staticmethod
    def delete_session(db: Session, token: str) -> bool:
        session = db.query(UserSessionEntity).filter(UserSessionEntity.token == token).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    # --- Modelos de Conexão (Connection Templates / Presets) ---

    @staticmethod
    def get_all_templates(
        db: Session,
        current_user: UserEntity | None = None,
        visibility: str | None = None,
    ) -> list[ConnectionTemplateEntity]:
        query = db.query(ConnectionTemplateEntity)
        if visibility:
            query = query.filter(ConnectionTemplateEntity.visibility == visibility)

        if current_user and current_user.role != "epy_root":
            query = query.filter(
                or_(
                    ConnectionTemplateEntity.visibility == "public",
                    ConnectionTemplateEntity.visibility == "shared",
                    (ConnectionTemplateEntity.visibility == "private") & (ConnectionTemplateEntity.user_id == current_user.id),
                )
            )

        return query.order_by(ConnectionTemplateEntity.name).all()

    @staticmethod
    def get_template_by_id(db: Session, template_id: str) -> ConnectionTemplateEntity | None:
        return db.query(ConnectionTemplateEntity).filter(ConnectionTemplateEntity.id == template_id).first()

    @staticmethod
    def create_template(
        db: Session,
        name: str,
        type: str,
        prefix: str,
        description: str = "",
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        auth_config: dict[str, Any] | None = None,
        visibility: str = "shared",
        user_id: str | None = None,
    ) -> ConnectionTemplateEntity:
        template = ConnectionTemplateEntity(
            name=name,
            description=description,
            type=type,
            prefix=prefix,
            command=command,
            args=args or [],
            env=env or {},
            auth_config=auth_config or {},
            visibility=visibility,
            user_id=user_id,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: str) -> bool:
        tmpl = db.query(ConnectionTemplateEntity).filter(ConnectionTemplateEntity.id == template_id).first()
        if tmpl:
            db.delete(tmpl)
            db.commit()
            return True
        return False

    @staticmethod
    def update_template(
        db: Session,
        template_id: str,
        name: str | None = None,
        description: str | None = None,
        template_type: str | None = None,
        prefix: str | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        auth_config: dict[str, Any] | None = None,
        visibility: str | None = None,
    ) -> ConnectionTemplateEntity | None:
        tmpl = db.query(ConnectionTemplateEntity).filter(ConnectionTemplateEntity.id == template_id).first()
        if not tmpl:
            return None
        if name is not None:
            tmpl.name = name
        if description is not None:
            tmpl.description = description
        if template_type is not None:
            tmpl.type = template_type
        if prefix is not None:
            tmpl.prefix = prefix
        if command is not None:
            tmpl.command = command
        if args is not None:
            tmpl.args = args
        if env is not None:
            tmpl.env = env
        if auth_config is not None:
            tmpl.auth_config = auth_config
        if visibility is not None:
            tmpl.visibility = visibility
        db.commit()
        db.refresh(tmpl)
        return tmpl

    # --- Modelos de Data-Source Kits ---

    @staticmethod
    def get_all_kits(
        db: Session,
        current_user: UserEntity | None = None,
        visibility: str | None = None,
        category: str | None = None,
    ) -> list[DataSourceKitEntity]:
        query = db.query(DataSourceKitEntity)
        if visibility:
            query = query.filter(DataSourceKitEntity.visibility == visibility)
        if category:
            query = query.filter(DataSourceKitEntity.category == category)

        if current_user and current_user.role != "epy_root":
            query = query.filter(
                or_(
                    DataSourceKitEntity.visibility == "public",
                    DataSourceKitEntity.visibility == "shared",
                    (DataSourceKitEntity.visibility == "private") & (DataSourceKitEntity.user_id == current_user.id),
                )
            )

        return query.order_by(DataSourceKitEntity.name).all()

    @staticmethod
    def get_kit_by_id(db: Session, kit_id: str) -> DataSourceKitEntity | None:
        return db.query(DataSourceKitEntity).filter(DataSourceKitEntity.id == kit_id).first()

    @staticmethod
    def create_kit(
        db: Session,
        name: str,
        description: str = "",
        category: str = "Geral",
        sources: list[dict[str, Any]] | None = None,
        visibility: str = "shared",
        user_id: str | None = None,
    ) -> DataSourceKitEntity:
        kit = DataSourceKitEntity(
            name=name,
            description=description,
            category=category,
            sources=sources or [],
            visibility=visibility,
            user_id=user_id,
        )
        db.add(kit)
        db.commit()
        db.refresh(kit)
        return kit

    @staticmethod
    def update_kit(
        db: Session,
        kit_id: str,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        sources: list[dict[str, Any]] | None = None,
        visibility: str | None = None,
    ) -> DataSourceKitEntity | None:
        kit = db.query(DataSourceKitEntity).filter(DataSourceKitEntity.id == kit_id).first()
        if not kit:
            return None

        if name is not None:
            kit.name = name
        if description is not None:
            kit.description = description
        if category is not None:
            kit.category = category
        if sources is not None:
            kit.sources = sources
        if visibility is not None:
            kit.visibility = visibility

        db.commit()
        db.refresh(kit)
        return kit

    @staticmethod
    def delete_kit(db: Session, kit_id: str) -> bool:
        kit = db.query(DataSourceKitEntity).filter(DataSourceKitEntity.id == kit_id).first()
        if kit:
            db.delete(kit)
            db.commit()
            return True
        return False
