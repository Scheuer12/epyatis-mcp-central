"""
Teste de verificação end-to-end para a Fase 0 (Bootstrap Testável).
"""

import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport

from central.gateway.manager import gateway_manager
from central.config import settings
from central.server import app


@pytest.mark.asyncio
async def test_instance_loading_and_internal_tools():
    # 1. Carrega configuração do YAML
    gateway_manager.load_config(settings.CONFIG_PATH)
    await gateway_manager.start_all()

    gateway = gateway_manager.get_instance("exampleco-suite")
    assert gateway is not None, "Instância 'exampleco-suite' deve estar carregada."

    # 2. Testa validação de tokens
    assert gateway.validate_token("epy_dev_token_123") is True
    assert gateway.validate_token("token_invalido") is False

    # 3. Lista ferramentas agregadas
    tools_result = await gateway._handle_list_tools(None)
    tool_names = [t.name for t in tools_result.tools]
    print(f"\n[Test] Ferramentas agregadas expostas: {tool_names}")

    assert "central__ping" in tool_names
    assert "central__get_data_sources_map" in tool_names

    # 4. Executa tool central__ping
    import mcp.types as types
    call_params = types.CallToolRequestParams(name="central__ping", arguments={})
    ping_result = await gateway._handle_call_tool(None, call_params)
    assert not ping_result.is_error
    assert "Pong! Epyatis MCP Central" in ping_result.content[0].text

    # 5. Executa tool central__get_data_sources_map
    map_params = types.CallToolRequestParams(name="central__get_data_sources_map", arguments={})
    map_result = await gateway._handle_call_tool(None, map_params)
    assert not map_result.is_error
    map_data = json.loads(map_result.content[0].text)
    assert map_data["organization"] == "ExampleCo Group"
    assert len(map_data["sources"]) >= 2
    print(f"[Test] Data sources map recuperado com sucesso para: {map_data['organization']}")

    await gateway_manager.stop_all()


@pytest.mark.asyncio
async def test_api_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "exampleco-suite" in data["instances"]
        print(f"[Test] Healthcheck status: {data}")
