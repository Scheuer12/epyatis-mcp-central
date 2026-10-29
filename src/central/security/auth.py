"""
Módulo de Cibersegurança do Epyatis MCP Central: Autenticação Administrativa e Autorização (SEC-01).
Protege todas as rotas da API REST (/api/v1/*) com Zero-Trust, validação de sessões, expiração e RBAC.
"""

from datetime import datetime, timezone
import logging
import secrets
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from central.config import settings
from central.db.entities import (
    ConnectionEntity,
    ConnectionShareEntity,
    InstanceEntity,
    InstanceShareEntity,
    UserEntity,
)
from central.db.session import get_db
from central.db.repository import CentralRepository

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(None, alias="X-Central-Admin-Key"),
    x_session_token: str | None = Header(None, alias="X-Central-Session-Token"),
    authorization: str | None = Header(None),
) -> UserEntity:
    """
    Identifica e autentica a identidade que está requisitando o recurso.
    Suporta:
    1. Chave Mestra Administrativa (Bearer ou X-Central-Admin-Key) -> epy_root
    2. Token de Sessão Ativa (Bearer ou X-Central-Session-Token)
    Aplica validação estrita de expiração (expires_at) e status de aprovação.
    """
    configured_key = settings.CENTRAL_ADMIN_KEY

    # 1. Checa autenticação via Chave Mestra Admin
    provided_key: str | None = None
    if x_admin_key:
        provided_key = x_admin_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        token_candidate = authorization.split(" ", 1)[1].strip()
        if configured_key and secrets.compare_digest(token_candidate, configured_key):
            provided_key = token_candidate
        elif not x_session_token:
            x_session_token = token_candidate

    if provided_key and configured_key and secrets.compare_digest(provided_key, configured_key):
        root_user = db.query(UserEntity).filter(UserEntity.username == "epy_root").first()
        if not root_user:
            root_user = UserEntity(
                id="user_root",
                username="epy_root",
                role="epy_root",
                display_name="Master Administrator",
                status="approved",
                is_active=True,
            )
            db.add(root_user)
            db.commit()
            db.refresh(root_user)
        return root_user

    # 2. Checa autenticação via Token de Sessão de Usuário
    session_token = x_session_token
    if session_token:
        session = CentralRepository.get_session_by_token(db, session_token.strip())

        if session:
            # Validação de expiração de sessão (SEC-01)
            if session.expires_at:
                exp = session.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < _utc_now():
                    logger.info(f"[Security/Auth] Sessão expirada para usuário {session.user_id}.")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Sessão expirada. Por favor, autentique-se novamente.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

            user = session.user
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Conta de usuário desativada ou inexistente.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if getattr(user, "status", "approved") != "approved":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso não autorizado: conta pendente de aprovação ou rejeitada.",
                )

            return user

    client_ip = request.client.host if request.client else "desconhecido"
    logger.warning(f"[Security/Auth] Acesso não autorizado a {request.url.path} de IP: {client_ip}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autorizado. Chave administrativa ou sessão de usuário válida ausente.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin_auth(
    current_user: UserEntity = Depends(get_current_user),
) -> bool:
    return True


def require_master_admin(
    current_user: UserEntity = Depends(get_current_user),
) -> UserEntity:
    if current_user.role != "epy_root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita. Apenas administradores master (root) têm permissão para esta operação.",
        )
    return current_user


def validate_visibility_permission(current_user: UserEntity, visibility: str | None) -> None:
    """Garante que apenas o master admin possa atribuir visibilidade 'public'."""
    if visibility == "public" and current_user.role != "epy_root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores master (root) podem definir visibilidade pública.",
        )


# =========================================================================
# Camada Centralizada de Autorização e Isolamento Multi-Tenant
# =========================================================================

def can_read_connection(conn: ConnectionEntity, user: UserEntity, db: Session) -> bool:
    """Verifica se o usuário possui permissão de leitura sobre a conexão."""
    if user.role == "epy_root":
        return True
    if conn.visibility == "public":
        return True
    if conn.user_id == user.id:
        return True
    if conn.visibility == "shared":
        # Checa se o usuário está na lista de compartilhamento explícito
        is_shared = db.query(ConnectionShareEntity).filter(
            ConnectionShareEntity.connection_id == conn.id,
            ConnectionShareEntity.user_id == user.id,
        ).first() is not None
        return is_shared
    return False


def can_modify_connection(conn: ConnectionEntity, user: UserEntity) -> bool:
    """Apenas o proprietário ou master admin podem modificar ou excluir uma conexão."""
    if user.role == "epy_root":
        return True
    return conn.user_id == user.id


def can_read_instance(inst: InstanceEntity, user: UserEntity, db: Session) -> bool:
    """Verifica se o usuário possui permissão de leitura sobre a instância."""
    if user.role == "epy_root":
        return True
    if inst.visibility == "public":
        return True
    if inst.user_id == user.id:
        return True
    if inst.visibility == "shared":
        is_shared = db.query(InstanceShareEntity).filter(
            InstanceShareEntity.instance_id == inst.id,
            InstanceShareEntity.user_id == user.id,
        ).first() is not None
        return is_shared
    return False


def can_modify_instance(inst: InstanceEntity, user: UserEntity) -> bool:
    """Apenas o proprietário ou master admin podem modificar, recarregar ou excluir uma instância."""
    if user.role == "epy_root":
        return True
    return inst.user_id == user.id


def can_use_connection(conn: ConnectionEntity, user: UserEntity, db: Session) -> bool:
    """Authorize credential-bearing use separately from public metadata visibility."""
    if can_modify_connection(conn, user):
        return True
    return db.query(ConnectionShareEntity).filter(
        ConnectionShareEntity.connection_id == conn.id,
        ConnectionShareEntity.user_id == user.id,
    ).first() is not None


def require_connection_access(
    conn: ConnectionEntity,
    user: UserEntity,
    db: Session,
    *,
    operation: str = "read",
) -> ConnectionEntity:
    """Fail closed for connection read, modify, or credential-bearing use."""
    allowed = {
        "read": can_read_connection(conn, user, db),
        "modify": can_modify_connection(conn, user),
        "use": can_use_connection(conn, user, db),
    }.get(operation, False)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à conexão solicitada.",
        )
    return conn


def require_instance_access(
    inst: InstanceEntity,
    user: UserEntity,
    db: Session,
    *,
    operation: str = "read",
) -> InstanceEntity:
    """Fail closed for instance read and mutation operations."""
    allowed = {
        "read": can_read_instance(inst, user, db),
        "modify": can_modify_instance(inst, user),
    }.get(operation, False)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à instância solicitada.",
        )
    return inst
