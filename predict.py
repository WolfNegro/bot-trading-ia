# predict.py (Versión Final Sincronizada con el modelo de 15m)

import yfinance as yf
import pandas as pd
from joblib import load
import logging
import os

# --- PARÁMETROS SINCRONIZADOS CON EL MODELO DE ALTA FRECUENCIA ---
# Estos parámetros deben ser idénticos a los usados en train_model.py y predict_live.py
SYMBOL = "BTC-USD"
PERIOD = "7d"
INTERVAL = "15m"

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

FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff', 
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
]

MODEL_PATH = os.path.join("models", "model.joblib")

def main_predict():
    """
    Función principal que ejecuta una única predicción para el pipeline de entrenamiento.
    """
    try:
        # --- 1. Cargar el Modelo ---
        print(f"Cargando modelo desde: {MODEL_PATH}")
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"No se encontró el modelo en '{MODEL_PATH}'. Ejecuta 'train_model.py' primero.")
        model = load(MODEL_PATH)
        print("Modelo cargado exitosamente.")

        # --- 2. Descargar Datos Recientes ---
        print(f"Descargando datos recientes para {SYMBOL} (Intervalo: {INTERVAL})...")
        df = yf.download(SYMBOL, period=PERIOD, interval=INTERVAL, auto_adjust=True, progress=False)
        if df.empty:
            raise ValueError("No se pudieron descargar datos.")
        print("Datos descargados correctamente.")

        # --- 3. Calcular Features ---
        print("Calculando features para la predicción...")
        # (Lógica de cálculo idéntica a train_model.py y predict_live.py)
        df['sma_20'] = df['Close'].rolling(window=SMA_SHORT).mean()
        df['sma_50'] = df['Close'].rolling(window=SMA_LONG).mean()
        delta = df['Close'].diff(1)
        gain = delta.where(delta > 0, 0); loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(com=RSI_WINDOW - 1, min_periods=RSI_WINDOW).mean()
        avg_loss = loss.ewm(com=RSI_WINDOW - 1, min_periods=RSI_WINDOW).mean()
        df['rsi'] = 100 - (100 / (1 + (avg_gain / avg_loss)))
        ema_fast = df['Close'].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=MACD_SLOW, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        df['macd_diff'] = df['macd'] - df['macd_signal']
        rsi_series = df['rsi']
        min_rsi = rsi_series.rolling(window=STOCH_RSI_WINDOW).min()
        max_rsi = rsi_series.rolling(window=STOCH_RSI_WINDOW).max()
        df['stochrsi'] = (rsi_series - min_rsi) / (max_rsi - min_rsi)
        df['obv'] = (df['Volume'] * (~df['Close'].diff().le(0) * 2 - 1)).cumsum()
        sma_bb = df['Close'].rolling(window=BB_WINDOW).mean()
        std_bb = df['Close'].rolling(window=BB_WINDOW).std()
        upper_bb = sma_bb + (std_bb * 2); lower_bb = sma_bb - (std_bb * 2)
        df['bb_width'] = (upper_bb - lower_bb) / sma_bb
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(alpha=1/ATR_WINDOW, adjust=False).mean()
        df['momentum'] = df['Close'].diff(MOMENTUM_WINDOW)
        df['contexto_estrategia'] = 0.0
        df.dropna(inplace=True)

        # --- 4. Generar Predicción ---
        print("Generando predicción...")
        X_predict = df[FEATURES].tail(1)
        prediction = model.predict(X_predict)[0]
        
        # --- 5. Mostrar Resultado ---
        print("\n--- PREDICCIÓN PARA LA PRÓXIMA VELA DE 15 MINUTOS ---")
        if prediction == 1:
            print("Resultado: 📈 COMPRA")
        else:
            print("Resultado: 📉 VENTA")
        print("--------------------------------------------------")

    except Exception as e:
        print(f"Ocurrió un error durante la predicción: {e}")

if __name__ == '__main__':
    main_predict()