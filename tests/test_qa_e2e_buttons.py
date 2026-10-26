"""
Script de Teste de QA Completo - Validação "Botão a Botão" e End-to-End do Epyatis MCP Central.

Testa:
1. Integridade do banco de dados SQLite (WAL mode, PRAGMA integrity, tabelas)
2. Healthcheck e status do gateway (/health)
3. Rota raiz da Interface Web (Dashboard HTML com Alpine.js e Tailwind)
4. Rota de Métricas e Overview (/api/v1/overview)
5. Rota de Conexões (/api/v1/connections)
6. Catálogo de Ferramentas e Busca (/api/v1/tools?query=...)
7. Instâncias e Tokens (/api/v1/instances)
8. Catálogo de Templates (/api/v1/templates)
9. Botão/Ação: Adicionar Conexão via Template (POST /api/v1/connections/from-template)
10. Botão/Ação: Gerenciar Ferramentas (Toggles de allowlist granular na instância)
11. Botão/Ação: Editor do Mapa de Fontes de Dados (GET e PUT /api/v1/instances/{slug}/sources-map)
12. Botão/Ação: Recarregar Instância (POST /api/v1/instances/{slug}/reload)
13. Botão/Ação: Histórico e Logs de Auditoria (/api/v1/logs e /api/v1/instances/{slug}/audit-logs)
14. Protocolo MCP End-to-End (list_tools e call_tool com interceptador de auditoria)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from central.config import settings
from central.db.entities import (
    ConnectionEntity,
    InstanceEntity,
    ToolEntity,
    AuditLogEntity,
)
from central.db.repository import CentralRepository
from central.db.seeder import init_database
from central.db.session import get_db_context
from central.gateway.manager import gateway_manager
from central.server import app


@pytest.fixture(scope="module", autouse=True)
def setup_qa_suite():
    """Garante que a base está migrada e carregada antes dos testes de QA."""
    init_database(settings.CONFIG_PATH)
    gateway_manager.load_from_db()


@pytest.mark.asyncio
async def test_qa_01_database_integrity():
    """Valida integridade estrutural do banco de dados SQLite."""
    with get_db_context() as session:
        # 1. Verifica modo WAL
        journal_mode = session.execute(text("PRAGMA journal_mode;")).scalar()
        assert journal_mode.lower() == "wal", f"Esperado WAL mode, obtido {journal_mode}"

        # 2. Verifica integridade do arquivo SQLite
        integrity = session.execute(text("PRAGMA integrity_check;")).scalar()
        assert integrity == "ok", f"Integridade falhou: {integrity}"

        # 3. Verifica contagem de tabelas essenciais
        conn_count = session.query(ConnectionEntity).count()
        inst_count = session.query(InstanceEntity).count()
        tool_count = session.query(ToolEntity).count()

        assert conn_count >= 1, "Deve haver conexões registradas no banco"
        assert inst_count >= 1, "Deve haver pelo menos 1 instância registrada"
        assert tool_count >= 1, "Deve haver ferramentas catalogadas no banco"


@pytest.mark.asyncio
async def test_qa_02_health_check():
    """Valida endpoint /health."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "instances" in data
        assert "horst-suite" in data["instances"]


@pytest.mark.asyncio
async def test_qa_03_dashboard_ui_rendering():
    """Valida carregamento completo da interface web do Dashboard (HTML, Alpine.js, Tailwind, modais)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        html = res.text
        assert "Epyatis" in html
        assert "Central Gateway" in html
        assert 'x-data="centralApp()"' in html
        assert "showTemplateModal" in html
        assert "showUserModal" in html
        assert "showSaveAsTemplateModal" in html
        assert "showInstantiateModal" in html
        assert "sourcesMapData" in html


@pytest.mark.asyncio
async def test_qa_04_overview_kpis():
    """Valida KPIs da Visão Geral (Instâncias Ativas, Conexões, Ferramentas, Taxa de Sucesso)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["active_instances"] >= 1
        assert data["total_connections"] >= 1
        assert data["total_tools"] >= 1
        assert "success_rate" in data
        assert "total_calls" in data


@pytest.mark.asyncio
async def test_qa_05_connections_tab():
    """Valida listagem de conexões upstream da aba Conexões."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/connections")
        assert res.status_code == 200
        conns = res.json()
        assert isinstance(conns, list)
        assert len(conns) >= 1
        types = [c["type"] for c in conns]
        assert any(t in ["internal", "stdio", "sse", "openapi"] for t in types)


@pytest.mark.asyncio
async def test_qa_06_tools_catalog_and_filter():
    """Valida catálogo de tools, paginação e filtro por busca de texto."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/tools?limit=50")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

        # Busca por ferramenta de ping ou data sources map
        res_search = await client.get("/api/v1/tools?query=data_sources_map")
        assert res_search.status_code == 200
        search_data = res_search.json()
        assert any("data_sources_map" in item["namespaced_name"] for item in search_data["items"])


@pytest.mark.asyncio
async def test_qa_07_instances_tab_and_tokens():
    """Valida listagem de instâncias, conexões agregadas e tokens para agentes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/instances")
        assert res.status_code == 200
        instances = res.json()
        assert len(instances) >= 1
        horst = next((i for i in instances if i["slug"] == "horst-suite"), None)
        assert horst is not None
        assert len(horst["tokens"]) >= 1
        assert horst["tokens"][0]["token"] is not None


@pytest.mark.asyncio
async def test_qa_08_templates_catalog():
    """Valida catálogo de templates pré-configurados (1-clique)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/templates")
        assert res.status_code == 200
        templates = res.json()
        tmpl_ids = [t["id"] for t in templates]
        assert "gdrive-template" in tmpl_ids
        assert "periskope-template" in tmpl_ids
        assert "filesystem-template" in tmpl_ids
        assert "postgres-template" in tmpl_ids
        assert "openapi-template" in tmpl_ids


