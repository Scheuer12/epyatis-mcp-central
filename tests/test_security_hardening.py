"""
Suite de Testes Automatizados de Cibersegurança & Hardening (SEC-01 a SEC-05).
Valida:
- SEC-01: Bloqueio de acessos não autenticados na API Administrativa (/api/v1/*)
- SEC-02: Bloqueio estrito de RCE via Allowlist de executáveis e metacaracteres no StdioUpstream
- SEC-03: Firewall Anti-SSRF impedindo requisições para localhost, 127.0.0.1 e metadados de nuvem
- SEC-04: Criptografia transparente em repouso (AES-256/Fernet) para env e auth_config no SQLite
- SEC-05: Postura Fail-Closed na validação de tokens MCP de instâncias
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from central.config import settings
from central.db.entities import ConnectionEntity, InstanceEntity
from central.db.repository import CentralRepository
from central.db.seeder import init_database
from central.db.session import get_db_context
from central.gateway.instance_gateway import InstanceGateway
from central.models import InstanceConfig
from central.security.crypto import encrypt_string, decrypt_string
from central.security.ssrf import is_safe_external_url
from central.security.validation import validate_stdio_command
from central.server import app


@pytest.fixture(scope="module", autouse=True)
def setup_security_suite():
    init_database(settings.CONFIG_PATH)


# ==============================================================================
# SEC-01: Autenticação Administrativa
# ==============================================================================

@pytest.mark.asyncio
async def test_sec01_unauthenticated_api_request_rejected():
    """Requisição anônima para /api/v1/connections deve ser sumariamente bloqueada com 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/connections")
        assert res.status_code == 401
        assert "Não autorizado" in res.json()["detail"]


