# run_bot_cycle.py (Versión Final - Robusta para Cron)

import logging
import asyncio
import sys
import os

# Añadimos la raíz del proyecto para que encuentre los módulos
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Apuntamos a la función principal de nuestro bot de operaciones REALES
from scripts.real_time_bot import run_real_bot_cycle

# Configuración de logging para este script maestro
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] - [ORQUESTADOR] %(message)s"
)

async def main_pipeline():
    """Función principal que ejecuta el ciclo del bot real."""
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Construimos la ruta ABSOLUTA al archivo del bot real
    real_bot_path = os.path.join(PROJECT_ROOT, 'scripts', 'real_time_bot.py')
    
    # Leemos el archivo usando la ruta absoluta para determinar el entorno
    try:
        with open(real_bot_path, 'r') as f:
            content = f.read()
        env = "Testnet" if "USE_TESTNET = True" in content else "Entorno REAL"
    except FileNotFoundError:
        logging.error(f"❌ No se pudo encontrar el archivo del bot en {real_bot_path}")
        env = "Desconocido"
    # --- FIN DE LA CORRECCIÓN ---

    logging.info(f"--- Iniciando el ciclo de operación del Bot REAL ({env}) ---")
    await run_real_bot_cycle()
    logging.info("--- Ciclo de operación REAL completado ---")

if __name__ == '__main__':
    logging.info("🚀 Invocando el ciclo completo del Bot de Trading IA (Modo Real)...")
    try:
        asyncio.run(main_pipeline())
        logging.info("✅ Ciclo completo (Real) ejecutado exitosamente.")
    except Exception as e:
        logging.error(f"❌ Error fatal en el orquestador: {e}", exc_info=True)