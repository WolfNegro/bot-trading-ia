# youtube_scraper/analizar_transcripciones.py (Versión con Fuentes Reales)

import os
import pandas as pd
import logging

# --- Configuración ---
TRANSCRIPCIONES_DIR = os.path.join('youtube_scraper', 'transcripciones')

# --- 1. DEFINICIÓN DE FUENTES Y PESOS (ACTUALIZADA CON TUS CANALES) ---
FUENTES_PONDERADAS = {
    # Nivel 1: Analistas Macro de Alta Confianza (Peso Alto)
    "UCRvqjQPSeaWn-uEx-w0XOIg": {"nombre": "Benjamin Cowen", "peso": 3.0},
    "UClgJyzwGs-GyaNxUHcLZrkg": {"nombre": "InvestAnswers", "peso": 3.0},
    
    # Nivel 2: Traders Técnicos Diarios (Peso Medio)
    "UCnMku7J_UtwlcSfZlIuQ3Kw": {"nombre": "Crypto Capital Venture", "peso": 1.5},
    "UC-5HLi3buMzdxjdTdic3Aig": {"nombre": "The Modern Investor", "peso": 1.5},

    # Nivel 3: Canales de Noticias y Visión General (Peso Normal)
    "UCqK_GSMbpiV8spgD3ZGloSw": {"nombre": "Coin Bureau", "peso": 1.0},
    "UCCatR7nWbYrkVXdxXb4cGXw": {"nombre": "DataDash", "peso": 1.0}
}

# --- 2. LISTAS DE PALABRAS CLAVE ---
PALABRAS_CLAVE_POSITIVAS = [
    'subirá', 'bullish', 'compra', 'comprar', 'oportunidad', 'soporte', 'alza', 
    'optimista', 'rally', 'despegue', 'aumento', 'ganancia', 'potencial', 'fuerte',
    'crecimiento', 'récord', 'máximo', 'recuperación', 'invertir', 'acumular'
]
PALABRAS_CLAVE_NEGATIVAS = [
    'bajará', 'bearish', 'venta', 'vender', 'riesgo', 'resistencia', 'caída', 
    'pesimista', 'corrección', 'burbuja', 'pérdida', 'peligro', 'débil', 
    'disminución', 'desplome', 'pánico', 'cuidado', 'sobrecomprado'
]

def analizar_sentimiento_frase(frase):
    """Analiza una sola frase y devuelve un puntaje de sentimiento base."""
    score = 0
    frase_lower = frase.lower()
    for palabra in PALABRAS_CLAVE_POSITIVAS:
        if palabra in frase_lower:
            score += 1
    for palabra in PALABRAS_CLAVE_NEGATIVAS:
        if palabra in frase_lower:
            score -= 1
    return score

def get_youtube_sentiment():
    """
    Lee las transcripciones, calcula un puntaje de sentimiento y devuelve una señal.
    (La lógica de ponderación se implementará al actualizar el scraper).
    """
    logging.info("🧠 [YouTube V2] Iniciando análisis de sentimiento de fuentes...")
    
    if not os.path.exists(TRANSCRIPCIONES_DIR) or not os.listdir(TRANSCRIPCIONES_DIR):
        logging.warning("⚠️ [YouTube V2] No se encontraron transcripciones para analizar.")
        return 0

    puntaje_total_ponderado = 0
    
    for filename in os.listdir(TRANSCRIPCIONES_DIR):
        if not filename.endswith(".txt"):
            continue
        
        filepath = os.path.join(TRANSCRIPCIONES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                texto = f.read()
            
            puntaje_video = 0
            frases = texto.split('.')
            for frase in frases:
                if len(frase.strip()) > 10:
                    puntaje_video += analizar_sentimiento_frase(frase)
            
            # TODO: Futura mejora - aplicar peso del canal aquí.
            puntaje_total_ponderado += puntaje_video

        except Exception as e:
            logging.error(f"❌ [YouTube V2] Error al leer el archivo {filename}: {e}")

    logging.info(f"📊 [YouTube V2] Análisis completado. Puntaje total: {puntaje_total_ponderado:.2f}")

    if puntaje_total_ponderado > 5:
        logging.info("✅ [YouTube V2] Sentimiento detectado: BULLISH (Fuerte)")
        return 1
    elif puntaje_total_ponderado < -5:
        logging.info("🛑 [YouTube V2] Sentimiento detectado: BEARISH (Fuerte)")
        return -1
    else:
        logging.info("⏸️ [YouTube V2] Sentimiento detectado: NEUTRAL")
        return 0

# Bloque de prueba
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando análisis de sentimiento (V2) en modo de prueba ---")
    
    sentimiento_final = get_youtube_sentiment()
    
    sentimiento_texto = "NEUTRAL"
    if sentimiento_final == 1:
        sentimiento_texto = "BULLISH"
    elif sentimiento_final == -1:
        sentimiento_texto = "BEARISH"
        
    print(f"\n✅ RESULTADO DEL ANÁLISIS: El sentimiento general es {sentimiento_texto} ({sentimiento_final})")