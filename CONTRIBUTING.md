# Contributing to Epyatis MCP Central

Thank you for your interest in contributing to **Epyatis MCP Central**. This project is an enterprise-grade gateway, orchestrator, and security proxy for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), designed to aggregate heterogeneous upstream tools (stdio subprocesses, remote SSE servers, OpenAPI endpoints) into scoped, multi-tenant endpoints for autonomous AI agents.

We welcome contributions from the community. To ensure architectural integrity, reliability, and security, all contributions must adhere to the standards outlined in this guide.

---

## Table of Contents

1. [Architectural Principles](#architectural-principles)
2. [Development Environment Setup](#development-environment-setup)
3. [Coding Standards](#coding-standards)
4. [Security Guidelines & Invariants](#security-guidelines--invariants)
5. [Testing & QA Protocols](#testing--qa-protocols)
6. [Contribution Workflow](#contribution-workflow)
7. [Reporting Security Issues](#reporting-security-issues)

---

## Architectural Principles

When writing or extending components in Epyatis MCP Central, keep the following core tenets in mind:

- **Defense in Depth & Zero Trust:** Never assume upstream servers or incoming agent clients are benign. Enforce strict token authentication, SSRF boundaries on external network requests, and filesystem containment on local tools.
- **Fail-Safe Isolation:** A failure in an upstream connection (e.g., an unresponsive stdio process or timed-out SSE server) must never crash the Central gateway or disrupt other isolated instances.
- **Strict Governance:** Scoping rules (`private`, `shared`, `public`) are enforced at the repository and controller layers. Only users with the `epy_root` master administrative role may elevate an asset to `public`.
- **Zero Secrets in Persistence:** Upstream authentication tokens, OAuth refresh credentials, and sensitive headers must be encrypted at rest using AES-128-CBC (Fernet) backed by `CENTRAL_SECRET_KEY`.
- **Stateless MCP Routing:** The gateway routes JSON-RPC 2.0 requests between AI agents and upstream tools dynamically while maintaining audit logs and metrics asynchronously.

---

## Development Environment Setup

### Prerequisites

- **Python 3.11+** (Python 3.12 or 3.13 recommended)
- **Node.js 18+** (required for `npx`-based stdio MCP servers like `@us-all/google-drive-mcp`)
- **Git**

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Scheuer12/epyatis-mcp-central.git
   cd epyatis-mcp-central
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv

   # Linux/macOS
   source .venv/bin/activate

   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install runtime and development dependencies:
   ```bash
   pip install -e .
   pip install pytest pytest-asyncio
   ```

4. Configure your environment variables:
   ```bash
   cp .env.example .env
   ```
   Generate a secure 32-byte secret key and assign it in `.env`:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. Run the local development server:
   ```bash
   python -m central.main
   ```
   Or with Uvicorn live-reload:
   ```bash
   uvicorn central.server:app --reload --port 8000
   ```
   Access the dashboard at `http://127.0.0.1:8000`.

---

## Coding Standards

### Python & Typing Guidelines

- **Strict Typing:** All function signatures and class definitions must include PEP 484/526 type hints. Avoid `Any` when a concrete Pydantic model, entity, or union type can be specified.
- **Async Concurrency:** Asynchronous endpoints and network operations must utilize `async/await` idiomatically. Use persistent `httpx.AsyncClient` instances rather than recreating clients per request.
- **No AI / Robotic Comments:** Avoid redundant meta-commentary (e.g., `"# Helper function for step 2"` or `"# Implemented as requested"`). Write idiomatic, self-explanatory code complemented by clear docstrings detailing arguments, return types, and failure states.
- **Database Contexts:** Always utilize `get_db_context()` or FastAPI's `Depends(get_db)` to ensure SQLite connection transactions are committed and closed reliably.

### Repository Layout

```
.
├── config/                  # Declarative bootstrap configurations (YAML)
├── scripts/                 # Operational utilities (OAuth token helpers, migration tools)
├── src/central/
│   ├── api/                 # FastAPI REST routing and controller layer
│   ├── db/                  # SQLAlchemy entities, repository CRUD, and migration seeders
│   ├── gateway/             # Core MCP Instance Gateway and dynamic proxy manager
│   ├── security/            # Token auth, AES crypto, SSRF validation, and input sanitization
│   ├── templates_catalog/   # Pre-configured upstream connection templates
│   ├── ui/                  # Operational Alpine.js / Tailwind CSS dashboard
│   ├── upstreams/           # Upstream drivers: Stdio, Remote SSE, and dynamic OpenAPI
│   ├── config.py            # Pydantic Settings configuration loader
│   ├── main.py              # CLI entry point
│   ├── models.py            # Pydantic schema validation models
│   └── server.py            # FastAPI application factory
└── tests/                   # Pytest automated test suites
```

---

## Security Guidelines & Invariants

All contributors must respect the following security invariants:

1. **Anti-SSRF Protection:** Any feature accepting user-supplied URLs (e.g., Remote SSE endpoints, OpenAPI spec URLs) must pass validation through `central.security.ssrf.is_safe_url`. Requests targeting loopback (`127.0.0.1`), link-local (`169.254.169.254`), or private RFC 1918 subnets without explicit admin opt-in must be rejected.
2. **Path Traversal Protection:** Filesystem tools or configuration loaders must resolve canonical paths using `pathlib.Path.resolve()` and verify they remain within explicitly authorized base directories.
3. **No Plaintext Secrets in Version Control:** Never commit real API keys, bearer tokens, private keys, or credentials files. The `.gitignore` must strictly exclude `.env`, `*.keys.json`, `.*credentials.json`, and database binaries.
4. **Visibility Authorization:** Whenever querying or altering `ConnectionEntity`, `InstanceEntity`, `ConnectionTemplateEntity`, or `DataSourceKitEntity`, enforce visibility filtering using the active `UserEntity.id` and role permissions.

---

## Testing & QA Protocols

Every pull request must pass the comprehensive automated test suite.

Run all tests:
```bash
pytest -v
```

### Writing New Tests

- Unit and integration tests reside in the `tests/` directory.
- Test names should clearly reflect the functional domain (e.g., `test_ssrf_mitigation_on_private_ip`, `test_standard_user_cannot_set_public_visibility`).
- Avoid network flakiness: mock external third-party APIs or use local HTTP test servers where appropriate.

---

## Contribution Workflow

1. **Fork & Branch:** Create a branch from `master` following standard naming:
   - `feat/feature-name`
   - `fix/bug-description`
   - `security/hardening-patch`
   - `docs/documentation-update`

2. **Commit Conventions:** Write descriptive, imperative commit messages:
   - `feat(gateway): implement retry backoff for SSE upstreams`
   - `fix(security): sanitize OpenAPI spec parameter resolution`
   - `test(auth): add visibility boundary tests for templates`

3. **Pre-Submission Checklist:**
   - [ ] All tests pass (`pytest -v`).
   - [ ] No temporary files, SQLite databases, or local credentials staged (`git status`).
   - [ ] Documentation updated to reflect changes.
   - [ ] Code is formatted and typed cleanly.

4. **Submit a Pull Request:** Open a PR against `master` with a clear description of changes, architectural rationale, and verification steps.

---

## Reporting Security Issues

If you discover a security vulnerability or potential threat in Epyatis MCP Central, please do **NOT** open a public issue. Instead, disclose it responsibly by contacting the maintainer directly at the email listed on their GitHub profile. We appreciate your efforts to keep this ecosystem secure.
