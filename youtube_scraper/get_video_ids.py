# youtube_scraper/get_video_ids.py (Versión Centrada en Fuentes Confiables)

import os
import logging
from googleapiclient.discovery import build
from dotenv import load_dotenv

# --- Importamos nuestra lista de fuentes desde el script de análisis ---
# Esto asegura que ambos scripts siempre estén sincronizados.
from analizar_transcripciones import FUENTES_PONDERADAS

# --- Configuración ---
OUTPUT_FILE = os.path.join('youtube_scraper', 'videos_filtrados.txt')

def get_video_ids_from_channels():
    """
    Se conecta a la API de YouTube, busca los videos más recientes de los canales
    predefinidos en FUENTES_PONDERADAS y guarda sus IDs.
    """
    logging.info("🔎 [YouTube Scraper] Iniciando búsqueda de videos de canales de confianza...")
    
    # --- Cargar la API Key de YouTube de forma segura ---
    # Asumimos que la clave está en el .env de la raíz del proyecto.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logging.error("❌ [YouTube Scraper] YOUTUBE_API_KEY no encontrada en el archivo .env. No se pueden buscar videos.")
        return

    try:
        youtube_service = build('youtube', 'v3', developerKey=api_key)
        
        video_ids_encontrados = []
        
        # --- Iterar sobre nuestra lista de canales de confianza ---
        for channel_id, info in FUENTES_PONDERADAS.items():
            logging.info(f"  -> Buscando videos recientes del canal: {info['nombre']}...")
            
            # 1. Buscar los uploads recientes de un canal por su ID
            request = youtube_service.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=2,  # Tomamos los 2 videos más recientes para mantener el análisis fresco
                order="date",    # Ordenar por fecha para obtener los últimos
                type="video"
            )
            response = request.execute()
            
            # 2. Extraer los IDs de los videos encontrados
            for item in response.get('items', []):
                video_id = item.get('id', {}).get('videoId')
                if video_id:
                    video_ids_encontrados.append(video_id)
                    logging.info(f"    -> Video encontrado: {item['snippet']['title']} (ID: {video_id})")

        if not video_ids_encontrados:
            logging.warning("⚠️ [YouTube Scraper] No se encontraron videos nuevos en los canales especificados.")
            return

        # --- Guardar los IDs en el archivo ---
        with open(OUTPUT_FILE, 'w') as f:
            for video_id in video_ids_encontrados:
                f.write(f"{video_id}\n")
        
        logging.info(f"✅ [YouTube Scraper] Búsqueda completada. {len(video_ids_encontrados)} IDs de video guardados en '{OUTPUT_FILE}'.")

    except Exception as e:
        logging.error(f"❌ [YouTube Scraper] Ocurrió un error al contactar la API de YouTube: {e}")
        # Esto puede pasar si se excede la cuota de la API.
        

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el recolector de videos de 'Top Traders' en modo de prueba ---")
    get_video_ids_from_channels()