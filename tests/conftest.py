"""
Test configuration and hermetic fixtures for Epyatis MCP Central test suite.
Ensures tests run against an isolated temporary database with sanitized fixtures.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine

# Ensure src is in sys.path for test discovery and CI runners
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Configure isolated temporary SQLite database for tests BEFORE importing any central modules
_test_db = tempfile.NamedTemporaryFile(suffix="_test_central.db", delete=False)
_test_db.close()
_db_norm_path = _test_db.name.replace("\\", "/")
_test_db_url = f"sqlite:///{_db_norm_path}"

# Set environment variables prior to importing central config or session modules so defaults never hit real database
os.environ["DATABASE_URL"] = _test_db_url
os.environ["CENTRAL_ENV"] = "testing"
os.environ["CENTRAL_SECRET_KEY"] = os.environ.get(
    "CENTRAL_SECRET_KEY", "ci-test-secret-key-with-at-least-32-characters"
)
os.environ["CENTRAL_ADMIN_KEY"] = os.environ.get(
    "CENTRAL_ADMIN_KEY", "ci-test-admin-key-with-at-least-32-characters"
)

import central.db.seeder as seeder_module
import central.db.session as session_module
from central.config import settings
from central.db.entities import (
    Base,
    ConnectionEntity,
    InstanceConnectionEntity,
    InstanceEntity,
    InstanceTokenEntity,
    UserEntity,
)
from central.db.seeder import init_database
from central.db.session import get_db_context
from central.gateway.manager import gateway_manager
from central.security.tokens import hash_bearer_token

# Explicitly ensure settings and all module-level engines point to the isolated temporary test database
settings.DATABASE_URL = _test_db_url
session_module.engine = create_engine(_test_db_url, connect_args={"check_same_thread": False})
session_module.SessionLocal.configure(bind=session_module.engine)
seeder_module.engine = session_module.engine


SANATIZED_EXAMPLECO_DATA_SOURCES = {
    "organization": "ExampleCo Group",
    "version": "1.0",
    "last_updated": "2026-10-29T12:00:00Z",
    "sources": [
        {
            "id": "exampleco.procurement.whatsapp.primary",
            "name": "ExampleCo - Compras (WhatsApp)",
            "description": "Grupo de compras para testes automatizados.",
            "purpose": "procurement_communications",
            "system": "periskope",
            "tags": ["procurement", "whatsapp", "official", "compras"],
            "authority": "official",
            "status": "active",
            "resource_type": "whatsapp_group",
            "native_resource_id": "120363000000000001@g.us",
            "primary_tools": ["periskope__periskope_list_messages_in_a_chat", "periskope__periskope_send_message"],
            "default_query_params": {"chat_id": "120363000000000001@g.us"},
            "guidance": "Grupo oficial de compras para teste.",
            "version": "1.0",
            "last_updated": "2026-10-29T12:00:00Z",
        },
        {
            "id": "exampleco.operations.whatsapp.field",
            "name": "ExampleCo - Operações em Campo (WhatsApp)",
            "description": "Grupo de operações em campo para testes.",
            "purpose": "field_operations_communications",
            "system": "periskope",
            "tags": ["operations", "whatsapp", "field", "official"],
            "authority": "official",
            "status": "active",
            "resource_type": "whatsapp_group",
            "native_resource_id": "120363000000000002@g.us",
            "primary_tools": ["periskope__periskope_list_messages_in_a_chat"],
            "default_query_params": {"chat_id": "120363000000000002@g.us"},
            "guidance": "Comunicações de campo para teste.",
            "version": "1.0",
            "last_updated": "2026-10-29T12:00:00Z",
        },
        {
            "id": "exampleco.procurement.spreadsheet.ssot",
            "name": "ExampleCo - Rastreio de Compras (Planilha SSoT)",
            "description": "Planilha oficial Single Source of Truth para conciliação e rastreamento de compras.",
            "purpose": "procurement_tracking",
            "system": "gdrive",
            "tags": ["procurement", "spreadsheet", "ssot", "official", "compras"],
            "authority": "official",
            "status": "active",
            "resource_type": "spreadsheet",
            "native_resource_id": "example-spreadsheet-ssot-id-12345",
            "primary_tools": ["gdrive__sheets-get-values", "gdrive__sheets-append-values", "gdrive__sheets-update-values"],
            "default_query_params": {"spreadsheetId": "example-spreadsheet-ssot-id-12345"},
            "guidance": "Planilha oficial Single Source of Truth para rastreamento de compras, conciliação e aprovações. Localizada na pasta Gestao SSoT.",
            "version": "1.0",
            "last_updated": "2026-10-29T12:00:00Z",
        },
        {
            "id": "exampleco.operations.spreadsheet.schedule",
            "name": "ExampleCo - Programação de Serviços Diários",
            "description": "Planilha de programação de equipes e cronograma de serviços diários.",
            "purpose": "field_schedule",
            "system": "gdrive",
            "tags": ["operations", "schedule", "spreadsheet", "official"],
            "authority": "official",
            "status": "active",
            "resource_type": "spreadsheet",
            "native_resource_id": "example-spreadsheet-schedule-id-67890",
            "primary_tools": ["gdrive__sheets-get-values", "gdrive__sheets-update-values"],
            "default_query_params": {"spreadsheetId": "example-spreadsheet-schedule-id-67890"},
            "guidance": "Planilha de programação de equipes e cronograma de serviços diários.",
            "version": "1.0",
            "last_updated": "2026-10-29T12:00:00Z",
        },
        {
            "id": "exampleco.governance.vault.primary",
            "name": "ExampleCo - Vault de Regras e Governança",
            "description": "Pasta de governança para testes.",
            "purpose": "governance_and_rules",
            "system": "gdrive",
            "tags": ["governance", "rules", "drive_folder", "official"],
            "authority": "official",
            "status": "active",
            "resource_type": "folder",
            "native_resource_id": "example-vault-folder-id-99999",
            "primary_tools": ["gdrive__list-files", "gdrive__read-file"],
            "default_query_params": {"folderId": "example-vault-folder-id-99999"},
            "guidance": "Vault de teste de governança.",
            "version": "1.0",
            "last_updated": "2026-10-29T12:00:00Z",
        },
    ],
}


@pytest.fixture(scope="session", autouse=True)
def setup_hermetic_test_environment():
    """Inicializa tabelas no banco isolado e garante fixtures sanitizadas 'exampleco-suite'."""
    Base.metadata.create_all(bind=session_module.engine)

    with get_db_context() as db:
        root_user = db.query(UserEntity).filter(UserEntity.username == "epy_root").first()
        if not root_user:
            root_user = UserEntity(
                id="user_root",
                username="epy_root",
                role="epy_root",
                password_hash=None,
                is_active=True,
            )
            db.add(root_user)
            db.flush()

        # Conexões sanitizadas de teste
        from central.security.crypto import encrypt_json_dict

        conn_defs = [
            ("internal", "Internal Diagnostics", "internal", "central"),
            ("gdrive", "Google Drive Connector", "internal", "gdrive"),
            ("periskope", "Periskope WhatsApp Connector", "internal", "periskope"),
        ]
        created_conns = {}
        for cid, cname, ctype, cprefix in conn_defs:
            c = db.query(ConnectionEntity).filter(ConnectionEntity.id == cid).first()
            if not c:
                c = ConnectionEntity(
                    id=cid,
                    user_id=root_user.id,
                    name=cname,
                    type=ctype,
                    prefix=cprefix,
                    args_json="[]",
                    env_json=encrypt_json_dict({}),
                    auth_config_json=encrypt_json_dict({}),
                    is_active=True,
                    health_status="healthy",
                )
                db.add(c)
                db.flush()
            created_conns[cid] = c

        # Instância exampleco-suite sanitizada
        inst = db.query(InstanceEntity).filter(InstanceEntity.slug == "exampleco-suite").first()
        if not inst:
            inst = InstanceEntity(
                id="exampleco-suite",
                user_id=root_user.id,
                name="ExampleCo Operational Suite",
                slug="exampleco-suite",
                description="Endpoint agregador de operações com Google Drive e Periskope WhatsApp para a ExampleCo Group.",
                is_active=True,
                data_sources_map_json=json.dumps(SANATIZED_EXAMPLECO_DATA_SOURCES),
            )
            db.add(inst)
            db.flush()

        for cid, conn in created_conns.items():
            link = (
                db.query(InstanceConnectionEntity)
                .filter(
                    InstanceConnectionEntity.instance_id == inst.id,
                    InstanceConnectionEntity.connection_id == conn.id,
                )
                .first()
            )
            if not link:
                db.add(InstanceConnectionEntity(instance_id=inst.id, connection_id=conn.id, is_enabled=True))

        token_hash = hash_bearer_token("epy_dev_token_123")
        existing_token = (
            db.query(InstanceTokenEntity)
            .filter(InstanceTokenEntity.instance_id == inst.id)
            .first()
        )
        if not existing_token:
            db.add(
                InstanceTokenEntity(
                    instance_id=inst.id,
                    token=token_hash,
                    label="ExampleCo Test Token",
                )
            )

        db.commit()

    gateway_manager.load_from_db()
    yield
    # Cleanup temporary test db
    try:
        os.remove(_test_db.name)
    except Exception:
        pass
