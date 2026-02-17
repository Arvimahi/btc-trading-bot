import pandas as pd
import pickle

print("="*60)
print("BACKTEST - TESTING PROFITABILITY")
print("="*60)

BANKROLL = 20.0
POSITION_SIZE = 0.10
MIN_CONFIDENCE = 0.60

print(f"Bankroll: ${BANKROLL}")
print(f"Position: {POSITION_SIZE*100:.0f}% per trade")
print(f"Min confidence: {MIN_CONFIDENCE*100:.0f}%\n")

# Load model
with open('models/model.pkl', 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_columns']

# Load data
df_1min = pd.read_csv('data/btc_1min.csv')
df_1min['window'] = (df_1min.index // 5)

# Recreate test set
windows = []
for window_id in df_1min['window'].unique():
    window_data = df_1min[df_1min['window'] == window_id].copy()
    
    if len(window_data) < 5:
        continue
    
    data_before = window_data.iloc[:2]
    
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

df_test = pd.DataFrame(windows)

# Use last 20%
split = int(len(df_test) * 0.8)
X_test = df_test[feature_cols][split:]
y_test = df_test['target'][split:]

X_test_scaled = scaler.transform(X_test)

# Predict
predictions = model.predict(X_test_scaled)
probabilities = model.predict_proba(X_test_scaled)

# Backtest
bankroll = BANKROLL
trades = []

for i in range(len(X_test)):
    pred = predictions[i]
    prob = probabilities[i]
    confidence = prob[pred]
    
    if confidence < MIN_CONFIDENCE or bankroll < 0.5:
        continue
    
    bet = bankroll * POSITION_SIZE
    market_price = 0.50 + (confidence - 0.5) * 0.5
    tokens = bet / market_price
    actual = y_test.iloc[i]
    
    # Polymarket mechanics
    if pred == actual:
        profit = (tokens * 1.0) - bet  # Win
    else:
        profit = -bet  # Loss
    
    bankroll += profit
    
    trades.append({
        'bet': bet,
        'profit': profit,
        'bankroll': bankroll,
        'win': pred == actual
    })

if trades:
    df_trades = pd.DataFrame(trades)
    wins = df_trades['win'].sum()
    total = len(df_trades)
    
    print("RESULTS")
    print("="*60)
    print(f"Trades: {total}")
    print(f"Wins: {wins} ({wins/total*100:.1f}%)")
    print(f"Starting: ${BANKROLL:.2f}")
    print(f"Ending: ${bankroll:.2f}")
    print(f"Profit: ${bankroll - BANKROLL:+.2f}")
    print(f"Return: {(bankroll/BANKROLL - 1)*100:+.1f}%")
    
    df_trades.to_csv('data/backtest.csv', index=False)
    print("\n✅ Saved to data/backtest.csv")
    
    if bankroll > BANKROLL * 1.1:
        print("\n✅ PROFITABLE! Consider paper trading")
        print("Next: python3 paper_trade.py")
    elif bankroll > BANKROLL:
        print("\n⚠️ Slight profit - Be cautious")
    else:
        print("\n❌ LOSING - Collect more data")
else:
    print("No trades (confidence too low)")