@pytest.mark.asyncio
async def test_sec01_invalid_key_rejected():
    """Requisição com chave administrativa inválida deve ser bloqueada com 401."""
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": "chave_incorreta_hacker_123"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.get("/api/v1/overview")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_sec01_valid_key_accepted():
    """Requisição com a chave correta via Header X-Central-Admin-Key ou Bearer deve ser aceita com 200."""
    transport = ASGITransport(app=app)
    # Teste via X-Central-Admin-Key
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.get("/api/v1/overview")
        assert res.status_code == 200

    # Teste via Authorization: Bearer
    bearer_headers = {"Authorization": f"Bearer {settings.CENTRAL_ADMIN_KEY}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=bearer_headers) as client:
        res = await client.get("/api/v1/connections")
        assert res.status_code == 200


# ==============================================================================
# SEC-02: Prevenção de RCE e Allowlist de Executáveis Stdio
# ==============================================================================

def test_sec02_prohibited_executables_blocked():
    """Executáveis perigosos de sistema (cmd, powershell, sh, bash) devem ser bloqueados."""
    with pytest.raises(ValueError, match="não autorizado por política de cibersegurança"):
        validate_stdio_command("cmd.exe", ["/c", "dir"])

    with pytest.raises(ValueError, match="não autorizado por política de cibersegurança"):
        validate_stdio_command("powershell.exe", ["-Command", "Get-Process"])

    with pytest.raises(ValueError, match="não autorizado por política de cibersegurança"):
        validate_stdio_command("/bin/bash", ["-c", "id"])


def test_sec02_shell_metacharacters_in_arguments_blocked():
    """Metacaracteres de injeção de shell (;, |, &, `, $) devem ser bloqueados."""
    with pytest.raises(ValueError, match="proibidos por política de segurança"):
        validate_stdio_command("npx", ["-y", "mcp-pkg; whoami"])

    with pytest.raises(ValueError, match="proibidos por política de segurança"):
        validate_stdio_command("python", ["script.py", "|", "calc.exe"])


def test_sec02_allowed_executables_accepted():
    """Binários homologados (npx, node, python, uvx) com argumentos limpos devem ser aceitos."""
    validate_stdio_command("npx", ["-y", "@modelcontextprotocol/server-filesystem", "C:\\temp"])
    validate_stdio_command("python", ["my_mcp_server.py"])
    validate_stdio_command("uvx", ["mcp-server-git"])


@pytest.mark.asyncio
async def test_sec02_api_blocks_rce_payload():
    """Endpoint POST /api/v1/connections deve rejeitar tentativas de registro de comandos maliciosos."""
    transport = ASGITransport(app=app)
    headers = {"X-Central-Admin-Key": settings.CENTRAL_ADMIN_KEY}
    payload = {
        "id": "malicious_conn",
        "name": "Exploit Test",
        "type": "stdio",
        "prefix": "exploit",
        "command": "cmd.exe",
        "args": ["/c", "calc.exe"],
    }
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        res = await client.post("/api/v1/connections", json=payload)
        assert res.status_code == 400
        assert "não autorizado por política de cibersegurança" in res.json()["detail"]


# ==============================================================================
# SEC-03: Firewall Anti-SSRF e Isolamento de Rede Host
# ==============================================================================

def test_sec03_local_and_private_destinations_blocked():
    """Destinos de loopback, RFC1918 e metadados devem ser sumariamente bloqueados."""
    safe, reason = is_safe_external_url("http://127.0.0.1:8000/api/v1/connections")
    assert safe is False
    assert "privado/local" in reason or "isolamento" in reason

    safe_lh, reason_lh = is_safe_external_url("http://localhost:3100/admin")
    assert safe_lh is False

    safe_meta, reason_meta = is_safe_external_url("http://169.254.169.254/latest/meta-data")
    assert safe_meta is False

    safe_priv, reason_priv = is_safe_external_url("http://192.168.1.1/router")
    assert safe_priv is False


def test_sec03_public_urls_accepted():
    """URLs públicas válidas na internet devem ser autorizadas."""
    safe, _ = is_safe_external_url("https://api.github.com/events")
    assert safe is True


# ==============================================================================
# SEC-04: Criptografia em Repouso de Segredos no SQLite
# ==============================================================================

def test_sec04_symmetric_encryption_cycle():
    """Garante que a criptografia AES-256/Fernet cifra e decifra dados com integridade."""
    secret = "sk_live_very_secret_whatsapp_token_999"
    encrypted = encrypt_string(secret)
    assert encrypted is not None
    assert encrypted.startswith("enc:")
    assert secret not in encrypted  # Texto claro não pode estar presente

    decrypted = decrypt_string(encrypted)
    assert decrypted == secret


def test_sec04_database_entity_stores_ciphertext():
    """Verifica que o banco grava os dados cifrados e os descriptografa de forma transparente."""
    with get_db_context() as db:
        # Cria ou atualiza conexão de teste
        conn = CentralRepository.create_or_update_connection(
            db=db,
            connection_id="test_crypto_conn",
            name="Conexão Criptografada",
            conn_type="internal",
            prefix="test_crypt",
            env={"SECRET_KEY": "minha_chave_ultra_secreta"},
            auth_config={"api_key": "bearer_secret_token_123"},
        )

        # 1. Leitura via objeto ORM (deve descriptografar transparentemente)
        assert conn.env["SECRET_KEY"] == "minha_chave_ultra_secreta"
        assert conn.auth_config["api_key"] == "bearer_secret_token_123"

        # 2. Leitura raw do SQLite direto no disco (deve conter o prefixo enc:)
        raw_row = db.execute(
            text("SELECT env_json, auth_config_json FROM connections WHERE id = 'test_crypto_conn'")
        ).fetchone()
        assert raw_row is not None
        raw_env, raw_auth = raw_row[0], raw_row[1]

        assert raw_env.startswith("enc:")
        assert "minha_chave_ultra_secreta" not in raw_env
        assert raw_auth.startswith("enc:")
        assert "bearer_secret_token_123" not in raw_auth


# ==============================================================================
# SEC-05: Postura Fail-Closed nos Tokens MCP
# ==============================================================================

def test_sec05_empty_tokens_fails_closed():
    """Se uma instância for criada sem nenhum token de acesso, deve negar o acesso (Fail-Closed)."""
    cfg = InstanceConfig(
        id="empty_instance",
        name="Empty Instance",
        slug="empty-instance",
        tokens=[],  # Sem tokens
        connections=[],
    )
    gw = InstanceGateway(cfg)
    assert len(gw.valid_tokens) == 0

    # Nenhuma requisição (com token ou sem token) pode passar
    assert gw.validate_token(None) is False
    assert gw.validate_token("qualquer_token") is False
    assert gw.validate_token("") is False
