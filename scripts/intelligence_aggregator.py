# scripts/intelligence_aggregator.py (Versión de Confluencia Total)

import logging
import sys
import os

# --- Añadir la raíz del proyecto al path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Importamos las funciones de nuestros tres módulos de inteligencia
from scripts.twitter_analyzer import get_twitter_sentiment
from scripts.fear_and_greed_analyzer import get_fear_and_greed_index
from scripts.news_analyzer import get_news_sentiment

def get_all_sentiment_signals():
    """
    Consulta TODAS las fuentes de inteligencia y devuelve sus señales individuales.
    Está diseñado para ser robusto: si una fuente falla, devuelve 0 para esa fuente
    pero continúa con las demás.

    Returns:
        dict: Un diccionario con las señales de cada fuente de inteligencia.
    """
    logging.info("🧠 [Agregador] Recolectando todas las señales de sentimiento...")

    signals = {
        "twitter": 0,
        "fear_and_greed": 0,
        "news": 0
    }

    try:
        signals["twitter"] = get_twitter_sentiment()
    except Exception as e:
        logging.error(f"❌ Error al obtener señal de Twitter: {e}", exc_info=True)
        signals["twitter"] = 0 # Aseguramos valor neutral en caso de error

    try:
        signals["fear_and_greed"] = get_fear_and_greed_index()
    except Exception as e:
        logging.error(f"❌ Error al obtener señal de Fear & Greed: {e}", exc_info=True)
        signals["fear_and_greed"] = 0

    try:
        signals["news"] = get_news_sentiment()
    except Exception as e:
        logging.error(f"❌ Error al obtener señal de Noticias: {e}", exc_info=True)
        signals["news"] = 0
        
    logging.info(f"📊 [Agregador] Señales recolectadas: Twitter={signals['twitter']}, F&G={signals['fear_and_greed']}, Noticias={signals['news']}")
    return signals

# --- Bloque de Prueba ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el Agregador de Inteligencia en modo de prueba (Confluencia Total) ---")
    
    final_signals = get_all_sentiment_signals()
    
    print(f"\n✅ SEÑALES RECOLECTADAS:")
    for source, signal in final_signals.items():
        sentiment_text = "NEUTRAL"
        if signal == 1: sentiment_text = "BULLISH"
        elif signal == -1: sentiment_text = "BEARISH"
        print(f"  -> {source.capitalize()}: {sentiment_text} ({signal})")