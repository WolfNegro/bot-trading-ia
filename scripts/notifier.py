# scripts/notifier.py (Versión Corregida - Asíncrona)

import os
import logging
import telegram
from dotenv import load_dotenv
import asyncio # <-- Importamos la librería para manejar operaciones asíncronas

def _load_env():
    """Función interna para cargar las variables de entorno de forma segura."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")

# --- La función de envío ahora es ASÍNCRONA ---
async def send_telegram_message(message):
    """
    Envía un mensaje de forma asíncrona a través del bot de Telegram.
    """
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = _load_env()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Credenciales de Telegram no configuradas. No se enviará notificación.")
        return False

    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        # Usamos 'await' para esperar a que el mensaje se envíe de verdad
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        logging.info("📢 Notificación de Telegram enviada con éxito.")
        return True
    except Exception as e:
        logging.error(f"❌ Error al enviar la notificación de Telegram: {e}")
        return False

# --- Las funciones de formato de mensajes no cambian ---
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

# --- Bloque de Prueba (Adaptado para ejecutar código asíncrono) ---
async def main_test():
    """Función principal asíncrona para la prueba."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    print("\n--- Probando el módulo notificador de Telegram (modo asíncrono) ---")
    
    print("Enviando mensaje de prueba...")
    success = await send_telegram_message("👋 ¡Hola! Esta es una notificación de prueba desde tu **Bot de Trading IA**.")
    
    if success:
        print("\n✅ Prueba exitosa. Revisa tu chat de Telegram para ver el mensaje.")
    else:
        print("\n❌ La prueba falló. Revisa los logs y tus credenciales en .env.")

if __name__ == '__main__':
    # Usamos asyncio.run() para ejecutar nuestra función de prueba asíncrona
    asyncio.run(main_test())