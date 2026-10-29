"""
Módulo de Cibersegurança do Epyatis MCP Central: Criptografia em Repouso (SEC-04).
Utiliza criptografia simétrica autenticada Fernet com chave derivada por SHA-256.
Implementa Fail-Closed estrito: falhas de criptografia nunca retornam texto plano.
"""

import base64
import hashlib
import json
import logging
import secrets
from typing import Any, cast
from cryptography.fernet import Fernet
from central.config import settings

logger = logging.getLogger(__name__)

_fernet_instance: Fernet | None = None

DEFAULT_PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 100_000


class CryptoError(RuntimeError):
    """Exceção levantada quando ocorre falha crítica de criptografia em repouso."""
    pass


def reset_fernet_instance() -> None:
    """Reseta a instância do Fernet (útil para testes ou rotação de chave em memória)."""
    global _fernet_instance
    _fernet_instance = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        raw_key = cast(str, settings.CENTRAL_SECRET_KEY).encode("utf-8")
        derived = hashlib.sha256(raw_key).digest()
        b64_key = base64.urlsafe_b64encode(derived)
        _fernet_instance = Fernet(b64_key)
    return _fernet_instance


def encrypt_string(plaintext: str | None) -> str | None:
    """
    Criptografa uma string em formato seguro com prefixo enc:.
    Princípio Fail-Closed: se houver falha, levanta CryptoError e NUNCA retorna plaintext.
    """
    if plaintext is None or plaintext == "":
        return plaintext
    try:
        f = _get_fernet()
        token = f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"enc:{token}"
    except Exception as e:
        logger.critical(f"[Security/Crypto] Falha crítica ao criptografar dado: {e}")
        raise CryptoError(f"Falha de criptografia em repouso: {e}. Persistência de plaintext abortada.") from e


def decrypt_string(ciphertext: str | None) -> str | None:
    """Decrypt an authenticated value and reject unmarked plaintext."""
    if ciphertext is None or ciphertext == "":
        return ciphertext
    if not ciphertext.startswith("enc:"):
        raise CryptoError("Dado sensível sem o prefixo criptográfico obrigatório.")

    token = ciphertext[4:]
    try:
        f = _get_fernet()
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"[Security/Crypto] Erro ao descriptografar dado sensível: {e}")
        raise CryptoError("Falha de integridade ou chave incorreta ao descriptografar dado sensível.") from e


def encrypt_json_dict(data: dict[str, Any] | None) -> str | None:
    """Serializa e criptografa um dicionário Python para salvar em coluna SQLite."""
    if data is None:
        return None
    raw_json = json.dumps(data, ensure_ascii=False)
    return encrypt_string(raw_json)


def decrypt_json_dict(stored_value: str | None) -> dict[str, Any]:
    """Descriptografa e desserializa um dicionário armazenado no SQLite."""
    if not stored_value:
        return {}
    decrypted_str = decrypt_string(stored_value)
    if not decrypted_str:
        raise CryptoError("Dado criptografado vazio ou inválido.")
    try:
        return json.loads(decrypted_str)
    except Exception as e:
        logger.error(f"Falha ao desserializar JSON descriptografado: {e}")
        raise CryptoError("Conteúdo descriptografado não contém JSON válido.") from e


def hash_password(password: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 com salt aleatório e fator de trabalho versionado."""
    if not password:
        return ""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), DEFAULT_PBKDF2_ITERATIONS)
    return f"pbkdf2:{DEFAULT_PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(password: str, hashed: str | None) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    Suporta hashes modernos com 'pbkdf2:iter$salt$key' e retrocompatibilidade com '$salt$key' (100.000 iterações).
    """
    if not password or not hashed or "$" not in hashed:
        return False

    try:
        if hashed.startswith("pbkdf2:"):
            # Formato moderno: pbkdf2:<iterations>$salt$key_hex
            parts = hashed.split("$")
            if len(parts) != 3:
                return False
            iterations_str = parts[0].split(":")[1]
            iterations = int(iterations_str)
            salt = parts[1]
            key_hex = parts[2]
            test_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
            return secrets.compare_digest(test_key.hex(), key_hex)
        else:
            # Formato legado: salt$key_hex (100.000 iterações)
            salt, key_hex = hashed.split("$", 1)
            test_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), LEGACY_PBKDF2_ITERATIONS)
            return secrets.compare_digest(test_key.hex(), key_hex)
    except Exception as e:
        logger.error(f"[Security/Crypto] Erro ao verificar hash de senha: {e}")
        return False
