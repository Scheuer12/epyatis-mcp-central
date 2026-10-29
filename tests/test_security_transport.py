"""Security regressions for HTTP and MCP transport handling."""

from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from central.server import app
from central.ui.dashboard import DASHBOARD_HTML


class FakeTransport:
    async def handle_post_message(self, scope, receive, send) -> None:
        raise AssertionError("unauthenticated message transport must not be invoked")


class FakeGateway:
    def __init__(self) -> None:
        self.config = SimpleNamespace(name="Test MCP")
        self.sse_transport = FakeTransport()

    def validate_token(self, token: str | None) -> bool:
        return token == "valid-instance-token"


@pytest.fixture()
def fake_gateway(monkeypatch) -> FakeGateway:
    gateway = FakeGateway()
    monkeypatch.setattr(
        "central.server.gateway_manager.get_instance",
        lambda slug: gateway if slug == "test-instance" else None,
    )
    return gateway


@pytest.mark.asyncio
async def test_mcp_token_in_query_string_is_rejected(fake_gateway) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/mcp/test-instance?token=valid-instance-token",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_initialize_issues_unique_sessions(fake_gateway) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    headers = {"Authorization": "Bearer valid-instance-token"}
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post("/mcp/test-instance", headers=headers, json=payload)
        second = await client.post("/mcp/test-instance", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["mcp-session-id"]
    assert first.headers["mcp-session-id"] != second.headers["mcp-session-id"]


@pytest.mark.asyncio
async def test_legacy_message_endpoint_requires_bearer_token(fake_gateway) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/mcp/test-instance/messages", content=b"{}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_untrusted_cors_origin_is_not_allowed() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.options(
            "/api/v1/overview",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.headers.get("access-control-allow-origin") is None


def test_dashboard_does_not_persist_or_embed_bearer_credentials() -> None:
    assert "localStorage" not in DASHBOARD_HTML
    assert "?token=" not in DASHBOARD_HTML
    assert 'x-text="t.token"' not in DASHBOARD_HTML
    assert "valor exibido somente na emissão" in DASHBOARD_HTML
