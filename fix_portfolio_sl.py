"""
🔧 Portfolio Stop Loss Correction Script

This script:
1. Updates all active positions' stop loss from 2% to 3%
2. Analyzes stopped-out trades to see which would survive with 3% SL
3. Reactivates positions that shouldn't have been stopped at 3% SL

Usage:
    python fix_portfolio_sl.py
"""

import json
import yfinance as yf
from datetime import datetime
from pathlib import Path

# Portfolio files
SWING_PORTFOLIO = 'data/swing_portfolio.json'
SWING_TRADES = 'data/swing_trades.json'
POSITIONAL_PORTFOLIO = 'data/positional_portfolio.json'
POSITIONAL_TRADES = 'data/positional_trades.json'

# Stop loss settings
OLD_SWING_SL = 0.02  # 2%
NEW_SWING_SL = 0.03  # 3%
POSITIONAL_SL = 0.04  # 4% (unchanged)


def load_json(file_path):
    """Load JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"⚠️ Invalid JSON in: {file_path}")
        return None


def save_json(file_path, data):
    """Save JSON file with backup"""
    # Create backup
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if Path(file_path).exists():
        import shutil
        shutil.copy(file_path, backup_path)
        print(f"   💾 Backup created: {backup_path}")

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   ✅ Updated: {file_path}")


def get_current_price(symbol):
    """Fetch current price for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"   ⚠️ Error fetching price for {symbol}: {e}")
    return None


def update_active_positions(portfolio_data, strategy_type='swing'):
    """Update stop losses in active positions"""
    if not portfolio_data or 'positions' not in portfolio_data:
        return portfolio_data, []

    updated_positions = []

    for symbol, position in portfolio_data['positions'].items():
        entry_price = position['entry_price']
        old_sl = position['stop_loss']

        # Calculate what the new SL should be
        if strategy_type == 'swing':
            new_sl = entry_price * (1 - NEW_SWING_SL)
        else:  # positional
            new_sl = entry_price * (1 - POSITIONAL_SL)

        # Update if different
        if abs(old_sl - new_sl) > 0.01:  # More than 1 paisa difference
            position['stop_loss'] = round(new_sl, 2)
            updated_positions.append({
                'symbol': symbol,
                'entry': entry_price,
                'old_sl': old_sl,
                'new_sl': new_sl,
                'change': new_sl - old_sl
            })

    portfolio_data['last_updated'] = datetime.now().isoformat()

    return portfolio_data, updated_positions


def analyze_stopped_trades(trades_data, strategy_type='swing'):
    """Find trades that were stopped at 2% but would survive at 3%"""
    if not trades_data:
        return []

    reactivate_candidates = []

    for trade in trades_data:
        # Only check STOP_LOSS exits
        if 'STOP_LOSS' not in trade.get('reason', ''):
            continue

        symbol = trade['symbol']
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        exit_date = trade['exit_date']

        # Calculate what 3% SL would have been
        if strategy_type == 'swing':
            new_sl = entry_price * (1 - NEW_SWING_SL)
        else:
            new_sl = entry_price * (1 - POSITIONAL_SL)

        # Would this trade have survived with 3% SL?
        if exit_price > new_sl:
            # Yes! This stock shouldn't have been stopped out
            print(f"\n   🔍 {symbol} - Stopped at 2% but would survive at 3%")
            print(f"      Entry: ₹{entry_price:.2f}")
            print(f"      Exit (2% SL): ₹{exit_price:.2f}")
            print(f"      3% SL would be: ₹{new_sl:.2f}")
            print(f"      Exit date: {exit_date}")

            # Get current price
            current_price = get_current_price(symbol)

            if current_price:
                print(f"      Current price: ₹{current_price:.2f}")

                # Check if it's still above 3% SL
                if current_price > new_sl:
                    pnl_percent = (current_price - entry_price) / entry_price * 100
                    print(f"      ✅ Still alive! Current P&L: {pnl_percent:+.2f}%")

                    reactivate_candidates.append({
                        'trade': trade,
                        'current_price': current_price,
                        'new_sl': new_sl,
                        'would_be_alive': True,
                        'current_pnl_percent': pnl_percent
                    })
                else:
                    print(f"      ❌ Would have been stopped anyway at 3% SL")
            else:
                print(f"      ⚠️ Couldn't fetch current price")

    return reactivate_candidates


