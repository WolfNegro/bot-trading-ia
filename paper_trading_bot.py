# paper_trading_bot.py (Versión Final con Triple Confirmación: Técnica + Social + Noticias)

import logging
import json
import os
from datetime import datetime
from decimal import Decimal

# --- Importamos NUESTROS TRES MÓDULOS DE INTELIGENCIA ---
from predict_live import get_prediction
from youtube_scraper.analizar_transcripciones import get_youtube_sentiment
from scripts.news_analyzer import get_news_sentiment # <-- ¡NUEVA IMPORTACIÓN!
from scripts.connect_binance import get_binance_client

# --- CONFIGURACIÓN DE RIESGO ---
STOP_LOSS_PERCENT = 1.5
TAKE_PROFIT_PERCENT = 3.0

# --- Configuración del Bot ---
PORTFOLIO_FILE = 'portfolio_state.json'
LOGS_DIR = 'logs'
TRADES_LOG_FILE = os.path.join(LOGS_DIR, 'paper_trades.log')
SYMBOL_ON_BINANCE = 'BTCUSDT'
VIRTUAL_USD_PER_TRADE = 20.0
MAX_TRADES = 50

# ... (El resto del código, desde la configuración de logging hasta la función execute_paper_sell, se mantiene exactamente igual. Pégalo aquí) ...

# --- Creación de directorios y configuración de Logging ---
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[logging.FileHandler(TRADES_LOG_FILE), logging.StreamHandler()])

def initialize_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        initial_state = {"cash_usd": 1000.0, "asset_holding": 0.0, "in_position": False, "total_trades": 0, "initial_value": 1000.0, "entry_price": 0.0, "stop_loss_price": 0.0, "take_profit_price": 0.0}
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
        logging.error(f"❌ No se pudo obtener el precio para {symbol}: {e}")
        return None

def execute_paper_buy(state, price):
    if state['cash_usd'] < VIRTUAL_USD_PER_TRADE:
        logging.warning("💰 Fondos virtuales insuficientes.")
        return state
    amount_to_buy = Decimal(VIRTUAL_USD_PER_TRADE) / price
    state['asset_holding'] = float(amount_to_buy)
    state['cash_usd'] -= VIRTUAL_USD_PER_TRADE
    state['in_position'] = True
    state['total_trades'] += 1
    state['entry_price'] = float(price)
    state['stop_loss_price'] = float(price * (Decimal(1) - Decimal(STOP_LOSS_PERCENT / 100)))
    state['take_profit_price'] = float(price * (Decimal(1) + Decimal(TAKE_PROFIT_PERCENT / 100)))
    logging.info(f"📈 COMPRA (simulada) de {float(amount_to_buy):.8f} {SYMBOL_ON_BINANCE.replace('USDT','')} a ${price:.2f}")
    logging.info(f"🛡️ GESTIÓN DE RIESGO: Stop-Loss fijado en ${state['stop_loss_price']:.2f}, Take-Profit en ${state['take_profit_price']:.2f}")
    return state

def execute_paper_sell(state, price, reason="Señal de Venta"):
    if not state['in_position']:
        return state
    value_of_sale = Decimal(state['asset_holding']) * price
    pnl = float(value_of_sale) - (state['asset_holding'] * state['entry_price'])
    state['cash_usd'] += float(value_of_sale)
    state['asset_holding'] = 0.0
    state['in_position'] = False
    state['entry_price'] = 0.0
    state['stop_loss_price'] = 0.0
    state['take_profit_price'] = 0.0
    logging.info(f"📉 VENTA ({reason}) a ${price:.2f}. P&L de la operación: ${pnl:.2f}")
    return state


def run_bot():
    """Función principal que ejecuta el ciclo del bot con lógica de triple confirmación."""
    logging.info("="*20 + " INICIANDO CICLO DEL BOT (IA 360°) " + "="*20)
    
    state = get_portfolio_state()
    
    # ... (Lógica de límite de trades y gestión de SL/TP se mantiene igual) ...

    # --- LÓGICA DE RECOPILACIÓN DE SEÑALES MEJORADA ---
    try:
        tech_prediction = get_prediction()
        youtube_sentiment = get_youtube_sentiment()
        news_sentiment = get_news_sentiment() # <-- ¡NUEVA SEÑAL!
    except Exception as e:
        logging.error(f"❌ Error crítico al obtener señales de IA: {e}")
        return

    client = get_binance_client(testnet=True)
    current_price = get_current_price(client, SYMBOL_ON_BINANCE)
    if not current_price:
        logging.error("❌ Abortando ciclo: no se pudo obtener precio.")
        return
        
    sentiment_map = {1: "BULLISH", -1: "BEARISH", 0: "NEUTRAL"}
    
    logging.info(f"📊 Estado actual: En posición: {state['in_position']}, Trades: {state['total_trades']}/{MAX_TRADES}")
    logging.info(f"🧠 Señal Técnica (Modelo): {'COMPRA' if tech_prediction == 1 else 'VENTA'} ({tech_prediction})")
    logging.info(f"📺 Señal Social (YouTube): {sentiment_map.get(youtube_sentiment, 'N/A')} ({youtube_sentiment})")
    logging.info(f"📰 Señal Fundamental (Noticias): {sentiment_map.get(news_sentiment, 'N/A')} ({news_sentiment})")
    logging.info(f"📈 Precio actual de {SYMBOL_ON_BINANCE}: ${current_price:.2f}")

    # --- LÓGICA DE DECISIÓN DE TRIPLE CONFIRMACIÓN ---
    if tech_prediction == 1 and youtube_sentiment == 1 and news_sentiment != -1 and not state['in_position']:
        # Compramos si la señal técnica y social son positivas, y las noticias NO son negativas.
        logging.info("✅ TRIPLE CONFIRMACIÓN POSITIVA. Ejecutando COMPRA.")
        new_state = execute_paper_buy(state, current_price)
        save_portfolio_state(new_state)
    
    else:
        logging.info("⏸️ No se cumplen las condiciones para una nueva entrada.")

    logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")


if __name__ == '__main__':
    # ... (el if __name__ == '__main__': se mantiene igual)
    initialize_portfolio()
    run_bot()