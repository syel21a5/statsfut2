#!/usr/bin/env python3
"""
Pipeline 100% Automático de Criação de Vídeos - StatsFut
Gera Roteiro -> Voz Neural Edge-TTS -> Animações Playwright -> Renderização MP4
"""
import os
import sys
import re
import time
import json
import asyncio
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path("/www/wwwroot/statsfut.com")
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.utils.text import slugify
from matches.models import Match
from matches.services.advanced_stats import MatchAnalyzer
import edge_tts
from moviepy.editor import AudioFileClip

async def generate_voice(text: str, audio_path: str, json_path: str, voice: str = "pt-BR-AntonioNeural"):
    """Gera o áudio MP3 e o cronograma JSON com timestamps precisos das palavras."""
    communicate = edge_tts.Communicate(text, voice=voice, rate="+4%")
    words_data = []
    
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] in ("SentenceBoundary", "WordBoundary"):
                s_text = chunk.get("text", "")
                s_offset = chunk.get("offset", 0) / 10_000_000
                s_dur = chunk.get("duration", 0) / 10_000_000
                
                if chunk["type"] == "WordBoundary":
                    words_data.append({
                        "text": s_text.lower().strip(),
                        "start": round(s_offset, 2),
                        "end": round(s_offset + s_dur, 2)
                    })
                else:
                    words = [w for w in re.findall(r'\b\w+\b', s_text)]
                    if words:
                        per_word = s_dur / len(words)
                        for idx, w in enumerate(words):
                            words_data.append({
                                "text": w.lower().strip(),
                                "start": round(s_offset + (idx * per_word), 2),
                                "end": round(s_offset + ((idx + 1) * per_word), 2)
                            })
                
    audio_clip = AudioFileClip(audio_path)
    total_dur = audio_clip.duration
    audio_clip.close()
    
    payload = {
        "duration": round(total_dur, 2),
        "words": words_data
    }
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(payload, jf, ensure_ascii=False, indent=2)

def build_script(match: Match, report: dict) -> tuple[str, str]:
    """Cria o roteiro de narração otimizado e dinâmico com tags de foco para sincronização."""
    home = match.home_team.name
    away = match.away_team.name
    league = match.league.name
    goals = report.get("goals", {})
    odds = report.get("odds_probs", {})
    
    over_15 = goals.get("over_15", 75)
    btts = goals.get("btts", 55)
    ht_goal = goals.get("ht_goal", 70)
    best_bet = odds.get("double_bet", "X2")
    best_prob = odds.get("double_bet_prob", 86)
    
    # Pronúncia esportiva natural para a Dupla Chance (evita "doze" ou frases longas)
    dc_map = {
        "12": "casa ou visitante, sem empate",
        "1X": "casa ou empate",
        "X2": "empate ou visitante"
    }
    best_bet_spoken = dc_map.get(str(best_bet).strip().upper(), str(best_bet))
    
    # Roteiro narrativo e tags sincronizadas
    narration_parts = [
        f"Fala apostador! Bem-vindo ao StatsFut. Hoje temos a análise completa de {home} e {away} pela {league}.",
        f"Nosso modelo matemático já calculou as probabilidades de maior valor para esta partida.",
        f"No mercado de gols, a probabilidade para Over 1.5 bate {over_15} por cento.",
        f"Para o Ambas as Equipes Marcam, o índice projetado é de {btts} por cento de probabilidade.",
        f"Já a tendência de gol sair ainda no primeiro tempo tem taxa de {ht_goal} por cento.",
        f"E para quem opera resultado, a Dupla Chance mais segura indicada pelo sistema é {best_bet_spoken}, com {best_prob} por cento de confiança matemática.",
        f"Lembrando que estes dados são puramente matemáticos e informativos, não são promessa de lucro nem recomendação de aposta.",
        f"Acesse o StatsFut agora mesmo para ver todos os detalhes e o Radar de Pressão ao vivo!"
    ]
    
    narration = " ".join(narration_parts)
    
    tags_script = (
        f"👇👇👇 TEXTO DO ÁUDIO (COPIE TUDO AQUI ABAIXO E COLE NO ELEVENLABS) 👇👇👇\n\n"
        f"{narration}\n\n"
        f"👇👇👇 TEXTO DA MÁQUINA (COPIE TUDO AQUI ABAIXO E COLE NO ARQUIVO roteiro.txt) 👇👇👇\n\n"
        f"[ABA: gols] [FOCO: {home}] {narration_parts[0]} "
        f"{narration_parts[1]} "
        f"[FOCO: Over 1.5] {narration_parts[2]} "
        f"[FOCO: Ambas Equipes Marcam] {narration_parts[3]} "
        f"[FOCO: Gol no 1º Tempo] {narration_parts[4]} "
        f"[FOCO: Chance Dupla] {narration_parts[5]} "
        f"[FOCO: {home}] {narration_parts[6]} "
        f"{narration_parts[7]}"
    )
    
    return narration, tags_script

