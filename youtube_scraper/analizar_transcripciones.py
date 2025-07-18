# youtube_scraper/analizar_transcripciones.py (Versión Robusta para Cron)

import os
import pandas as pd
import logging

# --- Rutas Absolutas ---
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPCIONES_DIR = os.path.join(SCRAPER_DIR, 'transcripciones')

# --- DEFINICIÓN DE FUENTES Y PESOS ---
FUENTES_PONDERADAS = {
    "UCRvqjQPSeaWn-uEx-w0XOIg": {"nombre": "Benjamin Cowen", "peso": 3.0},
    "UClgJyzwGs-GyaNxUHcLZrkg": {"nombre": "InvestAnswers", "peso": 3.0},
    "UCnMku7J_UtwlcSfZlIuQ3Kw": {"nombre": "Crypto Capital Venture", "peso": 1.5},
    "UC-5HLi3buMzdxjdTdic3Aig": {"nombre": "The Modern Investor", "peso": 1.5},
    "UCqK_GSMbpiV8spgD3ZGloSw": {"nombre": "Coin Bureau", "peso": 1.0},
    "UCCatR7nWbYrkVXdxXb4cGXw": {"nombre": "DataDash", "peso": 1.0}
}

# --- LISTAS DE PALABRAS CLAVE ---
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
    Lee las transcripciones, aplica pesos según la fuente, y devuelve una señal final.
    """
    logging.info("🧠 [YouTube V3] Iniciando análisis de sentimiento con PONDERACIÓN...")
    
    if not os.path.exists(TRANSCRIPCIONES_DIR) or not os.listdir(TRANSCRIPCIONES_DIR):
        logging.warning("⚠️ [YouTube V3] No se encontraron transcripciones para analizar.")
        return 0

    puntaje_total_ponderado = 0
    canales_analizados = []

    for filename in os.listdir(TRANSCRIPCIONES_DIR):
        if not filename.endswith(".txt"):
            continue
        
        try:
            channel_id = filename.split('___')[0]
            peso = FUENTES_PONDERADAS.get(channel_id, {}).get("peso", 0)

            if peso == 0:
                continue

            nombre_canal = FUENTES_PONDERADAS[channel_id]["nombre"]
            if nombre_canal not in canales_analizados:
                canales_analizados.append(nombre_canal)

            filepath = os.path.join(TRANSCRIPCIONES_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                texto = f.read()
            
            puntaje_base_video = 0
            frases = texto.split('.')
            for frase in frases:
                if len(frase.strip()) > 10:
                    puntaje_base_video += analizar_sentimiento_frase(frase)
            
            puntaje_ponderado_video = puntaje_base_video * peso
            logging.info(f"  -> Video de '{nombre_canal}': Base={puntaje_base_video}, Peso={peso}, Ponderado={puntaje_ponderado_video:.2f}")
            puntaje_total_ponderado += puntaje_ponderado_video

        except Exception as e:
            logging.error(f"❌ [YouTube V3] Error procesando {filename}: {e}")

    if not canales_analizados:
        logging.info("ℹ️ [YouTube V3] No se encontraron transcripciones de canales de confianza.")
        return 0

    logging.info(f"📊 [YouTube V3] Análisis completado. {len(canales_analizados)} canales analizados. Puntaje final: {puntaje_total_ponderado:.2f}")

    if puntaje_total_ponderado > 5:
        return 1
    elif puntaje_total_ponderado < -5:
        return -1
    else:
        return 0

# Bloque de prueba
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Ejecutando análisis de sentimiento V3 (Rutas Absolutas) ---")
    
    sentimiento_final = get_youtube_sentiment()
    
    sentimiento_texto = "NEUTRAL"
    if sentimiento_final == 1:
        sentimiento_texto = "BULLISH"
    elif sentimiento_final == -1:
        sentimiento_texto = "BEARISH"
        
    print(f"\n✅ RESULTADO: El sentimiento ponderado es {sentimiento_texto} ({sentimiento_final})")