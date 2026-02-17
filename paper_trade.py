import requests
import pandas as pd
import pickle
import time
from datetime import datetime

print("="*60)
print("PAPER TRADING BOT - NO REAL MONEY")
print("="*60)

MIN_CONFIDENCE = 0.65
CHECK_INTERVAL = 60

print(f"Min confidence: {MIN_CONFIDENCE*100:.0f}%")
print(f"Checking every {CHECK_INTERVAL} seconds")
print("Press Ctrl+C to stop\n")

# Load model
with open('models/model.pkl', 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_columns']

trades = []

def get_btc_data():
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "BTCUSDT", "interval": "1m", "limit": 2}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df
    except:
        return None

def predict(data):
    features = {
        'start_price': data.iloc[0]['open'],
        'current_price': data.iloc[-1]['close'],
        'high': data['high'].max(),
        'low': data['low'].min(),
        'volume': data['volume'].sum(),
        'price_change': (data.iloc[-1]['close'] - data.iloc[0]['open']) / data.iloc[0]['open'],
        'green_candles': (data['close'] > data['open']).sum(),
        'volatility': data['close'].std(),
        'volume_trend': data['volume'].iloc[-1] / data['volume'].iloc[0] if data['volume'].iloc[0] > 0 else 1,
        'return_min1': data.iloc[0]['close'] / data.iloc[0]['open'] - 1,
        'return_min2': data.iloc[1]['close'] / data.iloc[1]['open'] - 1,
    }
    
    X = pd.DataFrame([features])
    for col in feature_cols:
        if col not in X.columns:
            X[col] = 0
    
    X = X[feature_cols]
    X_scaled = scaler.transform(X)
    
    pred = model.predict(X_scaled)[0]
    prob = model.predict_proba(X_scaled)[0]
    
    return {
        'prediction': 'UP' if pred == 1 else 'DOWN',
        'confidence': prob[pred],
        'btc_price': data.iloc[-1]['close']
    }

print("Monitoring...\n")

try:
    while True:
        data = get_btc_data()
        
        if data is not None and len(data) >= 2:
            result = predict(data)
            time_now = datetime.now().strftime("%H:%M:%S")
            
            if result['confidence'] >= MIN_CONFIDENCE:
                print(f"[{time_now}] 🎯 TRADE SIGNAL")
                print(f"  {result['prediction']} @ ${result['btc_price']:,.2f}")
                print(f"  Confidence: {result['confidence']*100:.1f}%\n")
                
                trades.append({
                    'time': datetime.now().isoformat(),
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'price': result['btc_price']
                })
            else:
                print(f"[{time_now}] {result['prediction']} {result['confidence']*100:.0f}% (low)")
        
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\n\nStopped")
    
    if trades:
        df = pd.DataFrame(trades)
        filename = f'data/paper_trades_{datetime.now().strftime("%Y%m%d")}.csv'
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(trades)} predictions to {filename}")
