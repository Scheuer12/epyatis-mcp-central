"""
Integration test suite for connection templates, tool allowlists, and dynamic OpenAPI upstreams.
"""

import json
import pytest
from httpx import AsyncClient, ASGITransport

from central.config import settings
from central.db.repository import CentralRepository
from central.db.seeder import init_database
from central.db.session import get_db_context
from central.gateway.manager import gateway_manager
from central.server import app
from central.templates_catalog.registry import get_all_templates, get_template_by_id
from central.upstreams.openapi_upstream import OpenApiUpstream


@pytest.fixture(scope="module", autouse=True)
def setup_phase2_database():
    init_database(settings.CONFIG_PATH)
    gateway_manager.load_from_db()


@pytest.mark.asyncio
async def test_templates_catalog_and_registry():
    templates = get_all_templates()
    assert len(templates) >= 5
    tmpl_ids = [t.id for t in templates]
    assert "gdrive-template" in tmpl_ids
    assert "periskope-template" in tmpl_ids
    assert "filesystem-template" in tmpl_ids
    assert "postgres-template" in tmpl_ids
    assert "openapi-template" in tmpl_ids

    # Testa API GET /api/v1/templates
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.get("/api/v1/templates")
        assert res.status_code == 200

        data = res.json()
        assert len(data) >= 5


@pytest.mark.asyncio
async def test_openapi_upstream_engine():
    # Especificação OpenAPI 3.0 simulada
    sample_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test ERP API", "version": "1.0.0"},
        "servers": [{"url": "https://httpbin.org"}],
        "paths": {
            "/status/{code}": {
                "get": {
                    "operationId": "get_status",
                    "summary": "Retorna o código de status HTTP",
                    "parameters": [
                        {"name": "code", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ]
                }
            },
            "/post": {
                "post": {
                    "operationId": "create_item",
                    "summary": "Cria um novo item",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "price": {"type": "number"}
                                    },
                                    "required": ["title"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    upstream = OpenApiUpstream(
        connection_id="test_erp",
        prefix="erp",
        spec=sample_spec,
    )
    await upstream.start()
    assert await upstream.is_healthy() is True

    # 1. Verifica geração de tools a partir da OpenAPI spec
    tools = await upstream.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_status" in tool_names
    assert "create_item" in tool_names

    # 2. Inspeciona schemas gerados
    status_tool = next(t for t in tools if t.name == "get_status")
    assert "code" in status_tool.input_schema["properties"]
    assert "code" in status_tool.input_schema["required"]

    create_tool = next(t for t in tools if t.name == "create_item")
    assert "title" in create_tool.input_schema["properties"]
    assert "price" in create_tool.input_schema["properties"]
    assert "title" in create_tool.input_schema["required"]

    await upstream.stop()


@pytest.mark.asyncio
async def test_create_connection_from_template_api():
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:

        payload = {
            "template_id": "filesystem-template",
            "form_values": {
                "id": "fs-test-docs",
                "name": "Documentos de Teste",
                "prefix": "fstest",
                "allowed_dir": "C:\\Users\\Scheuer\\Documents",
            },
            "target_instance_slug": "exampleco-suite",
        }
        res = await client.post("/api/v1/connections/from-template", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["connection_id"] == "fs-test-docs"

        # Verifica se foi salva no banco
        with get_db_context() as db:
            conn = CentralRepository.get_connection_by_id(db, "fs-test-docs")
            assert conn is not None
            assert conn.name == "Documentos de Teste"
            assert "C:\\Users\\Scheuer\\Documents" in conn.args


@pytest.mark.asyncio
async def test_granular_tool_filtering_and_toggles():
    await gateway_manager.start_all()
    gateway = gateway_manager.get_instance("exampleco-suite")
    assert gateway is not None

    # 1. Lista tools inicialmente: central__ping deve estar presente
    tools_res = await gateway._handle_list_tools(None)
    names = [t.name for t in tools_res.tools]
    assert "central__ping" in names

    # 2. Desabilita central__ping via API de toggle
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.post(
            "/api/v1/instances/exampleco-suite/tools/central__ping/toggle",
            json={"is_enabled": False},
        )
        assert res.status_code == 200
        assert res.json()["is_enabled"] is False

    # 3. Recarrega gateway e verifica que central__ping foi OMITIDA da lista
    gateway = gateway_manager.get_instance("exampleco-suite")
    tools_after = await gateway._handle_list_tools(None)
    names_after = [t.name for t in tools_after.tools]
    assert "central__ping" not in names_after

    # 4. Tenta invocar a ferramenta desabilitada: deve ser bloqueada
    import mcp.types as types
    call_params = types.CallToolRequestParams(name="central__ping", arguments={})
    call_result = await gateway._handle_call_tool(None, call_params)
    assert call_result.is_error is True
    assert "está desabilitada para a instância" in call_result.content[0].text

    # 5. Re-habilita a ferramenta
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.post(
            "/api/v1/instances/exampleco-suite/tools/central__ping/toggle",
            json={"is_enabled": True},
        )
        assert res.status_code == 200

    gateway = gateway_manager.get_instance("exampleco-suite")
    tools_restored = await gateway._handle_list_tools(None)
    names_restored = [t.name for t in tools_restored.tools]
    assert "central__ping" in names_restored


@pytest.mark.asyncio
async def test_data_sources_map_editor_and_agent_sync():
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        # 1. Consulta mapa atual
        res = await client.get("/api/v1/instances/exampleco-suite/sources-map")
        assert res.status_code == 200
        curr_map = res.json()
        assert "ExampleCo" in curr_map["organization"]

        # 2. Atualiza com uma nova fonte de dados corporativa
        new_sources = list(curr_map.get("sources", []))
        new_sources.append({
            "name": "ERP Faturamento SAP",
            "system": "sap_erp",
            "content_types": ["notas_fiscais", "pedidos"],
            "primary_tools": ["sap__query_invoices"],
            "guidance": "Consulte o ERP SAP para dados fiscais e faturas emitidas.",
        })

        update_payload = {
            "organization": "ExampleCo Group Holding",
            "sources": new_sources,
        }
        put_res = await client.put("/api/v1/instances/exampleco-suite/sources-map", json=update_payload)
        assert put_res.status_code == 200

    # 3. Invoca a tool central__get_data_sources_map via MCP e verifica o novo dado
    gateway = gateway_manager.get_instance("exampleco-suite")
    import mcp.types as types
    call_params = types.CallToolRequestParams(name="central__get_data_sources_map", arguments={})
    result = await gateway._handle_call_tool(None, call_params)
    assert not result.is_error
    map_data = json.loads(result.content[0].text)
    assert map_data["organization"] == "ExampleCo Group Holding"
    assert any(s["system"] == "sap_erp" for s in map_data["sources"])

    # 4. Restaura mapa original
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        await client.put("/api/v1/instances/exampleco-suite/sources-map", json=curr_map)


