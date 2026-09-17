import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

BASE_DIR = "/www/wwwroot/statsfut.com"
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
YOUTUBE_TOKEN_FILE = os.path.join(BASE_DIR, "youtube_token.json")

# Escopos necessários para upload e agendamento de vídeos no YouTube
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_auth_url():
    """Gera a URL de consentimento OAuth para o usuário autorizar no navegador."""
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return flow, auth_url

def finish_auth(flow, code):
    """Troca o código gerado pelo Google pelo token permanente."""
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(YOUTUBE_TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    print("✅ youtube_token.json salvo com sucesso no servidor!")

if __name__ == "__main__":
    print("Módulo de autenticação YouTube pronto.")
