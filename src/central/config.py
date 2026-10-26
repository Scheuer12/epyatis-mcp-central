"""
Configurações do Epyatis MCP Central.
"""

from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class CentralSettings(BaseSettings):
    # Diretórios base
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_PATH: Path = BASE_DIR / "config" / "bootstrap_instances.yaml"
    DB_PATH: Path = BASE_DIR / "central.db"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'central.db'}"

    # Servidor HTTP
    CENTRAL_HOST: str = "127.0.0.1"
    CENTRAL_PORT: int = 8000
    CENTRAL_DEBUG: bool = True

    # Chave mestra de criptografia em repouso
    CENTRAL_SECRET_KEY: str = "epyatis-dev-master-secret-key-32b"

    # Chave mestra de autenticação administrativa (/api/v1/*)
    CENTRAL_ADMIN_KEY: str = "epy_admin_master_secret_2026"

    # Hosts permitidos (TrustedHostMiddleware)
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "mcpcentral.epyatis.com.br", "test", "*"]


    # Variáveis de ambiente para upstream integrations
    PERISKOPE_API_KEY: str | None = None
    PERISKOPE_MCP_URL: str = "https://api.periskope.app/mcp"

    GDRIVE_OAUTH_CREDENTIALS_FILE: str | None = None
    GDRIVE_OAUTH_TOKEN_FILE: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = CentralSettings()
