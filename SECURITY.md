# Security policy

Security reports are welcome and should be handled privately. Epyatis MCP Central processes bearer credentials, connection configuration and tool calls; a public issue is not an appropriate place for exploit details or sensitive evidence.

## Supported versions and deployment boundary

| Version | Security support | Intended use |
|---|---|---|
| `0.2.0.dev1` / `main` | Best-effort fixes during active development | Source review and isolated local development |
| Any version | Not approved | Public internet, production, highly available or untrusted multi-tenant deployment |

There is currently no stable release line or guaranteed security-response SLA. The known release blockers are documented in [Known limitations](docs/KNOWN_LIMITATIONS.md) and [Release readiness](docs/reports/RELEASE_READINESS.md).

## Reporting a vulnerability

Do **not** open a public issue, discussion or pull request containing vulnerability details.

Use GitHub's private vulnerability reporting for this repository when available. If that option is unavailable, contact the maintainer through the private contact method published on the [maintainer's GitHub profile](https://github.com/Scheuer12).

Include, when safe:

- affected commit, branch or version;
- vulnerability class and security impact;
- required preconditions and affected trust boundary;
- minimal reproduction using synthetic data;
- sanitized logs or proof of concept;
- suggested mitigation, if known;
- whether the issue is already being exploited or publicly known.

Never send real tokens, customer data or unrelated credentials. If a credential may have been exposed, revoke or rotate it before sharing evidence.

## Handling and disclosure

The maintainer will attempt to acknowledge the report, reproduce the issue, assess impact and coordinate a fix according to available capacity. Reporters are asked to avoid public disclosure until a remediation and disclosure plan has been discussed, unless immediate disclosure is required to protect users.

Security fixes should include a regression test when safe and practical. Public advisories must not claim affected versions, exploitability or remediation status without evidence.

## Operational security baseline

- Bind only to a trusted interface and place TLS and rate limiting at a reviewed reverse proxy.
- Supply independent `CENTRAL_SECRET_KEY` and `CENTRAL_ADMIN_KEY` values of at least 32 characters; never use examples or historical defaults.
- Send bearer credentials only in `Authorization` or the documented administrative/session headers.
- Keep `STDIO_ALLOWED_PACKAGES` empty unless a root administrator approves an exact package and version.
- Back up the database before upgrades and verify migrations on a disposable copy first.
- Treat logs, databases, `.env`, OAuth files, backup folders and generated SBOMs according to their sensitivity.
- Review Git history and old artifacts separately; cleaning the current tree does not revoke or remove historical secrets.

See the [Security hardening guide](docs/SECURITY_HARDENING_GUIDE.md) and [Security architecture](docs/architecture/SECURITY_ARCHITECTURE.md).
