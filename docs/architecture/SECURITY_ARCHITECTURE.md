# Security architecture

## Scope and trust boundaries

```text
Browser / MCP client
        |
        | explicit Host, Origin, body, JSON-RPC and bearer validation
        v
FastAPI boundary ---- REST authorization ---- SQLAlchemy / SQLite
        |
        | instance-scoped token + session binding + tool policy
        v
Instance gateway
   |             |                 |
stdio process   remote MCP        OpenAPI
allowlist/env   URL validation    URL validation/size cap
```

External requests, database content, YAML, OpenAPI documents, tool arguments, and upstream responses are untrusted data. None may change authorization or policy merely by containing instructions.

## Authentication and credential lifecycle

- Administrative and user sessions are accepted only through the `Authorization` header.
- `CENTRAL_ADMIN_KEY` authenticates the master administrator but is never accepted in a URL or cookie.
- User sessions expire, can be revoked, and are accepted only for active, approved users.
- Session and instance bearer values are generated with `secrets`, stored as `sha256:` digests, and compared with constant-time verification.
- A new instance/token response returns the clear value once. Subsequent API responses expose only a hint.
- Connection secret JSON is encrypted with Fernet using key material derived from `CENTRAL_SECRET_KEY`. Invalid or plaintext runtime values fail closed.

## Authorization model

`security/auth.py` is the policy seam for instance and connection access. Read, modify, and connection-use operations distinguish root, owner, explicit share, and visibility. Routes must call the corresponding `require_*_access` function before reading subresources or mutating state. Public visibility is not equivalent to permission to execute a connection.

The gateway repeats token and per-tool policy checks. A database/policy error denies execution; it does not fall back to allow.

## Transport controls

- Explicit trusted hosts and local development CORS origins.
- Security headers, request IDs, no-store responses, and HSTS in production.
- 1 MiB request-body cap and JSON-RPC shape validation.
- Unique, expiring MCP session identifiers bound to instance and bearer digest.
- Query-string bearer tokens are rejected.

## Upstream controls

- stdio is root-only and limited to exact-version packages in `STDIO_ALLOWED_PACKAGES`; command, arguments, environment, startup, call, and shutdown are constrained.
- Remote URLs reject embedded credentials, local/private/link-local/reserved addresses, unsafe DNS results, and redirects.
- OpenAPI calls ignore proxy environment variables and limit responses to 2 MiB.
- Audit records keep tool/argument metadata but not argument values or bearer secrets.

## Invariants

1. Missing or invalid authentication denies access.
2. Policy or database uncertainty denies tool execution.
3. Clear bearer values are never returned after issuance.
4. Runtime plaintext secret fields are rejected.
5. Standard users cannot register local subprocesses.
6. A resource identifier collision cannot overwrite another tenant's object.

## Residual architectural risk

DNS validation and the later socket connection are separate operations; an attacker controlling DNS may exploit that time-of-check/time-of-use gap. The dashboard also depends on third-party CDNs and inline script execution. The custom MCP transport has not been verified against a formal interoperability matrix. These are release blockers for public exposure.
