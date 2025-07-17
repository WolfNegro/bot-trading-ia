# scripts/news_analyzer.py

import os
import logging
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv

# --- Palabras clave para el análisis de sentimiento de titulares ---
# Simple pero efectivo. Se puede expandir o reemplazar con un modelo más complejo.
PALABRAS_POSITIVAS = [
    'aprueba', 'adopción', 'invierte', 'optimista', 'impulso', 'récord', 'aumenta', 'soporte', 
    'innovación', 'regulación positiva', 'halving', 'institucional', 'lanzamiento', 'alianza'
]
PALABRAS_NEGATIVAS = [
    'prohíbe', 'fraude', 'riesgo', 'cae', 'investigación', 'demanda', 'hackeo', 'volatilidad',
    'burbuja', 'regulación estricta', 'prohibición', 'estafa', 'colapso', 'pérdidas'
]

def analizar_sentimiento_noticias(articulos):
    """Analiza una lista de artículos y devuelve un puntaje de sentimiento agregado."""
    score = 0
    if not articulos:
        return 0
        
    for articulo in articulos:
        titulo = articulo.get('title', '').lower()
        if not titulo:
            continue
        
        for palabra in PALABRAS_POSITIVAS:
            if palabra in titulo:
                score += 1
        for palabra in PALABRAS_NEGATIVAS:
            if palabra in titulo:
                score -= 1
    return score

def get_news_sentiment():
    """
    Busca noticias recientes de Bitcoin y devuelve una señal de sentimiento estandarizada.
    Returns:
        int: 1 (Bullish), -1 (Bearish), 0 (Neutral).
    """
    logging.info("📰 [Noticias] Buscando noticias relevantes de Bitcoin...")

    # --- Cargar la API Key de forma segura ---
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logging.error("❌ [Noticias] NEWS_API_KEY no encontrada en el archivo .env.")
        return 0 # Devolver Neutral si no hay clave

    try:
        newsapi = NewsApiClient(api_key=api_key)
        
        # Buscar noticias de las últimas 24 horas sobre Bitcoin
        # Fuentes principales de finanzas para reducir el ruido
        fecha_desde = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = newsapi.get_everything(
            q='Bitcoin OR BTC',
            sources='bloomberg,reuters,financial-post,the-wall-street-journal,business-insider',
            from_param=fecha_desde,
            language='en', # El análisis de sentimiento es más robusto en inglés
            sort_by='relevancy'
        )

        articulos = data.get('articles', [])
        if not articulos:
            logging.info("ℹ️ [Noticias] No se encontraron noticias relevantes en las últimas 24 horas.")
            return 0

        puntaje_total = analizar_sentimiento_noticias(articulos)
        logging.info(f"📊 [Noticias] Análisis completado. {len(articulos)} artículos analizados. Puntaje: {puntaje_total}.")

        # --- Lógica de Decisión ---
        if puntaje_total >= 2: # Se necesita una señal de noticias positiva clara
            logging.info("✅ [Noticias] Sentimiento detectado: BULLISH (Positivo)")
            return 1
        elif puntaje_total <= -2: # Se necesita una señal negativa clara
            logging.info("🛑 [Noticias] Sentimiento detectado: BEARISH (Negativo)")
            return -1
        else:
            logging.info("⏸️ [Noticias] Sentimiento detectado: NEUTRAL")
            return 0
            
    except Exception as e:
        # Capturamos errores específicos de la API (ej. demasiadas peticiones, clave inválida)
        logging.error(f"❌ [Noticias] Error al contactar NewsAPI: {e}")
        return 0 # En caso de error, devolvemos Neutral para no afectar la operación


if __name__ == '__main__':
    # Bloque de prueba
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando analizador de noticias en modo de prueba ---")
    
    sentimiento_noticias = get_news_sentiment()
    
    sentimiento_texto = "NEUTRAL"
    if sentimiento_noticias == 1:
        sentimiento_texto = "BULLISH"
    elif sentimiento_noticias == -1:
        sentimiento_texto = "BEARISH"
        
    print(f"\n✅ RESULTADO DEL ANÁLISIS: El sentimiento de las noticias es {sentimiento_texto} ({sentimiento_noticias})")