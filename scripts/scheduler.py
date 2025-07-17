# scripts/real_time_bot.py
# Este script ejecuta el bot de trading en tiempo real. Carga el modelo
# entrenado, descarga los datos más recientes, calcula los indicadores,
# realiza una predicción y ejecuta/registra operaciones.

import os
import time
import pandas as pd
import yfinance as yf
import ta
import joblib
from datetime import datetime

# --- Configuración de Rutas y Constantes ---
MODELS_DIR = 'models'
LOGS_DIR = 'logs'
DATA_DIR = 'data'
MODEL_PATH = os.path.join(MODELS_DIR, 'model.joblib')
LOG_FILE_PATH = os.path.join(LOGS_DIR, 'trades.log')
DATA_FILE_PATH = os.path.join(DATA_DIR, 'btc_data.csv')
FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff',
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum'
]

# --- Estado del Bot (simulado en memoria) ---
# En un sistema real, esto estaría en una base de datos o un archivo de estado.
bot_state = {
    "capital": 1000.0,
    "position_open": False,
    "btc_amount": 0.0
}

def setup_environment():
    """Asegura que los directorios necesarios existan."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def load_prediction_model():
    """Carga el modelo de IA entrenado desde el archivo."""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Modelo no encontrado en '{MODEL_PATH}'.")
        print("Por favor, ejecuta 'train_model.py' primero.")
        return None
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Modelo de IA cargado exitosamente.")
        return model
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")
        return None

def fetch_and_prepare_data():
    """Descarga datos recientes y calcula todos los indicadores necesarios."""
    print("Descargando datos recientes (48h, intervalo 15min)...")
    try:
        # Se necesita un período mayor para calcular indicadores como SMA50
        data = yf.download('BTC-USD', period='5d', interval='15m', auto_adjust=True, progress=False)
        if data.empty:
            print("⚠️ No se pudieron descargar datos.")
            return None

        # Saneamiento de entradas para la librería 'ta'
        close = pd.Series(data['Close'].values.flatten(), index=data.index)
        high = pd.Series(data['High'].values.flatten(), index=data.index)
        low = pd.Series(data['Low'].values.flatten(), index=data.index)
        volume = pd.Series(data['Volume'].values.flatten(), index=data.index)

        # Cálculo de todos los indicadores usados en el entrenamiento
        data['sma_20'] = ta.trend.SMAIndicator(close=close, window=20).sma_indicator()
        data['sma_50'] = ta.trend.SMAIndicator(close=close, window=50).sma_indicator()
        data['rsi'] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        macd = ta.trend.MACD(close=close)
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()
        data['macd_diff'] = macd.macd_diff()
        data['stochrsi'] = ta.momentum.StochRSIIndicator(close=close, window=14).stochrsi()
        data['obv'] = ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        data['bb_width'] = ta.volatility.BollingerBands(close=close, window=20).bollinger_wband()
        data['atr'] = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        data['momentum'] = close - close.shift(14)
        
        data.dropna(inplace=True)
        print("Indicadores calculados y datos limpios.")
        
        # Guardar los datos procesados en CSV
        data.to_csv(DATA_FILE_PATH)
        print(f"Datos guardados en '{DATA_FILE_PATH}'.")

        return data
    except Exception as e:
        print(f"❌ Error durante la obtención o preparación de datos: {e}")
        return None

def execute_trade_logic(model, data):
    """Toma la decisión de trading basada en la última predicción del modelo."""
    if data.empty:
        print("No hay datos para procesar, saltando ciclo de trading.")
        return

    latest_features = data[FEATURES].tail(1)
    
    # Predecir: 1 = Sube (BUY), 0 = Baja (SELL)
    prediction = model.predict(latest_features)[0]
    latest_price = data['Close'].iloc[-1]
    
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time_str}] Precio actual: ${latest_price:,.2f}. Predicción del modelo: {prediction} (1=BUY, 0=SELL)")

    # Lógica de Compra
    if prediction == 1 and not bot_state['position_open']:
        bot_state['btc_amount'] = bot_state['capital'] / latest_price
        bot_state['position_open'] = True
        balance_after_trade = bot_state['btc_amount'] * latest_price
        log_trade('BUY', latest_price, balance_after_trade)
        bot_state['capital'] = 0.0 # El capital está ahora en BTC
    
    # Lógica de Venta
    elif prediction == 0 and bot_state['position_open']:
        bot_state['capital'] = bot_state['btc_amount'] * latest_price
        bot_state['position_open'] = False
        balance_after_trade = bot_state['capital']
        log_trade('SELL', latest_price, balance_after_trade)
        bot_state['btc_amount'] = 0.0
    else:
        action = "MANTENER"
        if prediction == 1:
            action += " (ya en posición)"
        else:
            action += " (no en posición)"
        print(f"Acción: {action}")

def log_trade(action, price, balance):
    """Registra una operación en el archivo de logs."""
    timestamp = datetime.now().strftime('%Y-%m-%d')
    log_message = f"Fecha: {timestamp}, Acción: {action}, Precio: ${price:.2f}, Saldo tras op: ${balance:.2f}\n"
    
    print(f"🟢 EJECUTANDO ORDEN: {action} a ${price:,.2f}")
    
    with open(LOG_FILE_PATH, 'a') as f:
        f.write(log_message)
    print(f"Operación registrada en '{LOG_FILE_PATH}'.")


if __name__ == "__main__":
    setup_environment()
    model = load_prediction_model()
    
    if model:
        while True:
            print("\n" + "="*50)
            print(f"Iniciando nuevo ciclo de bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Estado actual: Capital=${bot_state['capital']:,.2f}, Posición Abierta={bot_state['position_open']}, BTC={bot_state['btc_amount']:.6f}")
            
            processed_data = fetch_and_prepare_data()
            if processed_data is not None and not processed_data.empty:
                execute_trade_logic(model, processed_data)
            
            print("Ciclo finalizado. Esperando 15 minutos...")
            print("="*50 + "\n")
            time.sleep(900) # 15 minutos
    else:
        print("Bot no pudo iniciar debido a un error con el modelo.")