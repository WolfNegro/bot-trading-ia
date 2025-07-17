# filtrar_videos_valiosos.py

import re

# Cargar IDs y títulos
with open("video_ids.txt", "r", encoding="utf-8") as f:
    videos = [line.strip().split(" | ") for line in f.readlines()]

# Palabras clave valiosas
keywords = [
    "estrategia", "scalping", "day trading", "curso", "gratis", "principiante",
    "guía", "desde cero", "indicador", "trading rentable", "plan de trading",
    "psicotrading", "gestión de riesgo"
]

# Filtrar por coincidencia de palabras clave
filtrados = [
    video_id for video_id, title in videos
    if any(re.search(rf"\b{kw}\b", title.lower()) for kw in keywords)
]

# Guardar IDs filtrados
with open("videos_filtrados.txt", "w", encoding="utf-8") as f:
    for video_id in filtrados:
        f.write(f"{video_id}\n")

print(f"✅ {len(filtrados)} videos relevantes encontrados y guardados en videos_filtrados.txt")
