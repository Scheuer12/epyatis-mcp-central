"""Negative authorization tests across tenant-owned resources."""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from central.db.entities import Base
from central.db.repository import CentralRepository
from central.db.session import get_db
from central.server import app


@pytest.fixture()
def isolated_database() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield test_session
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


def _create_user_session(
    session_factory: sessionmaker[Session],
    username: str,
) -> tuple[str, str]:
    with session_factory() as db:
        user = CentralRepository.create_user_with_password(
            db,
            username=username,
            password=f"Long-password-for-{username}-1!",
        )
        token = f"session-{username}"
        CentralRepository.create_session(
            db,
            user.id,
            token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        return user.id, token


@pytest.mark.asyncio
async def test_connection_create_cannot_overwrite_another_users_id(
    isolated_database,
) -> None:
    session_factory = isolated_database
    alice_id, _ = _create_user_session(session_factory, "alice")
    _, bob_token = _create_user_session(session_factory, "bob")

    with session_factory() as db:
        CentralRepository.create_or_update_connection(
            db,
            connection_id="alice-private",
            name="Alice original",
            conn_type="internal",
            prefix="alice",
            visibility="private",
            user_id=alice_id,
        )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/connections",
            headers={"X-Central-Session-Token": bob_token},
            json={
                "id": "alice-private",
                "name": "Bob overwrite",
                "type": "internal",
                "prefix": "bob",
                "visibility": "private",
            },
        )

    assert response.status_code == 409
    with session_factory() as db:
        unchanged = CentralRepository.get_connection_by_id(db, "alice-private")
        assert unchanged is not None
        assert unchanged.name == "Alice original"
        assert unchanged.user_id == alice_id


@pytest.mark.asyncio
async def test_private_instance_subresources_deny_other_tenant(
    isolated_database,
    monkeypatch,
) -> None:
    session_factory = isolated_database
    alice_id, _ = _create_user_session(session_factory, "alice-instance-owner")
    _, bob_token = _create_user_session(session_factory, "bob-instance-attacker")

    with session_factory() as db:
        instance = CentralRepository.create_instance(
            db,
            name="Alice private instance",
            slug="alice-private-instance",
            user_id=alice_id,
            visibility="private",
            data_sources_map={"organization": "Alice", "sources": []},
        )
        connection = CentralRepository.create_or_update_connection(
            db,
            connection_id="alice-private-connection",
            name="Alice private connection",
            conn_type="internal",
            prefix="aliceprivate",
            visibility="private",
            user_id=alice_id,
        )
        instance_id = instance.id
        connection_id = connection.id

    async def fake_reload_instance(*args, **kwargs) -> bool:
        return True

    monkeypatch.setattr(
        "central.api.routes.gateway_manager.reload_instance",
        fake_reload_instance,
    )

    requests = [
        ("GET", "/api/v1/instances/alice-private-instance/shares", None),
        ("GET", "/api/v1/instances/alice-private-instance/sources-map", None),
        ("GET", "/api/v1/instances/alice-private-instance/tools", None),
        ("GET", "/api/v1/instances/alice-private-instance/audit-logs", None),
        (
            "POST",
            f"/api/v1/instances/{instance_id}/tokens",
            {"label": "stolen"},
        ),
        (
            "POST",
            "/api/v1/instances/alice-private-instance/connections",
            {"connection_id": connection_id},
        ),
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for method, url, body in requests:
            response = await client.request(
                method,
                url,
                headers={"X-Central-Session-Token": bob_token},
                json=body,
            )
            assert response.status_code == 403, (method, url, response.text)


@pytest.mark.asyncio
async def test_standard_user_cannot_register_stdio_connection(
    isolated_database,
) -> None:
    _, user_token = _create_user_session(isolated_database, "standard-stdio-user")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/connections",
            headers={"X-Central-Session-Token": user_token},
            json={
                "id": "unsafe-stdio",
                "name": "Unsafe stdio",
                "type": "stdio",
                "prefix": "unsafe",
                "command": "python",
                "args": ["arbitrary.py"],
                "visibility": "private",
            },
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_instance_listing_never_returns_bearer_tokens(
    isolated_database,
) -> None:
    owner_id, owner_token = _create_user_session(isolated_database, "token-list-owner")
    with isolated_database() as db:
        instance = CentralRepository.create_instance(
            db,
            name="Token list instance",
            slug="token-list-instance",
            user_id=owner_id,
            visibility="private",
        )
        stored_tokens = [token.token for token in instance.tokens]
        assert stored_tokens

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/instances",
            headers={"X-Central-Session-Token": owner_token},
        )

    assert response.status_code == 200
    serialized = response.text
    assert all(stored not in serialized for stored in stored_tokens)
    listed = next(item for item in response.json() if item["slug"] == "token-list-instance")
    assert all("token" not in item for item in listed["tokens"])
