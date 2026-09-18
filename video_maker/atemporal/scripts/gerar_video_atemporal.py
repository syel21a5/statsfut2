import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright
from moviepy.editor import VideoFileClip, AudioFileClip

OUTPUT_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
TEMPLATES_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/templates"
AUDIO_PATH = "/www/wwwroot/statsfut.com/video_maker/atemporal/audios/audio_teste_over15.mp3"
RAW_VIDEO_DIR = "/tmp/atemporal_raw_video"
FINAL_VIDEO_PATH = os.path.join(OUTPUT_DIR, "video_teste_atemporal_over15.mp4")

os.makedirs(RAW_VIDEO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def record_screens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=RAW_VIDEO_DIR,
            record_video_size={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        print("🎬 [1/5] Gravando Slide 1 (A Armadilha do Pré-Jogo)...")
        slide1_url = f"file://{TEMPLATES_DIR}/slide_1_intro.html"
        await page.goto(slide1_url)
        await page.wait_for_timeout(34000) # ~34s
        
        print("🎬 [2/5] Gravando Slide 2 (Cronograma Drip Staking)...")
        slide2_url = f"file://{TEMPLATES_DIR}/slide_2_cronograma.html"
        await page.goto(slide2_url)
        await page.wait_for_timeout(38000) # ~38s
        
        print("🎬 [3/5] Gravando Slide 3 (Gestão de Saída & Free Bet)...")
        slide3_url = f"file://{TEMPLATES_DIR}/slide_3_freebet.html"
        await page.goto(slide3_url)
        await page.wait_for_timeout(26000) # ~26s
        
        print("🎬 [4/5] Gravando Artigo Oficial no Blog (statsfut.com/blog)...")
        blog_url = "https://statsfut.com/blog/parte-3-over-1-5-ft-live-trading-avan-ado/"
        try:
            await page.goto(blog_url, wait_until="networkidle", timeout=20000)
            await page.evaluate("window.scrollBy({ top: 500, behavior: 'smooth' })")
            await page.wait_for_timeout(10000)
            await page.evaluate("window.scrollBy({ top: 600, behavior: 'smooth' })")
            await page.wait_for_timeout(8000)
        except Exception as e:
            print("Fallback no carregamento do blog:", e)
            await page.wait_for_timeout(18000)
            
        print("🎬 [5/5] Gravando Plataforma ao Vivo (StatsFut)...")
        try:
            await page.goto("https://statsfut.com/live/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(16000)
        except Exception:
            await page.goto(slide1_url)
            await page.wait_for_timeout(16000)
            
        await page.close()
        await context.close()
        await browser.close()
        print("Gravação de tela concluída!")

def process_video():
    # Encontra o arquivo gravado
    video_files = [os.path.join(RAW_VIDEO_DIR, f) for f in os.listdir(RAW_VIDEO_DIR) if f.endswith(".webm")]
    if not video_files:
        raise FileNotFoundError("Nenhum arquivo webm gravado!")
        
    latest_video = max(video_files, key=os.path.getctime)
    print(f"Vídeo gravado encontrado: {latest_video}")
    
    video_clip = VideoFileClip(latest_video)
    audio_clip = AudioFileClip(AUDIO_PATH)
    
    target_duration = audio_clip.duration
    print(f"Ajustando duração: Vídeo original {video_clip.duration:.1f}s -> Alvo áudio {target_duration:.1f}s")
    
    # Corta ou estende levemente para casar exatamente com o áudio
    final_video = video_clip.subclip(0, min(video_clip.duration, target_duration))
    final_video = final_video.set_audio(audio_clip)
    
    print("Renderizando MP4 final em 1080p Horizontal...")
    final_video.write_videofile(
        FINAL_VIDEO_PATH,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        bitrate="6000k"
    )
    print(f"✅ VÍDEO ATEMPORAL CONCLUÍDO: {FINAL_VIDEO_PATH}")

if __name__ == "__main__":
    asyncio.run(record_screens())
    process_video()
