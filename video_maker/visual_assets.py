#!/usr/bin/env python3
"""
Gera componentes visuais cinematográficos para os Shorts/TikTok do StatsFut:
1. Frame de Capa / Thumbnail (Primeiro 1.2 segundos - Alto Contraste)
2. Card Final de Conversão (Outro / Telegram & Site - Alta Legibilidade)
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

BASE_DIR = Path("/www/wwwroot/statsfut.com")
ASSETS_DIR = BASE_DIR / "video_maker" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int, bold: bool = False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def draw_centered_text(draw, y, text, font, fill=(255, 255, 255), width=1080):
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return x, y, w, bbox[3] - bbox[1]

def create_thumbnail_cover(home_name: str, away_name: str, league_name: str, market_pick: str, prob_pct: int, output_path: str):
    """Cria a Capa Oficial / Thumbnail (1080x1920)"""
    W, H = 1080, 1920
    # Fundo escuro sólido e sofisticado (#070b14)
    img = Image.new("RGB", (W, H), (7, 11, 20))
    draw = ImageDraw.Draw(img)

    font_brand = get_font(38, bold=True)
    font_badge = get_font(30, bold=True)
    font_vs = get_font(52, bold=True)
    font_team = get_font(60, bold=True)
    font_market = get_font(42, bold=True)
    font_prob = get_font(140, bold=True)
    font_cta = get_font(36, bold=True)

    # 1. Topo: Selo de Marca
    top_box = [200, 90, W - 200, 165]
    draw.rounded_rectangle(top_box, radius=16, fill=(15, 23, 42), outline=(16, 185, 129), width=2)
    draw_centered_text(draw, 105, "⚡ STATSFUT INTELLIGENCE", font_brand, fill=(16, 185, 129))

    # 2. Liga
    draw_centered_text(draw, 205, league_name.upper(), font_badge, fill=(148, 163, 184))

    # 3. Bloco dos Clubes
    clubs_box = [60, 270, W - 60, 770]
    draw.rounded_rectangle(clubs_box, radius=24, fill=(15, 23, 42), outline=(30, 41, 59), width=3)

    draw_centered_text(draw, 340, home_name, font_team, fill=(255, 255, 255))
    
    # VS centralizado com badge vermelho/laranja
    vs_box = [W//2 - 60, 475, W//2 + 60, 565]
    draw.rounded_rectangle(vs_box, radius=14, fill=(239, 68, 68))
    draw_centered_text(draw, 490, "VS", font_vs, fill=(255, 255, 255))

    draw_centered_text(draw, 625, away_name, font_team, fill=(255, 255, 255))

    # 4. Bloco de Oportunidade Matemática (Foco do Hook / Capa)
    stat_box = [60, 830, W - 60, 1480]
    draw.rounded_rectangle(stat_box, radius=24, fill=(11, 19, 38), outline=(16, 185, 129), width=4)

    # Selo Projeção
    tag_box = [100, 880, 520, 950]
    draw.rounded_rectangle(tag_box, radius=12, fill=(16, 185, 129))
    draw.text((120, 895), "PROJEÇÃO DO SISTEMA", font=font_badge, fill=(255, 255, 255))

    # Mercado
    draw_centered_text(draw, 1010, f"MERCADO: {market_pick.upper()}", font_market, fill=(226, 232, 240))

    # Porcentagem Gigante Verde Esmeralda (#10b981)
    draw_centered_text(draw, 1100, f"{prob_pct}%", font_prob, fill=(16, 185, 129))
    draw_centered_text(draw, 1340, "PROBABILIDADE CALCULADA", font_badge, fill=(148, 163, 184))

    # 5. Card Inferior (Chamada)
    cta_box = [60, 1550, W - 60, 1800]
    draw.rounded_rectangle(cta_box, radius=20, fill=(15, 23, 42), outline=(14, 165, 233), width=2)
    
    draw_centered_text(draw, 1605, "CONFIRA A ANÁLISE COMPLETA", font_cta, fill=(255, 255, 255))
    draw_centered_text(draw, 1690, "🌐 STATSFUT.COM | 📲 TELEGRAM FREE", font_badge, fill=(56, 189, 248))

    img.save(output_path, "PNG")
    return output_path

def create_outro_card(output_path: str):
    """Cria a tela final de encerramento / CTA (Outro) com contraste estrito e perfeito"""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (7, 11, 20))
    draw = ImageDraw.Draw(img)

    font_title = get_font(54, bold=True)
    font_sub = get_font(32, bold=False)
    font_btn = get_font(42, bold=True)
    font_desc = get_font(34, bold=False)
    font_badge = get_font(28, bold=True)

    # Topo
    draw_centered_text(draw, 220, "GOSTOU DA ANÁLISE?", font_title, fill=(255, 255, 255))
    draw_centered_text(draw, 310, "Receba análises matemáticas e tips diariamente!", font_sub, fill=(148, 163, 184))

    # 1. Card Telegram Free (Fundo Azul Escuro com borda e textos claros)
    tg_box = [70, 480, W - 70, 930]
    draw.rounded_rectangle(tg_box, radius=24, fill=(12, 33, 56), outline=(14, 165, 233), width=3)
    
    draw.text((120, 540), "CANAL TELEGRAM FREE", font=font_btn, fill=(56, 189, 248))
    draw.text((120, 640), "•  Tips diárias de valor", font=font_desc, fill=(255, 255, 255))
    draw.text((120, 715), "•  Alertas ao vivo automáticos", font=font_desc, fill=(255, 255, 255))
    
    tg_btn = [120, 805, W - 120, 880]
    draw.rounded_rectangle(tg_btn, radius=12, fill=(2, 132, 199)) # Azul escuro/forte para alto contraste
    draw_centered_text(draw, 825, "ACESSE: t.me/statsfut_free (LINK NA BIO)", font=font_badge, fill=(255, 255, 255))

    # 2. Card Plataforma StatsFut (Fundo Verde Escuro com borda e textos claros)
    web_box = [70, 1010, W - 70, 1460]
    draw.rounded_rectangle(web_box, radius=24, fill=(8, 38, 28), outline=(16, 185, 129), width=3)
    
    draw.text((120, 1070), "PLATAFORMA STATSFUT.COM", font=font_btn, fill=(52, 211, 153))
    draw.text((120, 1170), "•  Radar In-Play com Pressão ao Vivo", font=font_desc, fill=(255, 255, 255))
    draw.text((120, 1245), "•  Previsões de Gols, Cantos e Cartões", font=font_desc, fill=(255, 255, 255))
    
    web_btn = [120, 1335, W - 120, 1410]
    draw.rounded_rectangle(web_btn, radius=12, fill=(5, 150, 105)) # Verde forte para contraste de texto
    draw_centered_text(draw, 1355, "ACESSE GRÁTIS: statsfut.com", font=font_badge, fill=(255, 255, 255))

    # Rodapé final e Aviso Legal (Disclaimer Anti-Processo)
    draw_centered_text(draw, 1550, "Inscreva-se no canal para não perder os jogos!", font_desc, fill=(203, 213, 225))

    # Disclaimer Legal
    font_disc = get_font(20, bold=False)
    draw_centered_text(draw, 1680, "⚠️ AVISO LEGAL: Conteúdo estritamente informativo e analítico baseado em estatísticas.", font_disc, fill=(148, 163, 184))
    draw_centered_text(draw, 1715, "Não garantimos lucros nem incentivamos apostas. Aposte com responsabilidade (+18).", font_disc, fill=(148, 163, 184))

    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    t_path = "/tmp/test_thumb_v2.png"
    o_path = "/tmp/test_outro_v2.png"
    create_thumbnail_cover("Hartford Athletic", "SC Jacksonville", "USL Championship", "Over 1.5 Gols", 77, t_path)
    create_outro_card(o_path)
    print("V2 gerada com sucesso!")
