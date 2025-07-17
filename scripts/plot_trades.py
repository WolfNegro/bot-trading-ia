# scripts/plot_trades.py (Versión Final Definitiva - Simplificada y Robusta)

import os
import re
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_paper_trades():
    """
    Función principal para leer el log, manejar cualquier cantidad de datos,
    y generar un gráfico de operaciones claro y sin errores.
    """
    # --- 1. Definir Rutas ---
    LOG_FILE_PATH = os.path.join('logs', 'paper_trades.log')
    OUTPUT_DIR = 'output'
    OUTPUT_PLOT_PATH = os.path.join(OUTPUT_DIR, 'trades_plot.png')

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # --- 2. Leer y Parsear el Log ---
    if not os.path.exists(LOG_FILE_PATH):
        print(f"❌ Error: No se encontró el archivo de log en '{LOG_FILE_PATH}'.")
        return

    trades = []
    print(f"📄 Leyendo log de operaciones desde: {LOG_FILE_PATH}")
    log_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).* (COMPRA|VENTA).* a \$([\d\.]+)")
    with open(LOG_FILE_PATH, 'r') as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                trades.append({
                    'date': pd.to_datetime(match.group(1)),
                    'action': 'BUY' if 'COMPRA' in match.group(2) else 'SELL',
                    'price': float(match.group(3))
                })

    if not trades:
        print("ℹ️ No se encontraron operaciones de COMPRA o VENTA en el archivo de log.")
        return

    trades_df = pd.DataFrame(trades).set_index('date')
    print("\n📊 Resumen de operaciones encontradas:")
    print(trades_df)

    # --- 3. Descargar Datos de Precios ---
    start_date = trades_df.index.min() - pd.Timedelta(days=5)
    end_date = trades_df.index.max() + pd.Timedelta(days=5)
    
    print(f"\n📥 Descargando datos de precios de BTC-USD desde {start_date.date()} hasta {end_date.date()}...")
    try:
        price_data = yf.download('BTC-USD', start=start_date, end=end_date, auto_adjust=True, progress=False)
        if price_data.empty:
            raise ValueError("No se pudieron descargar los datos de precios.")
    except Exception as e:
        print(f"❌ Error al descargar datos de yfinance: {e}")
        return

    # --- 4. Crear el Gráfico (LÓGICA SIMPLIFICADA) ---
    print("\n🎨 Generando gráfico de operaciones...")
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(18, 9))

    # Dibuja la línea de precios. La función plot() es robusta y no falla con pocos datos.
    ax.plot(price_data.index, price_data['Close'], label='Precio de Cierre (BTC/USD)', color='skyblue', linewidth=2, zorder=1, marker='o', markersize=4)

    # Dibuja los puntos de compra/venta
    buy_signals = trades_df[trades_df['action'] == 'BUY']
    sell_signals = trades_df[trades_df['action'] == 'SELL']

    ax.scatter(buy_signals.index, buy_signals['price'], label='Compra (BUY)', marker='^', color='green', s=200, zorder=5, alpha=1, edgecolors='black')
    ax.scatter(sell_signals.index, sell_signals['price'], label='Venta (SELL)', marker='v', color='red', s=200, zorder=5, alpha=1, edgecolors='black')

    # --- 5. Configurar y Guardar el Gráfico ---
    ax.set_title('Visualización de Operaciones del Bot para BTC/USD', fontsize=20, pad=20)
    ax.set_xlabel('Fecha', fontsize=14)
    ax.set_ylabel('Precio (USD)', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x/1000)}K'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig(OUTPUT_PLOT_PATH)
    print(f"\n✅ Gráfico guardado exitosamente en: {OUTPUT_PLOT_PATH}")
    # Opcional: Descomenta la siguiente línea si quieres que el gráfico se muestre en una ventana
    # plt.show()

if __name__ == '__main__':
    plot_paper_trades()