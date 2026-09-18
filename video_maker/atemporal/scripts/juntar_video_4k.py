import os
import sys
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

OUTPUT_DIR = "/www/wwwroot/statsfut.com/video_maker/atemporal/output"
AUDIO_PATH = "/www/wwwroot/statsfut.com/video_maker/atemporal/audios/audio_4k_over15.mp3"
FINAL_VIDEO_PATH = f"{OUTPUT_DIR}/video_teste_atemporal_4k.mp4"

def assemble_video():
    print("--> Carregando clipes 4K gravados...")
    c1 = VideoFileClip(f"{OUTPUT_DIR}/scene_1_4k.webm")
    c2 = VideoFileClip(f"{OUTPUT_DIR}/scene_2_4k.webm")
    c3 = VideoFileClip(f"{OUTPUT_DIR}/scene_3_4k.webm")
    c4 = VideoFileClip(f"{OUTPUT_DIR}/scene_4_4k.webm")
    
    audio = AudioFileClip(AUDIO_PATH)
    print(f"Duração do áudio: {audio.duration}s")
    
    # Concatenar as 4 cenas
    video = concatenate_videoclips([c1, c2, c3, c4], method="compose")
    print(f"Duração combinada do vídeo bruto: {video.duration}s")
    
    # Ajustar para a duração exata do áudio
    if video.duration > audio.duration:
        video = video.subclip(0, audio.duration)
    
    video = video.set_audio(audio)
    
    print(f"--> Renderizando vídeo final 4K ({video.w}x{video.h})...")
    # Renderizar com preset rápido e alta taxa de bits para qualidade cristalina
    video.write_videofile(
        FINAL_VIDEO_PATH,
        codec="libx264",
        audio_codec="aac",
        preset="faster",
        bitrate="8000k",
        ffmpeg_params=["-movflags", "+faststart"],
        threads=4
    )
    print(f"Vídeo final 4K pronto em: {FINAL_VIDEO_PATH}")

if __name__ == "__main__":
    assemble_video()
