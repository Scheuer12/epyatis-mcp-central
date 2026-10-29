"""
Configurações do Epyatis MCP Central.
Define parâmetros de runtime, políticas de segurança, chaves de autenticação e criptografia.
"""

import hashlib
import logging
import secrets
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()
logger = logging.getLogger(__name__)


class CentralSettings(BaseSettings):
    # Ambiente de execução (development | testing | production)
    CENTRAL_ENV: str = "development"

    # Diretórios base
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_PATH: Path = BASE_DIR / "config" / "bootstrap_instances.yaml"
    DB_PATH: Path = BASE_DIR / "central.db"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'central.db'}"

    # Servidor HTTP - Secure by Default (DEBUG desativado por padrão)
    CENTRAL_HOST: str = "127.0.0.1"
    CENTRAL_PORT: int = 8000
    CENTRAL_DEBUG: bool = False

    # Chave mestra de criptografia em repouso
    # Em produção, DEVE ser fornecida via variável de ambiente com alta entropia
    CENTRAL_SECRET_KEY: str | None = Field(default=None, repr=False)

    # Chave mestra de autenticação administrativa (/api/v1/*)
    # Em produção, DEVE ser fornecida via variável de ambiente com alta entropia
    CENTRAL_ADMIN_KEY: str | None = Field(default=None, repr=False)

    # Exact, pinned npm package specs permitted for local MCP subprocesses.
    STDIO_ALLOWED_PACKAGES: list[str] = []

    # Hosts permitidos (TrustedHostMiddleware) - Wildcard '*' removido do padrão seguro
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "test"]

    # Origens permitidas para CORS
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Variáveis de ambiente para upstream integrations
    PERISKOPE_API_KEY: str | None = Field(default=None, repr=False)
    PERISKOPE_MCP_URL: str = "https://api.periskope.app/mcp"

    GDRIVE_OAUTH_CREDENTIALS_FILE: str | None = None
    GDRIVE_OAUTH_TOKEN_FILE: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "CentralSettings":
        """Reject deployable runtimes without explicit, non-legacy secrets."""
        environment = self.CENTRAL_ENV.strip().lower()
        if environment not in {"development", "testing", "production"}:
            raise ValueError("CENTRAL_ENV deve ser development, testing ou production.")

        if environment == "testing":
            self.CENTRAL_SECRET_KEY = self.CENTRAL_SECRET_KEY or secrets.token_urlsafe(48)
            self.CENTRAL_ADMIN_KEY = self.CENTRAL_ADMIN_KEY or secrets.token_urlsafe(48)
        else:
            if not self.CENTRAL_SECRET_KEY:
                raise ValueError("CENTRAL_SECRET_KEY deve ser configurada explicitamente.")
            if not self.CENTRAL_ADMIN_KEY:
                raise ValueError("CENTRAL_ADMIN_KEY deve ser configurada explicitamente.")

        legacy_secret_digests = {
            "012e6ff0a305a1a585fe7a32aca67544a402e2f488012331cf6d76cf913e1f7b",
            "2e733f8409afa49d7d74671222309411df9497a82c1a8787ffac9461fea21d59",
        }
        secret_digest = hashlib.sha256((self.CENTRAL_SECRET_KEY or "").encode()).hexdigest()
        admin_digest = hashlib.sha256((self.CENTRAL_ADMIN_KEY or "").encode()).hexdigest()
        if secret_digest in legacy_secret_digests:
            raise ValueError("CENTRAL_SECRET_KEY usa um valor legado previsível e deve ser rotacionada.")
        if admin_digest in legacy_secret_digests:
            raise ValueError("CENTRAL_ADMIN_KEY usa um valor legado previsível e deve ser rotacionada.")
        if len(self.CENTRAL_SECRET_KEY or "") < 32:
            raise ValueError("CENTRAL_SECRET_KEY deve ter no mínimo 32 caracteres.")
        if len(self.CENTRAL_ADMIN_KEY or "") < 32:
            raise ValueError("CENTRAL_ADMIN_KEY deve ter no mínimo 32 caracteres.")

        if self.CENTRAL_DEBUG and environment == "production":
            raise ValueError("CENTRAL_DEBUG não pode ser True em ambiente de produção.")
        if "*" in self.ALLOWED_HOSTS:
            raise ValueError("ALLOWED_HOSTS não pode conter wildcard '*'.")
        if "*" in self.CORS_ALLOWED_ORIGINS:
            raise ValueError("CORS_ALLOWED_ORIGINS não pode conter wildcard '*'.")

        return self


settings = CentralSettings()
