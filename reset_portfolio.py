"""
🔄 PORTFOLIO RESET SCRIPT

DANGEROUS: This will exit ALL positions and reset to fresh start!

Use this to:
1. Clear all open positions
2. Reset portfolio to initial capital
3. Start fresh with new settings

WARNING: This will close all your current trades!
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Portfolio files
SWING_PORTFOLIO = 'data/swing_portfolio.json'
SWING_TRADES = 'data/swing_trades.json'
POSITIONAL_PORTFOLIO = 'data/positional_portfolio.json'
POSITIONAL_TRADES = 'data/positional_trades.json'

# Initial capital
SWING_CAPITAL = 60000.0
POSITIONAL_CAPITAL = 40000.0


def backup_files():
    """Create timestamped backups before reset"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    files = [SWING_PORTFOLIO, SWING_TRADES, POSITIONAL_PORTFOLIO, POSITIONAL_TRADES]

    print(f"\n📦 Creating backups...")
    for file in files:
        if os.path.exists(file):
            backup_name = f"{file}.backup_before_reset_{timestamp}"
            import shutil
            shutil.copy(file, backup_name)
            print(f"   ✅ Backed up: {backup_name}")


def reset_portfolio(portfolio_file, trades_file, initial_capital, portfolio_type):
    """Reset a portfolio to fresh state"""

    # Load current data to show what we're closing
    if os.path.exists(portfolio_file):
        with open(portfolio_file, 'r') as f:
            current = json.load(f)

        positions = current.get('positions', {})
        performance = current.get('performance', {})

        print(f"\n{'='*70}")
        print(f"🔥 RESETTING {portfolio_type.upper()} PORTFOLIO")
        print(f"{'='*70}")
        print(f"   Current Capital: ₹{current.get('capital', 0):,.2f}")
        print(f"   Open Positions: {len(positions)}")
        print(f"   Total Trades: {performance.get('total_trades', 0)}")
        print(f"   Win Rate: {performance.get('winning_trades', 0)}/{performance.get('total_trades', 0)}")
        print(f"   Total P&L: ₹{performance.get('total_pnl', 0):+,.2f}")

        if positions:
            print(f"\n   📊 Positions to be CLOSED:")
            for symbol, pos in positions.items():
                shares = pos.get('shares', 0)
                entry = pos.get('entry_price', 0)
                value = shares * entry
                print(f"      • {symbol}: {shares} shares @ ₹{entry:.2f} = ₹{value:,.0f}")

    # Create fresh portfolio
    fresh_portfolio = {
        'capital': initial_capital,
        'positions': {},
        'performance': {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0
        },
        'start_date': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'initial_capital': initial_capital,
        'mode': 'PAPER_TRADING'
    }

    # Save fresh portfolio
    with open(portfolio_file, 'w') as f:
        json.dump(fresh_portfolio, f, indent=2)

    # Clear trade history
    with open(trades_file, 'w') as f:
        json.dump([], f, indent=2)

    print(f"\n   ✅ Reset complete!")
    print(f"   💰 Fresh Capital: ₹{initial_capital:,.0f}")
    print(f"   📊 Positions: 0")
    print(f"   📜 Trade History: Cleared")


def main():
    """Main reset function"""
    print("\n" + "="*70)
    print("⚠️  PORTFOLIO RESET - FRESH START")
    print("="*70)
    print("\n🚨 WARNING: This will CLOSE ALL POSITIONS and reset to fresh start!")
    print("\nCurrent portfolios will be backed up before reset.")
    print("\nAre you sure you want to continue?")

    # Safety confirmation
    response = input("\nType 'RESET' to confirm: ").strip()

    if response != 'RESET':
        print("\n❌ Reset cancelled. No changes made.")
        return

    print("\n🔄 Starting reset process...")

    # Create backups
    backup_files()

    # Reset swing portfolio
    reset_portfolio(
        SWING_PORTFOLIO,
        SWING_TRADES,
        SWING_CAPITAL,
        'swing'
    )

    # Reset positional portfolio
    reset_portfolio(
        POSITIONAL_PORTFOLIO,
        POSITIONAL_TRADES,
        POSITIONAL_CAPITAL,
        'positional'
    )

    print("\n" + "="*70)
    print("✅ RESET COMPLETE - FRESH START!")
    print("="*70)
    print(f"\n📊 NEW STATE:")
    print(f"   Swing Capital: ₹{SWING_CAPITAL:,.0f}")
    print(f"   Positional Capital: ₹{POSITIONAL_CAPITAL:,.0f}")
    print(f"   Total Capital: ₹{SWING_CAPITAL + POSITIONAL_CAPITAL:,.0f}")
    print(f"   Open Positions: 0")
    print(f"   Trade History: Empty")
    print(f"\n🎯 System is ready for fresh start with new settings!")
    print(f"   Backups saved in data/ directory")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Reset cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during reset: {e}")
        import traceback
        traceback.print_exc()
