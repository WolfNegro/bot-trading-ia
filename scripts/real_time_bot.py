# scripts/real_time_bot.py (Versión 2.2 - Con Heartbeat de Telegram)

import logging
import os
import sys
import asyncio
import json
from decimal import Decimal, ROUND_DOWN
from binance.exceptions import BinanceAPIException

# --- Añadir la raíz del proyecto al path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# --- Importamos NUESTROS módulos ---
from predict_live import get_prediction
from scripts.intelligence_aggregator import get_all_sentiment_signals
from scripts.connect_binance import get_binance_client
# --- ¡IMPORTAMOS LA NUEVA FUNCIÓN DE FORMATO! ---
from scripts.notifier import send_telegram_message, format_buy_message, format_sell_message, format_cycle_status_message

# --- INTERRUPTOR DE SEGURIDAD GLOBAL ---
USE_TESTNET = True

# --- CONFIGURACIÓN DE TRADING ---
SYMBOL = 'BTCUSDT'
BASE_ASSET = 'BTC'
QUOTE_ASSET = 'USDT'
USDT_PER_TRADE = 20.0

# --- CONFIGURACIÓN DE GESTIÓN DE RIESGO ---
STOP_LOSS_PERCENT = 1.5
TAKE_PROFIT_PERCENT = 3.0

# --- Archivo para guardar el estado de la operación ---
TRADE_STATE_FILE = 'trade_state.json' 

# --- Configuración de Logging ---
LOGS_DIR = 'logs'
TRADES_LOG_FILE = os.path.join(LOGS_DIR, 'real_trades.log')
if not os.path.exists(LOGS_DIR): os.makedirs(LOGS_DIR)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[logging.FileHandler(TRADES_LOG_FILE), logging.StreamHandler()])

# --- Funciones de Gestión de Estado y Órdenes (sin cambios) ---
def get_trade_state():
    if not os.path.exists(TRADE_STATE_FILE):
        return {"in_position": False, "entry_price": 0.0, "stop_loss_price": 0.0, "take_profit_price": 0.0}
    with open(TRADE_STATE_FILE, 'r') as f:
        return json.load(f)

