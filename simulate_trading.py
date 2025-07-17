# simulate_trading.py
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import logging

# 🎯 Parámetros personalizables
RSI_BUY_THRESHOLD = 70
RSI_SELL_THRESHOLD = 30
MIN_VOLUME_QUANTILE = 0.2

# ✅ Configurar logging profesional
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

logging.info("📊 Descargando datos históricos de BTC...")
df = yf.download("BTC-USD", start="2021-01-01", end="2023-01-01", auto_adjust=False)

# ✅ Validaciones iniciales
if df.empty:
    raise ValueError("❌ El DataFrame está vacío. Revisa tu conexión o el símbolo.")

# Manejar MultiIndex en columnas, renombrando a formato simple
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col).strip() for col in df.columns.values]
    logging.warning(f"⚠️ Columnas renombradas: {df.columns.tolist()}")

# Buscar la columna Close segura (que no sea Adj Close)
safe_close_col = next((col for col in df.columns if 'Close' in col and 'Adj' not in col), None)
if safe_close_col is None:
    raise ValueError("❌ No se encontró una columna de precios 'Close' válida.")
logging.info(f"✅ Usando columna de cierre: '{safe_close_col}'")

# Buscar la columna Volume segura
safe_volume_col = next((col for col in df.columns if 'Volume' in col), None)
if safe_volume_col is None:
    raise ValueError("❌ No se encontró una columna de volumen válida.")
logging.info(f"✅ Usando columna de volumen: '{safe_volume_col}'")

# Asegurar tipo float y filtrar volumen bajo el cuantil mínimo
df[safe_close_col] = df[safe_close_col].astype(float)
df[safe_volume_col] = df[safe_volume_col].astype(float)
df = df[df[safe_volume_col] > df[safe_volume_col].quantile(MIN_VOLUME_QUANTILE)]

# ✅ Indicadores técnicos
logging.info("🧮 Calculando SMA20, SMA50 y RSI14...")
df["SMA20"] = SMAIndicator(close=df[safe_close_col], window=20).sma_indicator()
df["SMA50"] = SMAIndicator(close=df[safe_close_col], window=50).sma_indicator()
df["RSI14"] = RSIIndicator(close=df[safe_close_col], window=14).rsi()

# Eliminar filas con valores nulos en indicadores
df.dropna(subset=[safe_close_col, "SMA20", "SMA50", "RSI14"], inplace=True)

# Crear columnas previas para detectar cruces
df["Prev_SMA20"] = df["SMA20"].shift(1)
df["Prev_SMA50"] = df["SMA50"].shift(1)

# --- Fragmento añadido para ver cruces y RSI ---
cross_up = (df["Prev_SMA20"] < df["Prev_SMA50"]) & (df["SMA20"] > df["SMA50"])
cross_down = (df["Prev_SMA20"] > df["Prev_SMA50"]) & (df["SMA20"] < df["SMA50"])

print("Cruces al alza con RSI actual:")
print(df.loc[cross_up, ["RSI14", safe_close_col]].head(10))

print("Cruces a la baja con RSI actual:")
print(df.loc[cross_down, ["RSI14", safe_close_col]].head(10))
# --- Fin fragmento añadido ---

# Inicializar columna de señales
df["Signal"] = ""

# Señal de compra
df.loc[
    (df["Prev_SMA20"] < df["Prev_SMA50"]) &
    (df["SMA20"] > df["SMA50"]) &
    (df["RSI14"] < RSI_BUY_THRESHOLD),
    "Signal"
] = "BUY"

# Señal de venta
df.loc[
    (df["Prev_SMA20"] > df["Prev_SMA50"]) &
    (df["SMA20"] < df["SMA50"]) &
    (df["RSI14"] > RSI_SELL_THRESHOLD),
    "Signal"
] = "SELL"

# Extraer señales limpias
signals = df[df["Signal"] != ""].copy()

# Eliminar señales consecutivas duplicadas para evitar ruido
signals["Signal_shift"] = signals["Signal"].shift()
signals = signals[signals["Signal"] != signals["Signal_shift"]]
signals.drop(columns=["Signal_shift", "Prev_SMA20", "Prev_SMA50"], inplace=True)

# Añadir columna de retorno simulado 1 día después (correcto cálculo)
signals["Return"] = signals[safe_close_col].shift(-1) / signals[safe_close_col] - 1

# Calcular ganancia total simulada considerando sentido de la señal
ganancia_total = 0.0
for _, row in signals.iterrows():
    if row["Signal"] == "BUY":
        ganancia_total += row["Return"]
    elif row["Signal"] == "SELL":
        ganancia_total -= row["Return"]  # Ganancia si precio baja

logging.info(f"📈 Ganancia total simulada: {ganancia_total:.4f} ({ganancia_total*100:.2f}%)")
logging.info(f"📊 Promedio retorno por señal: {signals['Return'].mean():.4f} ({signals['Return'].mean()*100:.2f}%)")

logging.info("📌 Últimas señales generadas:")
print(signals[[safe_close_col, "SMA20", "SMA50", "RSI14", "Signal", "Return"]].tail())

# Exportar señales a CSV
signals.to_csv("senales_generadas.csv", index=True)
logging.info("📁 Señales guardadas en 'senales_generadas.csv'")

# Gráfico visual de la estrategia y señales
plt.figure(figsize=(14, 6))
plt.plot(df.index, df[safe_close_col], label='Precio', alpha=0.6)
plt.plot(df.index, df["SMA20"], label='SMA20', linestyle='--', color='blue')
plt.plot(df.index, df["SMA50"], label='SMA50', linestyle='--', color='orange')

for label, color in [("BUY", "green"), ("SELL", "red")]:
    plt.scatter(
        signals[signals["Signal"] == label].index,
        signals[signals["Signal"] == label][safe_close_col],
        label=label,
        color=color,
        marker='o'
    )

plt.title("Simulación de Estrategia SMA + RSI (BTC-USD)")
plt.xlabel("Fecha")
plt.ylabel("Precio (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("simulacion_estrategia.png")
logging.info("📁 Gráfico guardado como 'simulacion_estrategia.png'")
