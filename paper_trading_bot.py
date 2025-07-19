# paper_trading_bot.py (Versión 3.1 - Estrategia de Confluencia Total)

import logging
import json
import os
import sys
import asyncio
from datetime import datetime
from decimal import Decimal

# --- Añadir la raíz del proyecto al path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# --- Importamos NUESTROS módulos ---
from predict_live import get_prediction
from scripts.intelligence_aggregator import get_all_sentiment_signals # <-- NUEVO RECOLECTOR
from scripts.connect_binance import get_binance_client
from scripts.notifier import send_telegram_message, format_buy_message, format_sell_message

# --- ARCHIVO DE BLOQUEO ---
LOCK_FILE = 'bot.lock'

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

# --- Configuración de Logging ---
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[logging.FileHandler(TRADES_LOG_FILE), logging.StreamHandler()])

# --- Funciones de Gestión de Portafolio (Sin cambios) ---
def initialize_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        initial_state = {"cash_usd": 1000.0, "asset_holding": 0.0, "in_position": False, "total_trades": 0, "initial_value": 1000.0, "entry_price": 0.0, "stop_loss_price": 0.0, "take_profit_price": 0.0}
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(initial_state, f, indent=4)
        logging.info(f"💼 Portafolio virtual inicializado.")

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

async def execute_paper_buy(state, price):
    amount_to_buy = Decimal(VIRTUAL_USD_PER_TRADE) / price
    state['asset_holding'] = float(amount_to_buy)
    state['cash_usd'] -= VIRTUAL_USD_PER_TRADE
    state['in_position'] = True
    state['total_trades'] += 1
    state['entry_price'] = float(price)
    state['stop_loss_price'] = float(price * (Decimal(1) - Decimal(STOP_LOSS_PERCENT / 100)))
    state['take_profit_price'] = float(price * (Decimal(1) + Decimal(TAKE_PROFIT_PERCENT / 100)))
    logging.info(f"📈 COMPRA (simulada) de {float(amount_to_buy):.8f} BTC a ${price:.2f}")
    logging.info(f"🛡️ RIESGO: SL=${state['stop_loss_price']:.2f}, TP=${state['take_profit_price']:.2f}")
    msg = format_buy_message(SYMBOL_ON_BINANCE, float(price), state['stop_loss_price'], state['take_profit_price'])
    await send_telegram_message(msg)
    return state

async def execute_paper_sell(state, price, reason="Señal de Venta"):
    value_of_sale = Decimal(state['asset_holding']) * price
    pnl = float(value_of_sale) - VIRTUAL_USD_PER_TRADE
    msg = format_sell_message(SYMBOL_ON_BINANCE, float(price), reason, pnl)
    await send_telegram_message(msg)
    state['cash_usd'] += float(value_of_sale)
    state['asset_holding'] = 0.0
    state['in_position'] = False
    state['entry_price'] = 0.0
    state['stop_loss_price'] = 0.0
    state['take_profit_price'] = 0.0
    logging.info(f"📉 VENTA ({reason}) a ${price:.2f}. P&L de la operación: ${pnl:.2f}")
    return state

# --- Lógica Principal del Bot (ESTRATEGIA DE CONFLUENCIA TOTAL) ---
async def run_bot():
    """Función principal que ejecuta el ciclo del bot."""
    logging.info("="*20 + " INICIANDO CICLO DEL BOT v3.1 (Confluencia Total) " + "="*20)
    
    state = get_portfolio_state()
    
    if state['total_trades'] >= MAX_TRADES:
        logging.info("🏁 Límite de operaciones alcanzado.")
        return

    client = get_binance_client(testnet=True)
    current_price = get_current_price(client, SYMBOL_ON_BINANCE)
    if not current_price:
        logging.error("❌ Abortando ciclo: no se pudo obtener precio.")
        return

    # Gestión de posición abierta
    if state['in_position']:
        logging.info(f"🔎 En posición. Precio: ${current_price:.2f}. SL: ${state['stop_loss_price']:.2f}, TP: ${state['take_profit_price']:.2f}")
        if current_price <= Decimal(state['stop_loss_price']):
            logging.warning("🔥 STOP-LOSS ALCANZADO.")
            new_state = await execute_paper_sell(state, current_price, reason="Stop-Loss")
            save_portfolio_state(new_state)
            return
        elif current_price >= Decimal(state['take_profit_price']):
            logging.info("🎉 TAKE-PROFIT ALCANZADO.")
            new_state = await execute_paper_sell(state, current_price, reason="Take-Profit")
            save_portfolio_state(new_state)
            return
            
    # Búsqueda de nueva entrada
    logging.info("Buscando nueva señal de entrada por confluencia...")
    try:
        tech_prediction = get_prediction()
        sentiment_signals = get_all_sentiment_signals()
    except Exception as e:
        logging.error(f"❌ Error crítico al obtener señales: {e}", exc_info=True)
        return
    
    # --- NUEVA LÓGICA DE PUNTUACIÓN POR CONFLUENCIA ---
    score = 0
    
    # 1. Señal Técnica (la más importante, peso 2)
    if tech_prediction == 1: score += 2
    if tech_prediction == 0: score -= 2

    # 2. Sentimiento de Expertos (X/Twitter) (peso 1.5)
    if sentiment_signals['twitter'] == 1: score += 1.5
    if sentiment_signals['twitter'] == -1: score -= 1.5
    
    # 3. Sentimiento de Mercado (F&G) (peso 1)
    if sentiment_signals['fear_and_greed'] == 1: score += 1
    if sentiment_signals['fear_and_greed'] == -1: score -= 1
    
    # 4. Contexto Fundamental (Noticias) (peso 0.5)
    if sentiment_signals['news'] == 1: score += 0.5
    if sentiment_signals['news'] == -1: score -= 0.5

    logging.info(f"🧠 Ponderación de Señales: Técnica={tech_prediction*2}, X={sentiment_signals['twitter']*1.5}, F&G={sentiment_signals['fear_and_greed']*1}, Noticias={sentiment_signals['news']*0.5} --> Score Total: {score:.2f}")

    # Umbral de decisión (lo ajustamos a 3.0 para buscar una fuerte confluencia)
    if score >= 3.0 and not state['in_position']:
        logging.info(f"✅ UMBRAL DE COMPRA ALCANZADO (Score: {score:.2f}). Ejecutando compra...")
        new_state = await execute_paper_buy(state, current_price)
        save_portfolio_state(new_state)
    elif score <= -3.0 and state['in_position']:
        logging.info(f"🛑 UMBRAL DE VENTA ALCANZADO (Score: {score:.2f}). Ejecutando venta por señal...")
        new_state = await execute_paper_sell(state, current_price, reason="Señal de Venta por Confluencia")
        save_portfolio_state(new_state)
    else:
        logging.info(f"⏸️ Condición de mercado no concluyente o ya en la posición correcta (Score: {score:.2f}). Manteniendo posición.")

    logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")

# --- BLOQUE PRINCIPAL (Sin cambios) ---
async def main():
    if os.path.exists(LOCK_FILE):
        logging.warning("✋ Bot ya en ejecución (bot.lock existe). Saliendo.")
        sys.exit()
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        initialize_portfolio()
        await run_bot()
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

if __name__ == '__main__':
    asyncio.run(main())