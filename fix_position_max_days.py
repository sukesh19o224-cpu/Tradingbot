#!/usr/bin/env python3
"""
🔧 Fix Max Holding Days in Existing Positions

This script updates max_holding_days in existing portfolio JSON files
to match the correct values based on strategy:
- Swing: 7 trading days
- Positional: 60 trading days
"""

import json
import os
from datetime import datetime


def fix_portfolio_file(filepath, strategy_type):
    """Fix max_holding_days in a portfolio file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False

    try:
        # Load portfolio
        with open(filepath, 'r') as f:
            portfolio = json.load(f)

        # Determine correct max days
        if strategy_type == 'swing':
            correct_max_days = 7
        elif strategy_type == 'positional':
            correct_max_days = 60
        else:
            correct_max_days = 15

        # Fix positions
        positions = portfolio.get('positions', {})
        if not positions:
            print(f"ℹ️  No positions in {filepath}")
            return True

        updated_count = 0
        for symbol, position in positions.items():
            old_max_days = position.get('max_holding_days', 0)
            position['max_holding_days'] = correct_max_days

            if old_max_days != correct_max_days:
                print(f"   ✓ {symbol}: {old_max_days} → {correct_max_days} days")
                updated_count += 1

        if updated_count > 0:
            # Backup original file
            backup_file = filepath + '.backup'
            with open(backup_file, 'w') as f:
                json.dump(portfolio, f, indent=2)
            print(f"   💾 Backup saved: {backup_file}")

            # Save updated portfolio
            portfolio['last_updated'] = datetime.now().isoformat()
            with open(filepath, 'w') as f:
                json.dump(portfolio, f, indent=2)

            print(f"✅ Updated {updated_count} positions in {filepath}")
        else:
            print(f"✅ All positions already correct in {filepath}")

        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False


def main():
    """Main function"""
    print("="*70)
    print("🔧 FIX MAX HOLDING DAYS IN EXISTING POSITIONS")
    print("="*70)
    print()

    # Fix swing portfolio
    print("📊 Fixing Swing Portfolio...")
    fix_portfolio_file('data/swing_portfolio.json', 'swing')
    print()

    # Fix positional portfolio
    print("📊 Fixing Positional Portfolio...")
    fix_portfolio_file('data/positional_portfolio.json', 'positional')
    print()

    print("="*70)
    print("✅ DONE!")
    print("="*70)
    print()
    print("💡 Next steps:")
    print("   1. Check the updated files in data/")
    print("   2. If something went wrong, restore from .backup files")
    print("   3. Restart your dashboard to see updated max days")
    print()


if __name__ == "__main__":
    main()
