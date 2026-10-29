# Changelog

## 0.2.0.dev1 - 2026-10-29

Security-hardening development preview.

### Changed

- Removed unauthenticated login, user-switch impersonation, query-string credentials, and browser credential persistence.
- Centralized tenant-aware authorization for instances, connections, shares, sources, tools, tokens, reloads, and logs.
- Replaced plaintext bearer persistence with SHA-256 token digests and one-time token disclosure.
- Required explicit runtime secrets and rejected historical defaults; secret fields no longer appear in settings representations.
- Made encryption/decryption fail closed and added controlled migration of legacy encrypted fields and token hashes.
- Restricted stdio execution to root-approved, exact-version `npx` packages with sanitized environments and timeouts.
- Added SSRF checks, redirect refusal, proxy-environment isolation, and a 2 MiB OpenAPI response limit.
- Added MCP session binding, request-size limits, security headers, trusted hosts, and restrictive CORS defaults.
- Replaced organization-specific bootstrap content with a generic internal demonstration instance.
- Pinned dependencies and added CI, static security analysis, dependency audit, and CycloneDX SBOM generation.
- Added 33 hermetic security regression tests and security/release documentation.
- Added public contributor onboarding, roadmap, known-limitations register, support policy, Code of Conduct, issue forms, and a pull request template.

### Known limitations

- The legacy integration suite is not isolated from local databases and real subprocess/network upstreams.
- The dashboard still loads third-party CDN assets and requires inline/eval-compatible CSP directives.
- SSRF validation does not pin the validated IP through connection establishment, leaving a DNS rebinding/TOCTOU gap.
- The MCP HTTP/SSE layer is custom and has not completed interoperability testing against named clients.
