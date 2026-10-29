"""Security configuration must fail closed outside isolated tests."""

import pytest
from pydantic import ValidationError

from central.config import CentralSettings
from central.security.crypto import CryptoError, decrypt_string, hash_password, verify_password


def test_deployment_requires_explicit_secrets(monkeypatch) -> None:
    monkeypatch.delenv("CENTRAL_SECRET_KEY", raising=False)
    monkeypatch.delenv("CENTRAL_ADMIN_KEY", raising=False)

    with pytest.raises(ValidationError, match="CENTRAL_SECRET_KEY"):
        CentralSettings(
            CENTRAL_ENV="production",
            CENTRAL_SECRET_KEY=None,
            CENTRAL_ADMIN_KEY=None,
            _env_file=None,
        )


def test_testing_secrets_are_ephemeral_and_not_predictable(monkeypatch) -> None:
    monkeypatch.delenv("CENTRAL_SECRET_KEY", raising=False)
    monkeypatch.delenv("CENTRAL_ADMIN_KEY", raising=False)

    first = CentralSettings(
        CENTRAL_ENV="testing",
        CENTRAL_SECRET_KEY=None,
        CENTRAL_ADMIN_KEY=None,
        _env_file=None,
    )
    second = CentralSettings(
        CENTRAL_ENV="testing",
        CENTRAL_SECRET_KEY=None,
        CENTRAL_ADMIN_KEY=None,
        _env_file=None,
    )

    assert first.CENTRAL_SECRET_KEY != second.CENTRAL_SECRET_KEY
    assert first.CENTRAL_ADMIN_KEY != second.CENTRAL_ADMIN_KEY
    assert len(first.CENTRAL_SECRET_KEY) >= 32
    assert len(first.CENTRAL_ADMIN_KEY) >= 32


@pytest.mark.parametrize(
    ("field", "known_value"),
    [
        ("CENTRAL_SECRET_KEY", "epyatis-dev-master-secret-key-32b"),
        ("CENTRAL_ADMIN_KEY", "epy_admin_master_secret_2026"),
    ],
)
def test_known_legacy_defaults_are_rejected(field, known_value) -> None:
    values = {
        "CENTRAL_ENV": "development",
        "CENTRAL_SECRET_KEY": "test-secret-key-with-at-least-32-characters",
        "CENTRAL_ADMIN_KEY": "test-admin-key-with-at-least-32-characters",
        "_env_file": None,
    }
    values[field] = known_value

    with pytest.raises(ValidationError):
        CentralSettings(**values)


def test_secret_values_are_redacted_from_settings_repr() -> None:
    marker = "unique-secret-marker-that-must-not-appear"
    configured = CentralSettings(
        CENTRAL_ENV="testing",
        CENTRAL_SECRET_KEY=marker + "-encryption-key",
        CENTRAL_ADMIN_KEY=marker + "-administrator-key",
        PERISKOPE_API_KEY=marker + "-integration-key",
        _env_file=None,
    )

    assert marker not in repr(configured)


def test_plaintext_is_not_accepted_as_encrypted_legacy_data() -> None:
    with pytest.raises(CryptoError):
        decrypt_string('{"api_key":"plaintext-secret"}')


def test_new_password_hashes_use_strengthened_work_factor() -> None:
    password = "Correct-Horse-Battery-Staple-4!"

    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2:600000$")
    assert verify_password(password, hashed) is True
