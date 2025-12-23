"""
Analyze Swing Trading Performance Issues
Identify what went wrong with yesterday's swing trading
"""

import json
from datetime import datetime
from collections import Counter

def analyze_swing_trades():
    """Analyze swing trading performance to identify issues"""

    # Load swing trades
    with open('data/swing_trades.json', 'r') as f:
        trades = json.load(f)

    # Focus on recent trades (last 20)
    recent_trades = trades[-30:]

    print("="*80)
    print("🔍 SWING TRADING PERFORMANCE ANALYSIS")
    print("="*80)

    # Issue 1: After-hours trading
    print("\n🚨 ISSUE 1: AFTER-HOURS TRADING (CRITICAL)")
    print("-"*80)
    after_hours_count = 0
    for trade in recent_trades:
        exit_time = datetime.fromisoformat(trade['exit_date'])
        # Market closes at 15:30 (3:30 PM)
        if exit_time.hour > 15 or (exit_time.hour == 15 and exit_time.minute > 30):
            after_hours_count += 1
            print(f"   ❌ {trade['symbol']}: Exit at {exit_time.strftime('%H:%M')} (market closed!)")
            print(f"      Reason: {trade['reason']} | P&L: ₹{trade['pnl']:+.2f}")

    if after_hours_count > 0:
        print(f"\n   💥 FOUND {after_hours_count} after-hours exits! This should NEVER happen!")
    else:
        print("   ✅ No after-hours trading detected")

    # Issue 2: Win rate and average P&L
    print("\n\n📊 ISSUE 2: WIN RATE & PROFITABILITY")
    print("-"*80)

    winners = [t for t in recent_trades if t['pnl'] > 0]
    losers = [t for t in recent_trades if t['pnl'] < 0]
    breakeven = [t for t in recent_trades if t['pnl'] == 0]

    win_rate = (len(winners) / len(recent_trades)) * 100 if recent_trades else 0
    avg_win = sum(t['pnl'] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t['pnl'] for t in losers) / len(losers) if losers else 0
    total_pnl = sum(t['pnl'] for t in recent_trades)

    print(f"   Total Trades: {len(recent_trades)}")
    print(f"   Winners: {len(winners)} ({win_rate:.1f}%)")
    print(f"   Losers: {len(losers)}")
    print(f"   Breakeven: {len(breakeven)}")
    print(f"   Average Win: ₹{avg_win:+.2f}")
    print(f"   Average Loss: ₹{avg_loss:+.2f}")
    print(f"   Total P&L: ₹{total_pnl:+.2f}")

    if win_rate < 40:
        print(f"\n   ⚠️ Win rate is TOO LOW ({win_rate:.1f}% < 40%)")
    if abs(avg_loss) > avg_win:
        print(f"   ⚠️ Avg loss (₹{abs(avg_loss):.2f}) > Avg win (₹{avg_win:.2f}) - Risk/Reward imbalanced!")

    # Issue 3: Exit reasons
    print("\n\n🚪 ISSUE 3: EXIT ANALYSIS")
    print("-"*80)

    exit_reasons = Counter([t['reason'] for t in recent_trades])
    for reason, count in exit_reasons.most_common():
        pct = (count / len(recent_trades)) * 100
        print(f"   {reason:40} | {count:3} ({pct:.1f}%)")

    # Check for problematic patterns
    stop_loss_count = sum(1 for t in recent_trades if 'STOP_LOSS' in t['reason'])
    breakeven_exit_count = sum(1 for t in recent_trades if 'BREAKEVEN_EXIT' in t['reason'])

    if stop_loss_count > len(recent_trades) * 0.3:
        print(f"\n   ⚠️ Too many stop-loss hits ({stop_loss_count}/{len(recent_trades)} = {stop_loss_count/len(recent_trades)*100:.1f}%)")
        print("      Possible causes:")
        print("      - Stop loss too tight for swing trading")
        print("      - Entry timing poor (entering at resistance)")
        print("      - ADX/momentum filters not strong enough")

    if breakeven_exit_count > len(recent_trades) * 0.2:
        print(f"\n   ⚠️ Too many breakeven exits ({breakeven_exit_count}/{len(recent_trades)} = {breakeven_exit_count/len(recent_trades)*100:.1f}%)")
        print("      Possible causes:")
        print("      - Signals not strong enough")
        print("      - Entering too late in the day")
        print("      - Momentum fading quickly")

    # Issue 4: Same-day exits
    print("\n\n⏰ ISSUE 4: HOLDING PERIOD")
    print("-"*80)

    same_day_exits = 0
    for trade in recent_trades:
        entry = datetime.fromisoformat(trade['entry_date'])
        exit = datetime.fromisoformat(trade['exit_date'])
        holding_mins = (exit - entry).total_seconds() / 60

        if holding_mins < 60:  # Less than 1 hour
            same_day_exits += 1

    same_day_pct = (same_day_exits / len(recent_trades)) * 100
    print(f"   Exits within 1 hour: {same_day_exits}/{len(recent_trades)} ({same_day_pct:.1f}%)")

    if same_day_pct > 40:
        print(f"\n   ⚠️ TOO MANY quick exits! Swing trades should hold longer.")
        print("      Possible causes:")
        print("      - Signals too weak")
        print("      - Stop loss too tight")
        print("      - Wrong market conditions for swing trading")

    # Issue 5: Charges eating profits
    print("\n\n💰 ISSUE 5: TRADING CHARGES")
    print("-"*80)

    total_charges = sum(t.get('trading_charges', 0) for t in recent_trades)
    gross_pnl = sum(t.get('gross_pnl', t['pnl']) for t in recent_trades)

    print(f"   Total Charges: ₹{total_charges:.2f}")
    print(f"   Gross P&L: ₹{gross_pnl:.2f}")
    print(f"   Net P&L: ₹{total_pnl:.2f}")

    if total_charges > abs(gross_pnl) * 0.5:
        print(f"\n   ⚠️ Charges are eating too much profit!")
        print(f"      Charges = {total_charges/abs(gross_pnl)*100:.1f}% of gross P&L")

    # Summary & Recommendations
    print("\n\n🎯 SUMMARY & RECOMMENDATIONS")
    print("="*80)

    if after_hours_count > 0:
        print("\n1. 🚨 FIX AFTER-HOURS TRADING IMMEDIATELY")
        print("   - Add market hours check (9:15 AM - 3:30 PM)")
        print("   - Never monitor or exit after market close")

    if win_rate < 40 or stop_loss_count > len(recent_trades) * 0.3:
        print("\n2. 🔧 TIGHTEN ENTRY CRITERIA")
        print("   - Increase minimum ADX (currently ≥12, try ≥20)")
        print("   - Increase minimum score (currently ≥5.5, try ≥7.0)")
        print("   - Add volume confirmation (volume > 1.5x avg)")
        print("   - Only enter in first 2 hours of market (9:15-11:15)")

    if breakeven_exit_count > 5:
        print("\n3. 📉 REDUCE BREAKEVEN EXITS")
        print("   - Increase quality filters (momentum score ≥40)")
        print("   - Don't enter after 11:00 AM (momentum fades)")
        print("   - Consider disabling swing during weak market days")

    if same_day_pct > 40:
        print("\n4. ⏱️ IMPROVE HOLDING PERIOD")
        print("   - Widen stop loss (from 1% to 1.5%)")
        print("   - Allow overnight holding (max 1-2 days)")
        print("   - Remove intraday breakeven exit (keep positions overnight)")

    print("\n5. 💡 CONSIDER TEMPORARILY DISABLING")
    print("   - Win rate < 35% → DISABLE until market improves")
    print("   - Avg loss > 2x avg win → DISABLE and reassess strategy")
    print("   - After-hours bugs → DISABLE until fixed")

    print("\n" + "="*80)


if __name__ == "__main__":
    analyze_swing_trades()
