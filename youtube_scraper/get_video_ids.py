# youtube_scraper/get_video_ids.py (Versión Robusta para Cron)

import os
import logging
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

# --- CAMBIO 1: Importación Relativa ---
# El punto '.' le dice a Python: "busca en el mismo directorio donde estoy yo".
from .analizar_transcripciones import FUENTES_PONDERADAS

# --- CAMBIO 2: Rutas Absolutas ---
# Hacemos que el script sea consciente de su propia ubicación.
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRAPER_DIR)
OUTPUT_FILE = os.path.join(SCRAPER_DIR, 'video_list.csv')

def get_video_ids_from_channels():
    """
    Busca videos de canales predefinidos y guarda sus IDs en un CSV.
    """
    logging.info("🔎 [YouTube Scraper] Iniciando búsqueda estructurada de videos...")
    
    # Carga el .env desde la raíz del proyecto
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logging.error("❌ [YouTube Scraper] YOUTUBE_API_KEY no encontrada.")
        return

    try:
        youtube_service = build('youtube', 'v3', developerKey=api_key)
        
        videos_encontrados = []
        
        for channel_id, info in FUENTES_PONDERADAS.items():
            logging.info(f"  -> Buscando videos del canal: {info['nombre']}...")
            
            request = youtube_service.search().list(
                part="snippet", channelId=channel_id, maxResults=2,
                order="date", type="video"
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item.get('id', {}).get('videoId')
                if video_id:
                    videos_encontrados.append({
                        "video_id": video_id,
                        "channel_id": channel_id,
                        "title": item['snippet']['title']
                    })
                    logging.info(f"    -> Video encontrado: {item['snippet']['title']}")

        if not videos_encontrados:
            logging.warning("⚠️ [YouTube Scraper] No se encontraron videos nuevos.")
            # Creamos un archivo vacío para que el siguiente script no falle
            pd.DataFrame(columns=["video_id", "channel_id", "title"]).to_csv(OUTPUT_FILE, index=False)
            return

        df = pd.DataFrame(videos_encontrados)
        df.to_csv(OUTPUT_FILE, index=False)
        
        logging.info(f"✅ [YouTube Scraper] Búsqueda completada. {len(videos_encontrados)} videos guardados.")

    except Exception as e:
        logging.error(f"❌ [YouTube Scraper] Ocurrió un error con la API de YouTube: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el recolector de videos (Rutas Absolutas) ---")
    get_video_ids_from_channels()