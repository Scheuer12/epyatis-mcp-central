# Contributing to Epyatis MCP Central

Thanks for considering a contribution. Epyatis MCP Central is an early-stage project being developed in public, and contributions are welcome from engineers, security researchers, technical writers, product thinkers and people testing real MCP workflows.

You do not need to understand the entire codebase before contributing. Start with a bounded problem, ask questions in the relevant issue and preserve the security invariants described below.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

1. Read the [README](README.md), [Roadmap](ROADMAP.md) and [Known limitations](docs/KNOWN_LIMITATIONS.md).
2. Search existing issues and pull requests to avoid duplicating work.
3. For a bug, documentation gap or small isolated fix, open the appropriate issue form.
4. For architecture, security behavior, public API changes or work spanning several modules, open an issue and agree on the direction before implementing.
5. Never post credentials, private customer data or exploit details in a public issue. Follow [SECURITY.md](SECURITY.md) for vulnerability reports.

## Contributions we are actively looking for

- isolating legacy tests from real databases, networks and subprocesses;
- MCP client and protocol compatibility fixtures;
- DNS rebinding-resistant outbound transport;
- self-hosted dashboard assets and stricter CSP;
- database migration and rollback infrastructure;
- browser E2E, accessibility and cross-platform testing;
- observability, diagnostics and safe failure handling;
- setup guides, examples, tutorials and architecture documentation;
- focused bug fixes with regression tests.

The roadmap expresses direction, not a promise that every listed feature will be accepted. We prefer small, reviewable changes that close a demonstrated gap.

## Development setup

### Requirements

- Python 3.11 through 3.13;
- Git;
- Node/npm only for explicitly approved stdio work.

### Windows PowerShell

```powershell
git clone https://github.com/Scheuer12/epyatis-mcp-central.git
cd epyatis-mcp-central
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e .
Copy-Item .env.example .env
```

### Linux/macOS

```bash
git clone https://github.com/Scheuer12/epyatis-mcp-central.git
cd epyatis-mcp-central
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e .
cp .env.example .env
```

Generate separate local values for `CENTRAL_SECRET_KEY` and `CENTRAL_ADMIN_KEY`. Use only disposable databases and synthetic credentials while developing.

## Safe test workflow

Set an isolated environment before running tests:

```powershell
$env:CENTRAL_ENV='testing'
$env:CENTRAL_SECRET_KEY='test-suite-secret-key-with-at-least-32-characters'
$env:CENTRAL_ADMIN_KEY='test-suite-admin-key-with-at-least-32-characters'
$env:DATABASE_URL='sqlite:///:memory:'
```

Run the current reproducible gate:

```powershell
python -m pytest -p no:cacheprovider tests/test_security_*.py -q
ruff check --no-cache src tests
bandit -q -r src/central -ll
python -m compileall -q src tests
```

The legacy suite is not fully hermetic. Do not run it against a meaningful database, real OAuth files or production upstreams. Contributions that isolate those tests are especially valuable.

## Engineering expectations

- Inspect existing contracts and conventions before modifying a module.
- Keep changes focused; avoid unrelated rewrites.
- Add a regression test that fails before the fix when practical.
- Treat upstream responses, OpenAPI documents, recovered content and tool arguments as untrusted data.
- Preserve explicit error handling, timeouts and fail-closed authorization.
- Do not weaken tests, CORS, SSRF or authentication to improve compatibility.
- Never commit `.env`, databases, logs, OAuth files, bearer tokens, API keys or generated backups.
- Update documentation when behavior, configuration or limitations change.

### Security invariants

Changes must preserve these properties:

1. Missing or invalid authentication denies access.
2. Resource operations enforce role, ownership and sharing rules.
3. Policy or database uncertainty denies tool execution.
4. Raw bearer values are not persisted or returned after issuance.
5. Sensitive connection configuration is encrypted at rest.
6. Standard users cannot register local subprocesses.
7. User-controlled outbound URLs pass the anti-SSRF boundary.

## Branches and commits

Create a branch from `main` using a descriptive prefix:

- `feat/short-description`
- `fix/short-description`
- `security/short-description`
- `docs/short-description`
- `test/short-description`

Use concise imperative commits when possible, for example:

- `fix(auth): reject revoked sessions`
- `test(ssrf): cover DNS rebinding attempt`
- `docs(contributing): clarify isolated test setup`

## Pull requests

Keep one logical change per pull request. Complete the pull request template and include:

- the problem and why it matters;
- the chosen approach and meaningful trade-offs;
- tests actually executed and their results;
- security or compatibility impact;
- documentation changes;
- screenshots only when they help evaluate UI behavior.

Draft pull requests are welcome for early feedback. A pull request may be declined when it lacks a reproducible problem, expands scope disproportionately, weakens a security boundary or conflicts with the project direction. Maintainers should explain material review decisions.

## AI-assisted contributions

AI-assisted work is welcome, but the contributor remains responsible for every submitted line. Review generated changes, remove fabricated claims, run the stated checks and disclose material AI assistance in the pull request when it helps reviewers understand provenance or risk.

Generated tests must verify requirements rather than merely mirror the implementation.

## Review and merge criteria

A contribution is ready to merge when:

- its scope and behavior are understandable;
- relevant tests pass in an isolated environment;
- security boundaries remain intact;
- public interfaces and configuration are documented;
- no secrets or organization-specific data are introduced;
- CI passes on the repository;
- review comments are resolved or explicitly discussed.

There is no guaranteed response or merge SLA while the project is maintained as an early-stage open-source effort. Constructive follow-ups on the issue or pull request are welcome.

## Communication

Use public issues and pull requests for ordinary project discussion so decisions remain searchable. Use private channels only for vulnerability reports, credentials, personal information or Code of Conduct incidents.

For usage questions and the current support boundary, see [SUPPORT.md](SUPPORT.md).
