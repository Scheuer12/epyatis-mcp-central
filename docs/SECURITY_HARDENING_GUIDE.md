# Security hardening guide

## 1. Create a clean configuration

Copy `.env.example` to a local, ignored `.env`. Generate independent values:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Assign one value to `CENTRAL_SECRET_KEY` and the other to `CENTRAL_ADMIN_KEY`. Do not reuse historical values. Production startup rejects missing, short, known-default, wildcard-host, wildcard-origin, and debug configurations.

## 2. Migrate existing data safely

1. Stop the service.
2. Make an encrypted, access-controlled backup outside the publication tree.
3. Rotate any credential that has appeared in logs, terminal output, Git history, backups, or shared files.
4. Start against a disposable copy first. Startup migrates legacy session/instance tokens to digests and validated JSON secret columns to encrypted values.
5. Verify login, instance access, token reissuance, and upstream connectivity before promoting the database.

Migration failure aborts startup. Do not bypass it by restoring plaintext fallback behavior.

## 3. Configure exposure

- Default to `127.0.0.1` and use an authenticated TLS reverse proxy for any broader access.
- Set exact `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`; do not use `*`.
- Add proxy rate limits and request timeouts. Application-level distributed rate limiting is not implemented.
- Restrict filesystem and database permissions to the service account.

## 4. Enable stdio only when necessary

Keep `STDIO_ALLOWED_PACKAGES=[]` by default. If required, add only reviewed exact identifiers such as `@vendor/package@1.2.3`. Unversioned packages, Python, Node, shell metacharacters, non-root registration, and unsafe environment variables are rejected.

## 5. Use bearer tokens correctly

Send `Authorization: Bearer <token>`. Never put credentials in URLs, bookmarks, screenshots, analytics, referrers, or browser storage. Save a newly issued value in a secret manager because the Central API will only show its hint later.

## 6. Verify before deployment

```powershell
python -m pytest -p no:cacheprovider tests/test_security_*.py -q
ruff check --no-cache src tests
bandit -q -r src/central -ll
pip-audit --requirement requirements.txt --strict
```

Review `docs/reports/RELEASE_READINESS.md`. Passing these checks alone does not authorize public or production deployment.
