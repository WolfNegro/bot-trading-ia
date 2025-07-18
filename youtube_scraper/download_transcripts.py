# youtube_scraper/download_transcripts.py (Versión Autónoma con Whisper ASR)

import os
import logging
import pandas as pd
from pytube import YouTube
import whisper_ctranslate2

# --- Rutas Absolutas ---
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRAPER_DIR, 'video_list.csv')
OUTPUT_DIR = os.path.join(SCRAPER_DIR, 'transcripciones')
TEMP_AUDIO_DIR = os.path.join(SCRAPER_DIR, 'temp_audio') # Directorio para audios temporales

# --- Configuración del Modelo de Transcripción (Whisper) ---
# "tiny" es el más rápido. "base" tiene mejor calidad. Empecemos con "tiny".
WHISPER_MODEL = "tiny" 
# Usamos 'float16' para una buena mezcla de velocidad y precisión en CPU/GPU modernas
COMPUTE_TYPE = "float16"

# --- Inicializar el modelo una sola vez ---
# La primera vez que se ejecute, descargará los archivos del modelo.
logging.info(f"🎤 [Whisper] Cargando modelo de transcripción '{WHISPER_MODEL}'...")
try:
    whisper_model = whisper_ctranslate2.WhisperModel(WHISPER_MODEL, device="cpu", compute_type=COMPUTE_TYPE)
    logging.info("✅ [Whisper] Modelo cargado exitosamente.")
except Exception as e:
    logging.error(f"❌ [Whisper] No se pudo cargar el modelo. Error: {e}")
    whisper_model = None

def download_and_transcribe():
    """
    Descarga el audio de videos de YouTube y los transcribe usando Whisper ASR.
    """
    global whisper_model
    if not whisper_model:
        logging.error("❌ Abortando: El modelo Whisper no está disponible.")
        return

    logging.info("📜 [Downloader V2] Iniciando descarga de audio y transcripción...")

    # --- Asegurarse de que los directorios existan ---
    for dir_path in [OUTPUT_DIR, TEMP_AUDIO_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        logging.error(f"❌ No se encontró '{INPUT_FILE}'. Ejecuta 'get_video_ids.py' primero.")
        return

    if df.empty:
        logging.warning("⚠️ El archivo CSV de videos está vacío.")
        return

    logging.info(f"  -> {len(df)} videos encontrados. Procesando...")
    
    # Limpiar transcripciones antiguas
    for old_file in os.listdir(OUTPUT_DIR):
        if old_file.endswith(".txt"):
            os.remove(os.path.join(OUTPUT_DIR, old_file))
    logging.info("  -> Transcripciones antiguas eliminadas.")

    successful_transcripts = 0
    for index, row in df.iterrows():
        video_id = row['video_id']
        channel_id = row['channel_id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        audio_path = None # Para asegurarnos de borrarlo al final
        try:
            logging.info(f"  -> Descargando audio para video: {video_id}...")
            yt = YouTube(video_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                logging.warning(f"    -> ⚠️ No se encontró stream de solo audio para {video_id}.")
                continue

            audio_path = audio_stream.download(output_path=TEMP_AUDIO_DIR)
            
            logging.info(f"    -> Transcribiendo audio...")
            # La magia de Whisper: transcribir el archivo de audio
            segments, _ = whisper_model.transcribe(audio_path, language="en", beam_size=5)
            
            full_transcript = " ".join([segment.text for segment in segments])

            # Guardar la transcripción
            filename = f"{channel_id}___{video_id}.txt"
            output_filepath = os.path.join(OUTPUT_DIR, filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(full_transcript)
            
            logging.info(f"    -> ✅ Transcripción guardada para {video_id}.")
            successful_transcripts += 1

        except Exception as e:
            logging.error(f"    -> ❌ Error procesando el video {video_id}: {type(e).__name__} - {e}")
        
        finally:
            # --- Limpieza del archivo de audio temporal ---
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    logging.info(f"✅ [Downloader V2] Proceso completado. {successful_transcripts}/{len(df)} videos transcritos.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el descargador y transcriptor autónomo (Whisper) ---")
    download_and_transcribe()