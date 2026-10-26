"""
Unit and integration test suite for core MCP gateway persistence and API endpoints.
"""

import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport

from central.config import settings
from central.db.entities import AuditLogEntity, ToolEntity
from central.db.repository import CentralRepository
from central.db.seeder import init_database
from central.db.session import get_db_context
from central.gateway.manager import gateway_manager
from central.server import app


@pytest.fixture(scope="module", autouse=True)
def setup_phase1_database():
    """Garante que o banco de dados SQLite está inicializado antes dos testes."""
    init_database(settings.CONFIG_PATH)
    gateway_manager.load_from_db()


@pytest.mark.asyncio
async def test_database_persistence_and_seeding():
    with get_db_context() as db:
        # 1. Verifica usuário root
        overview = CentralRepository.get_system_overview(db)
        assert overview["total_instances"] >= 1
        assert overview["total_connections"] >= 3

        # 2. Verifica instância horst-suite
        instance = CentralRepository.get_instance_by_slug(db, "horst-suite")
        assert instance is not None
        assert instance.slug == "horst-suite"
        assert len(instance.tokens) >= 1
        assert any(t.token == "epy_dev_token_123" for t in instance.tokens)

        # 3. Verifica conexões migradas
        connections = CentralRepository.get_all_connections(db)
        conn_ids = [c.id for c in connections]
        assert "internal" in conn_ids
        assert "gdrive" in conn_ids
        assert "periskope" in conn_ids


@pytest.mark.asyncio
async def test_admin_api_endpoints():
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:

        # 1. Overview
        res = await client.get("/api/v1/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["total_instances"] >= 1
        assert "success_rate" in data

        # 2. Conexões
        res = await client.get("/api/v1/connections")
        assert res.status_code == 200
        conns = res.json()
        assert len(conns) >= 3
        assert any(c["id"] == "gdrive" for c in conns)

        # 3. Instâncias
        res = await client.get("/api/v1/instances")
        assert res.status_code == 200
        instances = res.json()
        assert len(instances) >= 1
        assert any(i["slug"] == "horst-suite" for i in instances)

        # 4. Catálogo de Tools
        res = await client.get("/api/v1/tools?limit=10")
        assert res.status_code == 200
        tools_data = res.json()
        assert "items" in tools_data
        assert "total" in tools_data


@pytest.mark.asyncio
async def test_tool_call_audit_logging():
    # 1. Inicia o gateway e executa uma chamada via MCP
    await gateway_manager.start_all()
    gateway = gateway_manager.get_instance("horst-suite")
    assert gateway is not None

    import mcp.types as types
    call_params = types.CallToolRequestParams(name="central__ping", arguments={"test_arg": "fase1_val"})
    result = await gateway._handle_call_tool(None, call_params)
    assert not result.is_error
    assert "Pong! Epyatis MCP Central" in result.content[0].text

    # 2. Verifica se o log de auditoria foi gravado no banco SQLite
    with get_db_context() as db:
        recent_logs = CentralRepository.get_recent_audit_logs(db, limit=5)
        assert len(recent_logs) >= 1
        latest = recent_logs[0]
        assert latest.instance_slug == "horst-suite"
        assert latest.tool_name == "central__ping"
        assert latest.status == "success"
        assert latest.execution_time_ms >= 0

    # 3. Testa consulta de logs via API REST
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.get("/api/v1/logs?limit=5")
        assert res.status_code == 200

        logs = res.json()
        assert len(logs) >= 1
        assert logs[0]["tool_name"] == "central__ping"

    await gateway_manager.stop_all()


@pytest.mark.asyncio
async def test_web_ui_dashboard_rendering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text
        assert "Epyatis" in html
        assert "Central Gateway" in html
        assert "centralApp()" in html
