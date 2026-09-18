import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright
from moviepy.editor import VideoFileClip, AudioFileClip

OUTPUT_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
TEMPLATES_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/templates"
AUDIO_PATH = "/www/wwwroot/statsfut.com/video_maker/atemporal/audios/audio_4k_over15.mp3"

# Resolução 1080p Full HD para gravação ultrarrápida e leve
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

async def record_scene(browser, url, duration, output_path):
    print(f"--> Gravando cena 4K ({duration}s): {url}")
    page = await browser.new_page(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        record_video_dir=OUTPUT_DIR,
        record_video_size={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
    )
    
    await page.goto(url, wait_until="networkidle")
    await asyncio.sleep(duration)
    
    video_path = await page.video.path()
    await page.close()
    
    # Renomeia para o arquivo de destino
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(video_path, output_path)
    print(f"Cena gravada: {output_path}")

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 4 Cenas baseadas na locução de ~198s:
    # 1. Armadilha Pré-Jogo: ~58s
    # 2. Cronograma Drip Staking: ~60s
    # 3. Free Bet & Blindagem: ~50s
    # 4. Chamada Blog & Plataforma: ~30s
    
    scenes = [
        (f"file://{TEMPLATES_DIR}/slide_1_4k.html", 64.7, f"{OUTPUT_DIR}/scene_1_4k.webm"),
        (f"file://{TEMPLATES_DIR}/slide_2_4k.html", 58.5, f"{OUTPUT_DIR}/scene_2_4k.webm"),
        (f"file://{TEMPLATES_DIR}/slide_3_4k.html", 42.5, f"{OUTPUT_DIR}/scene_3_4k.webm"),
        (f"file://{TEMPLATES_DIR}/slide_4_4k.html", 32.7, f"{OUTPUT_DIR}/scene_4_4k.webm"),
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--font-render-hinting=none"
            ]
        )
        
        for url, dur, out in scenes:
            await record_scene(browser, url, dur, out)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
