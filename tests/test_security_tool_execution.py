"""Tool authorization must fail closed when policy state is unavailable."""

from contextlib import contextmanager

import mcp.types as types
import pytest

from central.gateway.instance_gateway import InstanceGateway
from central.models import InstanceConfig


class RecordingUpstream:
    prefix = "demo"

    def __init__(self) -> None:
        self.called = False

    async def call_tool(self, name, arguments):
        self.called = True
        return types.CallToolResult(
            is_error=False,
            content=[types.TextContent(type="text", text="executed")],
        )


@pytest.mark.asyncio
async def test_tool_execution_fails_closed_when_policy_database_is_unavailable(
    monkeypatch,
) -> None:
    gateway = InstanceGateway(
        InstanceConfig(
            id="fail-closed",
            name="Fail closed",
            slug="fail-closed",
            tokens=[],
            connections=[],
        )
    )
    upstream = RecordingUpstream()
    gateway.upstreams["demo-connection"] = upstream
    gateway.tool_prefix_map["demo"] = "demo-connection"

    @contextmanager
    def unavailable_database():
        raise RuntimeError("database unavailable")
        yield

    monkeypatch.setattr(
        "central.gateway.instance_gateway.get_db_context",
        unavailable_database,
    )

    result = await gateway._handle_call_tool(
        None,
        types.CallToolRequestParams(name="demo__dangerous", arguments={}),
    )

    assert result.is_error is True
    assert upstream.called is False
    assert "autorização" in result.content[0].text.lower()
