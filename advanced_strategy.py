"""
ADVANCED STRATEGY - Hybrid Bot (Directional + Market Making)
Combines gabagool22 and PBot1 strategies
"""

import pandas as pd
import pickle
import requests
from datetime import datetime

print("="*70)
print("ADVANCED HYBRID STRATEGY")
print("Directional Trading + Market Making")
print("="*70)

class HybridStrategy:
    """
    Two strategies combined:
    1. Market Making: Buy both UP and DOWN at <50¢ (guaranteed profit)
    2. Directional: Strong bets when model is >65% confident
    """
    
    def __init__(self):
        # Load your 2-min model
        with open('models/2min_model.pkl', 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_cols = model_data['feature_columns']
    
    def check_market_making_opportunity(self, market_odds):
        """
        PBot1 Strategy: Market Making
        
        If you can buy BOTH sides for <$1 total, guaranteed profit!
        
        Example:
        - Buy UP at 47¢
        - Buy DOWN at 48¢
        - Total cost: 95¢
        - Payout: $1.00 (one side always wins)
        - Profit: 5¢ (5.3% return!)
        """
        up_price = market_odds.get('up', 0.50)
        down_price = market_odds.get('down', 0.50)
        
        total_cost = up_price + down_price
        
        # If total cost < $1.00, we have guaranteed profit
        if total_cost < 0.98:  # 2% buffer for fees
            profit_pct = ((1.00 - total_cost) / total_cost) * 100
            
            return {
                'strategy': 'MARKET_MAKING',
                'action': 'BUY_BOTH',
                'up_price': up_price,
                'down_price': down_price,
                'total_cost': total_cost,
                'guaranteed_profit': 1.00 - total_cost,
                'profit_pct': profit_pct,
                'risk': 'ZERO'  # Guaranteed profit!
            }
        
        return None
    
    def check_directional_opportunity(self, prediction, market_odds):
        """
        gabagool22 Strategy: Directional Trading
        
        When model is very confident, bet heavy on one side
        """
        confidence = prediction['confidence']
        direction = prediction['prediction']
        
        # Only trade if very confident
        if confidence < 0.65:
            return None
        
        # Get market price for our predicted direction
        market_price = market_odds.get(direction.lower(), 0.50)
        
        # Calculate edge: If we predict 70% but market prices at 50¢, we have edge
        implied_probability = market_price
        model_probability = confidence
        
        edge = model_probability - implied_probability
        
        # Only bet if we have significant edge
        if edge > 0.10:  # 10%+ edge
            expected_value = (model_probability * (1.00 - market_price)) - ((1 - model_probability) * market_price)
            
            return {
                'strategy': 'DIRECTIONAL',
                'action': f'BUY_{direction}',
                'direction': direction,
                'market_price': market_price,
                'model_confidence': confidence,
                'edge': edge,
                'expected_value': expected_value,
                'risk': 'MEDIUM'
            }
        
        return None
    
    def get_best_strategy(self, prediction, market_odds):
        """
        Decide which strategy to use
        
        Priority:
        1. Market Making (risk-free) - Always take if available
        2. Directional (high confidence) - Only if big edge
        """
        # Check market making first (risk-free!)
        mm_opp = self.check_market_making_opportunity(market_odds)
        
        if mm_opp:
            return mm_opp
        
        # If no market making opportunity, check directional
        dir_opp = self.check_directional_opportunity(prediction, market_odds)
        
        return dir_opp
    
    def calculate_position_size(self, strategy, bankroll):
        """
        Position sizing based on strategy
        
        Market Making: Larger size (low risk)
        Directional: Smaller size (higher risk)
        """
        if strategy['strategy'] == 'MARKET_MAKING':
            # Risk-free, so can use larger size
            return bankroll * 0.20  # 20% of bankroll
        
        elif strategy['strategy'] == 'DIRECTIONAL':
            # Use Kelly Criterion for directional bets
            edge = strategy['edge']
            confidence = strategy['model_confidence']
            
            # Kelly: f* = (p * b - q) / b
            # Simplified: f* = edge
            kelly_fraction = edge
            
            # Use fractional Kelly (safer)
            fractional_kelly = kelly_fraction * 0.25  # 25% of Kelly
            
            # Cap at 10% of bankroll
            position = min(bankroll * fractional_kelly, bankroll * 0.10)
            
            return position
        
        return 0


# Example usage
if __name__ == "__main__":
    strategy = HybridStrategy()
    
    # Simulate market odds
    print("\nExample 1: Market Making Opportunity")
    print("-" * 50)
    
    market_odds_1 = {'up': 0.47, 'down': 0.48}  # Total = 0.95
    prediction_1 = {'prediction': 'UP', 'confidence': 0.60}
    
    opportunity = strategy.get_best_strategy(prediction_1, market_odds_1)
    
    if opportunity:
        print(f"Strategy: {opportunity['strategy']}")
        print(f"Action: {opportunity['action']}")
        
        if opportunity['strategy'] == 'MARKET_MAKING':
            print(f"Buy UP at: ${opportunity['up_price']:.2f}")
            print(f"Buy DOWN at: ${opportunity['down_price']:.2f}")
            print(f"Total cost: ${opportunity['total_cost']:.2f}")
            print(f"Guaranteed profit: ${opportunity['guaranteed_profit']:.2f} ({opportunity['profit_pct']:.1f}%)")
            print(f"Risk: {opportunity['risk']}")
    
    print("\n" + "="*70)
    print("\nExample 2: Directional Opportunity")
    print("-" * 50)
    
    market_odds_2 = {'up': 0.45, 'down': 0.55}  # Normal pricing
    prediction_2 = {'prediction': 'UP', 'confidence': 0.70}  # Very confident
    
    opportunity = strategy.get_best_strategy(prediction_2, market_odds_2)
    
    if opportunity:
        print(f"Strategy: {opportunity['strategy']}")
        print(f"Action: {opportunity['action']}")
        print(f"Direction: {opportunity['direction']}")
        print(f"Market price: ${opportunity['market_price']:.2f}")
        print(f"Model confidence: {opportunity['model_confidence']*100:.0f}%")
        print(f"Edge: {opportunity['edge']*100:.0f}%")
        print(f"Expected value: ${opportunity['expected_value']:.4f}")
        print(f"Risk: {opportunity['risk']}")
    
    print("\n" + "="*70)
    print("KEY INSIGHTS FROM WHALE BOTS")
    print("="*70)
    
    print("\n1. PBot1 ($140K) - Market Making:")
    print("   - Buy BOTH sides at <50¢ each")
    print("   - Total cost <$1, payout = $1")
    print("   - Risk-free 3-5% per trade")
    print("   - Volume = profit (thousands of trades)")
    
    print("\n2. gabagool22 ($824K) - Hybrid:")
    print("   - Market make when possible (like PBot1)")
    print("   - Go directional when very confident")
    print("   - Your 62% model does this!")
    
    print("\n3. 0x1d00 ($190K) - Latency Arbitrage:")
    print("   - Sees price changes BEFORE Polymarket")
    print("   - Requires API speed (harder)")
    print("   - Your 2-min entry catches some of this")
    
    print("\n" + "="*70)
    print("YOUR ADVANTAGE")
    print("="*70)
    
    print("\n✅ You have 62% accuracy (proven in backtest)")
    print("✅ You have 2-min entry timing (catches momentum)")
    print("✅ You can add market making (risk-free layer)")
    
    print("\n💡 RECOMMENDED STRATEGY:")
    print("   1. Always check for market making first")
    print("   2. If both sides <50¢, buy both (risk-free)")
    print("   3. If no market making, use your model")
    print("   4. Only bet directional if >65% confident")
    
    print("\n" + "="*70)