@pytest.mark.asyncio
async def test_qa_09_button_add_connection_from_template():
    """Valida botão/ação 'Adicionar via Template' criando conexão OpenAPI mock."""
    payload = {
        "template_id": "openapi-template",
        "form_values": {
            "id": "qa_pet_store",
            "name": "QA Petstore API",
            "prefix": "qa_pet",
            "base_url": "https://api.example.com/v1",
            "spec": """
openapi: 3.0.0
info:
  title: QA Petstore API
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets for QA
      operationId: listPets
      responses:
        '200':
          description: A list of pets
            """,
        },
        "target_instance_slug": "horst-suite",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.post("/api/v1/connections/from-template", json=payload)
        assert res.status_code in [200, 201]
        conn = res.json()
        assert conn["name"] == "QA Petstore API"
        assert conn["prefix"] == "qa_pet"

        # Confirma que a tool foi catalogada
        res_tools = await client.get("/api/v1/tools?query=qa_pet")
        assert res_tools.status_code == 200
        tools = res_tools.json()["items"]
        assert any("qa_pet__listPets" in t["namespaced_name"] for t in tools)


@pytest.mark.asyncio
async def test_qa_10_button_toggle_instance_tool():
    """Valida botão de toggle/allowlist granular (Habilitar/Desabilitar tool para instância)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        # 1. Busca tools da instância
        res = await client.get("/api/v1/instances/horst-suite/tools")
        assert res.status_code == 200
        inst_tools = res.json()
        assert len(inst_tools) >= 1

        target = inst_tools[0]
        target_id = target["id"]
        original_state = target["is_enabled"]

        # 2. Desabilita a tool (ou inverte o estado)
        res_toggle = await client.post(
            f"/api/v1/instances/horst-suite/tools/{target_id}/toggle",
            json={"is_enabled": not original_state},
        )
        assert res_toggle.status_code == 200
        updated = res_toggle.json()
        assert updated["is_enabled"] == (not original_state)

        # 3. Restaura o estado original
        res_restore = await client.post(
            f"/api/v1/instances/horst-suite/tools/{target_id}/toggle",
            json={"is_enabled": original_state},
        )
        assert res_restore.status_code == 200
        restored = res_restore.json()
        assert restored["is_enabled"] == original_state


@pytest.mark.asyncio
async def test_qa_11_button_sources_map_editor():
    """Valida botão e formulário 'Salvar Diretrizes' do Mapa de Fontes de Dados."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        # 1. Carrega dados atuais
        res_get = await client.get("/api/v1/instances/horst-suite/sources-map")
        assert res_get.status_code == 200
        current_map = res_get.json()

        # 2. Atualiza com uma nova fonte de teste de QA
        test_update = {
            "organization": "Horst QA Automation",
            "sources": [
                {
                    "name": "Diretrizes de QA",
                    "system": "qa_system",
                    "guidance": "Consultar este sistema sempre que realizar testes de aceitação automatizados.",
                }
            ],
        }
        res_put = await client.put("/api/v1/instances/horst-suite/sources-map", json=test_update)
        assert res_put.status_code == 200
        res_check = await client.get("/api/v1/instances/horst-suite/sources-map")
        assert res_check.status_code == 200
        saved = res_check.json()
        assert saved["organization"] == "Horst QA Automation"

        # 3. Restaura o mapa anterior para manter consistência
        res_restore = await client.put("/api/v1/instances/horst-suite/sources-map", json=current_map)
        assert res_restore.status_code == 200


@pytest.mark.asyncio
async def test_qa_12_button_reload_instance():
    """Valida botão 'Recarregar Instância'."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.post("/api/v1/instances/horst-suite/reload")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_qa_13_audit_logs_history():
    """Valida abas e endpoints de Logs de Auditoria."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}) as client:

        res = await client.get("/api/v1/logs?limit=10")
        assert res.status_code == 200
        logs = res.json()
        assert isinstance(logs, list)

        res_inst = await client.get("/api/v1/instances/horst-suite/audit-logs?limit=10")
        assert res_inst.status_code == 200
        inst_logs = res_inst.json()
        assert isinstance(inst_logs, list)


@pytest.mark.asyncio
async def test_qa_14_mcp_protocol_live_tool_call():
    """Valida protocolo MCP real via gateway_manager (list_tools e call_tool com gravação de auditoria)."""
    gw = gateway_manager.get_instance("horst-suite")
    assert gw is not None

    # 1. Lista tools pelo protocolo MCP
    list_result = await gw._handle_list_tools(None)
    tools = list_result.tools
    tool_names = [t.name for t in tools]
    assert "central__get_data_sources_map" in tool_names
    assert "central__ping" in tool_names

    # 2. Chama a tool central__ping
    import mcp.types as types
    ping_res = await gw._handle_call_tool(None, types.CallToolRequestParams(name="central__ping", arguments={}))
    assert ping_res.is_error is False
    assert len(ping_res.content) >= 1
    assert "pong" in ping_res.content[0].text.lower()

    # 3. Chama a tool central__get_data_sources_map
    map_res = await gw._handle_call_tool(None, types.CallToolRequestParams(name="central__get_data_sources_map", arguments={}))
    assert map_res.is_error is False
    assert "Fontes de Dados" in map_res.content[0].text or "Horst" in map_res.content[0].text

