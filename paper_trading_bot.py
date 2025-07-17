# paper_trading_bot.py (Versión Final con Fusión de Señales)

import logging
import json
import os
from datetime import datetime
from decimal import Decimal

# --- Importamos NUESTROS DOS MÓDULOS DE INTELIGENCIA ---
from predict_live import get_prediction
from youtube_scraper.analizar_transcripciones import get_youtube_sentiment # <-- ¡NUEVA IMPORTACIÓN!
from scripts.connect_binance import get_binance_client

# --- Configuración del Bot (sin cambios) ---
PORTFOLIO_FILE = 'portfolio_state.json'
LOGS_DIR = 'logs'
TRADES_LOG_FILE = os.path.join(LOGS_DIR, 'paper_trades.log')
SYMBOL_ON_BINANCE = 'BTCUSDT'
VIRTUAL_USD_PER_TRADE = 20.0
MAX_TRADES = 50

# --- Creación de directorios y configuración de Logging (sin cambios) ---
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(TRADES_LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Todas las funciones de gestión de portafolio (initialize, get, save, get_price, etc.) se mantienen igual ---
def initialize_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        initial_state = {"cash_usd": 1000.0, "asset_holding": 0.0, "in_position": False, "total_trades": 0, "initial_value": 1000.0}
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(initial_state, f, indent=4)
        logging.info(f"💼 Portafolio virtual inicializado con ${initial_state['cash_usd']} USD.")

def get_portfolio_state():
    with open(PORTFOLIO_FILE, 'r') as f:
        return json.load(f)

def save_portfolio_state(state):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def get_current_price(client, symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return Decimal(ticker['price'])
    except Exception as e:
        logging.error(f"❌ No se pudo obtener el precio para {symbol} desde Binance: {e}")
        return None

def execute_paper_buy(state, price):
    if state['cash_usd'] < VIRTUAL_USD_PER_TRADE:
        logging.warning("💰 Fondos virtuales insuficientes para ejecutar la compra.")
        return state
    amount_to_buy = Decimal(VIRTUAL_USD_PER_TRADE) / price
    state['asset_holding'] += float(amount_to_buy)
    state['cash_usd'] -= VIRTUAL_USD_PER_TRADE
    state['in_position'] = True
    state['total_trades'] += 1
    logging.info(f"📈 COMPRA (simulada) de {float(amount_to_buy):.8f} {SYMBOL_ON_BINANCE.replace('USDT','')} a ${price:.2f}")
    return state

def execute_paper_sell(state, price):
    if not state['in_position'] or state['asset_holding'] == 0:
        logging.warning("❌ Intento de venta sin tener una posición abierta. No se hace nada.")
        return state
    value_of_sale = Decimal(state['asset_holding']) * price
    asset_sold = state['asset_holding']
    state['cash_usd'] += float(value_of_sale)
    state['asset_holding'] = 0.0
    state['in_position'] = False
    logging.info(f"📉 VENTA (simulada) de {asset_sold:.8f} {SYMBOL_ON_BINANCE.replace('USDT','')} a ${price:.2f}. Valor total: ${float(value_of_sale):.2f}")
    return state


def run_bot():
    """Función principal que ejecuta el ciclo del bot de paper trading con lógica de fusión."""
    logging.info("="*20 + " INICIANDO CICLO DEL BOT CON IA MEJORADA " + "="*20)
    
    state = get_portfolio_state()

    if state['total_trades'] >= MAX_TRADES:
        logging.info(f"🏁 Límite de {MAX_TRADES} operaciones alcanzado. El bot se detiene.")
        # ... (lógica de P&L final sin cambios)
        return

    # --- NUEVA LÓGICA DE RECOPILACIÓN DE SEÑALES ---
    try:
        # 1. Obtener la predicción técnica de la IA
        tech_prediction = get_prediction()
        # 2. Obtener la señal de sentimiento de YouTube
        youtube_sentiment = get_youtube_sentiment()
    except Exception as e:
        logging.error(f"❌ Error crítico al obtener señales de IA: {e}")
        return
        
    client = get_binance_client(testnet=True)
    current_price = get_current_price(client, SYMBOL_ON_BINANCE)
    if not current_price:
        logging.error("❌ No se pudo obtener el precio actual. Abortando ciclo.")
        return

    # Mapeo de sentimiento para logs más claros
    sentiment_map = {1: "BULLISH", -1: "BEARISH", 0: "NEUTRAL"}
    
    logging.info(f"📊 Estado actual: En posición: {state['in_position']}, Trades: {state['total_trades']}/{MAX_TRADES}, Efectivo: ${state['cash_usd']:.2f}")
    logging.info(f"🧠 Señal Técnica (Modelo): {'COMPRA' if tech_prediction == 1 else 'VENTA'} ({tech_prediction})")
    logging.info(f"📺 Señal de Sentimiento (YouTube): {sentiment_map.get(youtube_sentiment, 'DESCONOCIDO')} ({youtube_sentiment})")
    logging.info(f"📈 Precio actual de {SYMBOL_ON_BINANCE}: ${current_price:.2f}")

    # --- LÓGICA DE DECISIÓN DE ALTA CONVICCIÓN ---
    if tech_prediction == 1 and youtube_sentiment == 1 and not state['in_position']:
        # SÓLO COMPRAMOS SI AMBAS SEÑALES SON ALCISTAS Y NO ESTAMOS EN UNA POSICIÓN
        logging.info("✅ CONFIRMACIÓN DOBLE: Técnica + YouTube. Ejecutando COMPRA.")
        new_state = execute_paper_buy(state, current_price)
        save_portfolio_state(new_state)
    
    elif tech_prediction == 0 and youtube_sentiment == -1 and state['in_position']:
        # SÓLO VENDEMOS SI AMBAS SEÑALES SON BAJISTAS Y SÍ ESTAMOS EN UNA POSICIÓN
        logging.info("🛑 CONFIRMACIÓN DOBLE: Técnica + YouTube. Ejecutando VENTA.")
        new_state = execute_paper_sell(state, current_price)
        save_portfolio_state(new_state)
        
    else:
        # Si las señales no coinciden o la condición de posición no es la adecuada, no hacemos nada.
        logging.info("⏸️ SEÑALES NO ALINEADAS o condición no cumplida. No se opera.")

    logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")


if __name__ == '__main__':
    initialize_portfolio()
    run_bot()