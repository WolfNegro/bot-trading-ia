# youtube_scraper/analizar_transcripciones.py

import os
import pandas as pd
import logging

# --- Configuración ---
TRANSCRIPCIONES_DIR = os.path.join('youtube_scraper', 'transcripciones')

# --- Listas de Palabras Clave (Puedes expandirlas enormemente) ---
# Estas listas son el "cerebro" de nuestro análisis de sentimiento simple.
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
    """
    Analiza una sola frase y devuelve un puntaje de sentimiento.
    +1 por cada palabra positiva, -1 por cada palabra negativa.
    """
    score = 0
    frase_lower = frase.lower() # Convertir a minúsculas para comparar
    
    for palabra in PALABRAS_CLAVE_POSITIVAS:
        if palabra in frase_lower:
            score += 1
    
    for palabra in PALABRAS_CLAVE_NEGATIVAS:
        if palabra in frase_lower:
            score -= 1
            
    return score

def get_youtube_sentiment():
    """
    Lee todas las transcripciones, calcula un puntaje de sentimiento agregado
    y devuelve una señal estandarizada (1: Bullish, -1: Bearish, 0: Neutral).
    """
    logging.info("🧠 [YouTube] Iniciando análisis de sentimiento de transcripciones...")
    
    if not os.path.exists(TRANSCRIPCIONES_DIR) or not os.listdir(TRANSCRIPCIONES_DIR):
        logging.warning("⚠️ [YouTube] No se encontraron transcripciones para analizar.")
        return 0 # Devuelve Neutral si no hay nada que analizar

    puntaje_total = 0
    frases_analizadas = 0

    # Leer cada transcripción
    for filename in os.listdir(TRANSCRIPCIONES_DIR):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(TRANSCRIPCIONES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                texto = f.read()
            
            # Dividir en frases y analizar cada una
            frases = texto.split('.') # Dividir por puntos es una heurística simple
            for frase in frases:
                if len(frase.strip()) > 10: # Ignorar frases muy cortas
                    puntaje_total += analizar_sentimiento_frase(frase)
                    frases_analizadas += 1
        except Exception as e:
            logging.error(f"❌ [YouTube] Error al leer el archivo {filename}: {e}")

    if frases_analizadas == 0:
        logging.info("ℹ️ [YouTube] No se encontraron frases válidas en las transcripciones.")
        return 0

    logging.info(f"📊 [YouTube] Análisis completado. Puntaje total: {puntaje_total} en {frases_analizadas} frases.")

    # --- Lógica de Decisión Final ---
    # Si el puntaje total es significativamente positivo, es Bullish.
    # Si es significativamente negativo, es Bearish.
    # De lo contrario, es Neutral. Puedes ajustar este umbral.
    if puntaje_total > 2: # Umbral para considerar una señal fuerte
        logging.info("✅ [YouTube] Sentimiento detectado: BULLISH (Positivo)")
        return 1
    elif puntaje_total < -2:
        logging.info("🛑 [YouTube] Sentimiento detectado: BEARISH (Negativo)")
        return -1
    else:
        logging.info("⏸️ [YouTube] Sentimiento detectado: NEUTRAL")
        return 0

# Este bloque permite ejecutar el script directamente para probarlo
if __name__ == '__main__':
    # Configuración de logging para la prueba
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    
    print("\n--- Ejecutando análisis de sentimiento de YouTube en modo de prueba ---")
    sentimiento_final = get_youtube_sentiment()
    
    sentimiento_texto = "NEUTRAL"
    if sentimiento_final == 1:
        sentimiento_texto = "BULLISH"
    elif sentimiento_final == -1:
        sentimiento_texto = "BEARISH"
        
    print(f"\n✅ RESULTADO DEL ANÁLISIS: El sentimiento general es {sentimiento_texto} ({sentimiento_final})")