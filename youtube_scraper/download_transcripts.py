# youtube_scraper/download_transcripts.py
from youtube_transcript_api import YouTubeTranscriptApi
import os

INPUT_FILE = "videos_filtrados.txt"
OUTPUT_DIR = "transcripciones"

# Crear carpeta de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    video_ids = [line.strip() for line in f.readlines()]

for video_id in video_ids:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        texto_completo = " ".join([entry['text'] for entry in transcript])
        
        with open(os.path.join(OUTPUT_DIR, f"{video_id}.txt"), "w", encoding="utf-8") as out:
            out.write(texto_completo)
        
        print(f"✅ Transcripción guardada para video: {video_id}")
    except Exception as e:
        print(f"⚠️ Error con {video_id}: {e}")
