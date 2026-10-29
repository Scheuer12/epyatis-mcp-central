"""One-way storage and constant-time validation for bearer credentials."""

import hashlib
import secrets


TOKEN_HASH_PREFIX = "sha256:"


def hash_bearer_token(token: str) -> str:
    if not token:
        raise ValueError("Token não pode ser vazio.")
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{TOKEN_HASH_PREFIX}{digest}"


def verify_bearer_token(candidate: str | None, stored: str) -> bool:
    if not candidate or not stored:
        return False
    if not stored.startswith(TOKEN_HASH_PREFIX):
        return False
    return secrets.compare_digest(hash_bearer_token(candidate), stored)


def mask_bearer_token(stored: str) -> str:
    if stored.startswith(TOKEN_HASH_PREFIX):
        return "configured"
    if len(stored) <= 8:
        return "********"
    return f"{stored[:4]}…{stored[-4:]}"
