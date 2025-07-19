import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURACIÓN FINAL Y COMPLETA ---
CREDENTIALS_FILE = "credenciales.json"
SPREADSHEET_NAME = "Exportacion de Proyecto"
FILE_EXTENSIONS_TO_EXPORT = (".py", ".txt", ".json", ".md", ".csv", ".log")

# SOLUCIÓN DEFINITIVA: Añadimos la carpeta "logs" a la lista de ignorados.
FOLDERS_TO_IGNORE = (
    "venv", "__pycache__", ".git", ".idea", 
    "output", "node_modules", ".vscode", "export_txt", "logs"
)

MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024
SHEETS_CELL_CHAR_LIMIT = 49999

def export_project_to_sheets():
    """
    Versión final y funcional. Exporta el proyecto a Google Sheets
    ignorando todas las carpetas y archivos problemáticos identificados.
    """
    print("Iniciando la exportación del proyecto a Google Sheets (Versión Final)...")

    try:
        print("1/5 - Autenticando con Google...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        print("   -> Autenticación exitosa.")

        print(f"2/5 - Abriendo la hoja de cálculo '{SPREADSHEET_NAME}'...")
        sheet = client.open(SPREADSHEET_NAME).sheet1
        print("   -> Hoja de cálculo abierta.")

        print("3/5 - Preparando la hoja (limpiando y añadiendo encabezados)...")
        sheet.clear()
        sheet.append_row(["Ruta del Archivo", "Contenido del Archivo"])
        print("   -> Hoja preparada.")

        print("4/5 - Recopilando el contenido de los archivos del proyecto...")
        project_data = []
        files_skipped_size = 0
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in FOLDERS_TO_IGNORE]
            
            for filename in files:
                if filename.endswith(FILE_EXTENSIONS_TO_EXPORT):
                    filepath = os.path.join(root, filename).replace("\\", "/")
                    try:
                        file_size = os.path.getsize(filepath)
                        if file_size > MAX_FILE_SIZE_BYTES:
                            files_skipped_size += 1
                            continue
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        truncated_content = content[:SHEETS_CELL_CHAR_LIMIT]
                        project_data.append([filepath, truncated_content])
                    except Exception as e:
                        print(f"  -> ADVERTENCIA: No se pudo leer o procesar el archivo {filepath}. Error: {e}")
        
        print(f"   -> Se encontraron {len(project_data)} archivos válidos para exportar.")
        if files_skipped_size > 0:
            print(f"   -> Se ignoraron {files_skipped_size} archivos por ser demasiado grandes.")

        if project_data:
            print("5/5 - Escribiendo datos en Google Sheets...")
            # Volvemos al método eficiente de subir en lotes
            sheet.append_rows(project_data, value_input_option='USER_ENTERED')
            print(f"   -> Lote completo de {len(project_data)} archivos subido.")
        
        print("\n========================================================")
        print("¡ÉXITO! La exportación se ha completado correctamente.")
        print(f"Puedes revisar tu hoja de cálculo aquí: {sheet.spreadsheet.url}")
        print("========================================================")

    except Exception as e:
        print(f"\nHa ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    export_project_to_sheets()