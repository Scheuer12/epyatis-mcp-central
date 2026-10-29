# QA validation report

**Date:** 2026-10-29  
**QA verdict:** **FAIL for full release qualification; PASS for the isolated security regression gate**

## Executed checks

| Check | Environment | Result |
|---|---|---|
| `pytest` security modules | Python 3.13.4, in-memory/temporary test databases, ASGI transport, test-only secrets | 33 passed, 0 failed, 6.02 s |
| `compileall -q -f src tests` | Python 3.13.4, external writable pycache prefix | Passed |
| `ruff check --no-cache src tests` | Ruff 0.16.8; E9/F63/F7/F82 gate | Passed |
| `bandit -q -r src/central -ll` | Bandit 1.9.4; medium/high | Passed, no findings |
| `pip-audit -r requirements.txt --strict` | pip-audit 2.10.1, online advisory lookup | No known vulnerabilities found |
| clean-database startup/migration smoke | Disposable SQLite database | Passed; created one generic instance and one root user |
| PEP 517 wheel build | Isolated build dependencies from `pyproject.toml` | Passed; `epyatis_mcp_central-0.2.0.dev1-py3-none-any.whl` built, then temporary artifact removed |

The security tests cover:

- password/admin/session authentication failures and revocation;
- cross-tenant access and collision prevention;
- secret configuration and crypto fail-closed behavior;
- stdio executable/package policy;
- one-way token storage and verification;
- fail-closed tool execution;
- MCP query-token rejection, session uniqueness, message auth, CORS, and dashboard credential handling.

## Full-suite limitation

The initial full legacy run did not complete: a bootstrap test launched a real `npx` upstream and hung. A later legacy crypto fixture attempted to initialize the repository's configured `central.db` and failed because that database was read-only in the audit environment. These are test-isolation defects. They do not prove product failure, but they prevent a truthful full-suite pass claim.

No legacy test was deleted or weakened to improve the result. Organization-specific legacy tests remain as migration work and are not part of the 33-test security gate.

## Not executed or not demonstrated

- coverage percentage and branch coverage;
- browser end-to-end and accessibility testing;
- Chrome/Edge/Firefox matrix;
- MCP named-client/version interoperability;
- live upstream integration in a disposable environment;
- migration/rollback against a sanitized production-size database copy;
- concurrency, load, soak, rate-limit, recovery, and chaos testing;
- CI execution on GitHub (workflow definitions were added but not remotely run);
- Linux Python 3.11/3.12/3.13 matrix (defined in CI, local evidence is Windows/Python 3.13 only).

## Acceptance status

| Target | Status | Reason |
|---|---|---|
| Local development preview | GO WITH CONDITIONS | Security gate passes; rotate local secrets and use disposable data. |
| Controlled isolated beta | NO-GO | Full hermetic suite, browser/interoperability, and migration evidence are missing. |
| Public beta / production | NO-GO | Security and operational blockers in the cybersecurity report remain. |

## Required next QA work

1. Introduce a global temporary-database fixture and prohibit real upstream startup by default.
2. Convert organization-bound tests to generic fixtures without removing behavioral assertions.
3. Add mocked hostile DNS/upstream tests and browser CSP/credential tests.
4. Run the Python 3.11/3.12/3.13 CI matrix and preserve JUnit, coverage, Bandit, dependency, and SBOM artifacts.
5. Establish supported MCP clients/versions and execute the interoperability matrix.
