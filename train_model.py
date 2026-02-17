import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("TRAINING BTC 2-MINUTE ENTRY MODEL")
print("="*60)

# Load data
df_1min = pd.read_csv('data/btc_1min.csv')
df_1min['window'] = (df_1min.index // 5)

print(f"Loaded {len(df_1min)} 1-minute candles")

# Create 2-minute entry features
ENTRY_POINT = 2
windows = []

for window_id in df_1min['window'].unique():
    window_data = df_1min[df_1min['window'] == window_id].copy()
    
    if len(window_data) < 5:
        continue
    
    data_before = window_data.iloc[:ENTRY_POINT]
    
    features = {
        'start_price': data_before.iloc[0]['open'],
        'current_price': data_before.iloc[-1]['close'],
        'high': data_before['high'].max(),
        'low': data_before['low'].min(),
        'volume': data_before['volume'].sum(),
        'price_change': (data_before.iloc[-1]['close'] - data_before.iloc[0]['open']) / data_before.iloc[0]['open'],
        'green_candles': (data_before['close'] > data_before['open']).sum(),
        'volatility': data_before['close'].std(),
        'volume_trend': data_before['volume'].iloc[-1] / data_before['volume'].iloc[0] if data_before['volume'].iloc[0] > 0 else 1,
        'return_min1': data_before.iloc[0]['close'] / data_before.iloc[0]['open'] - 1,
        'return_min2': data_before.iloc[1]['close'] / data_before.iloc[1]['open'] - 1,
    }
    
    final_price = window_data.iloc[-1]['close']
    current_price = data_before.iloc[-1]['close']
    features['target'] = 1 if final_price > current_price else 0
    
    windows.append(features)

df = pd.DataFrame(windows)
print(f"Created {len(df)} windows")

# Train
feature_cols = [col for col in df.columns if col != 'target']
X = df[feature_cols]
y = df['target']

split = int(len(df) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Try both models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=150, learning_rate=0.1, random_state=42)
}

best_acc = 0
best_model = None

for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"{name}: {acc*100:.2f}%")
    
    if acc > best_acc:
        best_acc = acc
        best_model = model

print(f"\n✅ Best: {best_acc*100:.2f}% accuracy")

# Save
os.makedirs('models', exist_ok=True)
model_data = {
    'model': best_model,
    'scaler': scaler,
    'feature_columns': feature_cols,
    'accuracy': best_acc
}

with open('models/model.pkl', 'wb') as f:
    pickle.dump(model_data, f)

print("✅ Saved to models/model.pkl")

if best_acc > 0.55:
    print("\n✅ GOOD! Accuracy >55% - Should be profitable")
    print("Next: python3 backtest.py")
elif best_acc > 0.52:
    print("\n⚠️ MARGINAL - May barely beat fees")
else:
    print("\n❌ TOO LOW - Need more data")
