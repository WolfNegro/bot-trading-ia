# youtube_scraper/download_transcripts.py

import os
import logging
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

# --- Configuración ---
INPUT_FILE = os.path.join('youtube_scraper', 'videos_filtrados.txt')
OUTPUT_DIR = os.path.join('youtube_scraper', 'transcripciones')

def download_transcripts_from_file():
    """
    Lee una lista de IDs de video desde un archivo y descarga sus transcripciones.
    """
    logging.info("📜 [Transcript Downloader] Iniciando descarga de transcripciones...")

    # --- Asegurarse de que el directorio de salida exista ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"  -> Directorio '{OUTPUT_DIR}' creado.")

    if not os.path.exists(INPUT_FILE):
        logging.error(f"❌ [Transcript Downloader] No se encontró el archivo de IDs '{INPUT_FILE}'. Ejecuta 'get_video_ids.py' primero.")
        return

    with open(INPUT_FILE, 'r') as f:
        video_ids = [line.strip() for line in f if line.strip()]

    if not video_ids:
        logging.warning("⚠️ [Transcript Downloader] El archivo de IDs está vacío. No hay nada que descargar.")
        return

    logging.info(f"  -> {len(video_ids)} IDs de video encontrados. Intentando descargar transcripciones...")
    
    successful_downloads = 0
    
    # --- Limpiar transcripciones antiguas antes de descargar las nuevas ---
    # Esto asegura que el análisis de sentimiento siempre se base en la información más reciente.
    for old_file in os.listdir(OUTPUT_DIR):
        if old_file.endswith(".txt"):
            os.remove(os.path.join(OUTPUT_DIR, old_file))
    logging.info("  -> Transcripciones antiguas eliminadas.")

    for video_id in video_ids:
        try:
            # Intentamos obtener la transcripción en español primero, luego en inglés
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            
            # Unimos todos los segmentos de la transcripción en un solo texto
            full_transcript = " ".join([item['text'] for item in transcript_list])
            
            # Guardamos el texto en un archivo .txt
            output_filepath = os.path.join(OUTPUT_DIR, f"{video_id}.txt")
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(full_transcript)
            
            logging.info(f"    -> ✅ Transcripción guardada para el video ID: {video_id}")
            successful_downloads += 1

        except (NoTranscriptFound, TranscriptsDisabled):
            logging.warning(f"    -> ⚠️ No se encontró transcripción o están deshabilitadas para el video ID: {video_id}")
        except Exception as e:
            logging.error(f"    -> ❌ Ocurrió un error inesperado con el video ID {video_id}: {e}")

    logging.info(f"✅ [Transcript Downloader] Proceso completado. {successful_downloads}/{len(video_ids)} transcripciones descargadas exitosamente.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el descargador de transcripciones en modo de prueba ---")
    download_transcripts_from_file()