def reactivate_position(portfolio_data, candidate, strategy_type='swing'):
    """Reactivate a position that shouldn't have been stopped"""
    trade = candidate['trade']
    symbol = trade['symbol']

    # Recreate position
    position = {
        'symbol': symbol,
        'shares': trade['shares'],
        'initial_shares': trade['shares'],
        'entry_price': trade['entry_price'],
        'entry_date': trade['entry_date'],
        'trade_type': trade['trade_type'],
        'target1': trade.get('target1', 0),
        'target2': trade.get('target2', 0),
        'target3': trade.get('target3', 0),
        'stop_loss': candidate['new_sl'],
        'score': trade.get('score', 7.0),
        'cost': trade['shares'] * trade['entry_price'],
        'max_holding_days': 7 if strategy_type == 'swing' else 30,
        'strategy': strategy_type,
        'signal_type': trade.get('signal_type', 'MOMENTUM'),
        't1_hit': False,
        't2_hit': False,
        't3_hit': False
    }

    # Add to portfolio
    portfolio_data['positions'][symbol] = position

    # Reduce capital (money is now invested again)
    portfolio_data['capital'] -= position['cost']

    return portfolio_data


def main():
    print("\n" + "="*70)
    print("🔧 PORTFOLIO STOP LOSS CORRECTION")
    print("="*70)
    print(f"\nUpdating stop losses:")
    print(f"  Swing: {OLD_SWING_SL*100}% → {NEW_SWING_SL*100}%")
    print(f"  Positional: {POSITIONAL_SL*100}% (unchanged)")
    print("\n" + "="*70)

    # Process SWING portfolio
    print("\n📊 SWING PORTFOLIO")
    print("-" * 70)

    swing_portfolio = load_json(SWING_PORTFOLIO)
    swing_trades = load_json(SWING_TRADES)

    if swing_portfolio:
        print("\n1️⃣ Updating active positions...")
        swing_portfolio, updated = update_active_positions(swing_portfolio, 'swing')

        if updated:
            print(f"\n   Updated {len(updated)} positions:")
            for pos in updated:
                print(f"   • {pos['symbol']}: ₹{pos['old_sl']:.2f} → ₹{pos['new_sl']:.2f} ({pos['change']:+.2f})")
        else:
            print("   ℹ️ No positions to update")

        print("\n2️⃣ Analyzing stopped trades...")
        candidates = analyze_stopped_trades(swing_trades, 'swing')

        if candidates:
            print(f"\n   📋 Found {len(candidates)} positions to reactivate")

            # Ask user confirmation
            print("\n   Do you want to reactivate these positions? (yes/no)")
            response = input("   > ").strip().lower()

            if response in ['yes', 'y']:
                for candidate in candidates:
                    symbol = candidate['trade']['symbol']
                    print(f"   ✅ Reactivating {symbol}")
                    swing_portfolio = reactivate_position(swing_portfolio, candidate, 'swing')
            else:
                print("   ⏭️ Skipping reactivation")
        else:
            print("   ℹ️ No positions to reactivate")

        # Save updated portfolio
        save_json(SWING_PORTFOLIO, swing_portfolio)

    # Process POSITIONAL portfolio
    print("\n📊 POSITIONAL PORTFOLIO")
    print("-" * 70)

    positional_portfolio = load_json(POSITIONAL_PORTFOLIO)
    positional_trades = load_json(POSITIONAL_TRADES)

    if positional_portfolio:
        print("\n1️⃣ Checking active positions (4% SL should be unchanged)...")
        positional_portfolio, updated = update_active_positions(positional_portfolio, 'positional')

        if updated:
            print(f"\n   Updated {len(updated)} positions:")
            for pos in updated:
                print(f"   • {pos['symbol']}: ₹{pos['old_sl']:.2f} → ₹{pos['new_sl']:.2f}")
        else:
            print("   ℹ️ No positions to update")

        print("\n2️⃣ Analyzing stopped trades...")
        candidates = analyze_stopped_trades(positional_trades, 'positional')

        if candidates:
            print(f"\n   📋 Found {len(candidates)} positions to reactivate")

            # Ask user confirmation
            print("\n   Do you want to reactivate these positions? (yes/no)")
            response = input("   > ").strip().lower()

            if response in ['yes', 'y']:
                for candidate in candidates:
                    symbol = candidate['trade']['symbol']
                    print(f"   ✅ Reactivating {symbol}")
                    positional_portfolio = reactivate_position(positional_portfolio, candidate, 'positional')
            else:
                print("   ⏭️ Skipping reactivation")
        else:
            print("   ℹ️ No positions to reactivate")

        # Save updated portfolio
        save_json(POSITIONAL_PORTFOLIO, positional_portfolio)

    print("\n" + "="*70)
    print("✅ PORTFOLIO CORRECTION COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  • Active positions updated with new stop losses")
    print("  • Stopped trades analyzed for reactivation")
    print("  • Backups created before any changes")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
