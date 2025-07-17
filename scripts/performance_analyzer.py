# scripts/performance_analyzer.py (Versión Corregida)

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging # <-- ¡LA LÍNEA QUE FALTABA!

# --- Configuración ---
LOGS_DIR = 'logs'
TRADES_LOG_FILE = os.path.join(LOGS_DIR, 'paper_trades.log')
OUTPUT_DIR = 'output'
PERFORMANCE_CHART_FILE = os.path.join(OUTPUT_DIR, 'performance_curve.png')
INITIAL_CAPITAL = 1000.0

def analyze_performance():
    """
    Lee el log de paper trading, calcula métricas de rendimiento clave,
    y genera un gráfico de la curva de equity.
    """
    logging.info("--- Iniciando Análisis de Rendimiento del Bot ---")

    if not os.path.exists(TRADES_LOG_FILE):
        print(f"❌ Error: No se encontró el archivo de log en '{TRADES_LOG_FILE}'.")
        return

    # --- 1. Leer y Parsear el Log para construir el historial del portafolio ---
    print(f"📄 Leyendo log de operaciones desde: {TRADES_LOG_FILE}")
    
    buy_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).* COMPRA .* a \$([\d\.]+)")
    sell_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).* VENTA \((.*?)\).* a \$([\d\.]+)\. P&L de la operación: \$(.*)")
    
    portfolio_history = [{'date': None, 'value': INITIAL_CAPITAL}]
    trades = []
    
    current_cash = INITIAL_CAPITAL
    last_buy_value = 0

    with open(TRADES_LOG_FILE, 'r') as f:
        for line in f:
            buy_match = buy_pattern.search(line)
            sell_match = sell_pattern.search(line)
            
            if buy_match:
                date = pd.to_datetime(buy_match.group(1))
                price = float(buy_match.group(2))
                # Asumimos que cada compra usa un valor fijo, ej. 20 USD
                last_buy_value = 20.0 
                current_cash -= last_buy_value
                trades.append({'type': 'BUY', 'price': price, 'date': date})
                
            elif sell_match:
                date = pd.to_datetime(sell_match.group(1))
                pnl_usd = float(sell_match.group(4))
                
                # Reconstruimos el valor de la venta
                sell_value = last_buy_value + pnl_usd
                current_cash += sell_value
                
                last_buy = next((t for t in reversed(trades) if t['type'] == 'BUY'), None)
                if last_buy:
                    pnl_percent = (pnl_usd / last_buy_value) * 100
                    trades.append({'type': 'SELL', 'price': float(sell_match.group(3)), 'date': date, 'pnl_percent': pnl_percent})
                    portfolio_history.append({'date': date, 'value': current_cash})

    if len([t for t in trades if t['type'] == 'SELL']) == 0:
        print("ℹ️ No hay operaciones de VENTA completas para un análisis de rendimiento.")
        return

    # --- 2. Calcular Métricas de Rendimiento ---
    print("\n" + "="*20 + " REPORTE DE RENDIMIENTO " + "="*20)
    
    df_trades = pd.DataFrame([t for t in trades if t['type'] == 'SELL'])
    
    total_trades = len(df_trades)
    win_trades = df_trades[df_trades['pnl_percent'] > 0]
    loss_trades = df_trades[df_trades['pnl_percent'] <= 0]
    
    win_rate = (len(win_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    total_profit = win_trades['pnl_percent'].sum()
    total_loss = abs(loss_trades['pnl_percent'].sum())
    
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    avg_win = win_trades['pnl_percent'].mean() if len(win_trades) > 0 else 0
    avg_loss = loss_trades['pnl_percent'].mean() if len(loss_trades) > 0 else 0

    final_capital = portfolio_history[-1]['value']
    net_profit_usd = final_capital - INITIAL_CAPITAL
    net_profit_percent = (net_profit_usd / INITIAL_CAPITAL) * 100

    print(f"  - Período Analizado: {portfolio_history[1]['date'].date()} a {portfolio_history[-1]['date'].date()}")
    print(f"  - Capital Inicial: ${INITIAL_CAPITAL:.2f}")
    print(f"  - Capital Final:   ${final_capital:.2f}")
    print(f"  - Ganancia/Pérdida Neta: ${net_profit_usd:.2f} ({net_profit_percent:.2f}%)")
    print("-" * 50)
    print(f"  - Total de Operaciones Cerradas: {total_trades}")
    print(f"  - Porcentaje de Aciertos (Win Rate): {win_rate:.2f}%")
    print(f"  - Profit Factor: {profit_factor:.2f}")
    print(f"  - Ganancia Promedio: {avg_win:.2f}%")
    print(f"  - Pérdida Promedio:  {avg_loss:.2f}%")
    print("=" * 56)

    # --- 3. Generar Gráfico de Curva de Equity ---
    df_history = pd.DataFrame(portfolio_history).dropna().set_index('date')
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))
    
    ax.plot(df_history.index, df_history['value'], marker='o', linestyle='-', label='Curva de Capital', color='dodgerblue')
    ax.fill_between(df_history.index, df_history['value'], INITIAL_CAPITAL, where=(df_history['value'] >= INITIAL_CAPITAL), color='green', alpha=0.3, interpolate=True, label='Ganancia')
    ax.fill_between(df_history.index, df_history['value'], INITIAL_CAPITAL, where=(df_history['value'] < INITIAL_CAPITAL), color='red', alpha=0.3, interpolate=True, label='Pérdida')
    ax.axhline(y=INITIAL_CAPITAL, color='grey', linestyle='--', label=f'Capital Inicial (${INITIAL_CAPITAL})')
    
    ax.set_title('Curva de Rendimiento del Portafolio (Equity Curve)', fontsize=18)
    ax.set_ylabel('Valor del Portafolio (USD)', fontsize=12)
    ax.set_xlabel('Fecha de Operación', fontsize=12)
    ax.legend()
    ax.grid(True)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART_FILE)
    print(f"\n✅ Gráfico de rendimiento guardado en '{PERFORMANCE_CHART_FILE}'")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
    analyze_performance()