import pytest
from httpx import AsyncClient, ASGITransport
from central.server import app
from central.config import settings

@pytest.mark.asyncio
async def test_edit_connection_lifecycle():
    """Valida edição completa de uma conexão no cofre."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        # 1. Cria uma conexão temporária
        create_res = await client.post("/api/v1/connections", json={
            "id": "qa_edit_conn",
            "name": "Conexão Teste Original",
            "type": "stdio",
            "prefix": "qa_orig",
            "command": "python",
            "args": ["-c", "print('hello')"],
            "env": {"TEST_VAR": "1"},
            "visibility": "shared"
        })
        assert create_res.status_code == 200

        # 2. Edita a conexão (PUT)
        update_res = await client.put("/api/v1/connections/qa_edit_conn", json={
            "name": "Conexão Teste Editada",
            "type": "stdio",
            "prefix": "qa_edit",
            "command": "python",
            "args": ["-c", "print('updated')"],
            "env": {"TEST_VAR": "2"},
            "visibility": "shared"
        })
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "success"

        # 3. Verifica se os dados foram atualizados
        list_res = await client.get("/api/v1/connections")
        assert list_res.status_code == 200
        conns = list_res.json()
        target = next((c for c in conns if c["id"] == "qa_edit_conn"), None)
        assert target is not None
        assert target["name"] == "Conexão Teste Editada"
        assert target["prefix"] == "qa_edit"

        # 4. Limpeza
        del_res = await client.delete("/api/v1/connections/qa_edit_conn")
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_edit_template_lifecycle():
    """Valida edição de modelo de conexão."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        # 1. Cria modelo a partir de template
        from central.db.repository import CentralRepository
        from central.db.session import SessionLocal
        with SessionLocal() as db:
            tmpl = CentralRepository.create_template(
                db=db,
                name="Modelo Original",
                type="stdio",
                prefix="mod_orig",
                description="Desc original",
                command="npx",
                args=["-y", "test-mcp"],
                visibility="shared"
            )
            tmpl_id = tmpl.id

        # 2. Edita modelo (PUT)
        update_res = await client.put(f"/api/v1/connection-templates/{tmpl_id}", json={
            "name": "Modelo Editado com Sucesso",
            "description": "Desc atualizada",
            "type": "stdio",
            "prefix": "mod_updated",
            "command": "npx",
            "args": ["-y", "updated-mcp"],
            "visibility": "shared"
        })
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "success"

        # 3. Verifica dados atualizados
        get_res = await client.get(f"/api/v1/connection-templates/{tmpl_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["name"] == "Modelo Editado com Sucesso"
        assert data["description"] == "Desc atualizada"
        assert data["prefix"] == "mod_updated"

        # 4. Limpeza
        del_res = await client.delete(f"/api/v1/connection-templates/{tmpl_id}")
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_edit_kit_and_instance_lifecycle():
    """Valida edição de Kit de Conhecimento e de Instância."""
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        # 1. Cria Kit
        kit_res = await client.post("/api/v1/data-source-kits", json={
            "name": "Kit QA Original",
            "category": "Testes",
            "description": "Desc inicial",
            "sources": [{"name": "Doc 1", "type": "doc", "description": "Guia 1"}],
            "visibility": "shared"
        })
        assert kit_res.status_code == 200
        kit_id = kit_res.json()["kit_id"]

        # 2. Edita Kit (PUT)
        update_kit_res = await client.put(f"/api/v1/data-source-kits/{kit_id}", json={
            "name": "Kit QA Atualizado",
            "category": "Engenharia",
            "description": "Desc nova",
            "sources": [
                {"name": "Doc 1", "type": "doc", "description": "Guia 1"},
                {"name": "DB Vendas", "type": "database", "description": "Tabelas de vendas"}
            ],
            "visibility": "shared"
        })
        assert update_kit_res.status_code == 200
        assert update_kit_res.json()["status"] == "success"

        # 3. Verifica Kit atualizado
        get_kit_res = await client.get(f"/api/v1/data-source-kits/{kit_id}")
        assert get_kit_res.status_code == 200
        k_data = get_kit_res.json()
        assert k_data["name"] == "Kit QA Atualizado"
        assert len(k_data["sources"]) == 2

        # 4. Limpeza Kit
        del_kit_res = await client.delete(f"/api/v1/data-source-kits/{kit_id}")
        assert del_kit_res.status_code == 200

        # 5. Edita Instância (PUT /instances/{slug})
        inst_res = await client.put("/api/v1/instances/exampleco-suite", json={
            "name": "ExampleCo Operational Suite (Editada)",
            "description": "Nova descrição para testes de edição UX"
        })
        assert inst_res.status_code == 200
        assert inst_res.json()["name"] == "ExampleCo Operational Suite (Editada)"

        # Restaura nome original
        await client.put("/api/v1/instances/exampleco-suite", json={
            "name": "ExampleCo Operational Suite",
            "description": "Endpoint agregador de operações com Google Drive e Periskope WhatsApp para a ExampleCo Group."
        })
