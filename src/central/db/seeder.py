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
    _migrate_legacy_secret_columns()
    _migrate_token_hashes()

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
            if "password_hash" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
                conn.commit()
            if "status" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN status VARCHAR(32) DEFAULT 'approved'")
                conn.commit()
    except Exception as e:
        logger.warning(f"Aviso durante verificação de migrações: {e}")


def _migrate_token_hashes() -> None:
    """Convert legacy plaintext bearer tokens to one-way digests in place."""
    from central.security.tokens import TOKEN_HASH_PREFIX, hash_bearer_token

    try:
        statements = (
            ("SELECT id, token FROM instance_tokens", "UPDATE instance_tokens SET token = ? WHERE id = ?"),
            ("SELECT id, token FROM user_sessions", "UPDATE user_sessions SET token = ? WHERE id = ?"),
        )
        with engine.begin() as conn:
            for select_sql, update_sql in statements:
                rows = conn.exec_driver_sql(select_sql).fetchall()
                for row_id, token in rows:
                    if token and not token.startswith(TOKEN_HASH_PREFIX):
                        conn.exec_driver_sql(
                            update_sql,
                            (hash_bearer_token(token), row_id),
                        )
    except Exception as exc:
        logger.error("Falha ao migrar tokens legados para hashes: %s", exc)
        raise


def _migrate_legacy_secret_columns() -> None:
    """Encrypt validated legacy JSON fields without accepting plaintext at runtime."""
    from central.security.crypto import encrypt_string

    statements = (
        (
            "connections.env_json",
            "SELECT id, env_json FROM connections",
            "UPDATE connections SET env_json = ? WHERE id = ?",
        ),
        (
            "connections.auth_config_json",
            "SELECT id, auth_config_json FROM connections",
            "UPDATE connections SET auth_config_json = ? WHERE id = ?",
        ),
        (
            "connection_templates.env_json",
            "SELECT id, env_json FROM connection_templates",
            "UPDATE connection_templates SET env_json = ? WHERE id = ?",
        ),
        (
            "connection_templates.auth_config_json",
            "SELECT id, auth_config_json FROM connection_templates",
            "UPDATE connection_templates SET auth_config_json = ? WHERE id = ?",
        ),
    )
    try:
        with engine.begin() as conn:
            for field_name, select_sql, update_sql in statements:
                rows = conn.exec_driver_sql(select_sql).fetchall()
                for row_id, stored in rows:
                    if not stored or stored.startswith("enc:"):
                        continue
                    parsed = json.loads(stored)
                    if not isinstance(parsed, dict):
                        raise ValueError(f"{field_name} deve conter um objeto JSON.")
                    conn.exec_driver_sql(
                        update_sql,
                        (encrypt_string(stored), row_id),
                    )
    except Exception as exc:
        logger.error("Falha na migração controlada de segredos legados: %s", exc)
        raise


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

    # Existing installations are never overwritten by example bootstrap data.
    existing_instance = db.query(InstanceEntity).first()
    if existing_instance:
        logger.info("O banco já contém instâncias. Pulando seed de exemplo.")
        return

    # 3. Lê o arquivo de bootstrap se fornecido
    if not yaml_path or not yaml_path.exists():
        logger.info("Arquivo de bootstrap YAML não encontrado. Criando instâncias padrão programaticamente.")
        _create_default_instance(db, root_user.id)
        return

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        instances_data = data.get("instances", [])
        if not instances_data:
            _create_default_instance(db, root_user.id)
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
                    conn_name = "Epyatis Internal Diagnostics" if conn_id == "internal" else f"Connection {conn_id.title()}"

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
                    from central.security.tokens import hash_bearer_token

                    inst_token = InstanceTokenEntity(
                        instance_id=instance.id,
                        token=hash_bearer_token(token_val),
                        label=label,
                    )
                    db.add(inst_token)

            logger.info(f"Instância '{slug}' migrada com sucesso para o SQLite.")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao popular dados de bootstrap no SQLite: {e}", exc_info=True)
        _create_default_instance(db, root_user.id)


def _create_default_instance(db: Session, user_id: str) -> None:
    """Create a credential-free local example when no bootstrap file exists."""
    try:
        inst = InstanceEntity(
            id="demo-suite",
            user_id=user_id,
            name="Demo MCP Suite",
            slug="demo-suite",
            description="Local development instance with internal diagnostics only.",
            visibility="private",
            is_active=True,
        )
        db.add(inst)
        db.flush()

        # Internal connection only; no subprocess and no pre-created bearer token.
        for cid, cname, ctype, cprefix, cmd, args, env in [
            ("internal", "Internal Diagnostics", "internal", "central", None, [], {}),
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
        logger.info("Instância de demonstração criada com sucesso no SQLite.")
    except Exception as e:
        db.rollback()
        logger.error(f"Falha ao criar instância fallback: {e}")
