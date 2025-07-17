# backtest.py
# CORRECCIÓN DE TIPO DE DATO: Se asegura que todas las variables numéricas
# (capital, btc_coins, precios, saldos) sean tratadas como escalares (float)
# para prevenir errores en operaciones y formateo de texto.

import yfinance as yf
import pandas as pd
import ta
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

# -- 1. Descarga de Datos Históricos --
try:
    data = yf.download('BTC-USD', period='2y', interval='1d', auto_adjust=True, progress=False)
    if data.empty:
        print("No se pudieron descargar datos. Verifica el ticker o tu conexión.")
        exit()
except Exception as e:
    print(f"Ocurrió un error al descargar los datos: {e}")
    exit()

# -- 2. Cálculo de Indicadores Técnicos --
print("Calculando indicadores técnicos...")
# Se crea una Serie 1D explícita para evitar errores de dimensionalidad
close_series = pd.Series(data['Close'].values.squeeze(), index=data.index)
data['SMA_20'] = SMAIndicator(close=close_series, window=20).sma_indicator()
data['SMA_50'] = SMAIndicator(close=close_series, window=50).sma_indicator()
data['RSI_14'] = RSIIndicator(close=close_series, window=14).rsi()
data.dropna(inplace=True)
print("Indicadores calculados y datos limpios.")

# -- 3. Simulación de Operaciones (Backtesting) --
initial_capital = 1000.0
capital = initial_capital
btc_coins = 0.0
position = 'NEUTRAL'
trades = []

print("Iniciando simulación de backtesting...")
for i in range(1, len(data)):
    # --- Condiciones de Compra (BUY) ---
    if data['SMA_20'].iloc[i-1] < data['SMA_50'].iloc[i-1] and \
       data['SMA_20'].iloc[i] > data['SMA_50'].iloc[i] and \
       position == 'NEUTRAL':
        
        # Extraer el precio como un escalar
        buy_price = float(data['Close'].iloc[i])
        
        # Realizar cálculos con escalares
        btc_coins = float(capital / buy_price)
        capital = 0.0
        position = 'LONG'
        
        trade_info = {
            'Date': data.index[i].strftime('%Y-%m-%d'),
            'Action': 'BUY',
            'Price': buy_price,
            'Balance': float(btc_coins * buy_price)
        }
        trades.append(trade_info)

    # --- Condiciones de Venta (SELL) ---
    elif data['SMA_20'].iloc[i-1] > data['SMA_50'].iloc[i-1] and \
         data['SMA_20'].iloc[i] < data['SMA_50'].iloc[i] and \
         position == 'LONG':
        
        # Extraer el precio como un escalar
        sell_price = float(data['Close'].iloc[i])

        # Realizar cálculos con escalares
        capital = float(btc_coins * sell_price)
        btc_coins = 0.0
        position = 'NEUTRAL'
        
        trade_info = {
            'Date': data.index[i].strftime('%Y-%m-%d'),
            'Action': 'SELL',
            'Price': sell_price,
            'Balance': capital
        }
        trades.append(trade_info)

# -- 4. Resultados Finales --
final_balance = capital
if btc_coins > 0:
    # Cálculo robusto del saldo final, asegurando que ambos operandos son float
    final_balance = float(btc_coins * float(data['Close'].iloc[-1]))

print("\n--- Backtesting Finalizado ---")
print(f"Capital Inicial: ${initial_capital:.2f}")
print(f"Saldo Final: ${final_balance:.2f}")
profit = ((final_balance - initial_capital) / initial_capital) * 100
print(f"Rentabilidad: {profit:.2f}%")
print("\n--- Lista de Operaciones Realizadas ---")

if not trades:
    print("No se realizaron operaciones con la estrategia y parámetros definidos.")
else:
    # Se extraen y convierten los valores a float antes de imprimir para evitar errores
    for trade in trades:
        date = trade['Date']
        action = trade['Action']
        price = float(trade['Price'])
        balance = float(trade['Balance'])
        print(f"Fecha: {date}, Acción: {action:<6}, Precio: ${price:<10.2f}, Saldo tras op: ${balance:.2f}")