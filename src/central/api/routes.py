"""
Rotas da API REST administrativa (v1) para o Epyatis MCP Central.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import secrets
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from central.db.entities import (
    ConnectionEntity,
    ConnectionTemplateEntity,
    DataSourceKitEntity,
    InstanceConnectionEntity,
    InstanceEntity,
    InstanceTokenEntity,
    ToolEntity,
    UserEntity,
    UserSessionEntity,
)
from central.db.repository import CentralRepository
from central.db.session import get_db
from central.gateway.manager import gateway_manager
from central.templates_catalog.registry import get_all_templates, get_template_by_id

from central.security import (
    get_current_user,
    require_connection_access,
    require_admin_auth,
    require_instance_access,
    require_master_admin,
    validate_stdio_command,
    validate_visibility_permission,
)
from central.security.tokens import hash_bearer_token, mask_bearer_token

logger = logging.getLogger(__name__)

auth_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

api_router = APIRouter(
    prefix="/api/v1",
    tags=["Admin API"],
    dependencies=[Depends(require_admin_auth)],
)


# --- Modelos Pydantic para Requisições ---

class LoginRequest(BaseModel):
    username: str
    password: str | None = None
    admin_key: str | None = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    invite_code: str | None = None


class CreateInviteRequest(BaseModel):
    expires_hours: int = 24
    role: str = "standard"


class ShareUsersRequest(BaseModel):
    user_ids: list[str] = Field(default_factory=list)


class UserCreateRequest(BaseModel):
    username: str
    role: str = "standard"  # standard | epy_root
    display_name: str | None = None


class ConnectionCreateRequest(BaseModel):
    id: str = Field(..., description="Identificador único (ex: gdrive, periskope)")
    name: str = Field(..., description="Nome amigável da conexão")
    type: str = Field("stdio", description="stdio | remote_mcp | internal | openapi")
    prefix: str = Field(..., description="Prefixo de namespace das ferramentas")
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    auth_config: dict[str, Any] = Field(default_factory=dict)
    visibility: str = Field("shared", description="private | shared | public")


class ConnectionUpdateRequest(BaseModel):
    name: str = Field(..., description="Nome amigável da conexão")
    type: str = Field("stdio", description="stdio | remote_mcp | internal | openapi")
    prefix: str = Field(..., description="Prefixo de namespace das ferramentas")
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    auth_config: dict[str, Any] = Field(default_factory=dict)
    visibility: str | None = Field(None, description="private | shared | public")


class ConnectionTemplateUpdateRequest(BaseModel):
    name: str = Field(..., description="Nome amigável do modelo")
    description: str = Field(default="", description="Descrição de uso do modelo")
    type: str = Field("stdio", description="stdio | remote_mcp | internal | openapi")
    prefix: str = Field(..., description="Prefixo de namespace das ferramentas")
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    auth_config: dict[str, Any] = Field(default_factory=dict)
    visibility: str | None = Field(None, description="private | shared | public")


class SaveConnectionAsTemplateRequest(BaseModel):
    name: str | None = None
    description: str = ""
    visibility: str = "shared"


class ConnectionTemplateCreateRequest(BaseModel):
    name: str
    description: str = ""
    type: str = "stdio"
    prefix: str
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    auth_config: dict[str, Any] = Field(default_factory=dict)
    visibility: str = "shared"


class InstantiateTemplateRequest(BaseModel):
    connection_id: str
    name: str
    prefix: str | None = None
    env_overrides: dict[str, str] = Field(default_factory=dict)
    visibility: str = "shared"


class InstanceCreateRequest(BaseModel):
    name: str = Field(..., description="Nome da instância")
    slug: str = Field(..., description="Slug único da URL (ex: finance-suite)")
    description: str = Field("", description="Descrição da instância")
    visibility: str = Field("shared", description="private | shared | public")
    connection_ids: list[str] = Field(default_factory=list, description="IDs das conexões associadas")


class InstanceUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None


class AttachConnectionRequest(BaseModel):
    connection_id: str


class VisibilityUpdateRequest(BaseModel):
    visibility: str


class SaveInstanceAsKitRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "Geral"
    visibility: str = "shared"


class DataSourceKitCreateRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "Geral"
    sources: list[dict[str, Any]] = Field(default_factory=list)
    visibility: str = "shared"


class DataSourceKitUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    sources: list[dict[str, Any]] | None = None
    visibility: str | None = None


class TokenCreateRequest(BaseModel):
    label: str = Field("Connector Token", description="Rótulo identificador")
    token: str | None = Field(None, description="Valor personalizado ou gerado automaticamente se omitido")


# --- Endpoints da API ---

# --- Endpoints de Autenticação e Usuários ---

@auth_router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Cria uma sessão para o usuário ou valida via Chave Mestra ou Senha."""
    from central.config import settings
    if data.admin_key and settings.CENTRAL_ADMIN_KEY and secrets.compare_digest(data.admin_key, settings.CENTRAL_ADMIN_KEY):
        user = CentralRepository.get_user_by_username(db, "epy_root")
        if not user:
            user = CentralRepository.create_user(db, "epy_root", role="epy_root", display_name="Master Administrator")
        session_token = f"sess_{secrets.token_hex(24)}"
        CentralRepository.create_session(
            db,
            user.id,
            session_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
        )
        return {
            "token": session_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name or user.username,
            }
        }

    # Se forneceu senha, autentica estritamente
    if data.password:
        user, err_msg = CentralRepository.authenticate_user(db, data.username, data.password)
        if not user:
            status_code = 403 if (err_msg and ("aguardando aprovação" in err_msg or "rejeitada" in err_msg)) else 401
            raise HTTPException(status_code=status_code, detail=err_msg or "Credenciais inválidas.")

        session_token = f"sess_{secrets.token_hex(24)}"
        CentralRepository.create_session(
            db,
            user.id,
            session_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
        )
        return {
            "token": session_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name or user.username,
            }
        }

    raise HTTPException(status_code=401, detail="Credenciais obrigatórias ausentes.")


