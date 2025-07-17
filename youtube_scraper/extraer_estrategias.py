# extraer_estrategias.py
import pandas as pd
import re

# Cargar ideas extraídas
df = pd.read_csv("ideas_extraidas.csv")

estrategias_detectadas = []

# Patrones clave para detectar estrategias
patrones = [
    r"estructura.*(bajista|alcista|market structure|cambio de estructura)",
    r"order block",
    r"(rompimiento|quiebre).*estructura",
    r"(compras|ventas).*confirmación",
    r"(highs|lows).*análisis",
    r"(entrada|salida).*basada.*(nivel|zona|estructura)",
    r"smart money",
    r"(liquidez|liquidity).*zona",
    r"breaker block",
    r"bos|choch|imbalance|fvg"
]

# Iterar sobre ideas y detectar estrategias
for idea in df["idea"]:
    idea_lower = idea.lower()
    for patron in patrones:
        if re.search(patron, idea_lower):
            estrategias_detectadas.append(idea)
            break  # Evita duplicados si un texto cumple varios patrones

# Guardar estrategias detectadas en un archivo
with open("estrategias_resumen.txt", "w", encoding="utf-8") as f:
    for i, estrategia in enumerate(estrategias_detectadas, start=1):
        f.write(f"📌 Estrategia #{i}:\n")
        f.write(estrategia.strip() + "\n")
        f.write("-" * 40 + "\n")

print(f"✅ Se detectaron {len(estrategias_detectadas)} estrategias y se guardaron en estrategias_resumen.txt")
