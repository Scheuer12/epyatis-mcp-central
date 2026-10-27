"""
Testes de Validação do Registro Operacional Nodal de Fontes de Dados (Fase: Upgrade Nodal).

Valida os 10 requisitos obrigatórios da especificação:
1. Busca por uma tag única.
2. Busca por múltiplas tags (semântica AND obrigatória).
3. Busca por propósito de negócio (purpose).
4. Recuperação detalhada de uma fonte específica por ID (central__get_data_source).
5. Múltiplos nós independentes no mesmo sistema subjacente (ex: 2 grupos Periskope, 3 nós GDrive).
6. Atualização de fontes, versionamento e frescor imediato (sem cache obsoleto).
7. Compatibilidade retroativa com central__get_data_sources_map.
8. Compatibilidade com Kits de Fontes de Dados (Data-Source Kits).
9. Persistência de metadados nodais através de recarga do serviço.
10. Ferramentas existentes e conectividade MCP permanecem funcionais.
+ Medição comparativa do tamanho da resposta (Token Context Efficiency).
"""

import json
import pytest
import mcp.types as types
from httpx import AsyncClient, ASGITransport

from central.config import settings
from central.db.entities import DataSourceKitEntity, InstanceEntity
from central.db.repository import CentralRepository
from central.db.session import get_db_context
from central.gateway.manager import gateway_manager
from central.server import app


@pytest.fixture(autouse=True)
def setup_gateway():
    """Garante que as instâncias estejam carregadas do banco de dados para os testes."""
    with get_db_context() as db:
        inst = db.query(InstanceEntity).filter(InstanceEntity.slug == "horst-suite").first()
        assert inst is not None, "Instância horst-suite deve existir no central.db"
    gateway_manager.load_from_db()


@pytest.mark.asyncio
async def test_01_search_by_single_tag():
    """Validação 1: Busca de fontes de dados por uma tag única."""
    gw = gateway_manager.get_instance("horst-suite")
    assert gw is not None

    call_params = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"tags": ["procurement"]}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert "sources" in data
    assert data["count"] >= 2
    ids = [s["id"] for s in data["sources"]]
    assert "horst.procurement.whatsapp.primary" in ids
    assert "horst.procurement.spreadsheet.ssot" in ids

    # Garante que campos leves foram retornados e campos pesados NÃO foram retornados na descoberta
    for s in data["sources"]:
        assert "id" in s
        assert "name" in s
        assert "purpose" in s
        assert "system" in s
        assert "tags" in s
        assert "authority" in s
        assert "status" in s
        assert "guidance" not in s, "Descoberta leve não deve vazar campo guidance pesado"
        assert "default_query_params" not in s, "Descoberta leve não deve vazar parâmetros de query"


@pytest.mark.asyncio
async def test_02_search_by_multiple_tags_and_semantics():
    """Validação 2: Busca por múltiplas tags utilizando semântica AND."""
    gw = gateway_manager.get_instance("horst-suite")

    # Ambas tags coincidem em 'horst.procurement.whatsapp.primary'
    call_params = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"tags": ["procurement", "whatsapp"]}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["count"] == 1
    assert data["sources"][0]["id"] == "horst.procurement.whatsapp.primary"

    # Combinação que não existe em nenhuma fonte isolada (AND semântica deve retornar zero)
    call_params_empty = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"tags": ["procurement", "field"]}
    )
    res_empty = await gw._handle_call_tool(None, call_params_empty)
    assert not res_empty.is_error
    data_empty = json.loads(res_empty.content[0].text)
    assert data_empty["count"] == 0
    assert len(data_empty["sources"]) == 0


@pytest.mark.asyncio
async def test_03_search_by_business_purpose():
    """Validação 3: Busca por propósito de negócio (purpose)."""
    gw = gateway_manager.get_instance("horst-suite")

    call_params = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"purpose": "field_schedule"}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["count"] == 1
    assert data["sources"][0]["id"] == "horst.operations.spreadsheet.schedule"
    assert data["sources"][0]["purpose"] == "field_schedule"


