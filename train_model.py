import yfinance as yf
import pandas as pd
import numpy as np
import ta
import json
from datetime import datetime
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
import matplotlib.pyplot as plt

def train_ia_model():
    print("Paso 1: Descargando datos históricos de BTC-USD...")
    try:
        data = yf.download('BTC-USD', period='5y', interval='1d', auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError("No se pudieron descargar datos.")
        print("✅ Datos descargados correctamente.")
    except Exception as e:
        print(f"❌ Error al descargar datos: {e}")
        return

    print("Paso 2: Calculando indicadores técnicos...")

    close = pd.Series(data['Close'].to_numpy().ravel(), index=data.index)
    high = pd.Series(data['High'].to_numpy().ravel(), index=data.index)
    low = pd.Series(data['Low'].to_numpy().ravel(), index=data.index)
    volume = pd.Series(data['Volume'].to_numpy().ravel(), index=data.index)

    data['sma_20'] = ta.trend.SMAIndicator(close=close, window=20).sma_indicator()
    data['sma_50'] = ta.trend.SMAIndicator(close=close, window=50).sma_indicator()
    data['rsi'] = ta.momentum.RSIIndicator(close=close, window=14).rsi()

    macd = ta.trend.MACD(close=close)
    data['macd'] = macd.macd()
    data['macd_signal'] = macd.macd_signal()
    data['macd_diff'] = macd.macd_diff()

    data['stochrsi'] = ta.momentum.StochRSIIndicator(close=close, window=14).stochrsi()
    data['obv'] = ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
    data['bb_width'] = ta.volatility.BollingerBands(close=close, window=20).bollinger_wband()
    data['atr'] = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    data['momentum'] = close - close.shift(14)

    print("✅ Indicadores técnicos calculados.")

    print("Paso 3: Limpiando NaNs...")
    data.dropna(inplace=True)
    if data.empty:
        print("❌ Error: El DataFrame quedó vacío tras limpiar NaNs.")
        return

    data['Date'] = data.index

    print("Paso 4: Incorporando estrategias de contexto...")
    try:
        contexto_df = pd.read_csv("data/estrategias_contexto.csv")
        contexto_df = contexto_df[contexto_df["fecha"] != "sin_fecha"]
        contexto_df["fecha"] = pd.to_datetime(contexto_df["fecha"])
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.merge(contexto_df[["fecha", "tipo"]], left_on="Date", right_on="fecha", how="left")
        data["contexto_estrategia"] = data["tipo"].notnull().astype(int)
        data.drop(columns=["fecha", "tipo"], inplace=True)
        print("✅ Contexto incorporado.")
    except FileNotFoundError:
        print("⚠️  Advertencia: No se encontró 'estrategias_contexto.csv'. Se continuará sin contexto.")
        data["contexto_estrategia"] = 0

    print("Paso 5: Creando variable objetivo binaria (sube/baja)...")
    price_diff = data['Close'].shift(-1) - data['Close']
    data['target'] = np.where(price_diff > 0, 1, np.where(price_diff < 0, 0, np.nan))
    data.dropna(inplace=True)

    print("✅ Distribución de clases:")
    print(data['target'].value_counts())

    features = [
        'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'macd_diff',
        'stochrsi', 'obv', 'bb_width', 'atr', 'momentum', 'contexto_estrategia'
    ]
    X = data[features]
    y = data['target']

    print("Paso 6: Configurando validación cruzada temporal...")
    tscv = TimeSeriesSplit(n_splits=5)

    print("Paso 7: Buscando hiperparámetros óptimos (GridSearchCV)...")
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    grid_search = GridSearchCV(
        estimator=XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            use_label_encoder=False,
            random_state=42
        ),
        param_grid=param_grid,
        cv=tscv,
        n_jobs=-1,
        verbose=2,
        scoring='accuracy'
    )

    grid_search.fit(X, y)
    model = grid_search.best_estimator_

    print("\n✅ Resultados GridSearchCV:")
    print("🔍 Mejores parámetros encontrados:", grid_search.best_params_)
    print("✅ Mejor puntuación (accuracy):", grid_search.best_score_)

    # 🧠 Tip adicional: Guardar los mejores parámetros
    os.makedirs("models", exist_ok=True)
    with open("models/best_params.json", "w") as f:
        json.dump(grid_search.best_params_, f)

    print("Paso 8: Importancia de variables...")
    importances = model.feature_importances_
    feature_series = pd.Series(importances, index=features).sort_values(ascending=False)

    plt.figure(figsize=(10, 6))
    feature_series.plot(kind='bar', title='Importancia de Features del Modelo')
    plt.ylabel('Importancia')
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    print("✅ Gráfico guardado como 'feature_importance.png'.")

    print("Paso 9: Evaluación final sobre todos los datos...")
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"✅ Precisión final sobre el dataset completo: {accuracy:.4f}")

    print("Paso 10: Guardando modelo y log...")
    joblib.dump(model, "models/model.joblib")

    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_type': 'binary',
        'best_cv_accuracy': round(grid_search.best_score_, 4),
        'final_accuracy_on_full_data': round(accuracy, 4),
        'best_params': grid_search.best_params_
    }

    log_file = 'training_log.json'
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_entry)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=4)

    print("✅ Entrenamiento completado y modelo guardado correctamente.")

if __name__ == '__main__':
    train_ia_model()
