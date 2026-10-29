# Known limitations

This document records known product limitations relevant to users and contributors. Sensitive, exploitable security details belong in private vulnerability reports, not public issues.

The current classification remains: development preview only. See the detailed [release readiness report](reports/RELEASE_READINESS.md).

## Test isolation is incomplete

**Impact:** Some legacy tests may start real `npx` processes or use the configured SQLite database. A generic full-suite command is not yet a safe reproducible gate.

**Current safe path:** Run `tests/test_security_*.py` with test-only secrets and a disposable database.

**Contribution opportunity:** Introduce shared temporary-database fixtures and fake upstream adapters, then migrate legacy tests without deleting behavioral assertions.

## SSRF protection does not pin the connected address

**Impact:** A hostname can be validated before a later, separate network connection. An attacker controlling DNS may attempt a time-of-check/time-of-use change.

**Current mitigation:** Private, loopback, link-local, reserved, credential-bearing and unsafe DNS results are rejected; redirects and ambient proxy variables are disabled for OpenAPI.

**Needed:** Connect through a validated address while preserving TLS verification/hostname semantics, or enforce the destination policy in a dedicated egress layer.

## Dashboard depends on third-party CDNs

**Impact:** Offline operation is incomplete and the current Content Security Policy permits inline/evaluated script behavior required by the dashboard implementation.

**Current mitigation:** CDN versions and allowed origins are explicit.

**Needed:** Vendor reviewed assets locally, introduce a frontend build/integrity process and remove unsafe CSP directives.

## MCP interoperability is not certified

**Impact:** The custom HTTP/SSE behavior has not been verified against a published matrix of named clients and protocol versions.

**Current mitigation:** Transport authentication, request limits and session binding have regression coverage.

**Needed:** Define supported clients/versions and test initialize, sessions, reconnects, cancellation, errors and tool results reproducibly.

## Sessions are process-local

**Impact:** MCP HTTP sessions do not survive a process restart and cannot be shared across replicas.

**Current mitigation:** The documented development topology is a single process/node.

**Needed:** Either formalize that topology as a supported constraint or introduce a durable session design with explicit expiration and revocation semantics.

## SQLite and migrations

**Impact:** SQLite is appropriate only for the current single-node preview, and startup schema changes do not provide a full versioned migration/rollback history.

**Current mitigation:** Clean-database startup and controlled legacy secret/token migration have local smoke coverage.

**Needed:** Adopt a migration framework, test upgrade/rollback on representative sanitized data and define backup/restore procedures.

## Rate limiting is external

**Impact:** The application does not provide a distributed rate limiter.

**Current mitigation:** Public exposure is unsupported; operators are instructed to use a reviewed reverse proxy.

**Needed:** Define deployment topology and abuse cases before choosing proxy-only or application-level enforcement.

## Browser, load and recovery testing are incomplete

**Impact:** Browser E2E, accessibility, concurrency, load, soak, failure recovery and production-like rollback are not release-qualified.

**Needed:** Add risk-based suites and preserve their artifacts in CI before expanding the supported deployment scenarios.

## Historical repository review remains an operator task

**Impact:** Cleaning the current working tree does not remove data from Git history, old clones, CI output or backups.

**Needed before broader publication:** Rotate exposed/historical credentials, run approved secret scanning, inspect history and coordinate any rewrite without invalidating collaborators' work unexpectedly.

