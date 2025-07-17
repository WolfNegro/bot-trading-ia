# paper_trading_bot.py (Versión con Lógica de Veto)

import logging
import json
import os
from datetime import datetime
from decimal import Decimal

# --- Importamos nuestros tres módulos de inteligencia ---
from predict_live import get_prediction
from youtube_scraper.analizar_transcripciones import get_youtube_sentiment
from scripts.news_analyzer import get_news_sentiment
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

# --- Creación de directorios y configuración de Logging ---
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

# --- Funciones de Gestión de Portafolio (sin cambios) ---
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
    # ... (esta función se mantiene igual)
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
    # ... (esta función se mantiene igual)
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
    """Función principal que ejecuta el ciclo del bot con la Lógica de Veto."""
    logging.info("="*20 + " INICIANDO CICLO DEL BOT (LÓGICA DE VETO) " + "="*20)
    
    state = get_portfolio_state()
    
    # ... (La lógica de límite de trades se mantiene igual)
    if state['total_trades'] >= MAX_TRADES:
        logging.info("🏁 Límite de operaciones alcanzado.")
        return

    client = get_binance_client(testnet=True)
    current_price = get_current_price(client, SYMBOL_ON_BINANCE)
    if not current_price:
        logging.error("❌ Abortando ciclo: no se pudo obtener precio.")
        return

    # La lógica de gestión de SL/TP se mantiene y es la prioridad número 1
    if state['in_position']:
        logging.info(f"🔎 En posición. Precio actual: ${current_price:.2f}. SL: ${state['stop_loss_price']:.2f}, TP: ${state['take_profit_price']:.2f}")
        if current_price <= Decimal(state['stop_loss_price']):
            logging.warning("🔥 STOP-LOSS ALCANZADO. Ejecutando venta forzosa.")
            new_state = execute_paper_sell(state, current_price, reason="Stop-Loss")
            save_portfolio_state(new_state)
            logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")
            return
            
        elif current_price >= Decimal(state['take_profit_price']):
            logging.info("🎉 TAKE-PROFIT ALCANZADO. Asegurando ganancias.")
            new_state = execute_paper_sell(state, current_price, reason="Take-Profit")
            save_portfolio_state(new_state)
            logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")
            return
            
    # Si no salimos por SL/TP, buscamos una nueva señal de entrada
    logging.info("Buscando nueva señal de entrada...")
    try:
        tech_prediction = get_prediction()
        youtube_sentiment = get_youtube_sentiment()
        news_sentiment = get_news_sentiment()
    except Exception as e:
        logging.error(f"❌ Error crítico al obtener señales de IA: {e}")
        return
        
    sentiment_map = {1: "BULLISH", -1: "BEARISH", 0: "NEUTRAL"}
    logging.info(f"🧠 Señal Técnica (Modelo): {'COMPRA' if tech_prediction == 1 else 'VENTA'} ({tech_prediction})")
    logging.info(f"📺 Señal Social (YouTube): {sentiment_map.get(youtube_sentiment, 'N/A')} ({youtube_sentiment})")
    logging.info(f"📰 Señal Fundamental (Noticias): {sentiment_map.get(news_sentiment, 'N/A')} ({news_sentiment})")

    # --- LÓGICA DE DECISIÓN (SISTEMA DE VETO) ---
    # La lógica de VENTA para cerrar la posición ahora es manejada por SL/TP,
    # por lo que nos enfocamos exclusivamente en las condiciones de ENTRADA.
    
    # Condición de Compra:
    # 1. La predicción técnica debe ser de COMPRA.
    # 2. El sentimiento de YouTube debe ser de COMPRA.
    # 3. Las noticias NO deben ser explícitamente negativas (actúan como veto).
    # 4. No debemos tener ya una posición abierta.
    if tech_prediction == 1 and youtube_sentiment == 1 and news_sentiment != -1 and not state['in_position']:
        logging.info("✅ SEÑALES ALINEADAS (Técnica + Social) Y SIN VETO DE NOTICIAS. Ejecutando COMPRA.")
        new_state = execute_paper_buy(state, current_price)
        save_portfolio_state(new_state)
    else:
        # Imprimimos una razón más clara de por qué no se operó
        reason = []
        if tech_prediction != 1: reason.append("Técnica no es COMPRA")
        if youtube_sentiment != 1: reason.append("Social no es BULLISH")
        if news_sentiment == -1: reason.append("Noticias negativas (VETO)")
        if state['in_position']: reason.append("Ya estamos en una posición")
        
        logging.info(f"⏸️ No se cumplen las condiciones para una nueva entrada. Razones: {', '.join(reason)}")

    logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")

if __name__ == '__main__':
    initialize_portfolio()
    run_bot()