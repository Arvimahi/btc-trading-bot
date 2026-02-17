import requests
import pandas as pd
import time
from datetime import datetime

print("Collecting data every 30 minutes...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Get data
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
        
        # Append to existing file
        import os
        if os.path.exists('data/btc_1min.csv'):
            existing = pd.read_csv('data/btc_1min.csv')
            combined = pd.concat([existing, result]).drop_duplicates(subset=['timestamp'])
            combined.to_csv('data/btc_1min.csv', index=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated: {len(combined)} total candles")
        else:
            result.to_csv('data/btc_1min.csv', index=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Created: {len(result)} candles")
        
        # Wait 30 minutes
        time.sleep(1800)
        
except KeyboardInterrupt:
    print("\n\nStopped")