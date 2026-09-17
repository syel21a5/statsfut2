import os, sys, time, json, datetime, requests

API_KEY = "e2382858-02c5-4f4b-988e-11b279278294"
DAILY_LIMIT = 15  # Trava estrita de segurança: no máximo 15 imagens geradas por dia
USAGE_FILE = "/www/wwwroot/statsfut.com/video_maker/leonardo_usage.json"
MEDIA_DIR = "/www/wwwroot/statsfut.com/media/videos/output"

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}"
}

def check_and_increment_daily_limit():
    """Trava de segurança 3: garante que nunca passe do limite diário estrito."""
    today = datetime.date.today().isoformat()
    usage = {"date": today, "count": 0}
    
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                usage = json.load(f)
        except Exception:
            pass
            
    if usage.get("date") != today:
        usage = {"date": today, "count": 0}
        
    if usage.get("count", 0) >= DAILY_LIMIT:
        raise RuntimeError(f"🚨 TRAVA DE SEGURANÇA ATIVA: Limite diário de {DAILY_LIMIT} imagens atingido hoje ({today})! Chamada bloqueada.")
        
    usage["count"] = usage.get("count", 0) + 1
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)
    print(f"🔒 [Segurança] Requisição permitida. Uso hoje: {usage['count']}/{DAILY_LIMIT}")

def check_account_balance():
    """Consulta o saldo real na API do Leonardo."""
    url = "https://cloud.leonardo.ai/api/rest/v1/me"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        return r.json()
    return None

def generate_leonardo_thumbnail(prompt, match_id=None, force_new=False):
    """
    Gera thumbnail profissional 9:16 no Leonardo.ai com travas rigorosas:
    - Trava 1: Cache local (se já gerou para este match_id, não chama API de novo).
    - Trava 2: num_images fixado estritamente em 1.
    - Trava 3: Limite diário de segurança anti-loop.
    """
    os.makedirs(MEDIA_DIR, exist_ok=True)
    
    # Trava 1: Cache local
    if match_id:
        cache_path = os.path.join(MEDIA_DIR, f"leonardo_thumb_match_{match_id}.jpg")
        if os.path.exists(cache_path) and not force_new:
            print(f"⚡ [Cache Ativo] Thumbnail para match {match_id} já existe em disco: {cache_path}. NENHUM token consumido!")
            return cache_path
    else:
        cache_path = os.path.join(MEDIA_DIR, f"leonardo_thumb_test_{int(time.time())}.jpg")

    # Trava 3: Limite diário
    check_and_increment_daily_limit()

    print("\n🎨 [Leonardo.ai] Disparando geração da imagem cinematográfica...")
    print(f"📝 Prompt: {prompt[:160]}...")
    
    gen_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    
    # Trava 2: num_images = 1, formato 9:16 vertical otimizado com modelo Kino XL (Cinema/Sports broadcast)
    payload = {
        "prompt": prompt,
        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628", # Leonardo Kino XL
        "width": 768,
        "height": 1344,
        "num_images": 1,
        "public": False
    }
    
    res = requests.post(gen_url, json=payload, headers=HEADERS, timeout=30)
        
    if res.status_code != 200:
        raise RuntimeError(f"Erro na API do Leonardo ({res.status_code}): {res.text}")
        
    data = res.json()
    gen_id = data.get("sdGenerationJob", {}).get("generationId")
    if not gen_id:
        raise RuntimeError(f"ID da geração não retornado: {res.text}")
        
    print(f"⏳ Job de renderização aceito (ID: {gen_id}). Aguardando processamento...")
    poll_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}"
    
    for attempt in range(25):
        time.sleep(3)
        poll_res = requests.get(poll_url, headers=HEADERS, timeout=15)
        if poll_res.status_code != 200:
            continue
        pdata = poll_res.json().get("generations_by_pk", {})
        status = pdata.get("status")
        
        if status == "COMPLETE":
            images = pdata.get("generated_images", [])
            if images:
                img_url = images[0].get("url")
                print(f"✅ Imagem pronta no Leonardo! Baixando para o servidor: {img_url}")
                img_data = requests.get(img_url, timeout=30).content
                with open(cache_path, "wb") as f:
                    f.write(img_data)
                print(f"💾 Thumbnail salva com sucesso em: {cache_path}")
                return cache_path
            else:
                raise RuntimeError("Status COMPLETE mas nenhuma imagem na lista.")
        elif status == "FAILED":
            raise RuntimeError(f"Geração falhou no Leonardo.ai: {pdata}")
            
    raise TimeoutError("Tempo limite esgotado aguardando renderização no Leonardo.ai.")

if __name__ == "__main__":
    balance = check_account_balance()
    print("Dados da conta / Saldo:", json.dumps(balance, indent=2))
