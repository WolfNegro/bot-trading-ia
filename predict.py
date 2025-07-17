# predict.py
# CORRECCIÓN: Se crea una Serie de pandas 'close_series' explícitamente 1D
# para asegurar la compatibilidad con la librería 'ta' y prevenir errores de
# dimensionalidad de forma robusta.

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import joblib
import os

# --- Constantes ---
MODEL_PATH = os.path.join('models', 'model.joblib')
FEATURES = ['sma_20', 'sma_50', 'rsi_14', 'returns', 'cruce']

# --- Funciones de Mapeo ---
def map_prediction_to_text(prediction):
    """Convierte la predicción numérica a texto."""
    mapping = {1: "Sube", -1: "Baja", 0: "Estable"}
    return mapping.get(prediction, "Desconocido")

def map_prediction_to_recommendation(prediction):
    """Convierte la predicción a una recomendación de trading."""
    mapping = {1: "COMPRAR", -1: "VENDER", 0: "ESPERAR"}
    return mapping.get(prediction, "SIN RECOMENDACIÓN")

# --- Lógica Principal ---
def run_prediction():
    """
    Ejecuta el proceso completo de predicción.
    """
    # -- 1. Cargar Modelo --
    print(f"Cargando modelo desde: {MODEL_PATH}")
    if not os.path.exists(MODEL_PATH):
        print(f"Error: No se encontró el archivo del modelo en '{MODEL_PATH}'.")
        print("Por favor, ejecuta primero el script 'train_model.py' para entrenar y guardar el modelo.")
        return

    try:
        model = joblib.load(MODEL_PATH)
        print("Modelo cargado exitosamente.")
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
        return

    # -- 2. Descargar Datos Recientes --
    print("Descargando los últimos 90 días de datos de BTC-USD...")
    try:
        data = yf.download('BTC-USD', period='90d', interval='1d', auto_adjust=True, progress=False)
        if data.empty or len(data) < 51:
            print("Error: No se pudieron descargar suficientes datos para el cálculo (se necesitan más de 50 días).")
            return
        print("Datos descargados correctamente.")
    except Exception as e:
        print(f"Error al descargar los datos: {e}")
        return

    # -- 3. Calcular Indicadores y Features (MÉTODO CORREGIDO) --
    print("Calculando indicadores para la predicción...")
    
    # Se crea una Serie limpia para evitar problemas de dimensionalidad
    close_series = pd.Series(data['Close'].values.squeeze(), index=data.index)

    # Se usa la nueva 'close_series' para todos los cálculos
    data['sma_20'] = SMAIndicator(close=close_series, window=20).sma_indicator()
    data['sma_50'] = SMAIndicator(close=close_series, window=50).sma_indicator()
    data['rsi_14'] = RSIIndicator(close=close_series, window=14).rsi()
    data['returns'] = data['Close'].pct_change()
    
    # Feature de Cruce de Medias Móviles
    data['cruce'] = 0
    condition_bullish = (data['sma_20'].shift(1) < data['sma_50'].shift(1)) & (data['sma_20'] > data['sma_50'])
    data.loc[condition_bullish, 'cruce'] = 1
    condition_bearish = (data['sma_20'].shift(1) > data['sma_50'].shift(1)) & (data['sma_20'] < data['sma_50'])
    data.loc[condition_bearish, 'cruce'] = -1

    # Preparar el último set de features para la predicción
    last_features = data[FEATURES].tail(1)

    # Verificación de robustez: asegurar que no haya valores nulos antes de predecir
    if last_features.isnull().values.any():
        print("Error: No se pudieron calcular todos los features para la última fecha. Faltan datos.")
        # print(last_features.to_string()) # Descomentar para depuración
        return

    # -- 4. Realizar la Predicción --
    print("Generando predicción...")
    try:
        prediction = model.predict(last_features)[0]
        probabilities = model.predict_proba(last_features)[0]
    except Exception as e:
        print(f"Ocurrió un error durante la predicción: {e}")
        return
        
    # -- 5. Mostrar Resultados --
    print("\n--- PREDICCIÓN PARA MAÑANA ---")
    
    prediction_text = map_prediction_to_text(prediction)
    print(f"Predicción: {prediction} ({prediction_text})")

    print("\nProbabilidades:")
    if hasattr(model, 'classes_'):
        for i, class_label in enumerate(model.classes_):
            class_text = map_prediction_to_text(class_label)
            print(f"  - Prob. de '{class_text}' ({class_label}): {probabilities[i]:.2%}")
    else:
        print(f"Probabilidades brutas: {probabilities}")

    recommendation = map_prediction_to_recommendation(prediction)
    print("\n--- RECOMENDACIÓN ---")
    print(f"Acción sugerida: {recommendation}")
    print("-----------------------\n")
    print("AVISO: Esta es una recomendación generada por un modelo de IA y no debe considerarse como asesoramiento financiero.")

if __name__ == "__main__":
    run_prediction()