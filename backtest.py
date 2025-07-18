# backtest.py (Versión Final Definitiva - Anti-TypeError)

import pandas as pd
import numpy as np
import yfinance as yf
from joblib import load
import os

# --- PARÁMETROS SINCRONIZADOS ---
TICKER = 'BTC-USD'
PERIODO_DATOS = '60d'
INTERVALO_VELAS = '15m'
INITIAL_CAPITAL = 1000.0
FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff', 
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
]

def run_backtest():
    """
    Realiza un backtest utilizando el modelo de IA entrenado.
    """
    print("Iniciando backtest con el modelo de IA de alta frecuencia...")
    
    # --- 1. Cargar Modelo ---
    model_path = os.path.join("models", "model.joblib")
    if not os.path.exists(model_path):
        print("❌ Error: No se encontró 'models/model.joblib'.")
        return
    model = load(model_path)
    print("Modelo cargado exitosamente.")

    # --- 2. Descargar Datos ---
    print(f"Descargando datos para el backtest ({PERIODO_DATOS}, {INTERVALO_VELAS})...")
    data = yf.download(TICKER, period=PERIODO_DATOS, interval=INTERVALO_VELAS, auto_adjust=True, progress=False)
    if data.empty:
        print("❌ Error: No se pudieron descargar los datos.")
        return

    # --- 3. Calcular Features ---
    print("Calculando features para el backtest...")
    # (Lógica de cálculo idéntica a los otros scripts)
    data['sma_20'] = data['Close'].rolling(window=20).mean(); data['sma_50'] = data['Close'].rolling(window=50).mean()
    delta = data['Close'].diff(1); gain = delta.where(delta > 0, 0); loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean(); avg_loss = loss.ewm(com=13, min_periods=14).mean()
    data['rsi'] = 100 - (100 / (1 + (avg_gain / avg_loss)))
    ema_fast = data['Close'].ewm(span=12, adjust=False).mean(); ema_slow = data['Close'].ewm(span=26, adjust=False).mean()
    data['macd'] = ema_fast - ema_slow; data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    data['macd_diff'] = data['macd'] - data['macd_signal']
    rsi_series = data['rsi']; min_rsi = rsi_series.rolling(window=14).min(); max_rsi = rsi_series.rolling(window=14).max()
    data['stochrsi'] = (rsi_series - min_rsi) / (max_rsi - min_rsi)
    data['obv'] = (data['Volume'] * (~data['Close'].diff().le(0) * 2 - 1)).cumsum()
    sma_bb = data['Close'].rolling(window=20).mean(); std_bb = data['Close'].rolling(window=20).std()
    upper_bb = sma_bb + (std_bb * 2); lower_bb = sma_bb - (std_bb * 2)
    data['bb_width'] = (upper_bb - lower_bb) / sma_bb
    high_low = data['High'] - data['Low']; high_close = (data['High'] - data['Close'].shift()).abs(); low_close = (data['Low'] - data['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['atr'] = tr.ewm(alpha=1/14, adjust=False).mean()
    data['momentum'] = data['Close'].diff(14)
    data["contexto_estrategia"] = 0
    data.dropna(inplace=True)
    print("Features calculadas exitosamente.")

    # --- 4. Generar Predicciones ---
    X_backtest = data[FEATURES]
    data['prediction'] = model.predict(X_backtest)
    
    # --- 5. Simulación de Trading ---
    print("Simulando operaciones...")
    balance = float(INITIAL_CAPITAL) # Aseguramos que el balance inicial es un float
    position = 0.0
    in_position = False
    
    for i in range(len(data) - 1):
        # --- SOLUCIÓN AL TYPEERROR ---
        # Aseguramos que el precio que usamos para el cálculo es un float
        current_price = float(data['Close'].iloc[i])
        
        if data['prediction'].iloc[i] == 1 and not in_position:
            position = balance / current_price
            balance = 0.0
            in_position = True
        elif data['prediction'].iloc[i] == 0 and in_position:
            balance = position * current_price
            position = 0.0
            in_position = False
    
    if in_position:
        balance = position * float(data['Close'].iloc[-1])
        
    # --- 6. Resultados ---
    rentabilidad = ((balance - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
    print("\n--- RESULTADOS DEL BACKTEST (MODELO IA 15m) ---")
    print(f"Capital Inicial: ${INITIAL_CAPITAL:.2f}")
    print(f"Capital Final:   ${balance:.2f}")
    print(f"Rentabilidad:    {rentabilidad:.2f}%")
    print("Aviso: Este es un backtest sobre datos de entrenamiento y tiende a ser optimista.")
    print("--------------------------------------------------")

if __name__ == '__main__':
    run_backtest()