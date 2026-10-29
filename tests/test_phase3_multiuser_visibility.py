"""
Integration test suite for multi-user session management, visibility isolation, and RBAC governance.
- User authentication and active session management
- Granular visibility scoping (private, shared, public)
- Master admin governance enforcement (only root can publish public assets)
- Connection template creation and instantiation
- Data-Source Kit presets and instance application
"""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from central.config import settings
from central.db.entities import ConnectionEntity, UserEntity, UserSessionEntity
from central.db.session import get_db
from central.server import app


@pytest.mark.asyncio
async def test_user_session_and_switch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login com admin_key para obter sessão root
        res = await client.post("/api/v1/auth/login", json={"username": "epy_root", "admin_key": settings.CENTRAL_ADMIN_KEY})
        assert res.status_code == 200
        root_data = res.json()
        assert root_data["user"]["role"] == "epy_root"
        root_token = root_data["token"]

        # 2. Verifica /auth/me com token de sessão
        me_res = await client.get("/api/v1/auth/me", headers={"X-Central-Session-Token": root_token})
        assert me_res.status_code == 200
        assert me_res.json()["username"] == "epy_root"
        assert me_res.json()["is_master_admin"] is True

        # 3. Cria usuário padrão via root
        test_user = f"analista_{uuid.uuid4().hex[:6]}"
        user_res = await client.post(
            "/api/v1/users",
            headers={"X-Central-Session-Token": root_token},
            json={"username": test_user, "role": "standard", "display_name": "Analista de Operações"},
        )
        assert user_res.status_code == 200
        assert user_res.json()["user"]["username"] == test_user
        assert user_res.json()["user"]["role"] == "standard"

        # 4. Alterna sessão para o novo usuário
        switch_res = await client.post("/api/v1/auth/switch-user", json={"username": test_user})
        assert switch_res.status_code == 200
        analista_token = switch_res.json()["token"]

        # 5. Verifica /auth/me para o analista
        analista_me = await client.get("/api/v1/auth/me", headers={"X-Central-Session-Token": analista_token})
        assert analista_me.status_code == 200
        assert analista_me.json()["username"] == test_user
        assert analista_me.json()["is_master_admin"] is False


@pytest.mark.asyncio
async def test_strict_governance_public_rule():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Obtém sessão para standard user
        switch_res = await client.post("/api/v1/auth/switch-user", json={"username": "standard_user_gov"})
        standard_token = switch_res.json()["token"]
        headers_standard = {"X-Central-Session-Token": standard_token}

        # 1. Usuário padrão tentando criar CONEXÃO pública -> DEVE FALHAR (403)
        conn_res = await client.post(
            "/api/v1/connections",
            headers=headers_standard,
            json={
                "id": "conn_test_public_fail",
                "name": "Conexão Pública Não Autorizada",
                "type": "internal",
                "prefix": "test_pub",
                "visibility": "public",
            },
        )
        assert conn_res.status_code == 403
        assert "Apenas administradores master" in conn_res.json()["detail"]

        # 2. Usuário padrão tentando criar INSTÂNCIA pública -> DEVE FALHAR (403)
        inst_res = await client.post(
            "/api/v1/instances",
            headers=headers_standard,
            json={
                "slug": "inst-test-public-fail",
                "name": "Instância Pública Não Autorizada",
                "visibility": "public",
            },
        )
        assert inst_res.status_code == 403
        assert "Apenas administradores master" in inst_res.json()["detail"]

        # 3. Usuário padrão tentando criar MODELO DE CONEXÃO público -> DEVE FALHAR (403)
        tmpl_res = await client.post(
            "/api/v1/connection-templates",
            headers=headers_standard,
            json={
                "name": "Template Público Inválido",
                "type": "internal",
                "prefix": "fail",
                "visibility": "public",
            },
        )
        assert tmpl_res.status_code == 403
        assert "Apenas administradores master" in tmpl_res.json()["detail"]

        # 4. Usuário padrão tentando criar KIT DE DADOS público -> DEVE FALHAR (403)
        kit_res = await client.post(
            "/api/v1/data-source-kits",
            headers=headers_standard,
            json={
                "name": "Kit Público Inválido",
                "visibility": "public",
                "sources": [],
            },
        )
        assert kit_res.status_code == 403
        assert "Apenas administradores master" in kit_res.json()["detail"]

        # 5. Master Admin criando entidade pública -> DEVE TER SUCESSO (200)
        headers_root = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
        root_conn_res = await client.post(
            "/api/v1/connections",
            headers=headers_root,
            json={
                "id": "conn_test_public_success",
                "name": "Conexão Pública Oficial",
                "type": "internal",
                "prefix": "test_pub_ok",
                "visibility": "public",
            },
        )
        assert root_conn_res.status_code == 200
        assert root_conn_res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_visibility_isolation_between_users():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Usuário Alice cria conexão privada
        alice_login = await client.post("/api/v1/auth/switch-user", json={"username": "alice"})
        alice_token = alice_login.json()["token"]

        await client.post(
            "/api/v1/connections",
            headers={"X-Central-Session-Token": alice_token},
            json={
                "id": "alice_secret_conn",
                "name": "Conexão Privada da Alice",
                "type": "internal",
                "prefix": "alice_pvt",
                "visibility": "private",
            },
        )

        # Alice lista conexões -> deve enxergar sua conexão privada
        alice_list = await client.get("/api/v1/connections", headers={"X-Central-Session-Token": alice_token})
        alice_ids = [c["id"] for c in alice_list.json()]
        assert "alice_secret_conn" in alice_ids

        # Usuário Bob lista conexões -> NÃO DEVE enxergar a conexão privada de Alice
        bob_login = await client.post("/api/v1/auth/switch-user", json={"username": "bob"})
        bob_token = bob_login.json()["token"]

        bob_list = await client.get("/api/v1/connections", headers={"X-Central-Session-Token": bob_token})
        bob_ids = [c["id"] for c in bob_list.json()]
        assert "alice_secret_conn" not in bob_ids

        # Master Admin lista conexões -> DEVE enxergar tudo
        root_list = await client.get("/api/v1/connections", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY})
        root_ids = [c["id"] for c in root_list.json()]
        assert "alice_secret_conn" in root_ids


