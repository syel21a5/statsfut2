import os
from PIL import Image, ImageDraw, ImageFont

def overlay_sports_broadcast(leonardo_bg_path, home_logo_path, away_logo_path, home_name, away_name, stat_prob, stat_label, output_path):
    """
    Layout com Safe-Zone Total para YouTube Shorts / TikTok:
    - Base livre (evita botões e título do Shorts)
    - Escudos e manchete no terço superior
    - Card de valor no terço médio
    - Fundo do Leonardo.ai brilhando com a bola mágica
    """
    bg = Image.open(leonardo_bg_path).convert("RGBA")
    bg = bg.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # Vinheta e contraste
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Gradiente escuro no topo para leitura cristalina
    for y in range(500):
        alpha = int(230 * (1 - y / 500))
        draw_overlay.line([(0, y), (1080, y)], fill=(2, 6, 23, alpha))
        
    img = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(img)
    
    try:
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_team = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_stat_num = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 170)
        font_stat_lbl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_cta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    except Exception:
        font_tag = font_headline = font_team = font_stat_num = font_stat_lbl = font_cta = ImageFont.load_default()

    # 1. TAG SUPERIOR
    tag_text = "🚨 TENDÊNCIA CONFIRMADA"
    tag_w = draw.textlength(tag_text, font=font_tag)
    tag_x = (1080 - tag_w) // 2
    draw.rounded_rectangle([tag_x - 30, 80, tag_x + tag_w + 30, 145], radius=30, fill=(239, 68, 68, 240), outline=(255, 255, 255, 255), width=3)
    draw.text((tag_x, 90), tag_text, fill=(255, 255, 255, 255), font=font_tag)

    # 2. MANCHETE
    hl_1 = "QUEM VENCE O DUELO?"
    w1 = draw.textlength(hl_1, font=font_headline)
    draw.text(((1080 - w1)//2, 175), hl_1, fill=(254, 240, 138, 255), font=font_headline)

    # 3. ESCUDOS DOS TIMES (Posicionados com folga)
    if home_logo_path and os.path.exists(home_logo_path):
        h_logo = Image.open(home_logo_path).convert("RGBA").resize((200, 200), Image.Resampling.LANCZOS)
        draw.ellipse([100, 290, 320, 510], fill=(15, 23, 42, 220), outline=(245, 158, 11, 255), width=5)
        img.paste(h_logo, (110, 300), h_logo)
        
    if away_logo_path and os.path.exists(away_logo_path):
        a_logo = Image.open(away_logo_path).convert("RGBA").resize((200, 200), Image.Resampling.LANCZOS)
        draw.ellipse([760, 290, 980, 510], fill=(15, 23, 42, 220), outline=(245, 158, 11, 255), width=5)
        img.paste(a_logo, (770, 300), a_logo)

    # Badge VS Central
    draw.ellipse([485, 345, 595, 455], fill=(239, 68, 68, 240), outline=(255, 255, 255, 255), width=4)
    vs_text = "VS"
    vs_w = draw.textlength(vs_text, font=font_team)
    draw.text(((1080 - vs_w)//2, 375), vs_text, fill=(255, 255, 255, 255), font=font_team)

    # Nomes dos times
    hn = home_name.upper()[:12]
    an = away_name.upper()[:12]
    hw = draw.textlength(hn, font=font_team)
    aw = draw.textlength(an, font=font_team)
    draw.text((210 - hw//2, 530), hn, fill=(255, 255, 255, 255), font=font_team)
    draw.text((870 - aw//2, 530), an, fill=(255, 255, 255, 255), font=font_team)

    # 4. CARD DE ESTATÍSTICA (Posicionado no terço médio seguro: 1080 a 1400px)
    draw.rounded_rectangle([80, 1120, 1000, 1420], radius=40, fill=(15, 23, 42, 235), outline=(16, 185, 129, 255), width=5)
    stat_str = f"{stat_prob}%"
    sw = draw.textlength(stat_str, font=font_stat_num)
    draw.text(((1080 - sw)//2, 1135), stat_str, fill=(16, 185, 129, 255), font=font_stat_num)
    
    lw = draw.textlength(stat_label.upper(), font=font_stat_lbl)
    draw.text(((1080 - lw)//2, 1330), stat_label.upper(), fill=(255, 255, 255, 255), font=font_stat_lbl)

    # 5. BOTÃO CTA (em 1460px — 100% visível sem encostar no rodapé do Shorts)
    draw.rounded_rectangle([80, 1460, 1000, 1570], radius=30, fill=(239, 68, 68, 250), outline=(254, 202, 202, 255), width=3)
    cta_text = "▶ VEJA A ANÁLISE COMPLETA"
    cw = draw.textlength(cta_text, font=font_cta)
    draw.text(((1080 - cw)//2, 1485), cta_text, fill=(255, 255, 255, 255), font=font_cta)

    img = img.convert("RGB")
    img.save(output_path, quality=95)
    print("Thumbnail final com Safe-Zone gerada em:", output_path)
    return output_path

if __name__ == "__main__":
    overlay_sports_broadcast(
        leonardo_bg_path="/www/wwwroot/statsfut.com/media/videos/output/leonardo_thumb_match_558792.jpg",
        home_logo_path="/www/wwwroot/statsfut.com/static/teams/estados-unidos/310968.png",
        away_logo_path="/www/wwwroot/statsfut.com/static/teams/estados-unidos/1077312.png",
        home_name="Hartford",
        away_name="Jacksonville",
        stat_prob="77",
        stat_label="Tendência Over 1.5 Gols",
        output_path="/www/wwwroot/statsfut.com/media/videos/output/thumb_leonardo_safezone.jpg"
    )
