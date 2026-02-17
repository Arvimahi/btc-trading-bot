"""
CHAINLINK DELAY ARBITRAGE BOT
================================
Polymarket resolves using Chainlink oracle (1-min delayed)
Strategy: Compare real Binance price vs Chainlink price
In final 60 seconds of market, resolution is KNOWN
"""

import requests
import time
from datetime import datetime, timezone
import json

# Chainlink BTC/USD on Polygon
# Contract: 0xc907E116054Ad103354f2D350FD2514433D57F6f
CHAINLINK_CONTRACT = "0xc907E116054Ad103354f2D350FD2514433D57F6f"
POLYGON_RPC = "https://polygon-rpc.com"

def get_binance_price():
    """Get REAL current BTC price from Binance"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCUSDT"}
        response = requests.get(url, params=params, timeout=3)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Binance error: {e}")
        return None

def get_chainlink_price():
    """
    Get Chainlink BTC/USD price from Polygon
    This is what Polymarket uses to RESOLVE markets
    Has ~1 minute delay vs real price
    """
    try:
        # Using Polygon RPC to call Chainlink contract
        # latestRoundData() function signature
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [
                {
                    "to": CHAINLINK_CONTRACT,
                    "data": "0xfeaf968c"  # latestRoundData() selector
                },
                "latest"
            ],
            "id": 1
        }

        response = requests.post(POLYGON_RPC, json=payload, timeout=5)
        result = response.json()

        if 'result' in result and result['result'] != '0x':
            raw = result['result']

            # Decode: roundId, answer, startedAt, updatedAt, answeredInRound
            # Each field is 32 bytes (64 hex chars)
            if len(raw) >= 194:
                answer_hex = raw[66:130]  # Second field = price
                updated_hex = raw[130:194]  # Fourth field = timestamp

                # Convert price (8 decimal places for BTC/USD)
                price = int(answer_hex, 16) / 1e8

                # Convert timestamp
                updated_at = int(updated_hex, 16)
                updated_time = datetime.fromtimestamp(updated_at, tz=timezone.utc)

                return {
                    'price': price,
                    'updated_at': updated_time,
                    'timestamp': updated_at
                }

        return None

    except Exception as e:
        print(f"Chainlink error: {e}")
        return None

def calculate_delay(chainlink_data):
    """Calculate how delayed Chainlink is vs current time"""
    if not chainlink_data:
        return None

    now = datetime.now(timezone.utc)
    delay_seconds = (now - chainlink_data['updated_at']).total_seconds()
    return delay_seconds

def monitor_prices():
    """
    Main monitoring loop
    Compares Binance (real) vs Chainlink (delayed)
    Detects arbitrage opportunities
    """
    print("="*70)
    print("CHAINLINK DELAY ARBITRAGE MONITOR")
    print("="*70)
    print("\nMonitoring price gap between Binance and Chainlink...")
    print("Press Ctrl+C to stop\n")

    prev_chainlink_price = None

    while True:
        try:
            # Get both prices
            binance_price = get_binance_price()
            chainlink_data = get_chainlink_price()

            if binance_price and chainlink_data:
                chainlink_price = chainlink_data['price']
                delay = calculate_delay(chainlink_data)

                # Price difference
                price_diff = binance_price - chainlink_price
                price_diff_pct = (price_diff / chainlink_price) * 100

                now = datetime.now().strftime("%H:%M:%S")

                print(f"[{now}]")
                print(f"  Binance (REAL):    ${binance_price:,.2f}")
                print(f"  Chainlink (ORACLE): ${chainlink_price:,.2f}")
                print(f"  Difference:        ${price_diff:+.2f} ({price_diff_pct:+.3f}%)")
                print(f"  Oracle delay:      {delay:.0f} seconds")

                # Detect significant gap
                if abs(price_diff_pct) > 0.3:
                    direction = "UP" if price_diff > 0 else "DOWN"
                    print(f"\n  🚨 OPPORTUNITY DETECTED!")
                    print(f"  Real BTC moved {price_diff_pct:+.3f}%")
                    print(f"  Chainlink hasn't updated yet")
                    print(f"  Expected resolution: {direction}")
                    print(f"  Edge: Buy {direction} before oracle updates\n")

                # Detect when Chainlink just updated
                if prev_chainlink_price and chainlink_price != prev_chainlink_price:
                    change = chainlink_price - prev_chainlink_price
                    print(f"\n  ⚡ CHAINLINK JUST UPDATED!")
                    print(f"  Old: ${prev_chainlink_price:,.2f}")
                    print(f"  New: ${chainlink_price:,.2f}")
                    print(f"  Change: ${change:+.2f}\n")

                prev_chainlink_price = chainlink_price
                print()

            time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print("\n\nStopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_prices()
