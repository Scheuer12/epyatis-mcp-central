"""
OAuth2 helper script to obtain a Google Drive refresh token with full read/write scopes.
"""

import http.server
import json
import urllib.parse
import webbrowser
from pathlib import Path
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
KEYS_FILE = BASE_DIR / "gdrive-oauth.keys.json"
ENV_FILE = BASE_DIR / ".env"

if not KEYS_FILE.exists():
    print(f"Erro: Arquivo {KEYS_FILE} não encontrado.")
    exit(1)

with open(KEYS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

installed = data.get("installed") or data.get("web")
client_id = installed["client_id"]
client_secret = installed["client_secret"]
redirect_uri = "http://localhost:8088"

# Full scopes to read and write drive files, documents, sheets, and presentations
scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.activity.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
]
scope_str = " ".join(scopes)

auth_code = None
auth_error = None


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code, auth_error
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Autenticado com sucesso!</h1><p>Pode fechar esta aba e voltar para o terminal.</p>")
        elif "error" in params:
            auth_error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>Erro na autenticacao:</h1><p>{auth_error}</p>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Erro: Codigo de autorizacao nao recebido.")

    def log_message(self, format, *args):
        pass


def main():
    global auth_code
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope_str,
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    server = http.server.HTTPServer(("127.0.0.1", 8088), OAuthCallbackHandler)
    print("\n" + "=" * 60)
    print("Iniciando autenticação Google Drive com permissões de LEITURA e ESCRITA...")
    print("=" * 60)
    print(f"Abrindo navegador em:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print("Aguardando confirmação no navegador (porta 8088)...")
    while not auth_code and not auth_error:
        server.handle_request()
    server.server_close()

    if auth_error:
        print(f"\nErro durante autenticação: {auth_error}")
        exit(1)

    print("\nCódigo de autorização recebido! Trocando por Refresh Token...")
    res = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )

    if res.status_code != 200:
        print(f"Erro ao obter token: {res.status_code} - {res.text}")
        exit(1)

    tokens = res.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("Aviso: Nenhum refresh_token retornado. Certifique-se de revogar acessos prévios se necessário.")
        exit(1)

    print("\nRefresh Token obtido com sucesso!")

    # Atualiza o arquivo .env
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = {}
    new_vars = {
        "GOOGLE_CLIENT_ID": client_id,
        "GOOGLE_CLIENT_SECRET": client_secret,
        "GOOGLE_REFRESH_TOKEN": refresh_token,
        "GOOGLE_DRIVE_ALLOW_WRITE": "true",
        "GOOGLE_DRIVE_SCOPES": ",".join(scopes),
    }

    new_lines = []
    for line in lines:
        key = line.split("=")[0].strip()
        if key in new_vars:
            new_lines.append(f"{key}={new_vars[key]}\n")
            updated[key] = True
        else:
            new_lines.append(line)

    for k, v in new_vars.items():
        if k not in updated:
            new_lines.append(f"{k}={v}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"\nCredenciais salvas no arquivo: {ENV_FILE}")
    print("Pronto! Agora o Google Drive possui permissões completas de criação e edição.")


if __name__ == "__main__":
    main()
