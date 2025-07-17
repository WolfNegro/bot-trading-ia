# predict_live.py (Versión Sincronizada con el Modelo de Alta Frecuencia)

import yfinance as yf
import pandas as pd
from joblib import load
import logging
import os

# --- PARÁMETROS SINCRONIZADOS CON EL NUEVO MODELO DE 15 MINUTOS ---
SYMBOL = "BTC-USD"
# Usamos '7d' para tener suficientes datos para los indicadores (SMA de 50, etc.)
# pero sin descargar datos innecesarios en cada ejecución.
PERIOD = "7d" 
# ¡CRÍTICO! El intervalo debe ser el mismo que en el entrenamiento.
INTERVAL = "15m" 

# Los parámetros de los indicadores son los mismos que en el entrenamiento.
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

# La lista de features debe ser idéntica.
FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff', 
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
]

# La ruta del modelo no cambia.
MODEL_PATH = os.path.join("models", "model.joblib")


def get_prediction():
    """
    Obtiene la predicción del modelo de ALTA FRECUENCIA para la vela más reciente.
    """
    logging.info(f"📥 [Predicción AF] Descargando datos para {SYMBOL} (Intervalo: {INTERVAL})...")
    
    # 1. DESCARGA DE DATOS
    df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True, progress=False)
    if df.empty:
        logging.error("❌ [Predicción AF] No se pudieron descargar datos.")
        raise ConnectionError("Fallo en la descarga de datos desde yfinance.")

    # 2. CÁLCULO DE FEATURES (Lógica idéntica al entrenamiento)
    logging.info("⚙️ [Predicción AF] Calculando features técnicas...")
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
        raise ValueError("DataFrame vacío después de limpiar NaNs en el módulo de predicción.")

    X = df[FEATURES]
    
    # 4. CARGA Y PREDICCIÓN
    model = load(MODEL_PATH)
    latest_data = X.tail(1)
    prediction = model.predict(latest_data)[0]
    
    logging.info(f"🤖 [Predicción AF] El modelo predice la clase para la próxima vela de 15m: {prediction}")
    return int(prediction)


# Este bloque permite ejecutar el script directamente para hacer una prueba rápida.
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("--- Ejecutando predict_live.py (Modo Alta Frecuencia) en modo de prueba ---")
    try:
        final_signal = get_prediction()
        if final_signal == 1:
            print("\n✅ RESULTADO: SEÑAL DE COMPRA")
        else:
            print("\n✅ RESULTADO: SEÑAL DE VENTA")
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la prueba: {e}")