@auth_router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Criação de novos usuários com convite (ativação instantânea) ou aprovação pelo Master Admin."""
    existing = CentralRepository.get_user_by_username(db, data.username.strip())
    if existing:
        raise HTTPException(status_code=400, detail="Este nome de usuário já está cadastrado.")

    if not data.password or len(data.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 6 caracteres.")

    # Caso 1: Cadastro com código de convite válido gerado pelo Master Admin
    if data.invite_code and data.invite_code.strip():
        code_clean = data.invite_code.strip()
        invite = CentralRepository.get_invite_by_code(db, code_clean)
        now = datetime.now(timezone.utc)
        if not invite:
            raise HTTPException(status_code=400, detail="Código de convite inválido ou inexistente.")
        if invite.is_used:
            raise HTTPException(status_code=400, detail="Este convite de uso único já foi utilizado.")
        expires_at = invite.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(status_code=400, detail="Este código de convite expirou.")

        user = CentralRepository.create_user_with_password(
            db=db,
            username=data.username.strip(),
            password=data.password,
            role=invite.role,
            display_name=data.display_name or data.username.strip(),
            status="approved",
        )
        invite.is_used = True
        invite.used_by_user_id = user.id
        db.commit()

        session_token = f"sess_{secrets.token_hex(24)}"
        CentralRepository.create_session(db, user.id, session_token)
        return {
            "status": "approved",
            "message": "Conta criada e ativada com sucesso pelo convite!",
            "token": session_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name or user.username,
            },
        }

    # Caso 2: Cadastro sem convite -> requer aprovação do Master Admin
    user = CentralRepository.create_user_with_password(
        db=db,
        username=data.username.strip(),
        password=data.password,
        role="standard",
        display_name=data.display_name or data.username.strip(),
        status="pending_approval",
    )
    return {
        "status": "pending_approval",
        "message": "Conta cadastrada com sucesso! Sua solicitação de acesso está aguardando aprovação pelo Master Admin.",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name or user.username,
        },
    }


@auth_router.get("/me")
def get_me(current_user: UserEntity = Depends(get_current_user)) -> dict[str, Any]:
    """Retorna os dados do usuário autenticado atual."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "display_name": current_user.display_name or current_user.username,
        "is_master_admin": current_user.role == "epy_root",
    }


@auth_router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Encerra a sessão ativa do usuário."""
    token = request.headers.get("X-Central-Session-Token") or request.cookies.get("central_session")
    if token:
        CentralRepository.delete_session(db, token)
    return {"status": "success", "message": "Sessão encerrada com sucesso."}


@api_router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> list[dict[str, Any]]:
    """Lista todos os usuários registrados."""
    users = CentralRepository.get_all_users(db)
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "display_name": u.display_name or u.username,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@api_router.post("/users")
def create_new_user(
    data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> dict[str, Any]:
    """Cria um novo usuário no sistema (requer Master Admin)."""
    existing = CentralRepository.get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=400, detail=f"Usuário '{data.username}' já existe.")

    user = CentralRepository.create_user(
        db=db,
        username=data.username,
        role=data.role,
        display_name=data.display_name,
    )
    return {
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name,
        }
    }


# --- Gestão de Convites e Aprovações (Restrito ao Master Admin) ---

@api_router.post("/admin/invites")
def create_invite_endpoint(
    data: CreateInviteRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> dict[str, Any]:
    """Gera um convite de uso único com expiração programada (Master Admin)."""
    invite = CentralRepository.create_invite(
        db=db,
        created_by_user_id=current_user.id,
        expires_hours=data.expires_hours,
        role=data.role,
    )
    return {
        "status": "success",
        "invite": {
            "id": invite.id,
            "code": invite.code,
            "role": invite.role,
            "expires_at": invite.expires_at.isoformat(),
            "is_used": invite.is_used,
        },
    }


@api_router.get("/admin/invites")
def list_invites_endpoint(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> list[dict[str, Any]]:
    """Lista todos os convites gerados e seus status de uso (Master Admin)."""
    invites = CentralRepository.get_all_invites(db, active_only=active_only)
    return [
        {
            "id": inv.id,
            "code": inv.code,
            "role": inv.role,
            "created_by": inv.created_by.username if inv.created_by else None,
            "expires_at": inv.expires_at.isoformat(),
            "is_used": inv.is_used,
            "used_by": inv.used_by.username if inv.used_by else None,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invites
    ]


@api_router.delete("/admin/invites/{code}")
def delete_invite_endpoint(
    code: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> dict[str, Any]:
    """Revoga um convite gerado (Master Admin)."""
    deleted = CentralRepository.delete_invite(db, code)
    if not deleted:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
    return {"status": "success", "message": "Convite revogado com sucesso."}


@api_router.get("/admin/pending-users")
def list_pending_users_endpoint(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> list[dict[str, Any]]:
    """Lista usuários que solicitaram cadastro e aguardam aprovação (Master Admin)."""
    pending = CentralRepository.get_pending_users(db)
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name or u.username,
            "role": u.role,
            "status": getattr(u, "status", "pending_approval"),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in pending
    ]


@api_router.post("/admin/pending-users/{user_id}/approve")
def approve_pending_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> dict[str, Any]:
    """Aprova o cadastro de um novo usuário (Master Admin)."""
    user = CentralRepository.approve_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return {"status": "success", "message": f"Usuário '{user.username}' aprovado com sucesso."}


@api_router.post("/admin/pending-users/{user_id}/reject")
def reject_pending_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> dict[str, Any]:
    """Rejeita a solicitação de cadastro (Master Admin)."""
    user = CentralRepository.reject_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return {"status": "success", "message": f"Usuário '{user.username}' rejeitado."}


@api_router.get("/overview")
def get_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retorna métricas gerais e status do sistema."""
    stats = CentralRepository.get_system_overview(db)

    # Status de instâncias carregadas na memória
    runtime_instances = {}
    for slug, gw in gateway_manager.instances.items():
        upstreams_status = {}
        for cid, up in gw.upstreams.items():
            upstreams_status[cid] = {
                "prefix": up.prefix,
                "type": getattr(up, "connection_id", cid),
            }
        runtime_instances[slug] = {
            "name": gw.config.name,
            "upstreams_count": len(gw.upstreams),
            "upstreams": upstreams_status,
        }

    stats["runtime_instances"] = runtime_instances
    return stats


@api_router.get("/connections")
def list_connections(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
    visibility: str | None = None,
) -> list[dict[str, Any]]:
    """Lista todas as conexões cadastradas com filtragem de visibilidade."""
    connections = CentralRepository.get_all_connections(
        db,
        current_user=current_user,
        visibility=visibility,
    )
    result = []
    for c in connections:
        tool_count = db.query(ToolEntity).filter(ToolEntity.connection_id == c.id).count()
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "name": c.name,
            "type": c.type,
            "prefix": c.prefix,
            "command": c.command,
            "args": c.args,
            "env_keys": list(c.env.keys()),
            "url": c.url,
            "visibility": getattr(c, "visibility", "shared"),
            "shared_user_ids": [s.user_id for s in c.shares],
            "is_active": c.is_active,
            "health_status": c.health_status,
            "tools_count": tool_count,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })
    return result


