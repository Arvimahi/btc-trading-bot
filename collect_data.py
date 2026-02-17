import requests
import pandas as pd
import os

os.makedirs("data", exist_ok=True)

print("Collecting BTC 1-minute data...")

url = "https://api.binance.com/api/v3/klines"
params = {"symbol": "BTCUSDT", "interval": "1m", "limit": 1000}

response = requests.get(url, params=params, timeout=10)
data = response.json()

df = pd.DataFrame(data, columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
    'taker_buy_quote', 'ignore'
])

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = df[col].astype(float)

result = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades']]
result.to_csv('data/btc_1min.csv', index=False)

print(f"✅ Saved {len(result)} candles to data/btc_1min.csv")
print(f"Range: {result['timestamp'].min()} to {result['timestamp'].max()}")
print("\nNext: python3 train_model.py")
