"""
Módulo de Cibersegurança do Epyatis MCP Central: Allowlist de Comandos e Prevenção de RCE (SEC-02).
Impede que qualquer comando arbitrário (ex: cmd.exe, powershell.exe, sh, bash) seja executado no host.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Lista estrita de executáveis permitidos para servidores MCP locais
ALLOWED_EXECUTABLES = {
    "npx",
    "npx.cmd",
    "node",
    "node.exe",
    "python",
    "python.exe",
    "uv",
    "uv.exe",
    "uvx",
    "uvx.exe",
}

# Pacotes e argumentos sensíveis proibidos
FORBIDDEN_PATTERNS = [
    re.compile(r"[;&|`$><]", re.IGNORECASE),  # Metacaracteres de encadeamento de shell
    re.compile(r"\b(cmd|powershell|pwsh|bash|sh|cscript|wscript|mshta|rundll32)\b", re.IGNORECASE),
]


def validate_stdio_command(command: str | None, args: list[str] | None = None) -> None:
    """
    Valida rigorosamente o comando e argumentos de uma conexão Stdio contra RCE.
    Lança ValueError se o comando violar a política de segurança.
    """
    if not command:
        raise ValueError("Comando não pode ser vazio para conexões do tipo stdio.")

    # Extrai o nome base do binário (independente de caminho absoluto ou extensão)
    basename = os.path.basename(command).lower()

    if basename not in ALLOWED_EXECUTABLES:
        logger.warning(f"[Security/RCE] Tentativa de execução de executável não homologado: '{command}'")
        raise ValueError(
            f"Executável '{command}' não autorizado por política de cibersegurança do Central. "
            f"Binários homologados: {', '.join(sorted(ALLOWED_EXECUTABLES))}."
        )

    # Verifica os argumentos para detectar injeções de comando ou invocação de interpretadores de shell
    if args:
        for arg in args:
            if not isinstance(arg, str):
                continue
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(arg):
                    logger.warning(f"[Security/RCE] Argumento malicioso detectado e bloqueado: '{arg}'")
                    raise ValueError(
                        f"Argumento '{arg}' contém caracteres ou referências a executáveis de sistema "
                        f"proibidos por política de segurança contra injeção de comandos."
                    )
