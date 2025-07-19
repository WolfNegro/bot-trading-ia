# scripts/twitter_analyzer.py (Versión Final con Caché Inteligente)

import os
import logging
import tweepy
import sys # <-- LÍNEA AÑADIDA
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- INICIO DE LA CORRECCIÓN: Añadir la raíz del proyecto al path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
# --- FIN DE LA CORRECCIÓN ---


# --- Configuración del Módulo ---
PALABRAS_POSITIVAS = [
    'bullish', 'buy', 'buying', 'opportunity', 'support', 'rally', 'breakout',
    'optimistic', 'long', 'undervalued', 'dip buying', 'strong', 'growth', 'accumulating'
]
PALABRAS_NEGATIVAS = [
    'bearish', 'sell', 'selling', 'risk', 'resistance', 'correction', 'bubble',
    'pessimistic', 'short', 'overvalued', 'dump', 'weak', 'crash', 'scam'
]

TOP_TRADERS_IDS = {
    "254333617": {"nombre": "Benjamin Cowen", "peso": 3.0},
    "833521223354900480": {"nombre": "Will Clemente", "peso": 2.5},
    "1044558696": {"nombre": "PlanB", "peso": 2.0},
    "2361225846": {"nombre": "TechDev", "peso": 1.5},
    "971162236": {"nombre": "Rekt Capital", "peso": 1.5},
    "27647228": {"nombre": "Peter Brandt", "peso": 1.0}
}

# --- Caché Inteligente ---
CACHE = {
    "signal": 0,
    "timestamp": None
}
CACHE_EXPIRATION = timedelta(minutes=30)

def _get_twitter_client():
    """Carga las credenciales y crea un cliente de la API de X v2."""
    # La ruta del .env ya se calcula desde la raíz del proyecto, así que no necesita cambios.
    project_root_env = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root_env, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        logging.error("❌ [X] X_BEARER_TOKEN no está definido en el archivo .env.")
        return None
    try:
        client = tweepy.Client(bearer_token)
        return client
    except Exception as e:
        logging.error(f"❌ [X] Error al autenticar con la API de X: {e}")
        return None

def analizar_sentimiento_tweets(tweets):
    score = 0
    if not tweets: return 0
    for tweet in tweets:
        texto = tweet.text.lower()
        if texto.startswith("rt @"): continue
        puntaje_tweet = sum(1 for palabra in PALABRAS_POSITIVAS if palabra in texto)
        puntaje_tweet -= sum(1 for palabra in PALABRAS_NEGATIVAS if palabra in texto)
        score += puntaje_tweet
    return score

def get_twitter_sentiment():
    """
    Obtiene el sentimiento de X. Si la API está ocupada, devuelve la última señal válida cacheadada.
    """
    global CACHE
    logging.info("🐦 [X] Iniciando análisis de sentimiento de traders...")
    client = _get_twitter_client()
    if not client: return 0

    puntaje_total_ponderado = 0
    
    try:
        for user_id, info in TOP_TRADERS_IDS.items():
            response = client.get_users_tweets(user_id, max_results=5, exclude=['replies', 'retweets'])
            tweets = response.data
            if not tweets: continue
            puntaje_base = analizar_sentimiento_tweets(tweets)
            puntaje_total_ponderado += puntaje_base * info['peso']
        
        logging.info(f"📊 [X] Análisis completado. Puntaje final ponderado: {puntaje_total_ponderado:.2f}")

        if puntaje_total_ponderado >= 3:
            signal = 1
        elif puntaje_total_ponderado <= -3:
            signal = -1
        else:
            signal = 0
        
        logging.info(f"✅ [X] Sentimiento detectado: {'BULLISH' if signal == 1 else 'BEARISH' if signal == -1 else 'NEUTRAL'}")
        CACHE["signal"] = signal
        CACHE["timestamp"] = datetime.now()
        return signal

    except tweepy.errors.TooManyRequests:
        logging.warning("⚠️ [X] Límite de frecuencia de la API alcanzado.")
        if CACHE["timestamp"] and (datetime.now() - CACHE["timestamp"] < CACHE_EXPIRATION):
            age = (datetime.now() - CACHE["timestamp"]).total_seconds() // 60
            logging.info(f"  -> ✅ Usando señal de la caché (hace {age:.0f} min). Señal: {CACHE['signal']}")
            return CACHE["signal"]
        else:
            logging.error("  -> ❌ La caché está vacía o ha expirado. Devolviendo NEUTRAL.")
            return 0
            
    except Exception as e:
        logging.error(f"❌ [X] Ocurrió un error inesperado al contactar la API de X: {e}")
        return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando el analizador de sentimiento de X (Twitter) en modo de prueba ---")
    sentiment = get_twitter_sentiment()
    sentiment_text = "NEUTRAL"
    if sentiment == 1:
        sentiment_text = "BULLISH"
    elif sentiment == -1:
        sentiment_text = "BEARISH"
    print(f"\n✅ RESULTADO DEL ANÁLISIS: La señal de sentimiento de X es {sentiment_text} ({sentiment})")