def save_trade_state(state):
    with open(TRADE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def get_asset_balance(client, asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return Decimal(balance['free'])
    except BinanceAPIException as e:
        logging.error(f"❌ Error al obtener balance de {asset}: {e}")
        return Decimal('0')

async def execute_real_buy(client, trade_state):
    logging.info(f"📈 Intentando ejecutar COMPRA de {USDT_PER_TRADE} {QUOTE_ASSET}...")
    try:
        ticker = client.get_symbol_ticker(symbol=SYMBOL)
        price = Decimal(ticker['price'])
        quantity = (Decimal(str(USDT_PER_TRADE)) / price).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
        
        logging.info(f"Enviando ORDEN MARKET BUY: {quantity} {BASE_ASSET} a ~${price:.2f}")
        order = client.order_market_buy(symbol=SYMBOL, quantity=float(quantity))
        
        entry_price = Decimal(order['fills'][0]['price'])
        trade_state.update({
            "in_position": True,
            "entry_price": float(entry_price),
            "stop_loss_price": float(entry_price * (Decimal(1) - Decimal(STOP_LOSS_PERCENT / 100))),
            "take_profit_price": float(entry_price * (Decimal(1) + Decimal(TAKE_PROFIT_PERCENT / 100)))
        })
        save_trade_state(trade_state)
        logging.info(f"✅ Compra exitosa. Precio de entrada: {entry_price:.2f}, SL: {trade_state['stop_loss_price']:.2f}, TP: {trade_state['take_profit_price']:.2f}")

        msg = format_buy_message(SYMBOL, trade_state['entry_price'], trade_state['stop_loss_price'], trade_state['take_profit_price'])
        await send_telegram_message(msg)
        return True
    except Exception as e:
        logging.error(f"❌ Error al ejecutar compra: {e}", exc_info=True)
        return False

async def execute_real_sell(client, trade_state, reason="Señal de Venta"):
    logging.info(f"📉 Intentando ejecutar VENTA de todo el {BASE_ASSET}...")
    try:
        quantity = get_asset_balance(client, BASE_ASSET)
        if quantity <= Decimal('0.00001'):
            logging.warning(f"⚠️ Se intentó vender pero el balance de {BASE_ASSET} es cero.")
            save_trade_state({"in_position": False, "entry_price": 0.0, "stop_loss_price": 0.0, "take_profit_price": 0.0})
            return False

        quantity_to_sell = float(quantity.quantize(Decimal('0.00001'), rounding=ROUND_DOWN))
        logging.info(f"Enviando ORDEN MARKET SELL: {quantity_to_sell} {BASE_ASSET}")
        order = client.order_market_sell(symbol=SYMBOL, quantity=quantity_to_sell)
        
        exit_price = Decimal(order['fills'][0]['price'])
        pnl = (exit_price - Decimal(str(trade_state.get('entry_price', exit_price)))) * quantity
        logging.info(f"✅ Venta exitosa. Precio de salida: {exit_price:.2f}. P&L: ${pnl:.2f}")

        msg = format_sell_message(SYMBOL, float(exit_price), reason, float(pnl))
        await send_telegram_message(msg)
        
        save_trade_state({"in_position": False, "entry_price": 0.0, "stop_loss_price": 0.0, "take_profit_price": 0.0})
        return True
    except Exception as e:
        logging.error(f"❌ Error al ejecutar venta: {e}", exc_info=True)
        return False

# --- Lógica Principal del Bot ---
async def run_real_bot_cycle():
    env = "Testnet" if USE_TESTNET else "Entorno REAL"
    logging.info("="*20 + f" INICIANDO CICLO DEL BOT REAL v2.2 ({env}) " + "="*20)
    
    client = get_binance_client(testnet=USE_TESTNET)
    trade_state = get_trade_state()
    action_taken = "Manteniendo Posición" # <-- Variable para el estado final
    score = 0 # <-- Inicializamos el score

    try:
        # 1. Gestión de posición abierta (SL/TP)
        if trade_state.get("in_position", False):
            current_price = Decimal(client.get_symbol_ticker(symbol=SYMBOL)['price'])
            sl = Decimal(str(trade_state.get('stop_loss_price', 0)))
            tp = Decimal(str(trade_state.get('take_profit_price', 0)))
            logging.info(f"🔎 En posición. Precio actual: ${current_price:.2f}. SL: ${sl:.2f}, TP: ${tp:.2f}")

            if sl > 0 and current_price <= sl:
                logging.warning("🔥 STOP-LOSS ALCANZADO.")
                if await execute_real_sell(client, trade_state, reason="Stop-Loss"):
                    action_taken = "Venta por Stop-Loss"
                # Finalizamos el ciclo aquí porque ya se tomó una acción
                status_message = format_cycle_status_message(score, action_taken)
                await send_telegram_message(status_message)
                return
            elif tp > 0 and current_price >= tp:
                logging.info("🎉 TAKE-PROFIT ALCANZADO.")
                if await execute_real_sell(client, trade_state, reason="Take-Profit"):
                    action_taken = "Venta por Take-Profit"
                status_message = format_cycle_status_message(score, action_taken)
                await send_telegram_message(status_message)
                return
        
        # 2. Búsqueda de nueva señal si no se ha cerrado una posición
        logging.info("Buscando nueva señal por confluencia...")
        tech_prediction = get_prediction()
        sentiment_signals = get_all_sentiment_signals()
        
        # 3. Lógica de puntuación
        if tech_prediction == 1: score += 2
        if tech_prediction == 0: score -= 2
        if sentiment_signals['twitter'] == 1: score += 1.5
        if sentiment_signals['twitter'] == -1: score -= 1.5
        if sentiment_signals['fear_and_greed'] == 1: score += 1
        if sentiment_signals['fear_and_greed'] == -1: score -= 1
        if sentiment_signals['news'] == 1: score += 0.5
        if sentiment_signals['news'] == -1: score -= 0.5
        logging.info(f"🧠 Ponderación de Señales: Técnica={tech_prediction*2}, X={sentiment_signals['twitter']*1.5}, F&G={sentiment_signals['fear_and_greed']*1}, Noticias={sentiment_signals['news']*0.5} --> Score Total: {score:.2f}")

        # 4. Decisión final de trading
        in_position_now = get_trade_state().get("in_position", False)
        if score >= 3.0 and not in_position_now:
            logging.info(f"✅ UMBRAL DE COMPRA ALCANZADO (Score: {score:.2f}).")
            if await execute_real_buy(client, get_trade_state()):
                action_taken = "Orden de COMPRA enviada"
        elif score <= -3.0 and in_position_now:
            logging.info(f"🛑 UMBRAL DE VENTA ALCANZADO (Score: {score:.2f}).")
            if await execute_real_sell(client, get_trade_state(), reason="Señal de Venta por Confluencia"):
                action_taken = "Orden de VENTA enviada"
        else:
            logging.info(f"⏸️ Condición de mercado no concluyente o ya en la posición correcta (Score: {score:.2f}).")
            # action_taken ya es "Manteniendo Posición" por defecto

    except Exception as e:
        logging.error(f"❌ Error crítico durante el ciclo del bot: {e}", exc_info=True)
        action_taken = f"ERROR: {e}"
    
    # --- ENVÍO DE NOTIFICACIÓN DE ESTADO FINAL ---
    status_message = format_cycle_status_message(score, action_taken)
    await send_telegram_message(status_message)

    logging.info("="*28 + " FIN DEL CICLO " + "="*28 + "\n")

# --- BLOQUE PRINCIPAL ---
if __name__ == '__main__':
    asyncio.run(run_real_bot_cycle())