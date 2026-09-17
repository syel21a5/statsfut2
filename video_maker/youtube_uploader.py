import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

CRED_DIR = "/www/wwwroot/statsfut.com/video_maker/credentials"
SECRETS_FILE = os.path.join(CRED_DIR, "client_secrets_youtube.json")
TOKEN_FILE = os.path.join(CRED_DIR, "youtube_token.json")

def get_youtube_service():
    """Carrega as credenciais salvas do YouTube e renova automaticamente."""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Arquivo {TOKEN_FILE} não encontrado!")
        
    with open(TOKEN_FILE, "r") as f:
        tdata = json.load(f)
        
    with open(SECRETS_FILE, "r") as f:
        sdata = json.load(f)
    cfg = sdata.get("web") or sdata.get("installed")

    creds = Credentials(
        token=tdata.get("access_token"),
        refresh_token=tdata.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tdata["access_token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(tdata, f, indent=2)
            
    return build("youtube", "v3", credentials=creds)

def upload_video_to_youtube(
    file_path: str,
    title: str,
    description: str,
    tags: list = None,
    publish_at_iso: str = None, # Ex: '2026-09-17T15:00:00Z' para agendado
    is_short: bool = True
):
    """
    Envia vídeo para o canal do YouTube:
    - Se publish_at_iso estiver definido: agenda para o horário e mantém privado até lá.
    - Se publish_at_iso for None: publica imediatamente como público.
    """
    youtube = get_youtube_service()
    
    if is_short and "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    status = {
        "selfDeclaredMadeForKids": False
    }
    
    if publish_at_iso:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at_iso
    else:
        status["privacyStatus"] = "public"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or ["futebol", "statsfut", "analise de futebol"],
            "categoryId": "17" # Sports
        },
        "status": status
    }

    media = MediaFileUpload(
        file_path,
        chunksize=1024*1024*5,
        resumable=True,
        mimetype="video/mp4"
    )

    print(f"🚀 [YouTube Uploader] Iniciando upload: {title}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        upload_status, response = request.next_chunk()
        if upload_status:
            print(f"⏳ Progresso: {int(upload_status.progress() * 100)}%")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"✅ VÍDEO ENVIADO COM SUCESSO!")
    print(f"🔗 Link: {video_url}")
    if publish_at_iso:
        print(f"📅 Publicação agendada para: {publish_at_iso}")
    else:
        print("📢 Publicado imediatamente como PÚBLICO!")

    return video_id, video_url

if __name__ == "__main__":
    print("Módulo youtube_uploader pronto!")
