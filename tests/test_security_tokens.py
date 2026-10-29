"""Bearer tokens are one-time credentials and are stored as digests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from central.db.entities import Base, UserSessionEntity
from central.db.repository import CentralRepository
from central.gateway.instance_gateway import InstanceGateway
from central.models import InstanceConfig, InstanceToken
from central.security.tokens import hash_bearer_token, mask_bearer_token, verify_bearer_token


def test_gateway_validates_hashed_instance_token() -> None:
    raw_token = "epy_test_very-long-random-instance-token"
    gateway = InstanceGateway(
        InstanceConfig(
            id="token-test",
            name="Token test",
            slug="token-test",
            tokens=[InstanceToken(token=hash_bearer_token(raw_token), label="test")],
            connections=[],
        )
    )

    assert gateway.validate_token(raw_token) is True
    assert gateway.validate_token("wrong-token") is False
    assert raw_token not in gateway.valid_tokens


def test_session_repository_does_not_store_plaintext_token() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    raw_token = "sess_test_plaintext_must_not_be_stored"

    with session_factory() as db:
        user = CentralRepository.create_user_with_password(
            db,
            username="token-user",
            password="Correct-Horse-Battery-Staple-4!",
        )
        CentralRepository.create_session(db, user.id, raw_token)
        stored = db.query(UserSessionEntity).one().token

        assert stored == hash_bearer_token(raw_token)
        assert raw_token not in stored
        assert CentralRepository.get_session_by_token(db, raw_token) is not None

    engine.dispose()


def test_token_mask_never_contains_stored_digest() -> None:
    stored = hash_bearer_token("epy_test_another-long-random-token")

    masked = mask_bearer_token(stored)

    assert stored not in masked
    assert masked.startswith("sha256:") is False


def test_runtime_validation_rejects_legacy_plaintext_storage() -> None:
    raw_token = "legacy-plaintext-token"

    assert verify_bearer_token(raw_token, raw_token) is False
