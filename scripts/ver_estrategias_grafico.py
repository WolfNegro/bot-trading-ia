import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_csv("data/historial_con_estrategias.csv", parse_dates=["Date"])

# Graficar
plt.figure(figsize=(14, 6))
plt.plot(df["Date"], df["Close"], label="Precio")

# Marcar donde hay contexto de estrategia
estrategias = df[df["contexto_estrategia"] == 1]
plt.scatter(estrategias["Date"], estrategias["Close"], color="red", label="Estrategia Detectada", marker="x")

plt.title("Precio BTC con estrategias detectadas")
plt.xlabel("Fecha")
plt.ylabel("Precio")
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()
