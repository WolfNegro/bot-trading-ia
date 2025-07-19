# scripts/notifier.py (Versión con notificación de estado de ciclo)

import os
import logging
import telegram
from dotenv import load_dotenv
import asyncio
import requests

def _load_env():
    """Función interna para cargar las variables de entorno de forma segura."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_message(message):
    """Envía un mensaje de forma asíncrona a través del bot de Telegram."""
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = _load_env()
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Credenciales de Telegram no configuradas.")
        return False
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        logging.info("📢 Notificación de Telegram (async) enviada con éxito.")
        return True
    except Exception as e:
        logging.error(f"❌ Error al enviar la notificación de Telegram (async): {e}")
        return False

# --- Funciones de Formato ---

def format_buy_message(symbol, price, sl_price, tp_price):
    return (
        f"✅ **COMPRA EJECUTADA** ✅\n\n"
        f"📈 *Activo:* `{symbol}`\n"
        f"💵 *Precio de Entrada:* `${price:,.2f}`\n\n"
        f"🛡️ *Stop-Loss:* `${sl_price:,.2f}`\n"
        f"🎯 *Take-Profit:* `${tp_price:,.2f}`"
    )

def format_sell_message(symbol, price, reason, pnl):
    emoji = "🎉" if reason == "Take-Profit" else "🔥"
    reason_text = f"_{reason} Alcanzado_"
    pnl_text = f"*Ganancia:* `${pnl:,.2f}`" if pnl >= 0 else f"*Pérdida:* `${pnl:,.2f}`"
    return (
        f"{emoji} **VENTA EJECUTADA** {emoji}\n\n"
        f"📉 *Activo:* `{symbol}`\n"
        f"➡️ *Motivo:* {reason_text}\n"
        f"💵 *Precio de Salida:* `${price:,.2f}`\n"
        f"💰 *Resultado (P&L):* {pnl_text}"
    )

# --- NUEVA FUNCIÓN DE FORMATO DE ESTADO ---
def format_cycle_status_message(score, action_taken):
    """Crea un mensaje de resumen del ciclo para el heartbeat."""
    emoji = "✅" if "COMPRA" in action_taken or "VENTA" in action_taken else "⏸️"
    return (
        f"{emoji} **Resumen del Ciclo** {emoji}\n\n"
        f"📊 *Score Final:* `{score:.2f}`\n"
        f"🎬 *Acción Tomada:* _{action_taken}_"
    )

# Bloque de prueba (no necesita cambios)
async def main_test():
    # ... (el bloque de prueba se mantiene igual)
    pass

if __name__ == '__main__':
    # ... (el bloque de prueba se mantiene igual)
    pass