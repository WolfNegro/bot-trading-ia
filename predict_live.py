# predict_live.py (Versión Corregida)

import yfinance as yf
import pandas as pd
from joblib import load
import logging
import os

# --- Parámetros de descarga (Sincronizados con train_model.py) ---
SYMBOL = "BTC-USD"
PERIOD = "1y" 
INTERVAL = "1d" 

# --- Parámetros de indicadores (Sincronizados con train_model.py) ---
SMA_SHORT = 20
SMA_LONG = 50
RSI_WINDOW = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
STOCH_RSI_WINDOW = 14
BB_WINDOW = 20
ATR_WINDOW = 14
MOMENTUM_WINDOW = 14

# --- Lista de Features (Debe ser idéntica a la del entrenamiento) ---
FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff', 
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
]

# --- Ruta del Modelo ---
MODEL_PATH = os.path.join("models", "model.joblib")


def get_prediction():
    """
    Ejecuta el pipeline completo de obtención de datos, cálculo de features y
    predicción del modelo para obtener una señal de trading.

    Returns:
        int: La predicción del modelo (1 para COMPRA, 0 para VENTA).

    Raises:
        FileNotFoundError: Si no se encuentra el archivo del modelo.
        ConnectionError: Si falla la descarga de datos de yfinance.
        ValueError: Si el DataFrame queda vacío tras la limpieza.
    """
    logging.info(f"📥 [Predicción] Descargando datos para {SYMBOL}...")
    
    # 1. DESCARGA DE DATOS (LÍNEA CORREGIDA)
    df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True, progress=False)
    if df.empty:
        logging.error("❌ [Predicción] No se pudieron descargar datos.")
        raise ConnectionError("Fallo en la descarga de datos desde yfinance.")

    # 2. CÁLCULO DE FEATURES
    logging.info("⚙️ [Predicción] Calculando features técnicas...")
    # --- SMAs ---
    df['sma_20'] = df['Close'].rolling(window=SMA_SHORT).mean()
    df['sma_50'] = df['Close'].rolling(window=SMA_LONG).mean()
    # --- RSI ---
    delta = df['Close'].diff(1)
    gain = delta.where(delta > 0, 0); loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=RSI_WINDOW - 1, min_periods=RSI_WINDOW).mean()
    avg_loss = loss.ewm(com=RSI_WINDOW - 1, min_periods=RSI_WINDOW).mean()
    df['rsi'] = 100 - (100 / (1 + (avg_gain / avg_loss)))
    # --- MACD ---
    ema_fast = df['Close'].ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=MACD_SLOW, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df['macd_diff'] = df['macd'] - df['macd_signal']
    # --- Stochastic RSI ---
    rsi_series = df['rsi']
    min_rsi = rsi_series.rolling(window=STOCH_RSI_WINDOW).min()
    max_rsi = rsi_series.rolling(window=STOCH_RSI_WINDOW).max()
    df['stochrsi'] = (rsi_series - min_rsi) / (max_rsi - min_rsi)
    # --- On-Balance Volume (OBV) ---
    df['obv'] = (df['Volume'] * (~df['Close'].diff().le(0) * 2 - 1)).cumsum()
    # --- Bollinger Bands Width ---
    sma_bb = df['Close'].rolling(window=BB_WINDOW).mean()
    std_bb = df['Close'].rolling(window=BB_WINDOW).std()
    upper_bb = sma_bb + (std_bb * 2); lower_bb = sma_bb - (std_bb * 2)
    df['bb_width'] = (upper_bb - lower_bb) / sma_bb
    # --- Average True Range (ATR) ---
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.ewm(alpha=1/ATR_WINDOW, adjust=False).mean()
    # --- Momentum ---
    df['momentum'] = df['Close'].diff(MOMENTUM_WINDOW)
    # --- Contexto Estrategia ---
    df['contexto_estrategia'] = 0.0

    # 3. LIMPIEZA Y PREPARACIÓN
    df.dropna(inplace=True)
    if df.empty:
        logging.error("❌ [Predicción] DataFrame vacío después de la limpieza. Aumentar el período de descarga podría ayudar.")
        raise ValueError("DataFrame vacío después de limpiar NaNs en el módulo de predicción.")

    X = df[FEATURES]
    
    # 4. CARGA DEL MODELO
    if not os.path.exists(MODEL_PATH):
        logging.error(f"❌ [Predicción] No se encontró el modelo en '{MODEL_PATH}'.")
        raise FileNotFoundError(f"El archivo del modelo no se encuentra en {MODEL_PATH}")
    
    model = load(MODEL_PATH)
    
    # 5. PREDICCIÓN
    latest_data = X.tail(1)
    prediction = model.predict(latest_data)[0]
    
    logging.info(f"🤖 [Predicción] El modelo predice la clase: {prediction}")
    return int(prediction)


# Este bloque permite ejecutar el script directamente para hacer una prueba rápida.
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("--- Ejecutando predict_live.py en modo de prueba ---")
    try:
        final_signal = get_prediction()
        if final_signal == 1:
            print("\n✅ RESULTADO: SEÑAL DE COMPRA")
        else:
            print("\n✅ RESULTADO: SEÑAL DE VENTA")
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la prueba: {e}")