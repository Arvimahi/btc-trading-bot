"""
MARKET RESOLUTION PREDICTOR
==============================
Uses Chainlink delay to predict market resolution
with near-certainty in final 60 seconds

How it works:
- Polymarket 5-min market opens at :00
- Resolves at :05 using Chainlink price
- Chainlink is ~60 seconds delayed
- At :04:00, Chainlink shows price from ~:03:00
- Real price at :04:00 ≈ resolution price
- BUY in final 60 seconds with high certainty
"""

import requests
import time
from datetime import datetime, timezone
import os

# Chainlink Contract
CHAINLINK_CONTRACT = "0xc907E116054Ad103354f2D350FD2514433D57F6f"
POLYGON_RPC = "https://polygon-rpc.com"

def get_binance_price():
    """Real-time BTC price"""
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=3
        )
        return float(r.json()['price'])
    except:
        return None

def get_chainlink_price():
    """Chainlink oracle price (what Polymarket uses)"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": CHAINLINK_CONTRACT,
                "data": "0xfeaf968c"
            }, "latest"],
            "id": 1
        }

        r = requests.post(POLYGON_RPC, json=payload, timeout=5)
        result = r.json()

        if 'result' in result and len(result['result']) >= 194:
            raw = result['result']
            price = int(raw[66:130], 16) / 1e8
            updated_at = int(raw[130:194], 16)
            return {
                'price': price,
                'updated_at': datetime.fromtimestamp(updated_at, tz=timezone.utc)
            }
        return None
    except:
        return None

def get_market_window():
    """
    Calculate current 5-minute market window
    Returns: seconds remaining in current window
    """
    now = datetime.now(timezone.utc)
    seconds_in_window = now.second + (now.minute % 5) * 60
    remaining = 300 - seconds_in_window  # 300 = 5 minutes
    elapsed = seconds_in_window
    return elapsed, remaining

def predict_resolution(market_strike_price, current_real_price, direction):
    """
    Predict if market will resolve UP or DOWN

    market_strike_price: The price BTC must be above/below
    current_real_price: Real Binance price right now
    direction: 'UP' or 'DOWN' (market question)
    """
    if direction == 'UP':
        will_resolve_up = current_real_price > market_strike_price
        confidence = abs(current_real_price - market_strike_price) / market_strike_price
        return 'YES' if will_resolve_up else 'NO', confidence
    else:
        will_resolve_down = current_real_price < market_strike_price
        confidence = abs(current_real_price - market_strike_price) / market_strike_price
        return 'YES' if will_resolve_down else 'NO', confidence

def run_predictor():
    """
    Main loop: Monitor market windows and predict resolutions
    """
    print("="*70)
    print("MARKET RESOLUTION PREDICTOR")
    print("Using Chainlink Delay for Near-Certain Predictions")
    print("="*70)
    print("\nStrategy:")
    print("  - Chainlink is ~60 seconds delayed")
    print("  - At minute 4 of a 5-min market")
    print("  - Real price ≈ Resolution price")
    print("  - Buy with HIGH confidence in final 60 seconds")
    print("\nPress Ctrl+C to stop\n")

    opportunities_found = 0
    best_windows = []

    while True:
        try:
            elapsed, remaining = get_market_window()
            binance_price = get_binance_price()
            chainlink_data = get_chainlink_price()

            if not binance_price or not chainlink_data:
                time.sleep(1)
                continue

            chainlink_price = chainlink_data['price']
            now = datetime.now(timezone.utc)
            oracle_delay = (now - chainlink_data['updated_at']).total_seconds()

            time_str = datetime.now().strftime("%H:%M:%S")

            # THE GOLDEN WINDOW: 60-30 seconds before market close
            # This is when you know the outcome with high certainty
            if 240 <= elapsed <= 270:  # 4:00 to 4:30 into window
                price_diff_pct = ((binance_price - chainlink_price) / chainlink_price) * 100

                print(f"\n{'='*70}")
                print(f"⚡ GOLDEN WINDOW - {remaining} SECONDS REMAINING")
                print(f"{'='*70}")
                print(f"\n[{time_str}]")
                print(f"  Real BTC (Binance):  ${binance_price:,.2f}")
                print(f"  Oracle (Chainlink):  ${chainlink_price:,.2f}")
                print(f"  Oracle Delay:        {oracle_delay:.0f} seconds")
                print(f"  Price Gap:           {price_diff_pct:+.3f}%")

                if oracle_delay > 45:
                    print(f"\n  🎯 HIGH CONFIDENCE OPPORTUNITY!")
                    print(f"  Oracle is {oracle_delay:.0f}s delayed")
                    print(f"  Real price will be used for resolution")

                    if binance_price > chainlink_price * 1.001:
                        prediction = "UP"
                        print(f"\n  Prediction: ✅ BTC is UP")
                        print(f"  Action: BUY 'UP' on Polymarket NOW")
                        print(f"  Time remaining: {remaining} seconds")
                    elif binance_price < chainlink_price * 0.999:
                        prediction = "DOWN"
                        print(f"\n  Prediction: ✅ BTC is DOWN")
                        print(f"  Action: BUY 'DOWN' on Polymarket NOW")
                        print(f"  Time remaining: {remaining} seconds")
                    else:
                        prediction = "NEUTRAL"
                        print(f"\n  Too close to call - SKIP this market")

                    opportunities_found += 1

                else:
                    print(f"\n  Oracle delay only {oracle_delay:.0f}s - marginal")

            # Normal monitoring
            elif remaining % 30 == 0 or remaining <= 10:
                print(f"[{time_str}] "
                      f"Elapsed: {elapsed:3.0f}s | "
                      f"Remaining: {remaining:3.0f}s | "
                      f"Binance: ${binance_price:,.0f} | "
                      f"Oracle: ${chainlink_price:,.0f} | "
                      f"Delay: {oracle_delay:.0f}s")

            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\nStopped")
            print(f"Opportunities detected: {opportunities_found}")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_predictor()
