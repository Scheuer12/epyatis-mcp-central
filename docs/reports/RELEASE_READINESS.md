# Release readiness

**Date:** 2026-10-29  
**Overall verdict:** **NO-GO for controlled or public beta**  
**Permitted state:** development preview only, after credential rotation and with isolated data.

## Readiness summary

| Area | Status | Evidence / gap |
|---|---|---|
| Critical auth and tenant isolation | Pass | Dedicated regression tests pass. |
| Token/session storage | Pass with migration condition | New values are digests; legacy migration must be tested on a sanitized copy. |
| Encryption/configuration | Pass with operator action | Fail-closed controls exist; current local historical secrets must be rotated. |
| stdio execution | Pass for disabled-by-default posture | Exact allowlist/root policy tested; no approved production package inventory exists. |
| SSRF/egress | Fail for public exposure | DNS-to-socket pinning is absent. |
| Dashboard supply chain/CSP | Fail | Third-party CDNs and unsafe CSP allowances remain. |
| Automated security gate | Pass locally | 33 tests, compile, Ruff, Bandit, and dependency audit pass. |
| Full regression suite | Fail | Legacy tests are non-hermetic and incomplete. |
| MCP interoperability | Not demonstrated | Custom transport lacks named-client evidence. |
| Operations/recovery | Not demonstrated | No production topology, rollback rehearsal, rate-limit test, or monitoring SLO. |

## Release gates

### Required before a controlled isolated beta

- Rotate the exposed integration key and every historical/default admin or encryption secret.
- Refactor and pass the entire test suite on temporary databases and fake upstreams.
- Run CI on Python 3.11, 3.12 and 3.13 and retain artifacts.
- Test database migration and restore on a sanitized copy.
- Define and pass at least one supported MCP client/version scenario.
- Complete browser smoke tests for login, one-time token issuance, tenant boundaries, and logout.

### Additional requirements before public beta

- Close DNS rebinding/TOCTOU and remote transport egress gaps.
- Self-host dashboard assets and enforce a strict CSP without unsafe inline/eval.
- Add reviewed TLS termination, rate limiting, monitoring, alerting, backup, restore, and incident runbooks.
- Add pinned secret scanning and review/rewrite history through a coordinated process.
- Perform independent penetration testing and remediate material findings.

### Additional requirements before production

- Define SLOs, capacity and recovery objectives, data retention, privacy obligations, support ownership, rollback authority, and change management.
- Prove multi-replica/session behavior or constrain the supported topology to one process.
- Complete threat-model and architecture review for the actual deployment environment.

## Prioritized action plan

1. **P0 — Credential containment:** rotate the redacted integration credential and local historical secrets; inspect logs/history/backups.
2. **P0 — Test isolation:** stop legacy tests from touching real databases, networks, and subprocesses; obtain a full green run.
3. **P0 — Egress correctness:** pin validated destinations through socket establishment or enforce policy with an egress proxy.
4. **P1 — Frontend supply chain:** vendor assets and tighten CSP.
5. **P1 — Compatibility:** define supported MCP clients and execute interoperability tests.
6. **P1 — Operations:** rate limits, TLS, monitoring, backup/restore, and migration rehearsal.
7. **P2 — Assurance:** coverage targets, browser matrix, load testing, secret scanning, and independent penetration test.

The no-go decision is driven by missing evidence and known architectural gaps, not by the number of changes completed.
