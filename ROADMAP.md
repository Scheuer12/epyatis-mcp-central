# Roadmap

Epyatis MCP Central is being built in public. This roadmap communicates direction and contribution opportunities; it is not a delivery commitment or release schedule.

Work is prioritized by security impact, evidence, user value and maintainability. GitHub issues and accepted design discussions are the source of truth for individual tasks.

## Now — qualify a controlled beta

- [ ] Isolate every legacy test from real SQLite files, credentials, network services and subprocesses.
- [ ] Obtain a complete green test run on Python 3.11, 3.12 and 3.13 in CI.
- [ ] Close the outbound DNS rebinding/TOCTOU gap through IP pinning or enforced egress policy.
- [ ] Self-host dashboard assets and remove unsafe inline/eval CSP requirements.
- [ ] Rehearse database migration, rollback and restore using a sanitized representative dataset.
- [ ] Define and validate the first supported MCP client/protocol compatibility matrix.
- [ ] Add pinned secret scanning and complete a coordinated history/credential review.
- [ ] Add browser smoke tests for authentication, token issuance, tenant boundaries and logout.

## Next — operational reliability

- [ ] Adopt a versioned database migration system with rollback tests.
- [ ] Define the supported single-process topology or implement durable/distributed MCP sessions.
- [ ] Add explicit reverse-proxy, TLS and rate-limit deployment guidance.
- [ ] Improve structured logs, metrics, health checks and operator diagnostics without leaking sensitive data.
- [ ] Add hostile-upstream integration tests for remote MCP and OpenAPI adapters.
- [ ] Add coverage reporting and establish risk-based coverage targets.
- [ ] Improve Linux/macOS development verification and clean-clone installation tests.

## Later — ecosystem and product evolution

- [ ] Publish a stable connector authoring contract and examples.
- [ ] Evaluate database backends beyond single-node SQLite based on demonstrated demand.
- [ ] Improve dashboard accessibility, responsiveness and operational workflows.
- [ ] Add import/export flows for reviewed configuration without exporting secrets.
- [ ] Establish release channels, compatibility policy and deprecation rules.
- [ ] Define community governance if the contributor base grows beyond maintainer-led decisions.

## Good first contribution areas

Not every useful contribution requires changing the gateway core. Good entry points include:

- documentation corrections and missing examples;
- cross-platform setup verification;
- isolated unit tests for edge cases;
- clearer validation and error messages;
- accessibility findings with reproducible evidence;
- generic example configurations that contain no real credentials or organization data.

Before starting a larger item, open an issue describing the problem, proposed acceptance criteria and intended scope. See [CONTRIBUTING.md](CONTRIBUTING.md).

