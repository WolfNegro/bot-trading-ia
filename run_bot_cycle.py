# run_bot_cycle.py (Versión Final con Importaciones Explícitas)

import logging
import asyncio
import sys
import os

# No necesitamos modificar el sys.path con este método más limpio.

# --- Importaciones Explícitas y Robustas ---
# Le decimos a Python que busque en la carpeta 'youtube_scraper' el módulo 'get_video_ids'
from youtube_scraper.get_video_ids import get_video_ids_from_channels
from youtube_scraper.download_transcripts import download_transcripts_from_csv

# Como paper_trading_bot.py está en la misma carpeta (raíz), se importa directamente.
from paper_trading_bot import main as run_trading_bot

# Configuración básica de logging para este script maestro
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - [ORQUESTADOR] %(message)s")

def run_intelligence_pipeline():
    """
    Ejecuta la secuencia completa de recolección de inteligencia social.
    """
    logging.info("--- INICIANDO PIPELINE DE INTELIGENCIA (YouTube) ---")
    get_video_ids_from_channels()
    download_transcripts_from_csv()
    logging.info("--- PIPELINE DE INTELIGENCIA COMPLETADO ---")

async def main_pipeline():
    """Función principal asíncrona que ejecuta todo en orden."""
    run_intelligence_pipeline()
    await run_trading_bot()

if __name__ == '__main__':
    logging.info("🚀 Invocando el ciclo completo del Bot de Trading IA...")
    
    asyncio.run(main_pipeline())
    
    logging.info("✅ Ciclo completo ejecutado.")