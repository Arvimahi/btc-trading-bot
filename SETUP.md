# COMPLETE SETUP GUIDE

---

## INSTALLATION (2 Minutes)

### Step 1: Install Python
Check if installed:
```bash
python3 --version
```

If not: Download from python.org

### Step 2: Install Packages
```bash
pip3 install -r requirements.txt
```

If error:
```bash
pip3 install requests pandas numpy scikit-learn
```

---

## RUNNING THE BOT (5 Minutes)

### Step 1: Collect Data
```bash
python3 collect_data.py
```

**Output:**
```
✅ Saved 1000 candles
Next: python3 train_model.py
```

**Creates:** `data/btc_1min.csv`

---

### Step 2: Train Model
```bash
python3 train_model.py
```

**Output:**
```
Random Forest: 62.50%
✅ GOOD! Accuracy >55%
Next: python3 backtest.py
```

**Creates:** `models/model.pkl`

---

### Step 3: Backtest
```bash
python3 backtest.py
```

**Output:**
```
Trades: 35
Wins: 22 (62.9%)
Profit: +$3.06 (+15.3%)
✅ PROFITABLE!
```

**Creates:** `data/backtest.csv`

---

### Step 4: Paper Trade (Optional)
```bash
python3 paper_trade.py
```

**Output:**
```
[14:23:45] 🎯 TRADE SIGNAL
  UP @ $68,234.50
  Confidence: 67.2%
```

Runs forever. Press Ctrl+C to stop.

**Creates:** `data/paper_trades_YYYYMMDD.csv`

---

## FOLDER STRUCTURE

After running:
```
your-folder/
├── collect_data.py
├── train_model.py
├── backtest.py
├── paper_trade.py
├── requirements.txt
├── README.md
├── WHALE_STRATEGY.md
├── SETUP.md
├── data/
│   ├── btc_1min.csv
│   ├── backtest.csv
│   └── paper_trades_*.csv
└── models/
    └── model.pkl
```

---

## TROUBLESHOOTING

**"Module not found"**
```bash
pip3 install -r requirements.txt
```

**"No file: data/btc_1min.csv"**
```bash
python3 collect_data.py
```

**"Accuracy too low"**
- BTC might be too random today
- Collect fresh data tomorrow
- Try again

**"No trades in backtest"**
- Lower MIN_CONFIDENCE in backtest.py
- Or collect more data

---

## CONFIGURATION

Edit these values:

**backtest.py:**
```python
BANKROLL = 20.0          # Your money
POSITION_SIZE = 0.10     # 10% per trade
MIN_CONFIDENCE = 0.60    # 60% minimum
```

**paper_trade.py:**
```python
MIN_CONFIDENCE = 0.65    # Higher = fewer trades
CHECK_INTERVAL = 60      # Seconds between checks
```

---

## DAILY ROUTINE

**Every day:**
```bash
python3 collect_data.py  # Get fresh data
```

**Every week:**
```bash
python3 train_model.py   # Retrain
python3 backtest.py      # Test
```

---

## LIVE TRADING (Future)

**After paper trading proves profitable:**

1. Create Polymarket account
2. Get API credentials
3. Fund with USDC ($20+)
4. Build live trading bot
5. Start with $1-2 per trade
6. Scale slowly if profitable

**Not recommended until:**
- 2+ weeks paper trading
- Consistent 55%+ win rate
- Understand all risks

---

## NEXT STEPS

**Right now:**
```bash
pip3 install -r requirements.txt
python3 collect_data.py
python3 train_model.py
python3 backtest.py
```

**If profitable:**
- Paper trade 1-2 weeks
- Track results
- Consider live trading

**If not:**
- Collect more data
- Try different times
- Accept it might not work

---

Total time: 10 minutes to test everything!
