import json
import yfinance as yf
import os
from datetime import datetime

def analyze_portfolio():
    filepath = 'data/positional_portfolio.json'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    positions = data.get('positions', {})
    if not positions:
        print("No open positions found.")
        return

    print(f"\n📊 PORTFOLIO ANALYSIS ({len(positions)} positions)")
    print("=" * 60)
    print(f"{'SYMBOL':<15} {'SHARES':<8} {'ENTRY':<10} {'CURRENT':<10} {'P&L %':<10} {'STATUS'}")
    print("-" * 70)

    for symbol, pos in positions.items():
        entry_price = pos['entry_price']
        stop_loss = pos['stop_loss']
        shares = pos.get('shares', 0)
        
        # Fetch current price
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
            else:
                # Fallback to daily if 1m fails
                hist = ticker.history(period="1d")
                current_price = hist['Close'].iloc[-1]
        except Exception as e:
            print(f"{symbol:<15} {shares:<8} Error fetching price")
            continue

        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        status = "🟢 HOLD"
        if current_price < stop_loss:
            status = "🔴 EXIT (SL HIT)"
        elif pnl_pct < -2.0:
            status = "🟡 HOLD (Pullback)"
        elif pnl_pct > 1.0:
            status = "🟢 PROFIT"

        print(f"{symbol:<15} {shares:<8} ₹{entry_price:<9.2f} ₹{current_price:<9.2f} {pnl_pct:>+6.2f}%    {status}")

    print("=" * 70)

if __name__ == "__main__":
    analyze_portfolio()
