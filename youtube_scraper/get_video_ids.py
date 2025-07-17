# youtube_scraper/get_video_ids.py (Versión con Salida Estructurada CSV)

import os
import logging
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

# --- Importamos nuestra lista de fuentes desde el script de análisis ---
from analizar_transcripciones import FUENTES_PONDERADAS

# --- Configuración ---
# La salida ahora será un archivo CSV más informativo.
OUTPUT_FILE = os.path.join('youtube_scraper', 'video_list.csv')

def get_video_ids_from_channels():
    """
    Busca los videos más recientes de los canales predefinidos y guarda
    sus IDs y los IDs de sus canales en un archivo CSV.
    """
    logging.info("🔎 [YouTube Scraper] Iniciando búsqueda estructurada de videos...")
    
    # --- Cargar la API Key de YouTube ---
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logging.error("❌ [YouTube Scraper] YOUTUBE_API_KEY no encontrada.")
        return

    try:
        youtube_service = build('youtube', 'v3', developerKey=api_key)
        
        videos_encontrados = []
        
        # --- Iterar sobre nuestra lista de canales de confianza ---
        for channel_id, info in FUENTES_PONDERADAS.items():
            logging.info(f"  -> Buscando videos del canal: {info['nombre']}...")
            
            request = youtube_service.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=2,
                order="date",
                type="video"
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item.get('id', {}).get('videoId')
                if video_id:
                    # Guardamos un diccionario con ambos IDs
                    videos_encontrados.append({
                        "video_id": video_id,
                        "channel_id": channel_id,
                        "title": item['snippet']['title']
                    })
                    logging.info(f"    -> Video encontrado: {item['snippet']['title']} (ID: {video_id})")

        if not videos_encontrados:
            logging.warning("⚠️ [YouTube Scraper] No se encontraron videos nuevos.")
            return

        # --- Guardar los resultados en un DataFrame y luego en CSV ---
        df = pd.DataFrame(videos_encontrados)
        df.to_csv(OUTPUT_FILE, index=False)
        
        logging.info(f"✅ [YouTube Scraper] Búsqueda completada. {len(videos_encontrados)} videos guardados en '{OUTPUT_FILE}'.")

    except Exception as e:
        logging.error(f"❌ [YouTube Scraper] Ocurrió un error con la API de YouTube: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el recolector de videos (Salida CSV) ---")
    get_video_ids_from_channels()