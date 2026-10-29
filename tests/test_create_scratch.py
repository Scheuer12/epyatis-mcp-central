"""
Testes de criação de Conexões e Modelos (Templates) do zero (sem presets).
Valida:
1. Criação de Conexão Manual (stdio, remote_mcp, openapi) via POST /api/v1/connections.
2. Vinculação direta de conexão manual a uma instância via POST /api/v1/instances/{slug}/connections.
3. Criação de Modelo (Template) do zero via POST /api/v1/connection-templates.
4. Instanciação de conexão a partir do modelo criado do zero.
5. Presença dos elementos de UI e hooks do Alpine no Dashboard HTML.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from central.config import settings
from central.server import app


@pytest.mark.asyncio
async def test_create_connection_scratch_stdio():
    """Cria conexão stdio manual sem template."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        payload = {
            "id": "scratch-sqlite-conn",
            "name": "SQLite Scratch Connection",
            "type": "stdio",
            "prefix": "sqlite_scratch",
            "command": "python",
            "args": ["-c", "print('mcp_scratch')"],
            "env": {"DB_PATH": "/tmp/test.db"},
            "visibility": "shared",
        }
        res = await client.post("/api/v1/connections", json=payload)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "success"
        assert data["connection_id"] == "scratch-sqlite-conn"

        # Busca detalhes da conexão
        get_res = await client.get("/api/v1/connections")
        assert get_res.status_code == 200
        conns = get_res.json()
        matching = [c for c in conns if c["id"] == "scratch-sqlite-conn"]
        assert len(matching) == 1
        assert matching[0]["name"] == "SQLite Scratch Connection"
        assert matching[0]["prefix"] == "sqlite_scratch"
        assert matching[0]["command"] == "python"

        # Limpeza
        await client.delete("/api/v1/connections/scratch-sqlite-conn")


@pytest.mark.asyncio
async def test_create_connection_scratch_remote_and_attach():
    """Cria conexão remota (remote_mcp) e vincula à instância exampleco-suite."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        payload = {
            "id": "scratch-remote-api",
            "name": "Remote API MCP",
            "type": "remote_mcp",
            "prefix": "remote_api",
            "url": "https://mcp.exemplo.com/sse",
            "auth_config": {"Authorization": "Bearer secret-token-xyz"},
            "visibility": "shared",
        }
        res = await client.post("/api/v1/connections", json=payload)
        assert res.status_code == 200, res.text

        # Vincula à instância exampleco-suite
        attach_res = await client.post(
            "/api/v1/instances/exampleco-suite/connections",
            json={"connection_id": "scratch-remote-api"},
        )
        assert attach_res.status_code == 200, attach_res.text

        # Verifica na instância
        inst_res = await client.get("/api/v1/instances/exampleco-suite")
        assert inst_res.status_code == 200
        inst_data = inst_res.json()
        attached_ids = [c["id"] for c in inst_data.get("connections", [])]
        assert "scratch-remote-api" in attached_ids

        # Desvincula e remove para limpeza
        await client.delete("/api/v1/instances/exampleco-suite/connections/scratch-remote-api")
        await client.delete("/api/v1/connections/scratch-remote-api")


@pytest.mark.asyncio
async def test_create_template_from_scratch():
    """Cria um novo modelo de conexão diretamente do zero (sem precisar partir de uma conexão)."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        payload = {
            "name": "Postgres Custom Recipe",
            "description": "Modelo de conexão PostgreSQL customizado para analytics",
            "type": "stdio",
            "prefix": "pg_custom",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
            "env": {"DATABASE_URL": "postgresql://user:pass@localhost:5432/analytics"},
            "visibility": "shared",
        }
        res = await client.post("/api/v1/connection-templates", json=payload)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "success"
        template_id = data["template_id"]

        # Busca o modelo criado
        tmpl_res = await client.get(f"/api/v1/connection-templates/{template_id}")
        assert tmpl_res.status_code == 200
        tmpl = tmpl_res.json()
        assert tmpl["name"] == "Postgres Custom Recipe"
        assert tmpl["prefix"] == "pg_custom"
        assert tmpl["command"] == "npx"

        # Instancia uma conexão a partir deste novo modelo
        instantiate_res = await client.post(
            f"/api/v1/connection-templates/{template_id}/instantiate",
            json={
                "connection_id": "pg-analytics-instantiated",
                "name": "Postgres Analytics Produção",
                "env_overrides": {"DATABASE_URL": "postgresql://prod_user:secret@prod:5432/analytics"},
                "visibility": "shared",
            },
        )
        assert instantiate_res.status_code == 200, instantiate_res.text
        assert instantiate_res.json()["connection_id"] == "pg-analytics-instantiated"

        # Limpeza
        await client.delete("/api/v1/connections/pg-analytics-instantiated")
        await client.delete(f"/api/v1/connection-templates/{template_id}")


@pytest.mark.asyncio
async def test_ui_dashboard_scratch_creation_elements():
    """Valida presença dos novos modais e botões de criação manual no Dashboard HTML."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text

        # Hooks e estados Alpine
        assert "showCreateConnectionModal" in html
        assert "newConnectionForm" in html
        assert "showCreateTemplateModal" in html
        assert "newTemplateForm" in html

        # Métodos Alpine
        assert "openCreateConnectionModal" in html
        assert "submitCreateConnection" in html
        assert "openCreateTemplateModal" in html
        assert "submitCreateTemplate" in html

        # Rótulos amigáveis de botões
        assert "Nova Conexão Manual" in html
        assert "Novo Modelo" in html
        assert "Novo Modelo do Zero" in html
