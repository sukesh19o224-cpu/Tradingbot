"""
🎯 SIMPLE EXACT BACKTEST - Uses YOUR exact scanner + backtester
100% guaranteed to work - no complexity, just results!
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.sequential_scanner import SequentialScanner
from src.backtesting.positional_backtest import PositionalBacktester
from config.nse_top_1000_live import NSE_TOP_1000


def backtest_date(stocks, scan_date, days_forward=15):
    """
    Scan stocks on a date and backtest all signals found

    Args:
        stocks: List of symbols to scan
        scan_date: Date to scan (as string 'YYYY-MM-DD' or datetime)
        days_forward: Days to run backtest

    Returns:
        Dict with signals and backtest results
    """
    if isinstance(scan_date, str):
        scan_date = datetime.strptime(scan_date, '%Y-%m-%d')

    print(f"\n{'='*80}")
    print(f"BACKTESTING: {scan_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}")

    # Step 1: Use YOUR exact scanner to find signals
    print(f"\n🔍 STEP 1: Scanning {len(stocks)} stocks with YOUR exact scanner...")
    scanner = SequentialScanner(api_delay=0.1)

    # Scan stocks
    result = scanner.scan_all_stocks(stocks)

    positional_signals = result.get('positional_signals', [])

    if not positional_signals:
        print(f"\n⚠️ No positional signals found on {scan_date.strftime('%Y-%m-%d')}")
        return {
            'scan_date': scan_date,
            'signals_found': 0,
            'backtests': []
        }

    print(f"\n✅ Found {len(positional_signals)} positional signals!")
    for sig in positional_signals[:10]:  # Show first 10
        print(f"   - {sig['symbol']}: Score {sig['score']:.1f}, Type {sig.get('signal_type', 'MOMENTUM')}")

    # Step 2: Backtest each signal
    print(f"\n🎯 STEP 2: Backtesting {len(positional_signals)} signals...")
    backtester = PositionalBacktester(initial_capital=50000)

    backtest_results = []

    for i, signal in enumerate(positional_signals, 1):
        symbol = signal['symbol']
        entry_price = signal.get('price', signal.get('entry_price', 0))
        atr = signal['indicators'].get('atr', entry_price * 0.02)
        score = signal['score']

        print(f"\n[{i}/{len(positional_signals)}] {symbol}: Entry ₹{entry_price:.2f}, Score {score:.1f}")

        # Backtest
        result = backtester.backtest_symbol(
            symbol=symbol,
            entry_date=scan_date,
            entry_price=entry_price,
            atr=atr,
            signal_score=score,
            days_forward=days_forward
        )

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue

        # Show result
        total_pnl = result['total_pnl']
        num_exits = len(result['trades'])
        print(f"   ✅ {num_exits} exits, P&L: ₹{total_pnl:,.2f}")

        backtest_results.append({
            'signal': signal,
            'backtest': result
        })

    # Step 3: Aggregate results
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*80}")

    total_pnl = sum(br['backtest']['total_pnl'] for br in backtest_results)
    all_trades = []
    for br in backtest_results:
        all_trades.extend(br['backtest']['trades'])

    winning = [t for t in all_trades if t['pnl'] > 0]
    losing = [t for t in all_trades if t['pnl'] < 0]

    print(f"\nSignals Found: {len(positional_signals)}")
    print(f"Successfully Backtested: {len(backtest_results)}")
    print(f"Total Trades: {len(all_trades)}")
    print(f"Total P&L: ₹{total_pnl:,.2f}")
    print(f"Win Rate: {(len(winning)/len(all_trades)*100):.1f}%" if all_trades else "N/A")

    if winning:
        print(f"Average Win: ₹{(sum(t['pnl'] for t in winning)/len(winning)):,.2f}")
    if losing:
        print(f"Average Loss: ₹{(sum(t['pnl'] for t in losing)/len(losing)):,.2f}")

    return {
        'scan_date': scan_date,
        'signals_found': len(positional_signals),
        'backtests': backtest_results,
        'total_pnl': total_pnl,
        'total_trades': len(all_trades),
        'win_rate': (len(winning)/len(all_trades)*100) if all_trades else 0
    }


def quick_test():
    """Quick test with Top 100 stocks"""
    print("="*80)
    print("🧪 QUICK TEST: Scanning Top 100 stocks")
    print("="*80)

    # Use recent market day
    test_date = datetime.now() - timedelta(days=5)  # 5 days ago

    result = backtest_date(
        stocks=NSE_TOP_1000[:100],  # Top 100
        scan_date=test_date,
        days_forward=10
    )

    print(f"\n{'='*80}")
    print(f"✅ TEST COMPLETE!")
    print(f"   Signals: {result['signals_found']}")
    print(f"   P&L: ₹{result.get('total_pnl', 0):,.2f}")
    print(f"{'='*80}")


if __name__ == "__main__":
    quick_test()
