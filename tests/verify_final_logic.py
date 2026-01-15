
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from config.settings import MOMENTUM_CONFIG
from src.paper_trading.paper_trader import PaperTrader

def test_sl_config():
    print("1. Checking Momentum SL Configuration...")
    sl = MOMENTUM_CONFIG['STOP_LOSS']
    expected_sl = 0.04
    if sl == expected_sl:
        print(f"   ✅ SUCCESS: Momentum SL is {sl*100}% (Expected: 4.0%)")
    else:
        print(f"   ❌ FAILURE: Momentum SL is {sl*100}% (Expected: 4.0%)")

def test_progressive_alerts():
    print("\n2. Checking Progressive Profit Alerts...")
    
    # Setup temporary test file
    test_file = 'data/test_portfolio.json'
    if os.path.exists(test_file):
        os.remove(test_file)
        
    trader = PaperTrader(capital=100000, portfolio_file=test_file)
    
    # Manually inject a position
    symbol = 'TEST_STOCK'
    entry_price = 100.0
    trader.positions[symbol] = {
        'symbol': symbol,
        'entry_price': entry_price,
        'shares': 10,
        'stop_loss': 96.0, # 4% SL
        'strategy': 'positional',
        'last_alert_milestone': 0.01 # Simulate last alert was at 1% or lower
    }
    
    # Case A: Price at 1.4% profit (Below 1.5% threshold)
    # Should NOT trigger alert
    print("   Test A: Price +1.4% (Below threshold)")
    current_prices = {symbol: 101.4}
    exits, alerts = trader.check_exits(current_prices)
    if not alerts:
        print("   ✅ Correct: No alert at 1.4%")
    else:
        print(f"   ❌ Failed: Unexpected alert at 1.4%: {alerts}")

    # Case B: Price at 1.6% profit (Crosses 1.5% threshold)
    # Should trigger 1.5% milestone
    print("   Test B: Price +1.6% (Crosses 1.5% threshold)")
    current_prices = {symbol: 101.6}
    exits, alerts = trader.check_exits(current_prices)
    
    milestone_alert = next((a for a in alerts if a.get('type') == 'PROFIT_MILESTONE'), None)
    if milestone_alert and milestone_alert['milestone'] == 0.015:
        print("   ✅ Correct: Alert triggered for 1.5% milestone")
    else:
        print(f"   ❌ Failed: Missing or incorrect alert for 1.6%: {alerts}")

    # Case C: Price at 1.8% profit (Same milestone, no new increase)
    # Should NOT trigger alert (already alerted 1.5%)
    print("   Test C: Price +1.8% (Same milestone level)")
    current_prices = {symbol: 101.8}
    exits, alerts = trader.check_exits(current_prices)
    if not any(a.get('type') == 'PROFIT_MILESTONE' for a in alerts):
         print("   ✅ Correct: No duplicate alert for same milestone")
    else:
         print(f"   ❌ Failed: Duplicate alert at 1.8%: {alerts}")

    # Case D: Price at 2.1% profit (Crosses 2.0% threshold)
    # Should trigger 2.0% milestone
    print("   Test D: Price +2.1% (Crosses 2.0% threshold)")
    current_prices = {symbol: 102.1}
    exits, alerts = trader.check_exits(current_prices)
    
    milestone_alert = next((a for a in alerts if a.get('type') == 'PROFIT_MILESTONE'), None)
    if milestone_alert and milestone_alert['milestone'] == 0.020:
        print("   ✅ Correct: Alert triggered for 2.0% milestone")
    else:
        print(f"   ❌ Failed: Missing or incorrect alert for 2.1%: {alerts}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_sl_config()
    test_progressive_alerts()