@api_router.post("/connections")
def create_connection(
    data: ConnectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Cria uma conexão upstream sem permitir colisões de identificador."""
    validate_visibility_permission(current_user, data.visibility)

    if CentralRepository.get_connection_by_id(db, data.id):
        raise HTTPException(
            status_code=409,
            detail=f"Já existe uma conexão com o identificador '{data.id}'. Use a rota de atualização.",
        )

    if data.type == "stdio":
        if current_user.role != "epy_root":
            raise HTTPException(status_code=403, detail="Conexões stdio são restritas ao master admin.")
        try:
            validate_stdio_command(data.command, data.args)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

    conn = CentralRepository.create_or_update_connection(
        db=db,
        connection_id=data.id,
        name=data.name,
        conn_type=data.type,
        prefix=data.prefix,
        command=data.command,
        args=data.args,
        env=data.env,
        url=data.url,
        auth_config=data.auth_config,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "connection_id": conn.id}


@api_router.put("/connections/{conn_id}")
async def update_connection_endpoint(
    conn_id: str,
    data: ConnectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza as configurações de uma conexão existente."""
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")

    if current_user.role != "epy_root" and conn.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar esta conexão.")

    if data.visibility:
        validate_visibility_permission(current_user, data.visibility)

    if data.type == "stdio":
        if current_user.role != "epy_root":
            raise HTTPException(status_code=403, detail="Conexões stdio são restritas ao master admin.")
        try:
            validate_stdio_command(data.command, data.args)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

    updated_conn = CentralRepository.create_or_update_connection(
        db=db,
        connection_id=conn_id,
        name=data.name,
        conn_type=data.type,
        prefix=data.prefix,
        command=data.command,
        args=data.args,
        env=data.env,
        url=data.url,
        auth_config=data.auth_config,
        visibility=data.visibility or conn.visibility,
    )

    # Recarrega upstreams nas instâncias ativas do gateway_manager se aplicável
    for slug, gw in list(gateway_manager.instances.items()):
        if conn_id in gw.upstreams:
            try:
                await gateway_manager.reload_instance(slug)
            except Exception as e:
                logger.warning(f"Erro ao recarregar instância '{slug}' após atualização da conexão '{conn_id}': {e}")

    return {"status": "success", "connection_id": updated_conn.id}


@api_router.post("/connections/{conn_id}/save-as-template")
def save_connection_as_template(
    conn_id: str,
    data: SaveConnectionAsTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Salva uma conexão existente como um modelo reutilizável."""
    validate_visibility_permission(current_user, data.visibility)

    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão de origem não encontrada.")
    require_connection_access(conn, current_user, db, operation="read")

    template_name = data.name or f"Modelo - {conn.name}"
    tmpl = CentralRepository.create_template(
        db=db,
        name=template_name,
        description=data.description or f"Modelo exportado da conexão {conn.name}",
        type=conn.type,
        prefix=conn.prefix,
        command=conn.command,
        args=conn.args,
        env=conn.env,
        auth_config=conn.auth_config,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "template_id": tmpl.id, "name": tmpl.name}


# --- Modelos de Conexão (Templates / Presets) ---

@api_router.get("/connection-templates")
def list_connection_templates(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
    visibility: str | None = None,
) -> list[dict[str, Any]]:
    """Lista todos os modelos de conexão disponíveis."""
    templates = CentralRepository.get_all_templates(db, current_user=current_user, visibility=visibility)
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "name": t.name,
            "description": t.description,
            "type": t.type,
            "prefix": t.prefix,
            "command": t.command,
            "args": t.args,
            "visibility": t.visibility,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


@api_router.post("/connection-templates")
def create_connection_template(
    data: ConnectionTemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Cria um novo modelo de conexão diretamente."""
    validate_visibility_permission(current_user, data.visibility)

    if data.type == "stdio":
        if current_user.role != "epy_root":
            raise HTTPException(status_code=403, detail="Templates stdio são restritos ao master admin.")
        try:
            validate_stdio_command(data.command, data.args)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

    tmpl = CentralRepository.create_template(
        db=db,
        name=data.name,
        description=data.description,
        type=data.type,
        prefix=data.prefix,
        command=data.command,
        args=data.args,
        env=data.env,
        auth_config=data.auth_config,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "template_id": tmpl.id}


@api_router.get("/connection-templates/{template_id}")
def get_connection_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna detalhes de um modelo de conexão específico."""
    tmpl = CentralRepository.get_template_by_id(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Modelo de conexão não encontrado.")

    if tmpl.visibility == "private" and current_user.role != "epy_root" and tmpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso restrito ao proprietário do modelo.")

    return {
        "id": tmpl.id,
        "user_id": tmpl.user_id,
        "name": tmpl.name,
        "description": tmpl.description,
        "type": tmpl.type,
        "prefix": tmpl.prefix,
        "command": tmpl.command,
        "args": tmpl.args,
        "visibility": tmpl.visibility,
        "created_at": tmpl.created_at.isoformat() if tmpl.created_at else None,
    }


@api_router.delete("/connection-templates/{template_id}")
def delete_connection_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove um modelo de conexão existente."""
    tmpl = CentralRepository.get_template_by_id(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Modelo de conexão não encontrado.")

    if current_user.role != "epy_root" and tmpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem excluir este modelo.")

    CentralRepository.delete_template(db, template_id)
    return {"status": "success", "message": "Modelo de conexão excluído com sucesso."}


@api_router.put("/connection-templates/{template_id}")
def update_connection_template_endpoint(
    template_id: str,
    data: ConnectionTemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza um modelo de conexão existente."""
    tmpl = CentralRepository.get_template_by_id(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Modelo de conexão não encontrado.")

    if current_user.role != "epy_root" and tmpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar este modelo.")

    if data.visibility:
        validate_visibility_permission(current_user, data.visibility)

    if data.type == "stdio":
        if current_user.role != "epy_root":
            raise HTTPException(status_code=403, detail="Conexões stdio são restritas ao master admin.")
        try:
            validate_stdio_command(data.command, data.args)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

    CentralRepository.update_template(
        db=db,
        template_id=template_id,
        name=data.name,
        description=data.description,
        template_type=data.type,
        prefix=data.prefix,
        command=data.command,
        args=data.args,
        env=data.env,
        auth_config=data.auth_config,
        visibility=data.visibility or tmpl.visibility,
    )
    return {"status": "success", "template_id": template_id}


@api_router.post("/connection-templates/{template_id}/instantiate")
def instantiate_connection_template(
    template_id: str,
    data: InstantiateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Instancia uma conexão ativa a partir de um modelo salvo."""
    validate_visibility_permission(current_user, data.visibility)

    tmpl = CentralRepository.get_template_by_id(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Modelo de conexão não encontrado.")
    if tmpl.visibility == "private" and current_user.role != "epy_root" and tmpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado ao modelo solicitado.")
    if CentralRepository.get_connection_by_id(db, data.connection_id):
        raise HTTPException(status_code=409, detail="O identificador de conexão já existe.")
    if tmpl.type == "stdio" and current_user.role != "epy_root":
        raise HTTPException(status_code=403, detail="Templates stdio são restritos ao master admin.")

    merged_env = dict(tmpl.env)
    merged_env.update(data.env_overrides or {})

    conn = CentralRepository.create_or_update_connection(
        db=db,
        connection_id=data.connection_id,
        name=data.name or tmpl.name,
        conn_type=tmpl.type,
        prefix=data.prefix or tmpl.prefix,
        command=tmpl.command,
        args=tmpl.args,
        env=merged_env,
        auth_config=tmpl.auth_config,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "connection_id": conn.id}


@api_router.post("/connections/{conn_id}/discover")
async def discover_connection_tools(
    conn_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Dispara a descoberta e sincronização de tools para uma conexão."""
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    require_connection_access(conn, current_user, db, operation="modify")

    # Procura um gateway em execução que tenha essa conexão
    matching_upstream = None
    for gw in gateway_manager.instances.values():
        if conn_id in gw.upstreams:
            matching_upstream = gw.upstreams[conn_id]
            break

    if not matching_upstream:
        # Se não estiver em nenhuma instância em execução, tenta instanciar temporariamente
        raise HTTPException(
            status_code=400,
            detail="A conexão não está ativa em nenhuma instância carregada no gateway.",
        )

    try:
        tools = await matching_upstream.list_tools()
        tools_data = [
            {
                "name": t.name,
                "title": t.title or t.name,
                "description": t.description or "",
                "inputSchema": t.input_schema or {},
            }
            for t in tools
        ]
        synced = CentralRepository.sync_discovered_tools(db, conn_id, tools_data)
        return {
            "status": "success",
            "connection_id": conn_id,
            "tools_discovered": len(tools),
            "tools_synced": synced,
        }
    except Exception as e:
        logger.error(f"Erro ao descobrir tools de '{conn_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Falha na descoberta de ferramentas: {e}")


@api_router.get("/tools")
def list_tools(
    connection_id: str | None = None,
    query: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Lista ferramentas do catálogo com filtro e paginação."""
    tools, total = CentralRepository.get_all_tools(
        db=db,
        connection_id=connection_id,
        query=query,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": t.id,
                "connection_id": t.connection_id,
                "original_name": t.original_name,
                "namespaced_name": t.namespaced_name,
                "title": t.title,
                "description": t.description,
                "input_schema": t.input_schema,
                "is_active": t.is_active,
            }
            for t in tools
        ],
    }


@api_router.get("/instances")
def list_instances(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
    visibility: str | None = None,
) -> list[dict[str, Any]]:
    """Lista todas as instâncias e seus conectores com controle de visibilidade."""
    instances = CentralRepository.get_all_instances(
        db,
        current_user=current_user,
        visibility=visibility,
    )
    result = []
    for inst in instances:
        conns = [
            {
                "id": assoc.connection_id,
                "name": assoc.connection.name if assoc.connection else assoc.connection_id,
                "prefix": assoc.connection.prefix if assoc.connection else "",
                "is_enabled": assoc.is_enabled,
            }
            for assoc in inst.connection_associations
        ]
        tokens = [
            {"id": t.id, "token_hint": mask_bearer_token(t.token), "label": t.label}
            for t in inst.tokens
        ]

        # Contagem de ferramentas ativas
        active_prefixes = [c["prefix"] for c in conns if c["is_enabled"]]
        tools_count = 0
        if active_prefixes:
            tools_count = (
                db.query(ToolEntity)
                .join(ConnectionEntity, ToolEntity.connection_id == ConnectionEntity.id)
                .filter(ConnectionEntity.prefix.in_(active_prefixes))
                .count()
            )

        result.append({
            "id": inst.id,
            "user_id": inst.user_id,
            "name": inst.name,
            "slug": inst.slug,
            "description": inst.description,
            "visibility": getattr(inst, "visibility", "shared"),
            "shared_user_ids": [s.user_id for s in inst.shares],
            "is_active": inst.is_active,
            "connections": conns,
            "tokens": tokens,
            "tools_count": tools_count,
            "created_at": inst.created_at.isoformat() if inst.created_at else None,
        })
    return result


@api_router.post("/instances")
async def create_instance(
    data: InstanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Cria uma nova instância e associa conexões, respeitando controle de visibilidade."""
    validate_visibility_permission(current_user, data.visibility)

    existing = CentralRepository.get_instance_by_slug(db, data.slug)
    if existing:
        raise HTTPException(status_code=400, detail=f"Instância com slug '{data.slug}' já existe.")

    instance = CentralRepository.create_instance(
        db=db,
        name=data.name,
        slug=data.slug,
        description=data.description,
        visibility=data.visibility,
        user_id=current_user.id,
    )

    # Associa conexões selecionadas
    for conn_id in data.connection_ids:
        conn = CentralRepository.get_connection_by_id(db, conn_id)
        if conn:
            require_connection_access(conn, current_user, db, operation="use")
            assoc = InstanceConnectionEntity(
                instance_id=instance.id,
                connection_id=conn.id,
                is_enabled=True,
            )
            db.add(assoc)
    db.commit()

    # Recarrega no gateway em memória
    await gateway_manager.reload_instance(data.slug)

    return {
        "status": "success",
        "instance_id": instance.id,
        "slug": instance.slug,
        "token": instance.issued_token,
    }


@api_router.get("/instances/{slug}")
def get_instance_detail(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna detalhes completos de uma instância, incluindo conexões vinculadas, mapa e tokens."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")

    require_instance_access(inst, current_user, db, operation="read")

    conns = [
        {
            "id": assoc.connection_id,
            "name": assoc.connection.name if assoc.connection else assoc.connection_id,
            "prefix": assoc.connection.prefix if assoc.connection else "",
            "type": assoc.connection.type if assoc.connection else "",
            "is_enabled": assoc.is_enabled,
        }
        for assoc in inst.connection_associations
    ]
    tokens = [
        {"id": t.id, "token_hint": mask_bearer_token(t.token), "label": t.label}
        for t in inst.tokens
    ]
    sources_map = {}
    if inst.data_sources_map_json:
        try:
            sources_map = json.loads(inst.data_sources_map_json)
        except Exception:
            sources_map = {}

    return {
        "id": inst.id,
        "user_id": inst.user_id,
        "name": inst.name,
        "slug": inst.slug,
        "description": inst.description,
        "visibility": getattr(inst, "visibility", "shared"),
        "is_active": inst.is_active,
        "connections": conns,
        "tokens": tokens,
        "sources_map": sources_map,
        "shared_user_ids": CentralRepository.get_instance_shared_user_ids(db, inst.id),
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
    }


@api_router.put("/instances/{slug}")
@api_router.patch("/instances/{slug}")
async def update_instance_metadata(
    slug: str,
    data: InstanceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza metadados ou visibilidade de uma instância."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")

    if current_user.role != "epy_root" and inst.user_id and inst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar esta instância.")

    if data.visibility:
        validate_visibility_permission(current_user, data.visibility)

    CentralRepository.update_instance(
        db=db,
        instance=inst,
        name=data.name,
        description=data.description,
        visibility=data.visibility,
    )
    await gateway_manager.reload_instance(slug)
    return {
        "status": "success",
        "slug": inst.slug,
        "name": inst.name,
        "description": inst.description,
        "visibility": inst.visibility,
    }


@api_router.get("/instances/{slug}/shares")
def get_instance_shares_endpoint(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna os IDs de usuários autorizados nesta instância."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(inst, current_user, db, operation="modify")
    shared_uids = CentralRepository.get_instance_shared_user_ids(db, inst.id)
    return {
        "instance_slug": slug,
        "shared_user_ids": shared_uids,
    }


@api_router.put("/instances/{slug}/shares")
def update_instance_shares_endpoint(
    slug: str,
    data: ShareUsersRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Define quais usuários possuem acesso a esta instância compartilhada."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    if current_user.role != "epy_root" and inst.user_id and inst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o proprietário ou o Master Admin podem gerenciar compartilhamento.")

    saved_uids = CentralRepository.set_instance_shares(db, inst.id, data.user_ids)
    return {
        "status": "success",
        "instance_slug": slug,
        "shared_user_ids": saved_uids,
    }


@api_router.delete("/instances/{slug}")
def delete_instance_endpoint(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Exclui uma instância permanentemente."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")

    if current_user.role != "epy_root" and inst.user_id and inst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem excluir esta instância.")

    CentralRepository.delete_instance(db, inst)
    return {"status": "success", "message": f"Instância '{slug}' excluída com sucesso."}


@api_router.post("/instances/{slug}/connections")
async def attach_connection_endpoint(
    slug: str,
    data: AttachConnectionRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Vincula uma conexão ativa a esta instância."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(inst, current_user, db, operation="modify")

    conn = CentralRepository.get_connection_by_id(db, data.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Conexão '{data.connection_id}' não encontrada.")
    require_connection_access(conn, current_user, db, operation="use")

    CentralRepository.attach_connection_to_instance(db, inst.id, conn.id)
    await gateway_manager.reload_instance(slug)
    return {"status": "success", "message": f"Conexão '{conn.name}' vinculada à instância '{inst.name}'."}


@api_router.delete("/instances/{slug}/connections/{conn_id}")
async def detach_connection_endpoint(
    slug: str,
    conn_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Desvincula uma conexão ativa desta instância."""
    inst = CentralRepository.get_instance_by_slug(db, slug)
    if not inst:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(inst, current_user, db, operation="modify")

    CentralRepository.detach_connection_from_instance(db, inst.id, conn_id)
    await gateway_manager.reload_instance(slug)
    return {"status": "success", "message": f"Conexão '{conn_id}' desvinculada com sucesso."}


@api_router.patch("/connections/{conn_id}/visibility")
def update_connection_visibility_endpoint(
    conn_id: str,
    data: VisibilityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Altera a visibilidade (private, shared, public) de uma conexão."""
    validate_visibility_permission(current_user, data.visibility)
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")

    if current_user.role != "epy_root" and conn.user_id and conn.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar esta conexão.")

    CentralRepository.update_connection_visibility(db, conn, data.visibility)
    return {"status": "success", "id": conn.id, "visibility": conn.visibility}


@api_router.get("/connections/{conn_id}/shares")
def get_connection_shares_endpoint(
    conn_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna a lista de IDs de usuários com acesso concedido a esta conexão."""
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    shared_uids = CentralRepository.get_connection_shared_user_ids(db, conn_id)
    return {
        "connection_id": conn_id,
        "shared_user_ids": shared_uids,
    }


@api_router.put("/connections/{conn_id}/shares")
def update_connection_shares_endpoint(
    conn_id: str,
    data: ShareUsersRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Define quais usuários possuem acesso a esta conexão compartilhada."""
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    if current_user.role != "epy_root" and conn.user_id and conn.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o proprietário ou o Master Admin podem gerenciar compartilhamento.")

    saved_uids = CentralRepository.set_connection_shares(db, conn_id, data.user_ids)
    return {
        "status": "success",
        "connection_id": conn_id,
        "shared_user_ids": saved_uids,
    }


@api_router.delete("/connections/{conn_id}")
def delete_connection_endpoint(
    conn_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Exclui uma conexão upstream permanentemente."""
    conn = CentralRepository.get_connection_by_id(db, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")

    if current_user.role != "epy_root" and conn.user_id and conn.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem excluir esta conexão.")

    CentralRepository.delete_connection(db, conn)
    return {"status": "success", "message": f"Conexão '{conn_id}' excluída com sucesso."}


# --- Modelos de Data-Source Kits ---

@api_router.post("/instances/{slug}/save-as-kit")
def save_instance_as_kit(
    slug: str,
    data: SaveInstanceAsKitRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Exporta o Mapa de Fontes de Dados atual de uma instância como um Kit reutilizável."""
    validate_visibility_permission(current_user, data.visibility)

    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")

    sources = []
    if instance.data_sources_map and isinstance(instance.data_sources_map, dict):
        sources = instance.data_sources_map.get("sources", [])

    kit = CentralRepository.create_kit(
        db=db,
        name=data.name or f"Kit de Fontes - {instance.name}",
        description=data.description or f"Kit gerado a partir da instância {instance.name}",
        category=data.category or "Geral",
        sources=sources,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "kit_id": kit.id, "name": kit.name}


@api_router.get("/data-source-kits")
def list_data_source_kits(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
    visibility: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Lista todos os Data-Source Kits disponíveis."""
    kits = CentralRepository.get_all_kits(
        db,
        current_user=current_user,
        visibility=visibility,
        category=category,
    )
    return [
        {
            "id": k.id,
            "user_id": k.user_id,
            "name": k.name,
            "description": k.description,
            "category": k.category,
            "sources": k.sources,
            "sources_count": len(k.sources),
            "visibility": k.visibility,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        }
        for k in kits
    ]


@api_router.post("/data-source-kits")
def create_data_source_kit(
    data: DataSourceKitCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Cria um novo Data-Source Kit."""
    validate_visibility_permission(current_user, data.visibility)

    kit = CentralRepository.create_kit(
        db=db,
        name=data.name,
        description=data.description,
        category=data.category,
        sources=data.sources,
        visibility=data.visibility,
        user_id=current_user.id,
    )
    return {"status": "success", "kit_id": kit.id}


@api_router.get("/data-source-kits/{kit_id}")
def get_data_source_kit(
    kit_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna detalhes de um Data-Source Kit específico."""
    kit = CentralRepository.get_kit_by_id(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Data-Source Kit não encontrado.")

    if kit.visibility == "private" and current_user.role != "epy_root" and kit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso restrito ao proprietário do Kit.")

    return {
        "id": kit.id,
        "user_id": kit.user_id,
        "name": kit.name,
        "description": kit.description,
        "category": kit.category,
        "sources": kit.sources,
        "visibility": kit.visibility,
        "created_at": kit.created_at.isoformat() if kit.created_at else None,
    }


@api_router.put("/data-source-kits/{kit_id}")
def update_data_source_kit(
    kit_id: str,
    data: DataSourceKitUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza um Data-Source Kit existente."""
    kit = CentralRepository.get_kit_by_id(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Data-Source Kit não encontrado.")

    if current_user.role != "epy_root" and kit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar este Kit.")

    if data.visibility:
        validate_visibility_permission(current_user, data.visibility)

    updated = CentralRepository.update_kit(
        db=db,
        kit_id=kit_id,
        name=data.name,
        description=data.description,
        category=data.category,
        sources=data.sources,
        visibility=data.visibility,
    )
    return {"status": "success", "kit_id": kit_id}


@api_router.delete("/data-source-kits/{kit_id}")
def delete_data_source_kit(
    kit_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove um Data-Source Kit existente."""
    kit = CentralRepository.get_kit_by_id(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Data-Source Kit não encontrado.")

    if current_user.role != "epy_root" and kit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem excluir este Kit.")

    CentralRepository.delete_kit(db, kit_id)
    return {"status": "success", "message": "Kit excluído com sucesso."}


class KitApplyRequest(BaseModel):
    target_instance_slug: str


@api_router.post("/data-source-kits/{kit_id}/apply")
async def apply_kit_to_instance_by_body(
    kit_id: str,
    data: KitApplyRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Aplica as fontes e diretrizes de um Kit à instância especificada no corpo JSON."""
    return await apply_kit_to_instance(
        kit_id=kit_id,
        slug=data.target_instance_slug,
        db=db,
        current_user=current_user,
    )


@api_router.post("/data-source-kits/{kit_id}/apply-to-instance/{slug}")
async def apply_kit_to_instance(
    kit_id: str,
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Aplica as fontes e diretrizes de um Kit ao Mapa de Fontes de uma instância."""
    kit = CentralRepository.get_kit_by_id(db, kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail="Data-Source Kit não encontrado.")

    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")
    if kit.visibility == "private" and current_user.role != "epy_root" and kit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado ao Kit solicitado.")

    # Mescla as fontes do Kit mantendo a organização da instância
    current_map = instance.data_sources_map or {"organization": instance.name, "sources": []}
    existing_sources = list(current_map.get("sources", []))

    # Adiciona ou atualiza fontes do kit com base no ID estável (permitindo múltiplos nós do mesmo sistema)
    existing_ids = {s.get("id") for s in existing_sources if isinstance(s, dict) and s.get("id")}
    for src in kit.sources:
        if not isinstance(src, dict):
            continue
        src_id = src.get("id")
        if not src_id or src_id not in existing_ids:
            existing_sources.append(src)
            if src_id:
                existing_ids.add(src_id)
        else:
            for idx, es in enumerate(existing_sources):
                if isinstance(es, dict) and es.get("id") == src_id:
                    existing_sources[idx] = src
                    break

    current_map["sources"] = existing_sources
    CentralRepository.update_instance_data_sources_map(db, slug, current_map)

    # Recarrega a instância no gateway
    await gateway_manager.reload_instance(slug)

    return {
        "status": "success",
        "message": f"Kit '{kit.name}' aplicado à instância '{slug}' com sucesso.",
        "sources_count": len(existing_sources),
    }

@api_router.post("/instances/{slug}/reload")
async def reload_instance_endpoint(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Recarrega uma instância no gateway assíncrono."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada ou inativa.")
    require_instance_access(instance, current_user, db, operation="modify")
    success = await gateway_manager.reload_instance(slug)
    if not success:
        raise HTTPException(status_code=404, detail=f"Instância '{slug}' não encontrada ou inativa.")
    return {"status": "success", "slug": slug, "message": "Instância recarregada com sucesso."}


@api_router.post("/instances/{instance_id}/tokens")
async def add_instance_token(
    instance_id: str,
    data: TokenCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Gera um novo token de acesso para a instância."""
    instance = CentralRepository.get_instance_by_id(db, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")

    if data.token is not None:
        raise HTTPException(status_code=400, detail="Tokens personalizados não são aceitos; omita o campo token.")
    token_val = f"epy_{secrets.token_urlsafe(32)}"
    token_entity = InstanceTokenEntity(
        instance_id=instance.id,
        token=hash_bearer_token(token_val),
        label=data.label,
    )
    db.add(token_entity)
    db.commit()
    await gateway_manager.reload_instance(instance.slug)

    return {"status": "success", "token": token_val, "label": data.label}


@api_router.delete("/instances/{instance_id}/tokens/{token_id}")
async def delete_instance_token(
    instance_id: str,
    token_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Revoga um token de acesso de uma instância."""
    instance = CentralRepository.get_instance_by_id(db, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")
    token_entity = (
        db.query(InstanceTokenEntity)
        .filter(InstanceTokenEntity.id == token_id, InstanceTokenEntity.instance_id == instance_id)
        .first()
    )
    if not token_entity:
        raise HTTPException(status_code=404, detail="Token não encontrado.")

    db.delete(token_entity)
    db.commit()
    await gateway_manager.reload_instance(instance.slug)
    return {"status": "success", "message": "Token revogado."}


@api_router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    instance_slug: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(require_master_admin),
) -> list[dict[str, Any]]:
    """Retorna os logs de auditoria mais recentes das execuções de ferramentas."""
    from central.db.entities import AuditLogEntity
    q = db.query(AuditLogEntity)
    if instance_slug:
        q = q.filter(AuditLogEntity.instance_slug == instance_slug)
    logs = q.order_by(AuditLogEntity.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "instance_slug": l.instance_slug,
            "tool_name": l.tool_name,
            "arguments_summary": l.arguments_summary,
            "status": l.status,
            "error_message": l.error_message,
            "execution_time_ms": l.execution_time_ms,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@api_router.get("/instances/{slug}/audit-logs")
def get_instance_audit_logs(
    slug: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Retorna os logs de auditoria específicos de uma instância."""
    from central.db.entities import AuditLogEntity
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")
    logs = (
        db.query(AuditLogEntity)
        .filter(AuditLogEntity.instance_slug == slug)
        .order_by(AuditLogEntity.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "instance_slug": l.instance_slug,
            "tool_name": l.tool_name,
            "arguments_summary": l.arguments_summary,
            "status": l.status,
            "error_message": l.error_message,
            "execution_time_ms": l.execution_time_ms,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]



# ------------------------------------------------------------------------------
# Template Instantiation & Data Source Mapping Endpoints
# ------------------------------------------------------------------------------

class CreateFromTemplateRequest(BaseModel):
    template_id: str = Field(..., description="ID do template (ex: gdrive-template, openapi-template)")
    form_values: dict[str, Any] = Field(..., description="Valores preenchidos no formulário do template")
    target_instance_slug: str = Field("demo-suite", description="Instância à qual associar a nova conexão")


class SourcesMapUpdateRequest(BaseModel):
    organization: str
    sources: list[dict[str, Any]] = Field(default_factory=list)


class NodalDataSourceCreateRequest(BaseModel):
    id: str | None = None
    name: str
    description: str = ""
    purpose: str = ""
    system: str
    tags: list[str] = Field(default_factory=list)
    authority: str = "official"
    status: str = "active"
    resource_type: str = "unspecified"
    native_resource_id: str | None = None
    primary_tools: list[str] = Field(default_factory=list)
    default_query_params: dict[str, Any] = Field(default_factory=dict)
    historical_or_alternative_sources: list[str] = Field(default_factory=list)
    version: str = "1.0"
    guidance: str = ""
    content_types: list[str] = Field(default_factory=list)


class NodalDataSourceUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    purpose: str | None = None
    system: str | None = None
    tags: list[str] | None = None
    authority: str | None = None
    status: str | None = None
    resource_type: str | None = None
    native_resource_id: str | None = None
    primary_tools: list[str] | None = None
    default_query_params: dict[str, Any] | None = None
    historical_or_alternative_sources: list[str] | None = None
    version: str | None = None
    guidance: str | None = None
    content_types: list[str] | None = None


class ToolToggleRequest(BaseModel):
    is_enabled: bool = Field(..., description="Novo estado da ferramenta nesta instância")


@api_router.get("/templates")
def list_connection_templates() -> list[dict[str, Any]]:
    """Lista todos os templates pré-configurados disponíveis para criação com 1 clique."""
    templates = get_all_templates()
    return [t.model_dump() for t in templates]


@api_router.post("/connections/from-template")
async def create_connection_from_template(
    data: CreateFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Cria uma nova conexão a partir de um template pré-definido e associa à instância."""
    tmpl = get_template_by_id(data.template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template '{data.template_id}' não encontrado.")

    vals = data.form_values
    conn_id = vals.get("id")
    if not conn_id:
        raise HTTPException(status_code=400, detail="Campo obrigatório 'id' não informado.")
    if CentralRepository.get_connection_by_id(db, conn_id):
        raise HTTPException(status_code=409, detail="O identificador de conexão já existe.")
    if tmpl.type == "stdio" and current_user.role != "epy_root":
        raise HTTPException(status_code=403, detail="Templates stdio são restritos ao master admin.")

    name = vals.get("name") or tmpl.name
    prefix = vals.get("prefix") or tmpl.default_prefix
    conn_type = tmpl.type
    command = tmpl.default_command
    args = list(tmpl.default_args)
    env = dict(tmpl.default_env)
    url = None
    auth_config = {}

    # Customizações por tipo de template
    if tmpl.id == "filesystem-template":
        allowed_dir = vals.get("allowed_dir")
        if not allowed_dir:
            raise HTTPException(status_code=400, detail="Campo 'allowed_dir' é obrigatório para Filesystem.")
        args.append(allowed_dir)

    elif tmpl.id == "postgres-template":
        conn_str = vals.get("connection_string")
        if not conn_str:
            raise HTTPException(status_code=400, detail="Campo 'connection_string' é obrigatório para PostgreSQL.")
        args.append(conn_str)

    elif tmpl.id == "periskope-template":
        api_key = vals.get("api_key")
        if api_key:
            env["PERISKOPE_API_KEY"] = api_key

    elif tmpl.id == "gdrive-template":
        allow_write = vals.get("allow_write", True)
        env["GOOGLE_DRIVE_ALLOW_WRITE"] = "true" if allow_write else "false"

    elif tmpl.id == "openapi-template":
        spec_content = vals.get("spec")
        if not spec_content:
            raise HTTPException(status_code=400, detail="Campo 'spec' (URL, JSON ou YAML) é obrigatório para OpenAPI.")
        url = vals.get("base_url") or ""
        auth_token = vals.get("auth_token")
        auth_headers = {}
        if auth_token:
            auth_headers["Authorization"] = auth_token if auth_token.lower().startswith("bearer ") else f"Bearer {auth_token}"

        auth_config = {
            "spec": spec_content,
            "base_url": url,
            "headers": auth_headers,
        }

    # Salva a conexão no SQLite
    conn = CentralRepository.create_or_update_connection(
        db=db,
        connection_id=conn_id,
        name=name,
        conn_type=conn_type,
        prefix=prefix,
        command=command,
        args=args,
        env=env,
        url=url,
        auth_config=auth_config,
        user_id=current_user.id,
    )

    # Associa à instância alvo
    target_inst = CentralRepository.get_instance_by_slug(db, data.target_instance_slug)
    if target_inst:
        require_instance_access(target_inst, current_user, db, operation="modify")
        existing_assoc = (
            db.query(InstanceConnectionEntity)
            .filter(
                InstanceConnectionEntity.instance_id == target_inst.id,
                InstanceConnectionEntity.connection_id == conn.id,
            )
            .first()
        )
        if not existing_assoc:
            assoc = InstanceConnectionEntity(
                instance_id=target_inst.id,
                connection_id=conn.id,
                is_enabled=True,
            )
            db.add(assoc)
            db.commit()

        # Recarrega a instância no gateway assíncrono para expor as novas ferramentas imediatamente
        await gateway_manager.reload_instance(data.target_instance_slug)
        gw = gateway_manager.get_instance(data.target_instance_slug)
        if gw:
            try:
                await gw._handle_list_tools(None)
            except Exception as e:
                logger.warning(f"Erro ao sincronizar tools após reload: {e}")


    return {
        "status": "success",
        "connection_id": conn.id,
        "name": conn.name,
        "prefix": conn.prefix,
        "type": conn.type,
    }


@api_router.get("/instances/{slug}/sources-map")
def get_instance_sources_map(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Retorna o Mapa de Fontes de Dados configurado para uma instância."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")
    return instance.data_sources_map or {"organization": instance.name, "sources": []}


@api_router.put("/instances/{slug}/sources-map")
async def update_instance_sources_map(
    slug: str,
    data: SourcesMapUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza as diretrizes do Mapa de Fontes de Dados e sincroniza com o gateway."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")
    ds_map_dict = {
        "organization": data.organization,
        "sources": data.sources,
    }
    updated = CentralRepository.update_instance_data_sources_map(db, slug, ds_map_dict)
    if not updated:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")

    # Atualiza o gateway em execução
    await gateway_manager.reload_instance(slug)

    return {"status": "success", "message": "Mapa de fontes atualizado com sucesso."}


# --- Endpoints de Registro Nodal de Fontes de Dados (Nodal Sources Registry) ---

@api_router.get("/instances/{slug}/sources")
def list_instance_sources_endpoint(
    slug: str,
    purpose: str | None = None,
    tag: str | None = None,
    system: str | None = None,
    authority: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Lista as fontes de dados registradas para uma instância com filtros opcionais."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")
    sources = CentralRepository.get_instance_sources(db, slug)

    if purpose:
        sources = [s for s in sources if purpose.lower() in (s.get("purpose") or "").lower()]
    if tag:
        sources = [s for s in sources if any(tag.lower() == t.lower() for t in s.get("tags", []))]
    if system:
        sources = [s for s in sources if (s.get("system") or "").lower() == system.lower()]
    if authority:
        sources = [s for s in sources if (s.get("authority") or "").lower() == authority.lower()]
    if status:
        sources = [s for s in sources if (s.get("status") or "").lower() == status.lower()]

    return {"sources": sources, "count": len(sources)}


@api_router.post("/instances/{slug}/sources")
async def create_instance_source_endpoint(
    slug: str,
    data: NodalDataSourceCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Registra uma nova fonte de dados operacional na instância (Administradores)."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")
    if current_user.role != "epy_root" and instance.user_id and instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o criador ou o master admin podem alterar fontes desta instância.")

    created = CentralRepository.add_instance_source(db, slug, data.model_dump())
    if not created:
        raise HTTPException(status_code=400, detail="Erro ao registrar fonte de dados.")

    await gateway_manager.reload_instance(slug)
    return {"status": "success", "source": created}


@api_router.get("/instances/{slug}/sources/{source_id}")
def get_instance_source_endpoint(
    slug: str,
    source_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Recupera a definição completa de uma fonte pelo ID."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")
    source = CentralRepository.get_instance_source_by_id(db, slug, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Fonte de dados '{source_id}' não encontrada.")
    return {"status": "success", "source": source}


@api_router.put("/instances/{slug}/sources/{source_id}")
async def update_instance_source_endpoint(
    slug: str,
    source_id: str,
    data: NodalDataSourceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Atualiza metadados, identificador nativo, tags ou status de uma fonte (Administradores)."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")

    updated = CentralRepository.update_instance_source(db, slug, source_id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Fonte de dados '{source_id}' não encontrada.")

    await gateway_manager.reload_instance(slug)
    return {"status": "success", "source": updated}


@api_router.delete("/instances/{slug}/sources/{source_id}")
async def delete_instance_source_endpoint(
    slug: str,
    source_id: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove uma fonte de dados do registro operacional (Administradores)."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")

    deleted = CentralRepository.delete_instance_source(db, slug, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Fonte de dados '{source_id}' não encontrada.")

    await gateway_manager.reload_instance(slug)
    return {"status": "success", "message": f"Fonte '{source_id}' excluída com sucesso."}


@api_router.get("/instances/{slug}/tools")
def list_instance_tools_state(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Lista todas as ferramentas disponíveis para uma instância e seu status ativo/inativo."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="read")

    # Conexões associadas à instância
    conns = [
        assoc.connection for assoc in instance.connection_associations
        if assoc.is_enabled and assoc.connection
    ]
    conn_ids = [c.id for c in conns]

    # Busca todas as tools dessas conexões
    from central.db.entities import ToolEntity, InstanceToolEntity
    all_tools = db.query(ToolEntity).filter(ToolEntity.connection_id.in_(conn_ids)).all()

    # Mapeia overrides de desabilitação
    disabled_tool_ids = {
        assoc.tool_id
        for assoc in instance.tool_associations
        if not assoc.is_enabled
    }

    result = []
    for t in all_tools:
        is_enabled = (t.id not in disabled_tool_ids) and (t.namespaced_name not in disabled_tool_ids)
        result.append({
            "id": t.id,
            "connection_id": t.connection_id,
            "namespaced_name": t.namespaced_name,
            "title": t.title,
            "description": t.description,
            "is_enabled": is_enabled,
        })

    return result


@api_router.post("/instances/{slug}/tools/{tool_id}/toggle")
async def toggle_tool_for_instance(
    slug: str,
    tool_id: str,
    data: ToolToggleRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
) -> dict[str, Any]:
    """Habilita ou desabilita uma ferramenta específica para uma instância (Allowlist)."""
    instance = CentralRepository.get_instance_by_slug(db, slug)
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada.")
    require_instance_access(instance, current_user, db, operation="modify")

    # Resolve o ID real da tool no banco (pode ter sido passado namespaced_name ou tool_id)
    from central.db.entities import ToolEntity
    tool_entity = db.query(ToolEntity).filter(
        (ToolEntity.id == tool_id) | (ToolEntity.namespaced_name == tool_id)
    ).first()

    if not tool_entity:
        raise HTTPException(status_code=404, detail=f"Ferramenta '{tool_id}' não encontrada no catálogo.")

    resolved_id = tool_entity.id

    CentralRepository.toggle_instance_tool(
        db=db,
        instance_id=instance.id,
        tool_id=resolved_id,
        is_enabled=data.is_enabled,
    )

    # Recarrega a instância no gateway
    await gateway_manager.reload_instance(slug)

    return {
        "status": "success",
        "instance_slug": slug,
        "tool_id": resolved_id,
        "namespaced_name": tool_entity.namespaced_name,
        "is_enabled": data.is_enabled,
    }
