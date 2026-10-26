"""
Registro de Templates de Conexão pré-configurados do Epyatis MCP Central.
"""

from typing import Any
from pydantic import BaseModel, Field


class TemplateFormField(BaseModel):
    name: str
    label: str
    type: str = "text"  # text | password | textarea | boolean
    default: Any = None
    required: bool = True
    placeholder: str = ""
    help_text: str = ""


class ConnectionTemplate(BaseModel):
    id: str
    name: str
    category: str
    type: str  # stdio | remote_mcp | openapi
    icon: str
    description: str
    default_prefix: str
    default_command: str | None = None
    default_args: list[str] = Field(default_factory=list)
    default_env: dict[str, str] = Field(default_factory=dict)
    form_fields: list[TemplateFormField] = Field(default_factory=list)
    help_tooltip: str = ""


BUILTIN_TEMPLATES: list[ConnectionTemplate] = [
    ConnectionTemplate(
        id="gdrive-template",
        name="Google Drive Workspace / Multi-Conta",
        category="Armazenamento & Docs",
        type="stdio",
        icon="fa-brands fa-google-drive",
        description="Integre múltiplas contas do Google Drive com namespaces isolados (ex: conta da empresa e conta pessoal).",
        default_prefix="gdrive",
        default_command="npx",
        default_args=["-y", "@us-all/google-drive-mcp"],
        default_env={"GOOGLE_DRIVE_ALLOW_WRITE": "true", "DOTENV_CONFIG_QUIET": "true"},
        form_fields=[
            TemplateFormField(name="id", label="Identificador Único", type="text", required=True, placeholder="gdrive-financeiro"),
            TemplateFormField(name="name", label="Nome da Conexão", type="text", required=True, placeholder="Google Drive Financeiro"),
            TemplateFormField(name="prefix", label="Prefixo das Tools", type="text", default="gdrive", required=True, placeholder="gdrive_fin", help_text="As ferramentas serão expostas como prefixo__read_file"),
            TemplateFormField(name="allow_write", label="Permitir Escrita / Criação de Arquivos", type="boolean", default=True),
        ],
        help_tooltip="Adicione contas extras com facilidade. Basta definir um prefixo único para que as ferramentas fiquem perfeitamente isoladas.",
    ),
    ConnectionTemplate(
        id="periskope-template",
        name="Periskope WhatsApp",
        category="Comunicação",
        type="stdio",
        icon="fa-brands fa-whatsapp",
        description="Conecte mensagens, chats de clientes e grupos de WhatsApp via Periskope.",
        default_prefix="periskope",
        default_command="npx",
        default_args=["-y", "@periskope/whatsapp-mcp"],
        form_fields=[
            TemplateFormField(name="id", label="Identificador Único", type="text", required=True, placeholder="periskope-suporte"),
            TemplateFormField(name="name", label="Nome da Conexão", type="text", required=True, placeholder="Periskope Suporte WhatsApp"),
            TemplateFormField(name="prefix", label="Prefixo das Tools", type="text", default="periskope", required=True, placeholder="periskope"),
            TemplateFormField(name="api_key", label="API Key do Periskope", type="password", required=False, placeholder="pk_live_...", help_text="Se não preenchido, usa a chave do arquivo .env"),
        ],
        help_tooltip="Obtenha sua API Key no painel do Periskope em Configurações > Integrações > API Keys.",
    ),
    ConnectionTemplate(
        id="filesystem-template",
        name="Filesystem Local Seguro",
        category="Armazenamento Local",
        type="stdio",
        icon="fa-solid fa-folder-open",
        description="Expõe uma pasta do seu computador para que agentes leiam e editem arquivos locais com segurança.",
        default_prefix="fs",
        default_command="npx",
        default_args=["-y", "@modelcontextprotocol/server-filesystem"],
        form_fields=[
            TemplateFormField(name="id", label="Identificador Único", type="text", required=True, placeholder="fs-projetos"),
            TemplateFormField(name="name", label="Nome da Conexão", type="text", required=True, placeholder="Arquivos de Projetos"),
            TemplateFormField(name="prefix", label="Prefixo das Tools", type="text", default="fs", required=True, placeholder="fs"),
            TemplateFormField(name="allowed_dir", label="Caminho Absoluto da Pasta", type="text", required=True, placeholder="C:\\Users\\Usuario\\Documents", help_text="O agente só acessará arquivos dentro deste diretório"),
        ],
        help_tooltip="O MCP Server Filesystem isola o acesso do agente estritamente à pasta especificada.",
    ),
    ConnectionTemplate(
        id="postgres-template",
        name="PostgreSQL Database",
        category="Bancos de Dados",
        type="stdio",
        icon="fa-solid fa-database",
        description="Conecta agentes a bancos PostgreSQL para inspeção de esquemas e execução de consultas analíticas.",
        default_prefix="pg",
        default_command="npx",
        default_args=["-y", "@modelcontextprotocol/server-postgres"],
        form_fields=[
            TemplateFormField(name="id", label="Identificador Único", type="text", required=True, placeholder="postgres-analytics"),
            TemplateFormField(name="name", label="Nome da Conexão", type="text", required=True, placeholder="Banco PostgreSQL de Métricas"),
            TemplateFormField(name="prefix", label="Prefixo das Tools", type="text", default="pg", required=True, placeholder="pg"),
            TemplateFormField(name="connection_string", label="URL de Conexão", type="password", required=True, placeholder="postgresql://usuario:senha@localhost:5432/meubanco"),
        ],
        help_tooltip="Insira a URI padrão do PostgreSQL com credenciais de leitura para o agente.",
    ),
    ConnectionTemplate(
        id="openapi-template",
        name="API REST via OpenAPI / Swagger",
        category="APIs & Web Services",
        type="openapi",
        icon="fa-solid fa-code",
        description="Converte automaticamente endpoints de uma API REST descrita em OpenAPI v3 / Swagger em ferramentas MCP.",
        default_prefix="api",
        form_fields=[
            TemplateFormField(name="id", label="Identificador Único", type="text", required=True, placeholder="api-erp"),
            TemplateFormField(name="name", label="Nome da Conexão", type="text", required=True, placeholder="ERP Corporativo API"),
            TemplateFormField(name="prefix", label="Prefixo das Tools", type="text", default="api", required=True, placeholder="erp"),
            TemplateFormField(name="base_url", label="URL Base da API (Opcional)", type="text", required=False, placeholder="https://api.empresa.com/v1"),
            TemplateFormField(name="spec", label="Especificação OpenAPI (URL, JSON ou YAML)", type="textarea", required=True, placeholder="https://petstore.swagger.io/v2/swagger.json ou cole o JSON/YAML"),
            TemplateFormField(name="auth_token", label="Bearer Token / Header de Autenticação", type="password", required=False, placeholder="Bearer eyJhbGci..."),
        ],
        help_tooltip="O Central lê os endpoints, parâmetros e corpos JSON da especificação e cria ferramentas MCP prontas para uso pelos agentes.",
    ),
]


def get_all_templates() -> list[ConnectionTemplate]:
    return BUILTIN_TEMPLATES


def get_template_by_id(template_id: str) -> ConnectionTemplate | None:
    for t in BUILTIN_TEMPLATES:
        if t.id == template_id:
            return t
    return None
