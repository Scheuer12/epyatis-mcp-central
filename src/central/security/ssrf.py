"""
Módulo de Cibersegurança do Epyatis MCP Central: Firewall Anti-SSRF e Isolamento de Rede Host (SEC-03).
Garante que o Central Gateway e qualquer cliente MCP fiquem estritamente impedidos de acessar a máquina host
(localhost/127.0.0.1), redes privadas internas (RFC 1918) ou serviços de metadados de nuvem.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Faixas de IP proibidas para requisições de rede originadas pelo Central
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback IPv4 (Host local)
    ipaddress.ip_network("::1/128"),          # Loopback IPv6 (Host local)
    ipaddress.ip_network("10.0.0.0/8"),       # Rede Privada Classe A (RFC 1918)
    ipaddress.ip_network("172.16.0.0/12"),    # Rede Privada Classe B (RFC 1918)
    ipaddress.ip_network("192.168.0.0/16"),   # Rede Privada Classe C (RFC 1918)
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local / Metadados AWS, GCP, Oracle
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-Grade NAT (RFC 6598)
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "::1",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
}


def is_safe_external_url(url: str) -> tuple[bool, str]:
    """
    Verifica se uma URL de destino é pública e segura, bloqueando qualquer tentativa de SSRF
    ou de acesso a recursos locais do host ou de redes internas.
    
    Retorna (is_safe, reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL nula ou inválida."

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Esquema de protocolo não permitido: '{parsed.scheme}'. Apenas http e https são autorizados."

        hostname = parsed.hostname
        if not hostname:
            return False, "A URL não contém um hostname ou domínio válido."

        hostname_clean = hostname.lower().strip()

        # 1. Bloqueia hostnames locais explícitos
        if hostname_clean in BLOCKED_HOSTNAMES:
            logger.warning(f"[Security/SSRF] Tentativa de acesso bloqueada para hostname restrito: {hostname_clean}")
            return False, f"Acesso ao host local '{hostname_clean}' é terminantemente proibido por política de isolamento."

        # 2. Resolução DNS para validar os endereços IP de destino
        try:
            addr_entries = socket.getaddrinfo(hostname_clean, None)
        except socket.gaierror as dns_err:
            return False, f"Falha na resolução de DNS para '{hostname_clean}': {dns_err}"

        for entry in addr_entries:
            ip_str = entry[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                for blocked_net in BLOCKED_NETWORKS:
                    if ip_obj in blocked_net:
                        logger.warning(f"[Security/SSRF] Tentativa de SSRF bloqueada: {hostname_clean} resolve para IP restrito {ip_str}")
                        return False, (
                            f"Acesso bloqueado: o host '{hostname_clean}' resolve para o endereço privado/local "
                            f"'{ip_str}', protegido pelo firewall anti-SSRF."
                        )
            except ValueError:
                return False, f"Endereço IP resolvido inválido: '{ip_str}'."

        return True, "URL segura e pública."

    except Exception as e:
        logger.error(f"[Security/SSRF] Erro inesperado durante validação de URL: {e}")
        return False, f"Erro interno na validação de segurança da URL: {e}"
