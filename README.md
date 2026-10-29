# Epyatis MCP Central

[![CI](https://github.com/Scheuer12/epyatis-mcp-central/actions/workflows/ci.yml/badge.svg)](https://github.com/Scheuer12/epyatis-mcp-central/actions/workflows/ci.yml)
[![Security](https://github.com/Scheuer12/epyatis-mcp-central/actions/workflows/security.yml/badge.svg)](https://github.com/Scheuer12/epyatis-mcp-central/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Development Preview](https://img.shields.io/badge/status-development%20preview-orange.svg)](ROADMAP.md)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

**An open-source control plane for composing MCP and OpenAPI tools into governed, access-controlled agent endpoints.**

Epyatis MCP Central is being built in public. The project is usable for source review, local experimentation and isolated development, but it is **not production-ready** and must not yet be exposed directly to the public internet or untrusted tenants.

This is a good moment to contribute: the core gateway exists, the main security boundaries have regression tests, and several important architecture, compatibility, QA and developer-experience problems are deliberately open for community work.

## Why this project exists

AI agents increasingly depend on tools distributed across MCP servers, REST APIs and local processes. Operating each integration separately makes authentication, ownership, tool policy, auditability and endpoint management difficult.

Epyatis MCP Central explores a single control plane that can:

- group multiple upstreams into logical MCP instances;
- issue per-instance credentials without persisting raw bearer tokens;
- control which tools are exposed by each instance;
- separate private, shared and public metadata;
- apply ownership and explicit sharing rules;
- connect internal tools, remote MCP servers and OpenAPI services;
- provide an administrative API and browser dashboard.

## Current project status

| Scenario | Status |
|---|---|
| Source review and local development | **Supported with documented constraints** |
| Isolated experimentation with disposable data | **Supported with caution** |
| Controlled multi-user beta | **Not ready** |
| Public internet or production deployment | **Not ready** |

The current security regression gate has **33 passing tests**. This does not replace the incomplete full integration, browser and interoperability suites. See [Known limitations](docs/KNOWN_LIMITATIONS.md) and [Release readiness](docs/reports/RELEASE_READINESS.md) for the evidence behind these classifications.

## Architecture at a glance

```text
MCP clients / Dashboard / Admin API
                 |
          FastAPI boundary
     auth · tenant policy · sessions
                 |
          Instance gateway
       tool policy · audit · routing
          /         |          \
     internal   remote MCP    OpenAPI
                                \
                       restricted stdio
```

The security design and trust boundaries are documented in [Security architecture](docs/architecture/SECURITY_ARCHITECTURE.md).

## Quick start for local development

### Requirements

- Python 3.11 through 3.13;
- Git;
- Node/npm only if a root administrator explicitly enables a reviewed, exact-version stdio connector.

### Install

```powershell
git clone https://github.com/Scheuer12/epyatis-mcp-central.git
cd epyatis-mcp-central
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
```

Generate **two independent** values and replace the placeholders in `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use one for `CENTRAL_SECRET_KEY` and the other for `CENTRAL_ADMIN_KEY`. Never reuse historical/example values.

Start the service:

```powershell
python -m central.main
```

Open `http://127.0.0.1:8000`. The generic bootstrap creates `demo-suite` with internal diagnostics only and no published bearer token.

For Linux/macOS and more context, see [Installation](docs/INSTALLATION.md).

## Safe verification gate

Install development tooling:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

Run the isolated gate:

```powershell
python -m pytest -p no:cacheprovider tests/test_security_*.py -q
ruff check --no-cache src tests
bandit -q -r src/central -ll
```

Do not run legacy integration tests against a valuable `central.db` or with production credentials. Some legacy tests still require isolation from real subprocesses and local data.

## Where contributors can help now

High-value contribution tracks include:

1. **Test isolation:** move legacy tests to disposable databases and fake upstreams.
2. **Network security:** close the DNS rebinding/TOCTOU gap with destination pinning or an enforced egress layer.
3. **Frontend hardening:** self-host dashboard assets and remove unsafe CSP requirements.
4. **MCP compatibility:** build a reproducible client/protocol interoperability matrix.
5. **Database evolution:** replace ad-hoc schema changes with reviewed migrations and rollback tests.
6. **Developer experience:** improve setup, examples, diagnostics and cross-platform instructions.
7. **Documentation:** tutorials, architecture explanations and contributor onboarding.

Read the [Roadmap](ROADMAP.md), then check existing issues before proposing work. Small documentation and test improvements are welcome; architecture or security changes should start with an issue.

## Security model

- Administrative and session credentials are accepted through headers, not URLs or browser persistence.
- Session and MCP bearer values are stored as one-way digests and raw instance tokens are disclosed only at creation.
- Resource access is checked against role, ownership, visibility and explicit sharing.
- stdio is root-only, disabled by default and restricted to exact-version packages in an administrative allowlist.
- Remote destinations are screened for local, private, link-local, reserved and metadata networks.
- Authorization or policy failures deny tool execution.

These controls reduce risk; they do not make the current preview suitable for hostile public deployment. Report vulnerabilities privately using [SECURITY.md](SECURITY.md).

## MCP client example

Send the token only through `Authorization`:

```json
{
  "mcpServers": {
    "epyatis-local": {
      "url": "http://127.0.0.1:8000/mcp/demo-suite",
      "headers": {
        "Authorization": "Bearer <token-returned-at-creation>"
      }
    }
  }
}
```

Compatibility with specific third-party clients is not yet certified. See the [MCP client guide](docs/MCP_CLIENT_GUIDE.md).

## Community and project documents

- [Contributing guide](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Support](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Security hardening guide](docs/SECURITY_HARDENING_GUIDE.md)
- [Cybersecurity audit](docs/reports/CYBERSECURITY_AUDIT.md)
- [QA validation](docs/reports/QA_VALIDATION_REPORT.md)
- [Release readiness](docs/reports/RELEASE_READINESS.md)
- [Maintainer launch checklist](docs/MAINTAINER_LAUNCH_CHECKLIST.md)
- [Changelog](CHANGELOG.md)

## License

Epyatis MCP Central is available under the [MIT License](LICENSE).
