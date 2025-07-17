# youtube_scraper/download_transcripts.py (Versión compatible con CSV y nombres estructurados)

import os
import logging
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

# --- Configuración ---
# El input ahora es el archivo CSV
INPUT_FILE = os.path.join('youtube_scraper', 'video_list.csv')
OUTPUT_DIR = os.path.join('youtube_scraper', 'transcripciones')

def download_transcripts_from_csv():
    """
    Lee una lista de videos desde un archivo CSV y descarga sus transcripciones,
    guardándolas con un nombre de archivo estructurado.
    """
    logging.info("📜 [Transcript Downloader] Iniciando descarga desde CSV...")

    # --- Asegurarse de que el directorio de salida exista ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"  -> Directorio '{OUTPUT_DIR}' creado.")

    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        logging.error(f"❌ [Transcript Downloader] No se encontró el archivo '{INPUT_FILE}'. Ejecuta 'get_video_ids.py' primero.")
        return

    if df.empty:
        logging.warning("⚠️ [Transcript Downloader] El archivo CSV está vacío. No hay nada que descargar.")
        return

    logging.info(f"  -> {len(df)} videos encontrados en el CSV. Intentando descargar transcripciones...")
    
    successful_downloads = 0
    
    # --- Limpiar transcripciones antiguas ---
    for old_file in os.listdir(OUTPUT_DIR):
        if old_file.endswith(".txt"):
            os.remove(os.path.join(OUTPUT_DIR, old_file))
    logging.info("  -> Transcripciones antiguas eliminadas.")

    # --- Iterar sobre el DataFrame ---
    for index, row in df.iterrows():
        video_id = row['video_id']
        channel_id = row['channel_id']
        
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            full_transcript = " ".join([item['text'].replace('\n', ' ') for item in transcript_list])
            
            # --- NUEVO NOMBRE DE ARCHIVO ESTRUCTURADO ---
            # Formato: IDCANAL___IDVIDEO.txt
            filename = f"{channel_id}___{video_id}.txt"
            output_filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(full_transcript)
            
            logging.info(f"    -> ✅ Transcripción guardada para el video ID: {video_id}")
            successful_downloads += 1

        except (NoTranscriptFound, TranscriptsDisabled):
            logging.warning(f"    -> ⚠️ Sin transcripción para el video ID: {video_id}")
        except Exception as e:
            logging.error(f"    -> ❌ Error inesperado con el video ID {video_id}: {e}")

    logging.info(f"✅ [Transcript Downloader] Proceso completado. {successful_downloads}/{len(df)} transcripciones descargadas.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el descargador de transcripciones (desde CSV) ---")
    download_transcripts_from_csv()