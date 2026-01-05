"""
🎯 COMPREHENSIVE BACKTEST RUNNER
Scans Top 1000 NSE stocks and backtests positional signals with EXACT system logic

Features:
- Scans Top 1000 NSE stocks for positional signals
- Uses EXACT scanner logic (MultiTimeframeAnalyzer)
- Backtests each signal with exact trading system
- Comprehensive results aggregation
- Performance analytics
"""

import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.positional_backtest import PositionalBacktester
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from config.nse_top_1000_live import NSE_TOP_1000
from config.settings import MIN_SIGNAL_SCORE, INITIAL_CAPITAL


class BacktestRunner:
    """
    Comprehensive backtesting system that scans stocks and backtests signals
    """

    def __init__(self, initial_capital: float = INITIAL_CAPITAL, api_delay: float = 0.1):
        """
        Initialize backtest runner

        Args:
            initial_capital: Starting capital for backtesting
            api_delay: Delay between API calls (seconds)
        """
        self.backtester = PositionalBacktester(initial_capital)
        self.data_fetcher = EnhancedDataFetcher(api_delay=api_delay)
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.api_delay = api_delay

        print(f"🎯 Backtest Runner initialized")
        print(f"💰 Initial Capital: ₹{initial_capital:,.0f}")
        print(f"📊 Stock Universe: {len(NSE_TOP_1000)} stocks (Top 1000 NSE)")
        print(f"⏱️ API Delay: {api_delay}s")

    def scan_for_signals(self, stocks: List[str], scan_date: datetime,
                        min_score: float = MIN_SIGNAL_SCORE) -> List[Dict]:
        """
        Scan stocks for positional signals on a specific date

        Args:
            stocks: List of stock symbols to scan
            scan_date: Date to scan for signals
            min_score: Minimum signal score (default: 7.7 from config)

        Returns:
            List of signals with entry details
        """
        print(f"\n{'='*80}")
        print(f"SCANNING FOR SIGNALS ON {scan_date.strftime('%Y-%m-%d')}")
        print(f"{'='*80}")

        signals = []
        errors = []

        for i, symbol in enumerate(stocks, 1):
            try:
                # Progress
                if i % 50 == 0:
                    print(f"Progress: {i}/{len(stocks)} stocks scanned... ({len(signals)} signals found)")

                # Fetch historical data up to scan date
                # Use period instead of end_date for better compatibility
                df_daily = self.data_fetcher.fetch_data(
                    symbol,
                    period='3mo',  # Need 60+ days for indicators
                    interval='1d'
                )

                if df_daily is None or len(df_daily) < 60:
                    errors.append((symbol, 'Insufficient data'))
                    continue

                # Get data up to scan date only
                df_daily = df_daily[df_daily.index <= scan_date]

                if len(df_daily) < 60:
                    errors.append((symbol, 'Insufficient data after date filter'))
                    continue

                # Run multitimeframe analysis
                mtf_result = self.mtf_analyzer.analyze(df_daily, symbol)

                if not mtf_result:
                    errors.append((symbol, 'MTF analysis failed'))
                    continue

                # Check if this is a valid positional signal
                signal_score = mtf_result.get('signal_score', 0)
                uptrend = mtf_result.get('uptrend', False)

                # Debug: Show top candidates
                if i <= 10 and signal_score > 0:  # Debug first 10
                    print(f"   {symbol}: Score={signal_score:.1f}, Uptrend={uptrend}, MinScore={min_score}")

                if signal_score >= min_score and uptrend:
                    # Get entry price (close of scan date)
                    entry_price = float(df_daily.iloc[-1]['Close'])
                    atr = mtf_result.get('atr', entry_price * 0.02)  # Fallback to 2%

                    signal = {
                        'symbol': symbol,
                        'entry_date': scan_date,
                        'entry_price': entry_price,
                        'atr': atr,
                        'signal_score': signal_score,
                        'indicators': mtf_result.get('indicators', {}),
                        'signal_type': mtf_result.get('signal_type', 'MOMENTUM')
                    }
                    signals.append(signal)
                    print(f"   ✅ {symbol}: Score {signal_score:.1f}, Price ₹{entry_price:.2f}")

                # Rate limiting
                time.sleep(self.api_delay)

            except Exception as e:
                errors.append((symbol, str(e)))
                continue

        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE: {len(signals)} signals found, {len(errors)} errors")
        print(f"{'='*80}")

        return signals

    def backtest_signals(self, signals: List[Dict], days_forward: int = 15) -> List[Dict]:
        """
        Backtest multiple signals

        Args:
            signals: List of signals to backtest
            days_forward: Days to backtest each signal

        Returns:
            List of backtest results
        """
        print(f"\n{'='*80}")
        print(f"BACKTESTING {len(signals)} SIGNALS")
        print(f"{'='*80}")

        results = []

        for i, signal in enumerate(signals, 1):
            print(f"\n[{i}/{len(signals)}] Backtesting {signal['symbol']}...")

            # Run backtest for this signal
            result = self.backtester.backtest_symbol(
                symbol=signal['symbol'],
                entry_date=signal['entry_date'],
                entry_price=signal['entry_price'],
                atr=signal['atr'],
                signal_score=signal['signal_score'],
                days_forward=days_forward
            )

            if 'error' not in result:
                result['signal_info'] = signal
                results.append(result)

                # Quick summary
                total_pnl = result['total_pnl']
                num_trades = len(result['trades'])
                print(f"   Result: {num_trades} exits, P&L: ₹{total_pnl:,.2f}")
            else:
                print(f"   ❌ Error: {result['error']}")

        print(f"\n{'='*80}")
        print(f"BACKTESTING COMPLETE: {len(results)} successful backtests")
        print(f"{'='*80}")

        return results

    def run_historical_backtest(self, start_date: datetime, end_date: datetime,
                               stocks: Optional[List[str]] = None,
                               scan_frequency_days: int = 7) -> Dict:
        """
        Run comprehensive historical backtest scanning periodically

        Args:
            start_date: Start date for backtesting
            end_date: End date for backtesting
            stocks: List of stocks to scan (default: Top 1000)
            scan_frequency_days: Days between scans (default: 7 = weekly)

        Returns:
            Comprehensive results dictionary
        """
        if stocks is None:
            stocks = NSE_TOP_1000

        print(f"\n{'='*80}")
        print(f"HISTORICAL BACKTEST")
        print(f"{'='*80}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Stocks: {len(stocks)}")
        print(f"Scan Frequency: Every {scan_frequency_days} days")
        print(f"{'='*80}")

        all_signals = []
        all_results = []

        # Scan periodically
        current_date = start_date
        scan_count = 0

        while current_date <= end_date:
            scan_count += 1
            print(f"\n\n{'#'*80}")
            print(f"SCAN #{scan_count}: {current_date.strftime('%Y-%m-%d')}")
            print(f"{'#'*80}")

            # Scan for signals on this date
            signals = self.scan_for_signals(stocks, current_date)
            all_signals.extend(signals)

            # Backtest these signals
            if signals:
                results = self.backtest_signals(signals, days_forward=15)
                all_results.extend(results)

            # Move to next scan date
            current_date += timedelta(days=scan_frequency_days)

        # Aggregate results
        return self._aggregate_results(all_signals, all_results)

    def _aggregate_results(self, signals: List[Dict], results: List[Dict]) -> Dict:
        """
        Aggregate and analyze all backtest results
        """
        print(f"\n\n{'='*80}")
        print(f"AGGREGATING RESULTS")
        print(f"{'='*80}")

        if not results:
            return {
                'total_signals': len(signals),
                'total_backtests': 0,
                'error': 'No successful backtests'
            }

        # Collect all trades
        all_trades = []
        for result in results:
            all_trades.extend(result['trades'])

        # Calculate statistics
        total_pnl = sum(t['pnl'] for t in all_trades)
        winning_trades = [t for t in all_trades if t['pnl'] > 0]
        losing_trades = [t for t in all_trades if t['pnl'] < 0]
        breakeven_trades = [t for t in all_trades if t['pnl'] == 0]

        win_rate = (len(winning_trades) / len(all_trades) * 100) if all_trades else 0

        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Best and worst trades
        best_trade = max(all_trades, key=lambda t: t['pnl']) if all_trades else None
        worst_trade = min(all_trades, key=lambda t: t['pnl']) if all_trades else None

        # Exit reason distribution
        exit_reasons = {}
        for trade in all_trades:
            reason = trade['reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

        # Print summary
        print(f"\n📊 BACKTEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Signals Found: {len(signals)}")
        print(f"Successful Backtests: {len(results)}")
        print(f"Total Trades Executed: {len(all_trades)}")
        print(f"\n💰 PERFORMANCE")
        print(f"{'='*80}")
        print(f"Total P&L: ₹{total_pnl:,.2f}")
        print(f"Return on Capital: {(total_pnl / self.backtester.initial_capital * 100):+.2f}%")
        print(f"Average Trade: ₹{(total_pnl / len(all_trades)):,.2f}" if all_trades else "N/A")
        print(f"\n📈 WIN/LOSS STATISTICS")
        print(f"{'='*80}")
        print(f"Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"Losing Trades: {len(losing_trades)}")
        print(f"Breakeven Trades: {len(breakeven_trades)}")
        print(f"Average Win: ₹{avg_win:,.2f}")
        print(f"Average Loss: ₹{avg_loss:,.2f}")
        print(f"Win/Loss Ratio: {(abs(avg_win/avg_loss) if avg_loss != 0 else 0):.2f}")

        if best_trade:
            print(f"\nBest Trade: {best_trade['symbol']} - ₹{best_trade['pnl']:,.2f} ({best_trade['reason']})")
        if worst_trade:
            print(f"Worst Trade: {worst_trade['symbol']} - ₹{worst_trade['pnl']:,.2f} ({worst_trade['reason']})")

        print(f"\n🎯 EXIT REASON DISTRIBUTION")
        print(f"{'='*80}")
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(all_trades) * 100) if all_trades else 0
            print(f"{reason}: {count} ({pct:.1f}%)")

        return {
            'total_signals': len(signals),
            'total_backtests': len(results),
            'total_trades': len(all_trades),
            'total_pnl': total_pnl,
            'return_pct': (total_pnl / self.backtester.initial_capital * 100),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'breakeven_trades': len(breakeven_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'exit_reasons': exit_reasons,
            'all_trades': all_trades,
            'all_results': results
        }


def test_single_scan():
    """Test: Scan Top 1000 on a single date"""
    runner = BacktestRunner(initial_capital=50000)

    # Scan on Nov 15, 2024 (a Friday - market open)
    scan_date = datetime(2024, 11, 15)

    # Test with Top 100 first (faster)
    print("\n🧪 TESTING: Scanning Top 100 stocks")
    signals = runner.scan_for_signals(NSE_TOP_1000[:100], scan_date)

    if signals:
        print(f"\n✅ Found {len(signals)} signals, backtesting...")
        results = runner.backtest_signals(signals[:5])  # Test first 5

        summary = runner._aggregate_results(signals, results)
        print(f"\n✅ Test completed successfully!")
    else:
        print(f"\n⚠️ No signals found. Try a different date or lower MIN_SIGNAL_SCORE.")


def test_historical_backtest():
    """Test: Full historical backtest on Top 100 stocks"""
    runner = BacktestRunner(initial_capital=50000)

    # Test 1 month with Top 100 stocks
    start_date = datetime(2024, 11, 1)
    end_date = datetime(2024, 11, 30)

    print("\n🧪 TESTING: 1-month historical backtest on Top 100")
    results = runner.run_historical_backtest(
        start_date=start_date,
        end_date=end_date,
        stocks=NSE_TOP_1000[:100],  # Top 100 for testing
        scan_frequency_days=7  # Weekly scans
    )

    print(f"\n✅ Historical backtest completed!")


if __name__ == "__main__":
    # Run test
    test_single_scan()
