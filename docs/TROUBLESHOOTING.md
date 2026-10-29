# Troubleshooting and beta limitations

## Startup rejects configuration

Missing, short, or historical default secrets are intentionally fatal. Generate new independent values. Production also rejects debug mode and wildcard hosts/origins.

## Existing database migration fails

Stop and preserve the original. Reproduce on a copy, inspect whether legacy JSON fields are malformed, and correct the source data through a reviewed migration. Do not re-enable plaintext fallback.

## A stdio connection is rejected

Only root administrators may register stdio. The command must be `npx`/`npx.cmd`, the package must include an exact semantic version, and that exact identifier must exist in `STDIO_ALLOWED_PACKAGES`.

## A remote URL is rejected

Private, loopback, link-local, reserved, credential-bearing, or ambiguously resolved destinations are blocked. There is no supported bypass for standard users.

## Known preview limitations

The maintained list, impact and contribution opportunities are in [Known limitations](KNOWN_LIMITATIONS.md). Do not copy that list into new documents; keeping one canonical list reduces stale or contradictory status claims.
