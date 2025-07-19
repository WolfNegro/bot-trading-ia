# scripts/fear_and_greed_analyzer.py

import requests
import logging
import sys # <-- LÍNEA AÑADIDA
import os # <-- LÍNEA AÑADIDA
from datetime import datetime, timedelta

# --- INICIO DE LA CORRECCIÓN: Añadir la raíz del proyecto al path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
# --- FIN DE LA CORRECCIÓN ---


# --- Configuración ---
API_URL = "https://api.alternative.me/fng/?limit=2"
CACHE = {
    "data": None,
    "timestamp": None
}
CACHE_DURATION = timedelta(minutes=10)

def get_fear_and_greed_index():
    """
    Obtiene el valor más reciente del Fear & Greed Index y lo traduce a una señal.
    Utiliza un sistema de caché simple para evitar peticiones innecesarias.
    """
    now = datetime.now()
    
    if CACHE["timestamp"] and (now - CACHE["timestamp"] < CACHE_DURATION):
        logging.info("🧠 [F&G] Usando valor de caché para el Fear & Greed Index.")
        data = CACHE["data"]
    else:
        logging.info("🧠 [F&G] Obteniendo nuevo valor del Fear & Greed Index...")
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            CACHE["data"] = data
            CACHE["timestamp"] = now
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ [F&G] Error al contactar la API de Fear & Greed: {e}")
            return 0

    if data and 'data' in data and len(data['data']) > 0:
        latest_value = int(data['data'][0]['value'])
        classification = data['data'][0]['value_classification']
        logging.info(f"📊 [F&G] Índice actual: {latest_value} ({classification})")

        if latest_value > 65: 
            logging.info("✅ [F&G] Sentimiento detectado: BULLISH (Codicia)")
            return 1
        elif latest_value < 25:
            logging.info("🛑 [F&G] Sentimiento detectado: BEARISH (Miedo Extremo)")
            return -1
        else:
            logging.info("⏸️ [F&G] Sentimiento detectado: NEUTRAL")
            return 0
    else:
        logging.warning("⚠️ [F&G] La respuesta de la API no tuvo el formato esperado.")
        return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el analizador de Fear & Greed en modo de prueba ---")
    sentiment = get_fear_and_greed_index()
    sentiment_text = "NEUTRAL"
    if sentiment == 1:
        sentiment_text = "BULLISH (Codicia)"
    elif sentiment == -1:
        sentiment_text = "BEARISH (Miedo Extremo)"
    print(f"\n✅ RESULTADO DEL ANÁLISIS: La señal de sentimiento es {sentiment_text} ({sentiment})")