@pytest.mark.asyncio
async def test_04_get_data_source_detailed_definition():
    """Validação 4: Recuperação detalhada e completa de uma fonte específica por ID."""
    gw = gateway_manager.get_instance("horst-suite")

    call_params = types.CallToolRequestParams(
        name="central__get_data_source",
        arguments={"source_id": "horst.procurement.whatsapp.primary"}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    source = json.loads(res.content[0].text)

    # Campos obrigatórios do contrato detalhado
    assert source["id"] == "horst.procurement.whatsapp.primary"
    assert source["name"] == "Horst - Compras (WhatsApp)"
    assert source["system"] == "periskope"
    assert source["purpose"] == "procurement_communications"
    assert "procurement" in source["tags"]
    assert source["authority"] == "official"
    assert source["status"] == "active"
    assert source["resource_type"] == "whatsapp_group"
    assert source["native_resource_id"] == "120363429855948681@g.us"
    assert "periskope__periskope_send_message" in source["primary_tools"]
    assert source["default_query_params"]["chat_id"] == "120363429855948681@g.us"
    assert "guidance" in source
    assert "version" in source
    assert "last_updated" in source

    # Teste de caso de erro estruturado (fonte inexistente)
    call_missing = types.CallToolRequestParams(
        name="central__get_data_source",
        arguments={"source_id": "fonte.inexistente.123"}
    )
    res_missing = await gw._handle_call_tool(None, call_missing)
    assert res_missing.is_error
    error_data = json.loads(res_missing.content[0].text)
    assert error_data["error"] == "not_found"
    assert error_data["source_id"] == "fonte.inexistente.123"


@pytest.mark.asyncio
async def test_05_multiple_sources_same_system():
    """Validação 5: Múltiplos nós independentes que pertencem ao mesmo sistema subjacente."""
    gw = gateway_manager.get_instance("horst-suite")

    # Sistema Periskope: dois grupos diferentes (Compras e Operações em Campo)
    call_periskope = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"system": "periskope"}
    )
    res_periskope = await gw._handle_call_tool(None, call_periskope)
    assert not res_periskope.is_error
    data_p = json.loads(res_periskope.content[0].text)
    p_ids = [s["id"] for s in data_p["sources"]]
    assert "horst.procurement.whatsapp.primary" in p_ids
    assert "horst.operations.whatsapp.field" in p_ids
    assert len(p_ids) >= 2

    # Sistema Google Drive: duas planilhas e uma pasta de vault governança
    call_gdrive = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"system": "gdrive"}
    )
    res_gdrive = await gw._handle_call_tool(None, call_gdrive)
    assert not res_gdrive.is_error
    data_g = json.loads(res_gdrive.content[0].text)
    g_ids = [s["id"] for s in data_g["sources"]]
    assert "horst.procurement.spreadsheet.ssot" in g_ids
    assert "horst.operations.spreadsheet.schedule" in g_ids
    assert "horst.governance.vault.primary" in g_ids
    assert len(g_ids) >= 3


@pytest.mark.asyncio
async def test_06_source_updates_and_version_freshness():
    """Validação 6: Atualizações de fontes por administradores, versionamento e frescor sem cache obsoleto."""
    gw = gateway_manager.get_instance("horst-suite")

    # 1. Recupera versão inicial e native_resource_id inicial
    with get_db_context() as db:
        orig = CentralRepository.get_instance_source_by_id(db, "horst-suite", "horst.procurement.spreadsheet.ssot")
        assert orig is not None
        v_init = orig.get("version", "1.0")
        orig_native = orig.get("native_resource_id")

    try:
        # 2. Atualiza via repositório simulando rota administrativa PUT
        with get_db_context() as db:
            updated = CentralRepository.update_instance_source(
                db,
                slug="horst-suite",
                source_id="horst.procurement.spreadsheet.ssot",
                updates={
                    "native_resource_id": "NOVO_SPREADSHEET_ID_2026_TESTE",
                    "guidance": "Guidance atualizado pelo administrador para compras 2026.",
                }
            )
            assert updated is not None
            assert updated["version"] != v_init
            assert "historical_or_alternative_sources" in updated
            assert any(orig_native in h for h in updated["historical_or_alternative_sources"])

        # Recarrega instância no gateway para simular o comportamento de notificação / frescor
        await gateway_manager.reload_instance("horst-suite")
        fresh_gw = gateway_manager.get_instance("horst-suite")

        # 3. Consulta imediatamente via MCP Tool e verifica que não há cache obsoleto
        call_get = types.CallToolRequestParams(
            name="central__get_data_source",
            arguments={"source_id": "horst.procurement.spreadsheet.ssot"}
        )
        res_get = await fresh_gw._handle_call_tool(None, call_get)
        fresh_source = json.loads(res_get.content[0].text)
        assert fresh_source["native_resource_id"] == "NOVO_SPREADSHEET_ID_2026_TESTE"
        assert fresh_source["guidance"] == "Guidance atualizado pelo administrador para compras 2026."
        assert len(fresh_source["historical_or_alternative_sources"]) >= 1

    finally:
        # Restaura o ID original para manter o ambiente estável
        with get_db_context() as db:
            CentralRepository.update_instance_source(
                db,
                slug="horst-suite",
                source_id="horst.procurement.spreadsheet.ssot",
                updates={
                    "native_resource_id": orig_native,
                    "guidance": "Planilha oficial Single Source of Truth para rastreamento de compras, conciliação e aprovações. Localizada na pasta Gestao SSoT.",
                }
            )
        await gateway_manager.reload_instance("horst-suite")


