"""
Integration test suite for:
- User registration with one-time invite code (instant activation)
- User registration without invite code (pending approval workflow)
- Master Admin approvals and rejections
- PBKDF2 password authentication
- Granular sharing ACL (private, shared with specific users, public)
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from central.config import settings
from central.server import app


@pytest.mark.asyncio
async def test_auth_registration_and_login_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Master admin logs in
        root_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "epy_root", "admin_key": settings.CENTRAL_ADMIN_KEY},
        )
        assert root_login.status_code == 200
        root_token = root_login.json()["token"]
        headers_root = {"X-Central-Session-Token": root_token}

        # 2. Registration WITHOUT invite -> pending approval
        reg_username = f"novo_dev_{uuid.uuid4().hex[:6]}"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "username": reg_username,
                "password": "SenhaForte123!",
                "display_name": "Desenvolvedor Externo",
            },
        )
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert reg_data["status"] == "pending_approval"
        assert "aguardando aprovação" in reg_data["message"]

        # 3. User tries to log in while pending -> 403 Forbidden
        pending_login = await client.post(
            "/api/v1/auth/login",
            json={"username": reg_username, "password": "SenhaForte123!"},
        )
        assert pending_login.status_code == 403
        assert "aguardando aprovação" in pending_login.json()["detail"]

        # 4. Master Admin lists pending users
        pending_res = await client.get("/api/v1/admin/pending-users", headers=headers_root)
        assert pending_res.status_code == 200
        pending_list = pending_res.json()
        user_entry = next((u for u in pending_list if u["username"] == reg_username), None)
        assert user_entry is not None
        pending_user_id = user_entry["id"]

        # 5. Master Admin approves the user
        approve_res = await client.post(
            f"/api/v1/admin/pending-users/{pending_user_id}/approve",
            headers=headers_root,
        )
        assert approve_res.status_code == 200

        # 6. Now user logs in successfully with password!
        user_login = await client.post(
            "/api/v1/auth/login",
            json={"username": reg_username, "password": "SenhaForte123!"},
        )
        assert user_login.status_code == 200
        assert "token" in user_login.json()
        dev_token = user_login.json()["token"]

        # 7. Wrong password fails
        wrong_pwd = await client.post(
            "/api/v1/auth/login",
            json={"username": reg_username, "password": "SenhaErrada!"},
        )
        assert wrong_pwd.status_code == 401


@pytest.mark.asyncio
async def test_invite_code_registration_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Master admin generates a 24h invite
        headers_root = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
        invite_create = await client.post(
            "/api/v1/admin/invites",
            headers=headers_root,
            json={"expires_hours": 24, "role": "standard"},
        )
        assert invite_create.status_code == 200
        invite_code = invite_create.json()["invite"]["code"]
        assert invite_code

        # 2. Register WITH invite code -> instantly approved and logged in
        invited_user = f"convidado_{uuid.uuid4().hex[:6]}"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "username": invited_user,
                "password": "SenhaSegura456!",
                "display_name": "Usuário Convidado",
                "invite_code": invite_code,
            },
        )
        assert reg_res.status_code == 200
        data = reg_res.json()
        assert data["status"] == "approved"
        assert "token" in data

        # 3. Attempting to reuse the same single-use invite must fail
        reuse_res = await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"invasor_{uuid.uuid4().hex[:6]}",
                "password": "SenhaSegura456!",
                "invite_code": invite_code,
            },
        )
        assert reuse_res.status_code == 400
        assert "já foi utilizado" in reuse_res.json()["detail"]


@pytest.mark.asyncio
async def test_granular_connection_sharing_acl():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create users: Alice, Bob, and Carlos
        alice_login = await client.post("/api/v1/auth/switch-user", json={"username": "alice_acl"})
        alice_token = alice_login.json()["token"]
        alice_headers = {"X-Central-Session-Token": alice_token}
        alice_id = alice_login.json()["user"]["id"]

        bob_login = await client.post("/api/v1/auth/switch-user", json={"username": "bob_acl"})
        bob_token = bob_login.json()["token"]
        bob_headers = {"X-Central-Session-Token": bob_token}
        bob_id = bob_login.json()["user"]["id"]

        carlos_login = await client.post("/api/v1/auth/switch-user", json={"username": "carlos_acl"})
        carlos_token = carlos_login.json()["token"]
        carlos_headers = {"X-Central-Session-Token": carlos_token}

        # 1. Alice creates a shared connection
        conn_id = f"conn_shared_{uuid.uuid4().hex[:6]}"
        create_res = await client.post(
            "/api/v1/connections",
            headers=alice_headers,
            json={
                "id": conn_id,
                "name": "Conexão Compartilhada Alice",
                "type": "internal",
                "prefix": "ashare",
                "visibility": "shared",
            },
        )
        assert create_res.status_code == 200

        # Before sharing with Bob: Bob does NOT see it
        bob_conns = await client.get("/api/v1/connections", headers=bob_headers)
        bob_cids = [c["id"] for c in bob_conns.json()]
        assert conn_id not in bob_cids

        # 2. Alice explicitly shares the connection with Bob
        share_res = await client.put(
            f"/api/v1/connections/{conn_id}/shares",
            headers=alice_headers,
            json={"user_ids": [bob_id]},
        )
        assert share_res.status_code == 200
        assert share_res.json()["shared_user_ids"] == [bob_id]

        # 3. Bob now sees it!
        bob_conns_after = await client.get("/api/v1/connections", headers=bob_headers)
        bob_cids_after = [c["id"] for c in bob_conns_after.json()]
        assert conn_id in bob_cids_after

        # 4. Carlos was NOT selected -> Carlos does NOT see it!
        carlos_conns = await client.get("/api/v1/connections", headers=carlos_headers)
        carlos_cids = [c["id"] for c in carlos_conns.json()]
        assert conn_id not in carlos_cids

        # 5. Master admin sees it regardless
        root_conns = await client.get("/api/v1/connections", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY})
        root_cids = [c["id"] for c in root_conns.json()]
        assert conn_id in root_cids


@pytest.mark.asyncio
async def test_granular_instance_sharing_acl():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create users
        alice_login = await client.post("/api/v1/auth/switch-user", json={"username": "alice_inst"})
        alice_token = alice_login.json()["token"]
        alice_headers = {"X-Central-Session-Token": alice_token}

        bob_login = await client.post("/api/v1/auth/switch-user", json={"username": "bob_inst"})
        bob_token = bob_login.json()["token"]
        bob_headers = {"X-Central-Session-Token": bob_token}
        bob_id = bob_login.json()["user"]["id"]

        carlos_login = await client.post("/api/v1/auth/switch-user", json={"username": "carlos_inst"})
        carlos_token = carlos_login.json()["token"]
        carlos_headers = {"X-Central-Session-Token": carlos_token}

        # 1. Alice creates a shared instance
        slug = f"inst-shared-{uuid.uuid4().hex[:6]}"
        create_res = await client.post(
            "/api/v1/instances",
            headers=alice_headers,
            json={
                "slug": slug,
                "name": "Instância Compartilhada da Alice",
                "visibility": "shared",
            },
        )
        assert create_res.status_code == 200

        # Before sharing: Bob does NOT see it
        bob_list = await client.get("/api/v1/instances", headers=bob_headers)
        assert slug not in [i["slug"] for i in bob_list.json()]

        # 2. Alice shares with Bob
        share_res = await client.put(
            f"/api/v1/instances/{slug}/shares",
            headers=alice_headers,
            json={"user_ids": [bob_id]},
        )
        assert share_res.status_code == 200
        assert share_res.json()["shared_user_ids"] == [bob_id]

        # 3. Bob now sees it
        bob_list_after = await client.get("/api/v1/instances", headers=bob_headers)
        assert slug in [i["slug"] for i in bob_list_after.json()]

        # 4. Carlos still does NOT see it
        carlos_list = await client.get("/api/v1/instances", headers=carlos_headers)
        assert slug not in [i["slug"] for i in carlos_list.json()]

