import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright

OUTPUT_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
TEMPLATES_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/templates"

VIEWPORT_WIDTH = 3840
VIEWPORT_HEIGHT = 2160

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
    
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(video_path, output_path)
    print(f"Cena gravada: {output_path}")

async def main():
    scenes = [
        (f"file://{TEMPLATES_DIR}/slide_3_4k.html", 50, f"{OUTPUT_DIR}/scene_3_4k.webm"),
        (f"file://{TEMPLATES_DIR}/slide_4_4k.html", 30, f"{OUTPUT_DIR}/scene_4_4k.webm"),
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
