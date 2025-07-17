import subprocess

def ejecutar_script(nombre, archivo):
    print(f"\n🔷 {nombre}")
    print("--------------------------------------------------")
    try:
        resultado = subprocess.run(["python", archivo], check=True, text=True)
        print("✅ Completado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando {archivo}:")
        print(e)
        exit(1)

if __name__ == '__main__':
    print("\n🚀 INICIANDO PIPELINE COMPLETO DE TRADING IA")
    print("==================================================")

    ejecutar_script("Paso 1: Entrenando modelo con IA (train_model.py)", "train_model.py")
    ejecutar_script("Paso 2: Ejecutando predicción con el modelo entrenado (predict.py)", "predict.py")
    ejecutar_script("Paso 3: Backtest de estrategia sobre datos históricos (backtest.py)", "backtest.py")

    print("\n🎯 TODOS LOS PROCESOS SE EJECUTARON EXITOSAMENTE")
    print("==================================================\n")
