"""
Módulo de Cibersegurança do Epyatis MCP Central: Firewall Anti-SSRF e Isolamento de Rede Host (SEC-03).
Garante que o Central Gateway e qualquer cliente MCP fiquem estritamente impedidos de acessar a máquina host
(localhost/127.0.0.1), redes privadas internas (RFC 1918), link-local, multicast, ou serviços de metadados de nuvem.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Faixas de IP adicionais bloqueadas
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),        # Current network / Default route
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback IPv4
    ipaddress.ip_network("::1/128"),          # Loopback IPv6
    ipaddress.ip_network("::/128"),           # Unspecified IPv6
    ipaddress.ip_network("10.0.0.0/8"),       # Rede Privada Classe A (RFC 1918)
    ipaddress.ip_network("172.16.0.0/12"),    # Rede Privada Classe B (RFC 1918)
    ipaddress.ip_network("192.168.0.0/16"),   # Rede Privada Classe C (RFC 1918)
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local / Metadados AWS, GCP, Azure, Oracle
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-Grade NAT (RFC 6598)
    ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments
    ipaddress.ip_network("198.18.0.0/15"),    # Benchmark tests
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast IPv4
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved / Future use
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
    ipaddress.ip_network("ff00::/8"),         # IPv6 Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "::1",
    str(ipaddress.ip_address(0)),  # Unspecified IPv4 denylist entry, not a bind address.
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "169.254.169.254",
    "100.100.100.200",                        # Alibaba Cloud Metadata
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
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return False, f"Esquema de protocolo não permitido: '{parsed.scheme}'. Apenas http e https são autorizados."

        # Proíbe credenciais embutidas na URL (ex: http://user:pass@host)
        if parsed.username or parsed.password:
            return False, "URLs com credenciais embutidas (user:pass) não são permitidas por política de segurança."

        hostname = parsed.hostname
        if not hostname:
            return False, "A URL não contém um hostname ou domínio válido."

        hostname_clean = hostname.lower().strip()

        # 1. Bloqueia hostnames locais explícitos
        if hostname_clean in BLOCKED_HOSTNAMES:
            logger.warning(f"[Security/SSRF] Tentativa de acesso bloqueada para hostname restrito: {hostname_clean}")
            return False, f"Acesso ao host local ou metadados '{hostname_clean}' é terminantemente proibido."

        # 2. Resolução DNS para validar todos os endereços IP de destino
        try:
            addr_entries = socket.getaddrinfo(hostname_clean, None)
        except socket.gaierror as dns_err:
            return False, f"Falha na resolução de DNS para '{hostname_clean}': {dns_err}"

        if not addr_entries:
            return False, f"Nenhum endereço IP resolvido para o host '{hostname_clean}'."

        for entry in addr_entries:
            ip_str = entry[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)

                # Tratamento de IPv4-mapped IPv6 (ex: ::ffff:127.0.0.1 ou ::ffff:169.254.169.254)
                if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                    ip_obj = ip_obj.ipv4_mapped

                # Verificações padrão de propriedades de IP do Python
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_reserved
                    or ip_obj.is_unspecified
                ):
                    logger.warning(f"[Security/SSRF] Host '{hostname_clean}' resolve para IP restrito: {ip_obj}")
                    return False, f"Acesso bloqueado: o host '{hostname_clean}' resolve para o endereço privado/local '{ip_obj}'."

                # Verificação contra listas de redes bloqueadas explícitas
                for blocked_net in BLOCKED_NETWORKS:
                    if ip_obj in blocked_net:
                        logger.warning(f"[Security/SSRF] Tentativa de SSRF bloqueada: {hostname_clean} resolve para IP restrito {ip_obj} na faixa {blocked_net}")
                        return False, (
                            f"Acesso bloqueado: o host '{hostname_clean}' resolve para o endereço restrito "
                            f"'{ip_obj}', protegido pelo firewall anti-SSRF."
                        )
            except ValueError:
                return False, f"Endereço IP resolvido inválido: '{ip_str}'."

        return True, "URL segura e pública."

    except Exception as e:
        logger.error(f"[Security/SSRF] Erro inesperado durante validação de URL: {e}")
        return False, f"Erro interno na validação de segurança da URL: {e}"


def validate_safe_url(url: str) -> None:
    """Valida a URL e levanta ValueError se for insegura (anti-SSRF)."""
    is_safe, reason = is_safe_external_url(url)
    if not is_safe:
        raise ValueError(reason)
