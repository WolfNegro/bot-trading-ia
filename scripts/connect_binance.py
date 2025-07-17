# scripts/connect_binance.py (Versión Final y Limpia)

import os
from binance.client import Client
from dotenv import load_dotenv

def get_binance_client(testnet=False):
    """
    Crea y devuelve un cliente de Binance, cargando las variables de entorno
    desde el archivo .env ubicado en la raíz del proyecto.
    
    Args:
        testnet (bool): Si es True, se conecta al entorno de Testnet.
    
    Returns:
        binance.client.Client: El cliente de Binance inicializado.
    """
    # Encuentra la ruta raíz del proyecto y el .env de forma explícita
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    
    # Carga las variables desde esa ruta específica
    load_dotenv(dotenv_path=dotenv_path)
    
    if testnet:
        api_key = os.getenv("BINANCE_TESTNET_API_KEY")
        api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")
        if not api_key or not api_secret:
            raise ValueError("❌ Error: BINANCE_TESTNET_API_KEY y BINANCE_TESTNET_API_SECRET deben estar definidos en el archivo .env de la raíz.")
        
        client = Client(api_key, api_secret, testnet=True)
        # El mensaje de conexión se imprimirá desde el bot principal si es necesario.
    else:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        if not api_key or not api_secret:
            raise ValueError("❌ Error: BINANCE_API_KEY y BINANCE_API_SECRET deben estar definidos en el archivo .env de la raíz.")
        
        client = Client(api_key, api_secret)

    return client

def test_connection(testnet=True):
    """
    Prueba la conexión obteniendo los saldos de la cuenta.
    Se usa principalmente para verificar que las claves API son correctas.
    """
    try:
        print(f"--- Probando conexión al {'Testnet' if testnet else 'Entorno Real'} ---")
        client = get_binance_client(testnet=testnet)
        # Imprimimos el mensaje de conexión aquí para el test
        print(f"🔌 Conectando al {'Testnet' if testnet else 'Entorno Real'} de Binance...")
        account_info = client.get_account()
        
        print("✅ Conexión exitosa.")
        print("🏦 Saldos disponibles:")
        for asset in account_info['balances']:
            if float(asset['free']) > 0:
                print(f"  -> {asset['asset']}: {asset['free']}")
    except Exception as e:
        print(f"❌ Error al conectar con Binance: {e}")

# Este bloque solo se ejecuta si corres 'python scripts/connect_binance.py'
if __name__ == "__main__":
    test_connection(testnet=True)