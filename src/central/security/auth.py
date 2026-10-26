"""
Módulo de Cibersegurança do Epyatis MCP Central: Autenticação Administrativa (SEC-01).
Protege todas as rotas da API REST (/api/v1/*) e endpoints sensíveis usando comparação em tempo constante.
"""

import logging
import secrets
from fastapi import Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from central.config import settings
from central.db.entities import UserEntity, UserSessionEntity
from central.db.session import get_db

logger = logging.getLogger(__name__)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(None, alias="X-Central-Admin-Key"),
    x_session_token: str | None = Header(None, alias="X-Central-Session-Token"),
    authorization: str | None = Header(None),
    admin_key_query: str | None = Query(None, alias="admin_key"),
) -> UserEntity:
    configured_key = settings.CENTRAL_ADMIN_KEY

    # 1. Checa autenticação via Chave Mestra Admin (atribui automaticamente ao root)
    provided_key: str | None = None
    if x_admin_key:
        provided_key = x_admin_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        token_candidate = authorization.split(" ", 1)[1].strip()
        if configured_key and secrets.compare_digest(token_candidate, configured_key):
            provided_key = token_candidate
        elif not x_session_token:
            x_session_token = token_candidate
    elif admin_key_query:
        provided_key = admin_key_query.strip()
    elif "central_admin_key" in request.cookies:
        provided_key = request.cookies.get("central_admin_key", "").strip()

    if provided_key and configured_key and secrets.compare_digest(provided_key, configured_key):
        root_user = db.query(UserEntity).filter(UserEntity.username == "epy_root").first()
        if not root_user:
            root_user = UserEntity(
                id="user_root",
                username="epy_root",
                role="epy_root",
                display_name="Master Administrator",
                is_active=True,
            )
            db.add(root_user)
            db.commit()
            db.refresh(root_user)
        return root_user

    # 2. Checa autenticação via Token de Sessão de Usuário
    session_token = x_session_token or request.cookies.get("central_session")
    if session_token:
        session = db.query(UserSessionEntity).filter(
            UserSessionEntity.token == session_token.strip()
        ).first()
        if session and session.user and session.user.is_active:
            return session.user

    client_ip = request.client.host if request.client else "desconhecido"
    logger.warning(f"[Security/Auth] Acesso não autorizado a {request.url.path} de IP: {client_ip}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autorizado. Chave administrativa ou sessão de usuário inválida ou ausente.",
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
