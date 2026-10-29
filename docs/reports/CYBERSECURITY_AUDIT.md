# Cybersecurity audit report

**Assessment date:** 2026-10-29  
**Baseline:** commit `4ff8497d0cdeabd54c5fdd908a0c1b5de85d571a`, branch `hardening/beta-readiness`  
**Verdict:** **PASS WITH CONDITIONS for source-code development preview; FAIL for public beta or production exposure**

## Scope and method

The review covered FastAPI routes/middleware, authentication, tenant authorization, token/session lifecycle, SQLite persistence and startup migration, encryption, MCP gateway policy, stdio, remote SSE, OpenAPI, dashboard credential handling, bootstrap data, dependencies, tests, and CI definitions.

Evidence came from direct source inspection, deliberately failing regression tests followed by fixes, Python compilation, Ruff undefined-name/syntax checks, Bandit medium/high static analysis, and an online `pip-audit` query against the pinned dependency graph. No browser end-to-end, penetration test, packet-level verification, named-client interoperability run, or production-like load test was performed.

## Remediated findings

| ID | Initial severity | Finding | Disposition and evidence |
|---|---:|---|---|
| SEC-001 | Critical | Passwordless login and user-switch endpoint enabled impersonation. | Removed; missing password/admin credential, switch-user, expired/revoked/inactive sessions, and query admin key are regression-tested in `tests/test_security_authentication.py`. |
| SEC-002 | Critical | Instance/connection subresources lacked consistent tenant checks and create could overwrite colliding IDs. | Central `require_instance_access`/`require_connection_access` policies applied; cross-tenant shares, sources, tools, logs, tokens, attachment, and collision cases are tested. |
| SEC-003 | High | Instance/session bearer values could persist or be returned in plaintext. | New values use high entropy, are stored as SHA-256 digests, compared in constant time, migrated at startup, and disclosed once. Lists expose hints only. |
| SEC-004 | High | Tool-policy database failures could allow upstream execution. | Changed to fail closed; `tests/test_security_tool_execution.py` confirms the upstream is not invoked. |
| SEC-005 | High | stdio accepted broad executable classes and inherited a permissive environment. | Root-only exact-version `npx` allowlist, environment filtering, and timeouts added; negative/positive policy tests cover Python, Node, unpinned, and allowlisted packages. |
| SEC-006 | High | Bearer/admin credentials could travel in query strings or browser persistence. | Query/cookie paths and `localStorage` removed; dashboard URLs contain no bearer; messages are authenticated. |
| SEC-007 | High | Predictable runtime defaults and secret representations risked credential disclosure. | Secrets are mandatory outside tests, known defaults are rejected, production wildcards/debug are rejected, and secret fields have `repr=False`. |
| SEC-008 | High | Secret decryption accepted plaintext/invalid values. | Runtime decrypt fails closed. Startup has a separate validated migration path for legacy JSON fields. |
| SEC-009 | Medium | OpenAPI could use ambient proxies and return unbounded response bodies. | `trust_env=False`, redirects disabled, URL revalidation, and a 2 MiB streamed response cap added. |
| SEC-010 | Medium | Audit records could retain tool argument values or oversized errors. | Records now store argument keys/size/redaction metadata and bounded errors instead of values. |
| SEC-011 | Medium | Organization-specific bootstrap/script content was publishable. | Generic `demo-suite` bootstrap installed, organization-specific sync script removed, and `backups/` ignored. |

## Residual findings and blockers

| ID | Severity | Residual risk | Required closure |
|---|---:|---|---|
| RES-001 | High | Anti-SSRF validates DNS before a separate connection; the resolved address is not pinned. A DNS rebinding/TOCTOU attacker may redirect after validation. | Connect to the validated IP while preserving TLS SNI/Host, or use an egress proxy that enforces destination policy; add rebinding tests. |
| RES-002 | High | Dashboard JavaScript/CSS/icons load from third-party CDNs and current CSP permits inline/eval behavior. | Vendor reviewed assets locally, add integrity/build controls, remove unsafe directives, and run browser CSP tests. |
| RES-003 | High | The legacy integration suite is non-hermetic and may start real `npx` processes or modify the configured database. | Refactor fixtures to temporary databases and fake upstreams; run the full suite green before beta. |
| RES-004 | Medium | Custom MCP HTTP/SSE/session behavior has no named-client interoperability evidence and sessions are process-local. | Test supported client/version matrix and adopt the maintained SDK transport where feasible. |
| RES-005 | Medium | No application-level rate limiter or distributed session store exists. | Define deployment topology and enforce authenticated proxy rate limits; add an application control if direct/multi-replica exposure is required. |
| RES-006 | Medium | Remote SSE behavior depends on SDK transport details; response-size and socket-IP pinning controls are not demonstrated there. | Add a controlled transport adapter and hostile-upstream integration tests. |
| RES-007 | Medium | Secret scanning is not yet a CI gate and Git history was not rewritten. | Add a pinned secret-scanning action, review history/backups, rotate exposed credentials, and rewrite history only under an approved coordinated procedure. |

## Credential incident note

During the local audit, a settings object from the pre-hardening code path printed a real integration credential into local test output. The value is intentionally omitted here. `repr=False` now prevents that representation path, but output suppression does not revoke the credential. **Rotate that integration credential immediately**, review terminal/CI logs and backups for copies, and invalidate any historical default admin/encryption secrets. The current local `.env` still uses rejected historical defaults and will fail startup until it is rotated; it was not modified by this audit.

## Verification results

- Hermetic security regression suite: **33 passed in 6.02 s**.
- Python `compileall` over `src` and `tests`: **passed**.
- Ruff configured fatal checks: **passed**.
- Bandit medium/high scan of `src/central`: **passed with no findings**.
- `pip-audit 2.10.1` against pinned requirements on 2026-10-29: **no known vulnerabilities found**. This is time-bound and is not proof of absence.
- Clean disposable-database startup/migration smoke: **passed** with one generic instance and one root user.
- Isolated PEP 517 wheel build for version `0.2.0.dev1`: **passed**; the temporary artifact was removed after verification.

## Security conclusion

The highest-impact authentication, cross-tenant, bearer-storage, stdio, and fail-open defects were fixed with reproducible regression coverage. The remaining DNS rebinding, CDN/CSP, non-hermetic full-suite, and interoperability gaps are material. The repository can be reviewed and developed as a preview after local credential rotation; it is **not approved for public beta or production**.
