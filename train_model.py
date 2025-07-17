# train_model.py (Versión de Alta Frecuencia - 15m)

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
import matplotlib.pyplot as plt

# --- PARÁMETROS DEL MODELO DE ALTA FRECUENCIA ---
# Símbolo a descargar
TICKER = 'BTC-USD'
# Período de datos. '60d' (60 días) es el máximo permitido por yfinance para intervalos de 15m.
PERIODO_DATOS = '60d'
# Intervalo de velas: 15 minutos para operaciones intradiarias.
INTERVALO_VELAS = '15m'

def train_ia_model():
    """
    Entrena un modelo de IA de alta frecuencia para predecir movimientos de precios
    en velas de 15 minutos.
    """
    print(f"--- Fase 1: Entrenamiento del Modelo de Alta Frecuencia ({INTERVALO_VELAS}) ---")
    
    # --- PASO 1: Descarga de Datos de Alta Frecuencia ---
    print(f"Paso 1: Descargando datos históricos para {TICKER} (Período: {PERIODO_DATOS}, Intervalo: {INTERVALO_VELAS})...")
    try:
        data = yf.download(TICKER, period=PERIODO_DATOS, interval=INTERVALO_VELAS, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError("No se pudieron descargar datos. Verifica el ticker o el período.")
        print(f"✅ Datos descargados correctamente. {len(data)} velas de {INTERVALO_VELAS} obtenidas.")
    except Exception as e:
        print(f"❌ Error al descargar datos: {e}")
        return

    # --- PASO 2: Cálculo de Indicadores Técnicos con Pandas (Versión Robusta) ---
    print("Paso 2: Calculando indicadores técnicos...")
    
    # Los parámetros de los indicadores se mantienen, pero ahora se aplican a velas de 15m.
    # --- SMAs ---
    data['sma_20'] = data['Close'].rolling(window=20).mean()
    data['sma_50'] = data['Close'].rolling(window=50).mean()
    # --- RSI ---
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0); loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=14 - 1, min_periods=14).mean()
    avg_loss = loss.ewm(com=14 - 1, min_periods=14).mean()
    data['rsi'] = 100 - (100 / (1 + (avg_gain / avg_loss)))
    # --- MACD ---
    ema_fast = data['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=26, adjust=False).mean()
    data['macd'] = ema_fast - ema_slow
    data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    data['macd_diff'] = data['macd'] - data['macd_signal']
    # --- Stochastic RSI ---
    rsi_series = data['rsi']
    min_rsi = rsi_series.rolling(window=14).min(); max_rsi = rsi_series.rolling(window=14).max()
    data['stochrsi'] = (rsi_series - min_rsi) / (max_rsi - min_rsi)
    # --- On-Balance Volume (OBV) ---
    data['obv'] = (data['Volume'] * (~data['Close'].diff().le(0) * 2 - 1)).cumsum()
    # --- Bollinger Bands Width ---
    sma_bb = data['Close'].rolling(window=20).mean()
    std_bb = data['Close'].rolling(window=20).std()
    upper_bb = sma_bb + (std_bb * 2); lower_bb = sma_bb - (std_bb * 2)
    data['bb_width'] = (upper_bb - lower_bb) / sma_bb
    # --- Average True Range (ATR) ---
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['atr'] = tr.ewm(alpha=1/14, adjust=False).mean()
    # --- Momentum ---
    data['momentum'] = data['Close'].diff(14)
    # --- Contexto --- (Se mantiene como placeholder, ya que es menos relevante en alta frecuencia)
    data["contexto_estrategia"] = 0

    print("✅ Indicadores técnicos calculados.")

    # --- PASO 3: Limpieza y Creación de la Variable Objetivo ---
    print("Paso 3: Limpiando NaNs y creando la variable objetivo (target)...")
    
    # La variable objetivo ahora predice si la *próxima vela de 15 minutos* subirá o bajará.
    price_diff = data['Close'].shift(-1) - data['Close']
    data['target'] = np.where(price_diff > 0, 1, 0) # Simplificado a 1 si sube, 0 si baja o es igual
    
    data.dropna(inplace=True)
    if data.empty:
        print("❌ Error: El DataFrame quedó vacío tras limpiar NaNs.")
        return

    print("✅ Distribución de clases (1: Sube, 0: Baja):")
    print(data['target'].value_counts(normalize=True))

    # --- PASO 4: Entrenamiento del Modelo ---
    features = [
        'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff',
        'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
    ]
    X = data[features]
    y = data['target']

    print("Paso 4: Configurando y ejecutando la búsqueda de hiperparámetros (GridSearchCV)...")
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Reducimos un poco la complejidad para un entrenamiento más rápido
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8, 0.9]
    }

    grid_search = GridSearchCV(
        estimator=XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42),
        param_grid=param_grid, cv=tscv, n_jobs=-1, verbose=1, scoring='accuracy'
    )
    grid_search.fit(X, y)
    model = grid_search.best_estimator_

    print("\n✅ Resultados de GridSearchCV:")
    print(f"🔍 Mejores parámetros encontrados: {grid_search.best_params_}")
    print(f"🎯 Mejor puntuación de validación cruzada (accuracy): {grid_search.best_score_:.4f}")

    # --- PASO 5: Evaluación y Guardado ---
    print("Paso 5: Evaluando y guardando el nuevo modelo de alta frecuencia...")
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/model.joblib")

    y_pred = model.predict(X)
    final_accuracy = accuracy_score(y, y_pred)
    print(f"✅ Precisión final sobre todo el dataset de entrenamiento: {final_accuracy:.4f}")
    
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_type': f'High-Frequency ({INTERVALO_VELAS})',
        'best_cv_accuracy': round(grid_search.best_score_, 4),
        'final_accuracy_on_full_data': round(final_accuracy, 4),
        'best_params': grid_search.best_params_
    }
    with open('training_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

    print("\n✅ ¡Entrenamiento del modelo de alta frecuencia completado! El archivo 'models/model.joblib' ha sido actualizado.")

if __name__ == '__main__':
    train_ia_model()