"""
Módulo de Cibersegurança do Epyatis MCP Central: Allowlist de Comandos e Prevenção de RCE (SEC-02).
Impede que qualquer comando arbitrário (ex: cmd.exe, powershell.exe, sh, bash) seja executado no host.
"""

import logging
import os
import re

from central.config import settings

logger = logging.getLogger(__name__)

# Lista estrita de executáveis permitidos para servidores MCP locais
ALLOWED_EXECUTABLES = {
    "npx",
    "npx.cmd",
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

    normalized_args = args or []
    package_candidates = [
        arg for arg in normalized_args
        if isinstance(arg, str) and arg not in {"-y", "--yes"} and not arg.startswith("-")
    ]
    if not package_candidates:
        raise ValueError("npx exige um pacote MCP explicitamente versionado e homologado.")

    package = package_candidates[0]
    if package.startswith("@"):
        package_name, separator, version = package.rpartition("@")
        pinned = bool(separator and "/" in package_name and version)
    else:
        package_name, separator, version = package.rpartition("@")
        pinned = bool(separator and package_name and version)

    exact_version = bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version))
    if not pinned or not exact_version:
        raise ValueError("O pacote npx deve usar versão semântica exata (ex.: pacote@1.2.3).")

    if package not in settings.STDIO_ALLOWED_PACKAGES:
        raise ValueError(f"Pacote stdio '{package}' não está na allowlist administrativa.")

    # Verifica os argumentos para detectar injeções de comando ou invocação de interpretadores de shell
    if normalized_args:
        for arg in normalized_args:
            if not isinstance(arg, str):
                continue
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(arg):
                    logger.warning(f"[Security/RCE] Argumento malicioso detectado e bloqueado: '{arg}'")
                    raise ValueError(
                        f"Argumento '{arg}' contém caracteres ou referências a executáveis de sistema "
                        f"proibidos por política de segurança contra injeção de comandos."
                    )