def v_name(name):
    return name

def main():
    parser = argparse.ArgumentParser(description="Criador Automático de Vídeos StatsFut")
    parser.add_argument('--match-url', type=str, help='URL da partida no StatsFut')
    parser.add_argument('--match-id', type=int, help='ID da partida no banco de dados')
    parser.add_argument("--format", choices=["short", "long"], default="short", help="Formato do vídeo")
    parser.add_argument("--post-youtube", action="store_true", help="Faz upload automático para o YouTube após renderizar")
    parser.add_argument("--publish-at", type=str, default=None, help="Data/Hora ISO para agendamento (ex: 2026-09-17T15:00:00Z)")
    args = parser.parse_args()

    if args.match_url:
        # Extrair ID da URL
        parts = args.match_url.split('/')
        match_id = int(parts[-2]) if parts[-1] == 'villarreal' else int(parts[-1])
        match = Match.objects.get(id=match_id)
    elif args.match_id:
        match = Match.objects.get(id=args.match_id)
    else:
        raise ValueError("Você deve fornecer --match-id ou --match-url")
    slug = f"{slugify(match.home_team.name)}-vs-{slugify(match.away_team.name)}"
    match_url = f"https://statsfut.com/pt-br/match/{match.id}/{slug}/"
    
    print(f"\n========================================================")
    print(f"🎬 INICIANDO FÁBRICA AUTOMÁTICA DE VÍDEO")
    print(f"Partida: {match.home_team.name} vs {match.away_team.name}")
    print(f"Liga: {match.league.name} | Formato: {args.format.upper()}")
    print(f"URL: {match_url}")
    print(f"========================================================\n")
    
    # 1. Análise Estatística
    print("📊 1/4 - Calculando probabilidades matemáticas...")
    analyzer = MatchAnalyzer(match)
    report = analyzer.generate_full_report()
    narration_text, tags_script = build_script(match, report)
    
    # 2. Gerar Áudio e Timestamps
    print("🎙️ 2/4 - Gerando narração esportiva com Edge-TTS Neural...")
    media_dir = BASE_DIR / "media" / "audios_locucao"
    media_dir.mkdir(parents=True, exist_ok=True)
    
    audio_path = media_dir / f"match_{match.id}.mp3"
    json_path = media_dir / f"match_{match.id}.json"
    txt_path = media_dir / f"match_{match.id}.txt"
    
    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write(tags_script)
        
    asyncio.run(generate_voice(narration_text, str(audio_path), str(json_path)))
    print(f"✅ Áudio e marcações gerados com sucesso: {audio_path}")
    
    # 2.5 Gerar ou Usar Capa/Thumbnail e Outro
    print("🎨 2.5/4 - Verificando Capa oficial (Frame 0) e Card Final (Outro)...")
    from video_maker.visual_assets import create_thumbnail_cover, create_outro_card
    
    # Verifica se o usuário colocou uma thumbnail customizada na pasta video_maker/thumbnails/
    user_thumb_jpg = BASE_DIR / "video_maker" / "thumbnails" / f"match_{match.id}.jpg"
    user_thumb_png = BASE_DIR / "video_maker" / "thumbnails" / f"match_{match.id}.png"
    
    thumb_path = media_dir / f"match_{match.id}_thumb.png"
    outro_path = media_dir / "outro_telegram_statsfut.png"
    
    if user_thumb_jpg.exists():
        print(f"🌟 [Thumbnail Personalizada Detectada!] Usando: {user_thumb_jpg}")
        thumb_path = user_thumb_jpg
    elif user_thumb_png.exists():
        print(f"🌟 [Thumbnail Personalizada Detectada!] Usando: {user_thumb_png}")
        thumb_path = user_thumb_png
    else:
        print("ℹ️ Nenhuma thumbnail manual encontrada em video_maker/thumbnails/. Gerando thumbnail padrão do sistema...")
        goals = report.get("goals", {})
        over_15 = goals.get("over_15", 75)
        create_thumbnail_cover(
            home_name=match.home_team.name,
            away_name=match.away_team.name,
            league_name=match.league.name,
            market_pick="Over 1.5 Gols",
            prob_pct=over_15,
            output_path=str(thumb_path)
        )
    create_outro_card(str(outro_path))
    
    # 3. Invocar o motor de gravação e renderização
    print("🎥 3/4 - Gravando telas com Playwright e renderizando MP4 com Capa e Outro...")
    if args.format == "short":
        script_runner = BASE_DIR / "video_maker" / "gerar_video_curto.py"
    else:
        script_runner = BASE_DIR / "video_maker" / "gerar_video.py"
        
    cmd = [
        str(BASE_DIR / "venv" / "bin" / "python"),
        str(script_runner),
        "--url", match_url,
        "--audio", str(audio_path),
        "--roteiro", str(txt_path),
        "--json", str(json_path),
        "--thumb", str(thumb_path),
        "--outro", str(outro_path)
    ]
    
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = "sk-placeholder" # Fallback para usar o JSON direto do Edge-TTS
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
        sys.exit(result.returncode)
        
    print("\n🎉 VÍDEO PRONTO E DISPONÍVEL!")
    
    # 4. Upload automático para o YouTube se solicitado
    if args.post_youtube:
        print("\n📤 [YouTube] Iniciando upload e agendamento automático...")
        from video_maker.youtube_uploader import upload_video_to_youtube
        import re
        
        # Encontra o arquivo mp4 gerado na saída
        mp4_match = re.search(r'(video_cinema_\d+\.mp4)', result.stdout)
        if mp4_match:
            video_filename = mp4_match.group(1)
            output_dir = BASE_DIR / "media" / "videos" / "output"
            final_mp4_path = str(output_dir / video_filename)
            
            # Título e Descrição de Alto CTR
            video_title = f"{match.home_team.name} vs {match.away_team.name} - Análise Estatística e Tendências"
            video_desc = (
                f"Análise estatística completa para o confronto entre {match.home_team.name} e {match.away_team.name} pela {match.league.name}.\n\n"
                f"📊 Estatísticas em tempo real, radar de pressão e tendências matemáticas no StatsFut:\n"
                f"👉 Acesse: https://statsfut.com\n\n"
                f"🚀 Entre no nosso Canal Gratuito no Telegram para projeções diárias:\n"
                f"👉 https://t.me/statsfut_free\n\n"
                f"⚠️ AVISO LEGAL / DISCLAIMER:\n"
                f"Este conteúdo tem caráter puramente informativo e educacional, baseado em análise de dados e probabilidades estatísticas.\n"
                f"Não fazemos recomendações de apostas nem garantimos lucros. Apostas envolvem risco financeiro. Seja responsável (+18).\n\n"
                f"#Shorts #Futebol #StatsFut #PalpitesDeFutebol #{match.home_team.name.replace(' ', '')} #{match.away_team.name.replace(' ', '')}"
            )
            tags = [
                match.home_team.name,
                match.away_team.name,
                match.league.name,
                "futebol",
                "statsfut",
                "analise de futebol",
                "estatisticas de futebol",
                "palpites",
                "apostas esportivas"
            ]
            
            upload_video_to_youtube(
                file_path=final_mp4_path,
                title=video_title,
                description=video_desc,
                tags=tags,
                publish_at_iso=args.publish_at,
                is_short=(args.format == "short")
            )
        else:
            print("⚠️ Arquivo de vídeo final não detectado na saída do renderizador.")

if __name__ == "__main__":
    main()
