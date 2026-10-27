"""
Módulo de Cibersegurança do Epyatis MCP Central: Criptografia em Repouso (SEC-04).
Utiliza criptografia simétrica autenticada AES-256 (Fernet) com chave derivada por SHA-256.
"""

import base64
import hashlib
import json
import logging
import secrets
from typing import Any
from cryptography.fernet import Fernet
from central.config import settings

logger = logging.getLogger(__name__)

_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        raw_key = settings.CENTRAL_SECRET_KEY.encode("utf-8")
        derived = hashlib.sha256(raw_key).digest()
        b64_key = base64.urlsafe_b64encode(derived)
        _fernet_instance = Fernet(b64_key)
    return _fernet_instance


def encrypt_string(plaintext: str | None) -> str | None:
    """Criptografa uma string em formato seguro com prefixo enc:."""
    if plaintext is None or plaintext == "":
        return plaintext
    try:
        f = _get_fernet()
        token = f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"enc:{token}"
    except Exception as e:
        logger.error(f"Erro ao criptografar dado: {e}")
        return plaintext


def decrypt_string(ciphertext: str | None) -> str | None:
    """Descriptografa uma string. Se não tiver o prefixo enc:, retorna o valor original (compatibilidade retroativa)."""
    if ciphertext is None or ciphertext == "":
        return ciphertext
    if not ciphertext.startswith("enc:"):
        return ciphertext  # Texto legado sem cifragem

    token = ciphertext[4:]
    try:
        f = _get_fernet()
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro ao descriptografar dado sensível: {e}")
        return None


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
        return {}
    try:
        return json.loads(decrypted_str)
    except Exception as e:
        logger.warning(f"Falha ao desserializar JSON descriptografado: {e}")
        return {}


def hash_password(password: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 com salt aleatório para armazenamento seguro de senhas."""
    if not password:
        return ""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, hashed: str | None) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    if not password or not hashed or "$" not in hashed:
        return False
    salt, key_hex = hashed.split("$", 1)
    test_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return secrets.compare_digest(test_key.hex(), key_hex)
