# scripts/real_time_bot.py

import os
import time
import pandas as pd
import yfinance as yf
import ta
import joblib
from datetime import datetime
from dotenv import load_dotenv
from binance.client import Client

# --- Configuración ---
load_dotenv()
USE_BINANCE = True  # 🔁 Cambia a False para simular sin operar

# Conexión Binance
if USE_BINANCE:
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    client = Client(api_key, api_secret)

# --- Rutas y Constantes ---
MODELS_DIR = 'models'
LOGS_DIR = 'logs'
DATA_DIR = 'data'
MODEL_PATH = os.path.join(MODELS_DIR, 'model.joblib')
LOG_FILE_PATH = os.path.join(LOGS_DIR, 'trades.log')
DATA_FILE_PATH = os.path.join(DATA_DIR, 'btc_data.csv')
SYMBOL = "BTCUSDT"
FEATURES = [
    'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff',
    'stochrsi', 'obv', 'bb_width', 'atr', 'momentum'
]

bot_state = {
    "capital": 1000.0,
    "position_open": False,
    "btc_amount": 0.0
}

def setup_environment():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def load_prediction_model():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Modelo no encontrado en '{MODEL_PATH}'.")
        return None
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Modelo de IA cargado exitosamente.")
        return model
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")
        return None

def fetch_and_prepare_data():
    print("Descargando datos recientes (5 días, 15min)...")
    try:
        data = yf.download('BTC-USD', period='5d', interval='15m', auto_adjust=True, progress=False)
        if data.empty:
            return None

        close = data['Close'].astype(float)
        high = data['High'].astype(float)
        low = data['Low'].astype(float)
        volume = data['Volume'].astype(float)

        data['sma_20'] = ta.trend.SMAIndicator(close, 20).sma_indicator()
        data['sma_50'] = ta.trend.SMAIndicator(close, 50).sma_indicator()
        data['rsi'] = ta.momentum.RSIIndicator(close).rsi()
        macd = ta.trend.MACD(close)
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()
        data['macd_diff'] = macd.macd_diff()
        data['stochrsi'] = ta.momentum.StochRSIIndicator(close).stochrsi()
        data['obv'] = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        bb = ta.volatility.BollingerBands(close)
        data['bb_width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        data['atr'] = ta.volatility.AverageTrueRange(high, low, close).average_true_range()
        data['momentum'] = close - close.shift(14)

        data.dropna(inplace=True)
        data.to_csv(DATA_FILE_PATH)

        print("✅ Indicadores calculados.")
        return data
    except Exception as e:
        print(f"❌ Error al preparar datos: {e}")
        return None

def execute_trade_logic(model, data):
    if data.empty:
        print("⚠️ No hay datos para procesar.")
        return

    features = data[FEATURES].tail(1)
    prediction = model.predict(features)[0]
    price = float(data['Close'].iloc[-1])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"[{now}] Precio: ${price:,.2f} | Predicción: {prediction} (1=BUY, 0=SELL)")

    if prediction == 1 and not bot_state['position_open']:
        btc = bot_state['capital'] / price
        if USE_BINANCE:
            try:
                order = client.order_market_buy(symbol=SYMBOL, quoteOrderQty=bot_state['capital'])
                print("🟢 ORDEN DE COMPRA REAL enviada a Binance.")
            except Exception as e:
                print(f"❌ Falló la orden BUY: {e}")
                return
        bot_state.update({"btc_amount": btc, "position_open": True, "capital": 0.0})
        log_trade("BUY", price, btc * price)

    elif prediction == 0 and bot_state['position_open']:
        usdt = bot_state['btc_amount'] * price
        if USE_BINANCE:
            try:
                order = client.order_market_sell(symbol=SYMBOL, quantity=round(bot_state['btc_amount'], 6))
                print("🔴 ORDEN DE VENTA REAL enviada a Binance.")
            except Exception as e:
                print(f"❌ Falló la orden SELL: {e}")
                return
        bot_state.update({"capital": usdt, "position_open": False, "btc_amount": 0.0})
        log_trade("SELL", price, usdt)
    else:
        print("⏸ MANTENER (sin cambio de posición)")

def log_trade(action, price, balance):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Fecha: {ts}, Acción: {action}, Precio: ${price:,.2f}, Saldo tras op: ${balance:,.2f}\n"
    with open(LOG_FILE_PATH, 'a') as f:
        f.write(msg)
    print(msg.strip())

# --- Bucle principal ---
if __name__ == "__main__":
    setup_environment()
    model = load_prediction_model()

    if model:
        while True:
            try:
                print("\n" + "="*50)
                print(f"Iniciando ciclo - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Estado: Capital=${bot_state['capital']:,.2f}, BTC={bot_state['btc_amount']:.6f}, Posición={bot_state['position_open']}")

                data = fetch_and_prepare_data()
                if data is not None:
                    execute_trade_logic(model, data)

                print("Ciclo completo. Esperando 15 minutos...")
                print("="*50)
                time.sleep(900)
            except KeyboardInterrupt:
                print("\n🛑 Bot detenido por usuario.")
                break
            except Exception as e:
                print(f"❌ Error en el ciclo principal: {e}")
                time.sleep(60)
    else:
        print("⚠️ El modelo no pudo cargarse. Bot abortado.")
