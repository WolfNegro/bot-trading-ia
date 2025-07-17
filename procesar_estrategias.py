# scripts/procesar_estrategias.py

import re
import pandas as pd

# Rutas
ruta_txt = "data/estrategias_resumen.txt"
ruta_csv = "data/estrategias_contexto.csv"

# Cargar el archivo
with open(ruta_txt, "r", encoding="utf-8") as f:
    lineas = f.readlines()

datos = []
for linea in lineas:
    linea = linea.strip()
    if not linea:
        continue

    # Detectar fecha (si existe)
    fecha = None
    match_fecha = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", linea)
    if match_fecha:
        fecha = match_fecha.group(1)
    else:
        fecha = "sin_fecha"

    # Detectar tipo de estrategia (simple)
    tipo = "Otro"
    if "order block" in linea.lower():
        tipo = "Order Block"
    elif "estructura" in linea.lower() or "bos" in linea.lower():
        tipo = "Cambio Estructura"
    elif "liquidez" in linea.lower():
        tipo = "Liquidez"
    elif "fvg" in linea.lower():
        tipo = "Fair Value Gap"
    elif "mitigación" in linea.lower():
        tipo = "Mitigación"

    datos.append({"fecha": fecha, "estrategia": linea, "tipo": tipo})

# Guardar CSV
df = pd.DataFrame(datos)
df.to_csv(ruta_csv, index=False)
print(f"✅ Archivo generado: {ruta_csv}")
