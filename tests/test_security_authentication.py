"""Security regressions for the public authentication interface."""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from central.db.entities import Base
from central.config import settings
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


@pytest.mark.asyncio
async def test_login_without_password_cannot_issue_session(isolated_database) -> None:
    session_factory = isolated_database
    with session_factory() as db:
        CentralRepository.create_user_with_password(
            db,
            username="alice",
            password="Correct-Horse-Battery-Staple-1!",
        )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/auth/login", json={"username": "alice"})

    assert response.status_code == 401
    assert "token" not in response.json()


@pytest.mark.asyncio
async def test_public_switch_user_impersonation_endpoint_is_not_available(isolated_database) -> None:
    session_factory = isolated_database
    with session_factory() as db:
        CentralRepository.create_user_with_password(
            db,
            username="admin-target",
            password="Correct-Horse-Battery-Staple-2!",
            role="epy_root",
        )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/switch-user",
            json={"username": "admin-target"},
        )

    assert response.status_code in {404, 405}
    assert "token" not in response.json()


@pytest.mark.asyncio
async def test_admin_key_in_query_string_is_rejected(isolated_database) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/overview",
            params={"admin_key": settings.CENTRAL_ADMIN_KEY},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("session_state", ["expired", "revoked", "inactive"])
async def test_invalid_session_states_are_rejected(
    isolated_database,
    session_state: str,
) -> None:
    session_factory = isolated_database
    token = f"session-{session_state}"
    with session_factory() as db:
        user = CentralRepository.create_user_with_password(
            db,
            username=f"user-{session_state}",
            password="Correct-Horse-Battery-Staple-3!",
        )
        if session_state == "inactive":
            user.is_active = False
            db.commit()
        if session_state != "revoked":
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            if session_state == "expired":
                expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            CentralRepository.create_session(db, user.id, token, expires_at=expires_at)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"X-Central-Session-Token": token},
        )

    assert response.status_code == 401