@pytest.mark.asyncio
async def test_connection_template_and_instantiation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}

        # 1. Salva conexão existente como template
        save_res = await client.post(
            "/api/v1/connections/internal/save-as-template",
            headers=headers,
            json={"name": "Modelo Gateway Interno", "description": "Template para testes", "visibility": "shared"},
        )
        assert save_res.status_code == 200
        template_id = save_res.json()["template_id"]

        # 2. Lista templates
        list_res = await client.get("/api/v1/connection-templates", headers=headers)
        assert list_res.status_code == 200
        tmpl_ids = [t["id"] for t in list_res.json()]
        assert template_id in tmpl_ids

        # 3. Instancia uma nova conexão a partir do template
        inst_res = await client.post(
            f"/api/v1/connection-templates/{template_id}/instantiate",
            headers=headers,
            json={
                "connection_id": "instantiated_internal_conn",
                "name": "Conexão Instanciada via Modelo",
                "prefix": "inst_prefix",
                "visibility": "shared",
            },
        )
        assert inst_res.status_code == 200
        assert inst_res.json()["connection_id"] == "instantiated_internal_conn"


@pytest.mark.asyncio
async def test_data_source_kit_and_application():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}

        # 1. Salva data sources da instância exampleco-suite como um Kit
        kit_res = await client.post(
            "/api/v1/instances/exampleco-suite/save-as-kit",
            headers=headers,
            json={
                "name": "Kit Operações ExampleCo Padrão",
                "category": "Operações",
                "description": "Kit oficial com Drive e Periskope",
                "visibility": "shared",
            },
        )
        assert kit_res.status_code == 200
        kit_id = kit_res.json()["kit_id"]

        # 2. Lista os kits cadastrados
        kits_list = await client.get("/api/v1/data-source-kits", headers=headers)
        assert kits_list.status_code == 200
        kit_ids = [k["id"] for k in kits_list.json()]
        assert kit_id in kit_ids

        # 3. Cria uma instância secundária
        await client.post(
            "/api/v1/instances",
            headers=headers,
            json={"slug": "suite-secundaria", "name": "Suite Secundária", "visibility": "shared"},
        )

        # 4. Aplica o kit à instância secundária
        apply_res = await client.post(
            f"/api/v1/data-source-kits/{kit_id}/apply-to-instance/suite-secundaria",
            headers=headers,
        )
        assert apply_res.status_code == 200
        assert apply_res.json()["status"] == "success"
        assert apply_res.json()["sources_count"] >= 1
