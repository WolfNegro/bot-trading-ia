import requests
import os
from dotenv import load_dotenv

# ✅ Cargar API_KEY desde .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = "UC1AZPvFr6v1WZaPw_YX19DA"  # ← Cambia esto si necesitas otro canal

KEYWORDS = [
    "estrategia", "scalping", "day trading", "curso", "guía", "desde cero", 
    "para principiantes", "psicotrading", "gestión de riesgo", "plan de trading",
    "mejor indicador", "indicador oculto", "rsi", "macd", "estocástico",
    "99% de aciertos", "trading rentable"
]

def contiene_palabras_clave(titulo):
    titulo_lower = titulo.lower()
    return any(keyword in titulo_lower for keyword in KEYWORDS)

def get_video_ids(api_key, channel_id):
    base_url = "https://www.googleapis.com/youtube/v3/search"
    video_ids = []
    page_token = ""
    
    while True:
        params = {
            "key": api_key,
            "channelId": channel_id,
            "part": "snippet",
            "order": "date",
            "maxResults": 50,
            "pageToken": page_token,
            "type": "video"
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            titulo = item["snippet"]["title"]

            if contiene_palabras_clave(titulo):
                print(f"✅ Aceptado: {titulo}")
                video_ids.append(video_id)
            else:
                print(f"❌ Ignorado: {titulo}")

        if "nextPageToken" not in data:
            break
        page_token = data["nextPageToken"]

    return video_ids

# 🎯 Ejecutar y guardar resultados
if __name__ == "__main__":
    ids_valiosos = get_video_ids(API_KEY, CHANNEL_ID)
    with open("videos_filtrados.txt", "w") as f:
        for vid in ids_valiosos:
            f.write(f"{vid}\n")
    print(f"\n🎯 Se guardaron {len(ids_valiosos)} videos valiosos en videos_filtrados.txt")