@pytest.mark.asyncio
async def test_07_legacy_data_sources_map_compatibility():
    """Validação 7: central__get_data_sources_map continua operacional e compatível."""
    gw = gateway_manager.get_instance("horst-suite")

    call_params = types.CallToolRequestParams(
        name="central__get_data_sources_map",
        arguments={}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    map_data = json.loads(res.content[0].text)
    assert map_data["organization"] == "Horst Group"
    assert len(map_data["sources"]) >= 5
    for s in map_data["sources"]:
        assert "name" in s
        assert "system" in s


@pytest.mark.asyncio
async def test_08_data_source_kit_compatibility():
    """Validação 8: Compatibilidade com Data-Source Kits contendo metadados nodais."""
    with get_db_context() as db:
        sources = CentralRepository.get_instance_sources(db, "horst-suite")
        kit = DataSourceKitEntity(
            id="kit_test_nodal",
            user_id="user_root",
            name="Kit Operacional Horst Teste",
            description="Kit contendo fontes nodais para teste",
            sources_json=json.dumps(sources),
            category="Operações",
            visibility="shared",
        )
        db.merge(kit)
        db.commit()

        # Recupera o kit e valida integridade dos nós
        saved_kit = db.query(DataSourceKitEntity).filter(DataSourceKitEntity.id == "kit_test_nodal").first()
        assert saved_kit is not None
        assert len(saved_kit.sources) >= 5
        assert any(s["id"] == "horst.procurement.whatsapp.primary" for s in saved_kit.sources)

        # Limpeza
        db.delete(saved_kit)
        db.commit()

        # Limpeza
        db.delete(saved_kit)
        db.commit()


@pytest.mark.asyncio
async def test_09_persistence_across_service_reload():
    """Validação 9: Persistência de metadados nodais no SQLite através de recarga completa."""
    # 1. Recarrega gateway a partir do banco de dados
    gateway_manager.load_from_db()
    gw = gateway_manager.get_instance("horst-suite")
    assert gw is not None

    # 2. Confirma que os nós persistiram intactos
    call_params = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"authority": "official"}
    )
    res = await gw._handle_call_tool(None, call_params)
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["count"] >= 5


@pytest.mark.asyncio
async def test_10_existing_mcp_tools_and_connections_remain_functional():
    """Validação 10: Ferramentas pré-existentes permanecem listadas e ativas."""
    gw = gateway_manager.get_instance("horst-suite")
    tools_result = await gw._handle_list_tools(None)
    tool_names = [t.name for t in tools_result.tools]

    # Ferramentas internas essenciais
    assert "central__ping" in tool_names
    assert "central__get_data_sources_map" in tool_names
    assert "central__search_data_sources" in tool_names
    assert "central__get_data_source" in tool_names

    # Testa execução da ferramenta central__ping
    call_ping = types.CallToolRequestParams(name="central__ping", arguments={})
    res_ping = await gw._handle_call_tool(None, call_ping)
    assert not res_ping.is_error
    assert "Pong! Epyatis MCP Central" in res_ping.content[0].text


@pytest.mark.asyncio
async def test_response_size_measurement_token_efficiency():
    """
    Medição comparativa do tamanho da resposta:
    Mede a diferença em bytes entre carregar o mapa completo de fontes e
    descobrir um conjunto filtrado de descritores leves.
    """
    gw = gateway_manager.get_instance("horst-suite")

    # 1. Resposta do mapa completo legado (central__get_data_sources_map)
    call_full = types.CallToolRequestParams(
        name="central__get_data_sources_map",
        arguments={}
    )
    res_full = await gw._handle_call_tool(None, call_full)
    full_text = res_full.content[0].text
    full_bytes = len(full_text.encode("utf-8"))

    # 2. Resposta da descoberta leve filtrada (central__search_data_sources)
    call_search = types.CallToolRequestParams(
        name="central__search_data_sources",
        arguments={"tags": ["procurement"]}
    )
    res_search = await gw._handle_call_tool(None, call_search)
    search_text = res_search.content[0].text
    search_bytes = len(search_text.encode("utf-8"))

    reduction_percentage = ((full_bytes - search_bytes) / full_bytes) * 100
    print(f"\n================ RESUMO DE EFICIÊNCIA DE CONTEXTO ================")
    print(f"Tamanho do Mapa Completo (get_data_sources_map): {full_bytes} bytes")
    print(f"Tamanho da Busca Leve Nodal (search_data_sources): {search_bytes} bytes")
    print(f"Redução de payload para o contexto do Agente: {reduction_percentage:.1f}%")
    print(f"==================================================================")

    # A descoberta deve ser substancialmente menor que o mapa completo
    assert search_bytes < full_bytes, "A busca leve deve ser significativamente menor que o mapa completo"
