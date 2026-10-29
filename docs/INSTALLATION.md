# Installation

## Supported development setup

Python 3.11 through 3.13 is the intended development range.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --requirement requirements-dev.txt
python -m pip install --editable .
Copy-Item .env.example .env
```

Replace every placeholder secret in `.env`, keep `CENTRAL_ENV=development`, and run:

```powershell
python -m central.main
```

The generic bootstrap creates `demo-suite` without an external upstream or published bearer value. Create an instance token through the authenticated API/dashboard and store the one-time value securely.

This project is not an installer or production distribution. Database upgrade rollback, operating-system service management, TLS, rate limiting, and secret-manager integration remain operator responsibilities.
