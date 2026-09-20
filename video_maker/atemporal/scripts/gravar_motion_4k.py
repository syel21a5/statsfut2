import os
import sys
import asyncio
from playwright.async_api import async_playwright

OUTPUT_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
TEMPLATES_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/templates"

VIEWPORT_WIDTH = 3840
VIEWPORT_HEIGHT = 2160

async def record_scene(browser, url, duration, output_path):
    print(f"--> Gravando cena Sincronizada 4K ({duration}s): {url}")
    page = await browser.new_page(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        record_video_dir=OUTPUT_DIR,
        record_video_size={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
    )
    
    await page.goto(url, wait_until="networkidle")
    await asyncio.sleep(duration)
    
    video_path = await page.video.path()
    await page.close()
    
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(video_path, output_path)
    print(f"Cena sincronizada gravada: {output_path}")

async def main():
    # Durações exatas baseadas nos Sentence Boundaries:
    # Cena 1: 0.0s a 64.11s -> 64.11s
    # Cena 2: 64.11s a 121.98s -> 57.87s
    # Cena 3: 121.98s a 164.09s -> 42.11s
    # Cena 4: 164.09s a 198.34s -> 34.25s
    scenes = [
        (f"file://{TEMPLATES_DIR}/slide_1_motion.html", 64.2, f"{OUTPUT_DIR}/scene_1_motion.webm"),
        (f"file://{TEMPLATES_DIR}/slide_2_motion.html", 58.0, f"{OUTPUT_DIR}/scene_2_motion.webm"),
        (f"file://{TEMPLATES_DIR}/slide_3_motion.html", 42.2, f"{OUTPUT_DIR}/scene_3_motion.webm"),
        (f"file://{TEMPLATES_DIR}/slide_4_motion.html", 34.5, f"{OUTPUT_DIR}/scene_4_motion.webm"),
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
