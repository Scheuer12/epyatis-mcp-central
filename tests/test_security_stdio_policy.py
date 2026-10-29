"""Security policy for local subprocess-backed MCP connectors."""

import pytest

from central.config import settings
from central.security.validation import validate_stdio_command
from central.upstreams.stdio_upstream import StdioUpstream


@pytest.mark.parametrize(
    ("command", "args"),
    [
        ("python", ["connector.py"]),
        ("node", ["connector.js"]),
        ("npx", ["-y", "untrusted-package"]),
        ("npx", ["-y", "@scope/untrusted@latest"]),
    ],
)
def test_dynamic_or_unpinned_stdio_execution_is_rejected(command, args) -> None:
    with pytest.raises(ValueError):
        validate_stdio_command(command, args)


def test_exact_admin_allowlisted_package_is_accepted(monkeypatch) -> None:
    package = "@modelcontextprotocol/server-filesystem@1.2.3"
    monkeypatch.setattr(settings, "STDIO_ALLOWED_PACKAGES", [package])

    validate_stdio_command("npx", ["-y", package, "C:\\sandbox"])


def test_stdio_environment_does_not_inherit_runtime_injection_paths(monkeypatch) -> None:
    package = "@modelcontextprotocol/server-filesystem@1.2.3"
    monkeypatch.setattr(settings, "STDIO_ALLOWED_PACKAGES", [package])
    monkeypatch.setenv("PYTHONPATH", "C:\\attacker")
    monkeypatch.setenv("NODE_PATH", "C:\\attacker")
    monkeypatch.setenv("CENTRAL_ADMIN_KEY", "must-not-leak")

    upstream = StdioUpstream(
        connection_id="safe-env",
        prefix="safe",
        command="npx",
        args=["-y", package, "C:\\sandbox"],
        env={"CENTRAL_SECRET_KEY": "must-not-inject", "CONNECTOR_SCOPE": "sandbox"},
    )
    child_env = upstream._get_server_params().env

    assert "PYTHONPATH" not in child_env
    assert "NODE_PATH" not in child_env
    assert "CENTRAL_ADMIN_KEY" not in child_env
    assert "CENTRAL_SECRET_KEY" not in child_env
    assert child_env["CONNECTOR_SCOPE"] == "sandbox"
