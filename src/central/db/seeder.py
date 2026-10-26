"""
Seeder do Epyatis MCP Central: inicializa tabelas e migra bootstrap declarativo para o SQLite.
"""

from pathlib import Path
import json
import logging
import yaml
from sqlalchemy.orm import Session

from central.db.entities import (
    Base,
    ConnectionEntity,
    InstanceConnectionEntity,
    InstanceEntity,
    InstanceTokenEntity,
    UserEntity,
)
from central.db.session import engine, get_db_context

logger = logging.getLogger(__name__)


def init_database(yaml_path: Path | None = None) -> None:
    """Cria tabelas se não existirem e migra a configuração de bootstrap."""
    logger.info("Verificando integridade das tabelas do banco SQLite...")
    Base.metadata.create_all(bind=engine)
    _migrate_columns()

    with get_db_context() as db:
        _seed_default_data(db, yaml_path)


def _migrate_columns() -> None:
    """Migração idempotente para colunas adicionadas em tabelas existentes."""
    try:
        with engine.connect() as conn:
            cols = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(connections)").fetchall()]
            if "visibility" not in cols:
                conn.exec_driver_sql("ALTER TABLE connections ADD COLUMN visibility VARCHAR(32) DEFAULT 'shared'")
                conn.commit()

            cols = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(instances)").fetchall()]
            if "visibility" not in cols:
                conn.exec_driver_sql("ALTER TABLE instances ADD COLUMN visibility VARCHAR(32) DEFAULT 'shared'")
                conn.commit()

            cols = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
            if "display_name" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN display_name VARCHAR(128)")
                conn.commit()
    except Exception as e:
        logger.warning(f"Aviso durante verificação de migrações: {e}")


def _seed_default_data(db: Session, yaml_path: Path | None = None) -> None:
    # 1. Cria usuário epy_root se não existir
    root_user = db.query(UserEntity).filter(UserEntity.username == "epy_root").first()
    if not root_user:
        logger.info("Criando usuário administrador mestre 'epy_root'...")
        root_user = UserEntity(
            id="user_root",
            username="epy_root",
            role="epy_root",
            password_hash=None,
            is_active=True,
        )
        db.add(root_user)
        db.flush()

    # 2. Verifica se a instância horst-suite já existe no banco
    existing_instance = db.query(InstanceEntity).filter(InstanceEntity.slug == "horst-suite").first()
    if existing_instance:
        logger.info("Instância 'horst-suite' já existe no banco SQLite. Pulando seed.")
        return

    # 3. Lê o arquivo de bootstrap se fornecido
    if not yaml_path or not yaml_path.exists():
        logger.info("Arquivo de bootstrap YAML não encontrado. Criando instâncias padrão programaticamente.")
        _create_default_horst_suite(db, root_user.id)
        return

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        instances_data = data.get("instances", [])
        if not instances_data:
            _create_default_horst_suite(db, root_user.id)
            return

        for inst_data in instances_data:
            slug = inst_data.get("slug") or inst_data.get("id")
            name = inst_data.get("name", slug)
            description = inst_data.get("description", "")
            ds_map = inst_data.get("data_sources_map")

            instance = InstanceEntity(
                id=slug,
                user_id=root_user.id,
                name=name,
                slug=slug,
                description=description,
                is_active=True,
                data_sources_map_json=json.dumps(ds_map) if ds_map else None,
            )
            db.add(instance)
            db.flush()

            # Conexões associadas
            for conn_data in inst_data.get("connections", []):
                conn_id = conn_data.get("id")
                prefix = conn_data.get("prefix", conn_id)
                conn_type = conn_data.get("type", "internal")
                command = conn_data.get("command")
                args = conn_data.get("args", [])
                env = conn_data.get("env", {})
                url = conn_data.get("url")
                auth = conn_data.get("auth", {})
                enabled = conn_data.get("enabled", True)

                # Busca ou cria a conexão
                conn = db.query(ConnectionEntity).filter(ConnectionEntity.id == conn_id).first()
                if not conn:
                    conn_name = f"Conexão {conn_id.title()}"
                    if conn_id == "gdrive":
                        conn_name = "Google Drive (@horstgroup.net)"
                    elif conn_id == "periskope":
                        conn_name = "Periskope WhatsApp"
                    elif conn_id == "internal":
                        conn_name = "Epyatis Diagnósticos Internos"

                    conn = ConnectionEntity(
                        id=conn_id,
                        user_id=root_user.id,
                        name=conn_name,
                        type=conn_type,
                        prefix=prefix,
                        command=command,
                        args_json=json.dumps(args),
                        env_json=json.dumps(env),
                        url=url,
                        auth_config_json=json.dumps(auth),
                        is_active=enabled,
                        health_status="healthy",
                    )
                    db.add(conn)
                    db.flush()

                # Associa à instância
                inst_conn = InstanceConnectionEntity(
                    instance_id=instance.id,
                    connection_id=conn.id,
                    is_enabled=enabled,
                )
                db.add(inst_conn)

            # Tokens associados
            for token_data in inst_data.get("tokens", []):
                token_val = token_data.get("token")
                label = token_data.get("label", "Default Token")
                if token_val:
                    inst_token = InstanceTokenEntity(
                        instance_id=instance.id,
                        token=token_val,
                        label=label,
                    )
                    db.add(inst_token)

            logger.info(f"Instância '{slug}' migrada com sucesso para o SQLite.")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao popular dados de bootstrap no SQLite: {e}", exc_info=True)
        _create_default_horst_suite(db, root_user.id)


def _create_default_horst_suite(db: Session, user_id: str) -> None:
    """Criação programática de fallback para a instância horst-suite."""
    try:
        inst = InstanceEntity(
            id="horst-suite",
            user_id=user_id,
            name="Horst Operational Suite",
            slug="horst-suite",
            description="Endpoint agregador de operações com Google Drive e Periskope WhatsApp para a Horst Group.",
            is_active=True,
        )
        db.add(inst)
        db.flush()

        tok = InstanceTokenEntity(
            instance_id=inst.id,
            token="epy_dev_token_123",
            label="Paperclip Local Dev Connector",
        )
        db.add(tok)

        # Conexões básicas
        for cid, cname, ctype, cprefix, cmd, args, env in [
            ("internal", "Diagnósticos Internos", "internal", "central", None, [], {}),
            ("gdrive", "Google Drive (@horstgroup.net)", "stdio", "gdrive", "npx", ["-y", "@us-all/google-drive-mcp"], {"GOOGLE_DRIVE_ALLOW_WRITE": "true"}),
            ("periskope", "Periskope WhatsApp", "stdio", "periskope", "npx", ["-y", "@periskope/whatsapp-mcp"], {}),
        ]:
            c = db.query(ConnectionEntity).filter(ConnectionEntity.id == cid).first()
            if not c:
                c = ConnectionEntity(
                    id=cid,
                    user_id=user_id,
                    name=cname,
                    type=ctype,
                    prefix=cprefix,
                    command=cmd,
                    args_json=json.dumps(args),
                    env_json=json.dumps(env),
                    is_active=True,
                )
                db.add(c)
                db.flush()

            db.add(InstanceConnectionEntity(instance_id=inst.id, connection_id=c.id, is_enabled=True))

        db.commit()
        logger.info("Instância horst-suite padrão criada com sucesso no SQLite.")
    except Exception as e:
        db.rollback()
        logger.error(f"Falha ao criar instância fallback: {e}")
