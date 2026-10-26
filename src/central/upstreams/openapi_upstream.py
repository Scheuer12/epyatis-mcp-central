"""
Upstream para APIs REST via especificação OpenAPI v3 / Swagger.
Converte endpoints REST automaticamente em ferramentas MCP dinâmicas.
"""

import json
import logging
import re
from typing import Any
import httpx
import mcp.types as types
import yaml

from central.upstreams.base import BaseUpstream

logger = logging.getLogger(__name__)


class OpenApiUpstream(BaseUpstream):
    def __init__(
        self,
        connection_id: str,
        prefix: str,
        spec: dict[str, Any] | str,
        base_url: str | None = None,
        auth_headers: dict[str, str] | None = None,
    ):
        super().__init__(connection_id=connection_id, prefix=prefix)
        self.raw_spec = spec
        self.base_url = base_url
        self.auth_headers = auth_headers or {}
        self.parsed_spec: dict[str, Any] = {}
        self.operations: dict[str, dict[str, Any]] = {}
        self._http_client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        logger.info(f"[{self.prefix}] Inicializando upstream OpenAPI...")
        self._http_client = httpx.AsyncClient(timeout=30.0)

        # Carrega e parseia a especificação
        if isinstance(self.raw_spec, str):
            if self.raw_spec.startswith("http://") or self.raw_spec.startswith("https://"):
                from central.security.ssrf import is_safe_external_url
                is_safe, reason = is_safe_external_url(self.raw_spec)
                if not is_safe:
                    logger.error(f"[{self.prefix}] Tentativa de download de OpenAPI bloqueada por SSRF: {reason}")
                    raise ValueError(f"URL de OpenAPI rejeitada por proteção anti-SSRF: {reason}")

                resp = await self._http_client.get(self.raw_spec)
                resp.raise_for_status()
                text = resp.text
                try:
                    self.parsed_spec = json.loads(text)
                except Exception:
                    self.parsed_spec = yaml.safe_load(text)
            else:

                try:
                    self.parsed_spec = json.loads(self.raw_spec)
                except Exception:
                    self.parsed_spec = yaml.safe_load(self.raw_spec) or {}
        elif isinstance(self.raw_spec, dict):
            self.parsed_spec = self.raw_spec

        # Determina base_url se não fornecida
        if not self.base_url:
            servers = self.parsed_spec.get("servers", [])
            if servers and isinstance(servers, list):
                self.base_url = servers[0].get("url", "").rstrip("/")

        self._build_operations()
        logger.info(f"[{self.prefix}] OpenAPI carregado com sucesso. {len(self.operations)} operações mapeadas.")

    def _build_operations(self) -> None:
        paths = self.parsed_spec.get("paths", {})
        for path_url, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                op = path_item[method]
                if not isinstance(op, dict):
                    continue

                # Nome da operação
                op_id = op.get("operationId")
                if not op_id:
                    # Gera a partir do método e path (ex: /users/{id} -> get_users_by_id)
                    clean_path = re.sub(r"[{}]", "", path_url).strip("/").replace("/", "_").replace("-", "_")
                    op_id = f"{method}_{clean_path}" if clean_path else method

                # Sanitiza nome para respeitar o padrão de identificadores MCP
                clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", op_id)

                summary = op.get("summary") or op.get("description") or f"{method.upper()} {path_url}"

                # Constrói o input_schema
                properties: dict[str, Any] = {}
                required_fields: list[str] = []

                # Parâmetros de rota e query
                parameters = path_item.get("parameters", []) + op.get("parameters", [])
                for param in parameters:
                    if not isinstance(param, dict):
                        continue
                    p_name = param.get("name")
                    if not p_name:
                        continue
                    p_in = param.get("in", "query")
                    p_desc = param.get("description", "")
                    p_schema = param.get("schema", {"type": "string"})
                    p_type = p_schema.get("type", "string")

                    properties[p_name] = {
                        "type": p_type,
                        "description": f"[{p_in.upper()}] {p_desc}".strip(),
                    }
                    if param.get("required", False) or p_in == "path":
                        required_fields.append(p_name)

                # Request Body (para POST, PUT, PATCH)
                req_body = op.get("requestBody")
                if req_body and isinstance(req_body, dict):
                    content = req_body.get("content", {})
                    json_media = content.get("application/json", {})
                    body_schema = json_media.get("schema", {})
                    if body_schema.get("type") == "object" and "properties" in body_schema:
                        for bp_name, bp_def in body_schema["properties"].items():
                            properties[bp_name] = bp_def
                        for r in body_schema.get("required", []):
                            if r not in required_fields:
                                required_fields.append(r)
                    else:
                        properties["body"] = {
                            "type": "object",
                            "description": "Corpo da requisição JSON",
                        }

                schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required_fields,
                }

                self.operations[clean_name] = {
                    "method": method.upper(),
                    "path": path_url,
                    "summary": summary,
                    "parameters": parameters,
                    "input_schema": schema,
                }

    async def stop(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def list_tools(self) -> list[types.Tool]:
        tools: list[types.Tool] = []
        for op_id, op_info in self.operations.items():
            tools.append(
                types.Tool(
                    name=op_id,
                    title=op_id,
                    description=op_info["summary"],
                    input_schema=op_info["input_schema"],
                )
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        args = arguments or {}
        if name not in self.operations:
            return types.CallToolResult(
                is_error=True,
                content=[types.TextContent(type="text", text=f"Operação '{name}' não encontrada na API.")],
            )

        op = self.operations[name]
        method = op["method"]
        path_template = op["path"]
        parameters = op["parameters"]

        # 1. Separa parâmetros de rota, query e body
        path_params: dict[str, Any] = {}
        query_params: dict[str, Any] = {}
        body_params: dict[str, Any] = {}

        param_names_in_path = set()
        param_names_in_query = set()

        for p in parameters:
            p_name = p.get("name")
            p_in = p.get("in")
            if p_in == "path":
                param_names_in_path.add(p_name)
            elif p_in == "query":
                param_names_in_query.add(p_name)

        for k, v in args.items():
            if k in param_names_in_path:
                path_params[k] = v
            elif k in param_names_in_query:
                query_params[k] = v
            elif k == "body" and isinstance(v, dict):
                body_params = v
            else:
                body_params[k] = v

        # 2. Interpola path
        resolved_path = path_template
        for pk, pv in path_params.items():
            resolved_path = resolved_path.replace(f"{{{pk}}}", str(pv))

        full_url = f"{self.base_url.rstrip('/')}/{resolved_path.lstrip('/')}" if self.base_url else resolved_path

        # Validação anti-SSRF para impedir que o agente acesse a máquina local ou rede interna
        if full_url.startswith("http://") or full_url.startswith("https://"):
            from central.security.ssrf import is_safe_external_url
            is_safe, reason = is_safe_external_url(full_url)
            if not is_safe:
                logger.error(f"[{self.prefix}] Chamada de tool bloqueada por política anti-SSRF: {reason}")
                return types.CallToolResult(
                    is_error=True,
                    content=[types.TextContent(type="text", text=f"Violação de Segurança (Anti-SSRF): {reason}")],
                )

        headers = {"Content-Type": "application/json", **self.auth_headers}

        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)


        try:
            req_kwargs: dict[str, Any] = {"headers": headers, "params": query_params}
            if method in ["POST", "PUT", "PATCH"] and body_params:
                req_kwargs["json"] = body_params

            resp = await self._http_client.request(method, full_url, **req_kwargs)

            try:
                formatted_body = json.dumps(resp.json(), indent=2, ensure_ascii=False)
            except Exception:
                formatted_body = resp.text

            is_err = resp.status_code >= 400
            result_text = f"HTTP {resp.status_code} {resp.reason_phrase}\n{formatted_body}"

            return types.CallToolResult(
                is_error=is_err,
                content=[types.TextContent(type="text", text=result_text)],
            )
        except Exception as e:
            logger.error(f"[{self.prefix}] Erro ao chamar {method} {full_url}: {e}", exc_info=True)
            return types.CallToolResult(
                is_error=True,
                content=[types.TextContent(type="text", text=f"Erro de conexão com upstream REST: {e}")],
            )

    async def is_healthy(self) -> bool:
        return bool(self.operations)
