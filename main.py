"""
🚀 SUPER MATH HYBRID TRADING SYSTEM - Main Application
Dual strategy: Swing Trading + Positional Trading running simultaneously
"""

import time
from datetime import datetime, time as dt_time
import pytz
from typing import List, Dict
import argparse

from config.settings import *
from src.data.data_fetcher import DataFetcher
from src.data.hybrid_scanner import HybridScanner
from src.data.eod_scanner import EODScanner
from src.data.nse_stock_fetcher import NSEStockFetcher
from src.strategies.signal_generator import SignalGenerator
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.paper_trading.dual_portfolio import DualPortfolio
from src.alerts.discord_alerts import DiscordAlerts
from src.comparison.portfolio_comparison import PortfolioComparison

IST = pytz.timezone('Asia/Kolkata')


class TradingSystem:
    """
    Hybrid Trading System Orchestrator

    Manages BOTH swing and positional trading simultaneously:
    - Scans ALL stocks for opportunities
    - Detects swing setups → Swing portfolio
    - Detects positional setups → Positional portfolio
    - Never misses opportunities!
    """

    def __init__(self, enable_comparison=False):
        print("🚀 Initializing HYBRID Trading System...")
        print("   🔥 Swing Trading + 📈 Positional Trading")

        self.data_fetcher = DataFetcher()
        self.hybrid_scanner = HybridScanner(max_workers=10)  # Multi-threaded hybrid scanner
        self.signal_generator = SignalGenerator()

        # DUAL PORTFOLIO SYSTEM (60% swing, 40% positional)
        self.dual_portfolio = DualPortfolio(total_capital=INITIAL_CAPITAL)

        self.discord = DiscordAlerts()

        # EOD scanner and multi-timeframe analyzer
        self.eod_scanner = EODScanner(max_workers=20)
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.nse_fetcher = NSEStockFetcher()

        # Portfolio comparison (for live strategy testing)
        self.enable_comparison = enable_comparison
        self.portfolio_comparison = PortfolioComparison() if enable_comparison else None

        # Scan ALL verified NSE stocks (no tier selection needed!)
        self.watchlist = self.nse_fetcher.fetch_nse_stocks()

        self.is_running = False

        print("✅ Hybrid System initialized successfully!")
        print(f"📊 Scanning Universe: {len(self.watchlist)} verified NSE stocks")
        print(f"⚡ Hybrid Scanner: ENABLED (swing + positional detection)")
        print(f"⚡ Multi-threaded: 10 parallel workers")
        print(f"⚡ Multi-timeframe: Daily + 15-minute candles")
        print(f"💼 Dual Portfolio System:")
        print(f"   🔥 Swing Portfolio: ₹{INITIAL_CAPITAL * 0.60:,.0f} (60%)")
        print(f"   📈 Positional Portfolio: ₹{INITIAL_CAPITAL * 0.40:,.0f} (40%)")
        print(f"   💰 Total Capital: ₹{INITIAL_CAPITAL:,.0f}")
        print(f"📱 Discord Alerts: {'Enabled' if self.discord.enabled else 'Disabled'}")
        if enable_comparison:
            print(f"🎯 Portfolio Comparison: ENABLED (3 strategies)")
            print(f"   📊 A: EXCELLENT (≥8.5) | B: MODERATE (≥8.0) | C: ALL (≥7.0)")

    def run_scan(self) -> Dict:
        """
        Run hybrid scan - detects BOTH swing and positional opportunities

        Returns:
            Dict with 'swing_signals' and 'positional_signals'
        """
        print("\n" + "="*70)
        print(f"🎯 HYBRID SCAN - Swing + Positional Detection")
        print(f"⏰ {self._get_ist_time()}")
        print("="*70)

        # Use hybrid scanner (detects both types)
        result = self.hybrid_scanner.scan_all_stocks(self.watchlist)

        swing_signals = result['swing_signals']
        positional_signals = result['positional_signals']
        stats = result['stats']

        return {
            'swing_signals': swing_signals,
            'positional_signals': positional_signals,
            'stats': stats
        }

    def process_signals(self, scan_result: Dict):
        """
        Process BOTH swing and positional signals

        Args:
            scan_result: Dict with 'swing_signals' and 'positional_signals'
        """
        swing_signals = scan_result.get('swing_signals', [])
        positional_signals = scan_result.get('positional_signals', [])

        if not swing_signals and not positional_signals:
            print("\n⚠️ No signals to process")
            return

        print(f"\n📋 Processing Signals...")
        print(f"   🔥 Swing: {len(swing_signals)} signals")
        print(f"   📈 Positional: {len(positional_signals)} signals")

        # Process swing signals → Swing portfolio
        for signal in swing_signals:
            symbol = signal['symbol']

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_swing_signal(signal)

                if executed:
                    # Send Discord alert (swing trade)
                    if self.discord.enabled:
                        self.discord.send_swing_signal(signal)
                    print(f"   🔥 Swing: {symbol} executed")
                else:
                    print(f"   ⏭️ Swing: {symbol} skipped (already holding or insufficient capital)")

        # Process positional signals → Positional portfolio
        for signal in positional_signals:
            symbol = signal['symbol']

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_positional_signal(signal)

                if executed:
                    # Send Discord alert (positional trade)
                    if self.discord.enabled:
                        self.discord.send_positional_signal(signal)
                    print(f"   📈 Positional: {symbol} executed")
                else:
                    print(f"   ⏭️ Positional: {symbol} skipped (already holding or insufficient capital)")

        print("\n✅ Signal processing complete")

    def monitor_positions(self):
        """
        Monitor open positions and check for exits

        Checks:
        - Target hits
        - Stop loss
        - Time-based exits
        """
        if not self.paper_trader.positions and not (self.enable_comparison and self.portfolio_comparison):
            return

        # Monitor paper trading positions
        if self.paper_trader.positions:
            print(f"\n👁️ Monitoring {len(self.paper_trader.positions)} paper trading positions...")

            # Get current prices
            current_prices = {}
            for symbol in self.paper_trader.positions.keys():
                price = self.data_fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits
            exits = self.paper_trader.check_exits(current_prices)

            if exits:
                print(f"\n🚪 {len(exits)} position(s) exited:")

                for exit_info in exits:
                    symbol = exit_info['symbol']
                    pnl = exit_info['pnl']
                    reason = exit_info['reason']

                    print(f"   {symbol}: ₹{pnl:+,.0f} ({reason})")

                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, paper_trade=True)

        # Monitor comparison portfolios
        if self.enable_comparison and self.portfolio_comparison:
            # Get all symbols from all portfolios
            all_symbols = set()
            for portfolio in self.portfolio_comparison.portfolios.values():
                all_symbols.update(portfolio['positions'].keys())

            if all_symbols:
                print(f"\n👁️ Monitoring {len(all_symbols)} comparison portfolio positions...")

                # Get current prices for comparison portfolios
                comparison_prices = {}
                for symbol in all_symbols:
                    price = self.data_fetcher.get_current_price(symbol)
                    if price > 0:
                        comparison_prices[symbol] = price

                # Check exits for comparison portfolios
                comparison_exits = self.portfolio_comparison.check_exits(comparison_prices)

                # Display exits by portfolio
                for portfolio_name, exits in comparison_exits.items():
                    if exits:
                        print(f"\n   📊 {portfolio_name}: {len(exits)} exit(s)")

    def send_daily_summary(self):
        """Send end-of-day summary to Discord"""
        print("\n📊 Generating daily summary...")

        summary = self.paper_trader.get_summary()

        # Send to Discord
        if self.discord.enabled and SEND_DAILY_SUMMARY:
            self.discord.send_daily_summary(summary)

        # Print to console
        print("\n" + "="*60)
        print("📊 DAILY SUMMARY")
        print("="*60)
        print(f"💼 Portfolio Value: ₹{summary['portfolio_value']:,.0f}")
        print(f"📈 Total Return: {summary['total_return_percent']:+.2f}%")
        print(f"💰 Cash: ₹{summary['capital']:,.0f}")
        print(f"📊 Open Positions: {summary['open_positions']}")
        print(f"🎯 Win Rate: {summary['win_rate']:.1f}%")
        print(f"📈 Total Trades: {summary['total_trades']}")
        print("="*60)

    def run_continuous(self):
        """
        Run system continuously during market hours with automatic EOD scan

        Schedule:
        - Pre-market: Wait for 9:15 AM
        - Market hours (9:15 AM - 3:30 PM): Scan every SCAN_INTERVAL_MINUTES
        - Position monitoring: Every 3 minutes
        - Post-market (3:30 PM): Daily summary
        - EOD scan (4:00 PM): Automatic full NSE scan for next day
        - Night: Sleep until next market open
        """
        print("\n🔄 Starting FULLY AUTOMATIC continuous mode...")
        print(f"⏰ Market Hours: {MARKET_OPEN_TIME} - {MARKET_CLOSE_TIME} IST")
        print(f"🔍 Intraday Scan: Every {SCAN_INTERVAL_MINUTES} minutes")
        print(f"📊 Position Monitor: Every {POSITION_MONITOR_INTERVAL} minutes")
        print(f"🌙 EOD Scan: 4:00 PM IST (automatic)")
        print(f"✨ FULLY AUTOMATIC: Just run once, system handles everything!")

        self.is_running = True
        last_scan_time = None
        last_monitor_time = None
        eod_scan_done_today = False  # Track if EOD scan completed today

        try:
            while self.is_running:
                current_time = datetime.now(IST).time()
                current_date = datetime.now(IST).date()

                # Market hours
                market_open = dt_time(9, 15)
                market_close = dt_time(15, 30)
                eod_scan_time = dt_time(16, 0)  # 4:00 PM for EOD scan

                if market_open <= current_time <= market_close:
                    # MARKET HOURS - Intraday scanning and monitoring
                    print(f"\n🟢 Market OPEN - Active trading mode")

                    # Run intraday scan
                    if (last_scan_time is None or
                        (datetime.now() - last_scan_time).seconds >= SCAN_INTERVAL_MINUTES * 60):

                        signals = self.run_scan()
                        self.process_signals(signals)
                        last_scan_time = datetime.now()

                    # Monitor positions
                    if (last_monitor_time is None or
                        (datetime.now() - last_monitor_time).seconds >= POSITION_MONITOR_INTERVAL * 60):

                        self.monitor_positions()
                        last_monitor_time = datetime.now()

                    # Small sleep to prevent CPU overuse
                    time.sleep(10)

                elif market_close < current_time < dt_time(22, 0):
                    # POST-MARKET (3:30 PM - 10:00 PM)

                    # Daily summary (once per day, right after market close)
                    if last_scan_time and last_scan_time.date() == current_date:
                        print(f"\n🌆 Market CLOSED - Generating daily summary...")
                        self.send_daily_summary()
                        last_scan_time = None  # Reset for next day

                    # Automatic EOD scan at 4:00 PM (once per day)
                    if current_time >= eod_scan_time and not eod_scan_done_today:
                        print(f"\n🌙 EOD SCAN TIME - Running automatic full NSE scan...")
                        print(f"⏰ {self._get_ist_time()}")
                        print(f"📊 This will scan ALL verified NSE stocks and rank them for tomorrow")
                        print(f"⏱️  Expected time: 5-10 minutes\n")

                        try:
                            # Run full EOD scan (automatic, no prompt)
                            self.run_eod_scan(top_n=500, auto=True)
                            eod_scan_done_today = True
                            print(f"\n✅ EOD scan completed! Top stocks ranked for tomorrow.")
                            print(f"   • TIER 1: Top 50 (Swing Trading)")
                            print(f"   • TIER 2: Top 100 (Swing + Positional)")
                            print(f"   • TIER 3: Top 250 (Positional)")
                            print(f"   • TIER 4: Top 500 (All Viable)")

                        except Exception as e:
                            print(f"\n⚠️  EOD scan failed: {e}")
                            print(f"   Will retry tomorrow at 4:00 PM")

                    if eod_scan_done_today:
                        print(f"\n💤 EOD scan complete. Sleeping until tomorrow's market open...")
                    else:
                        print(f"\n⏳ Waiting for EOD scan time (4:00 PM)...")

                    # Sleep for 30 minutes
                    time.sleep(1800)

                else:
                    # NIGHT TIME (10:00 PM - 9:15 AM)
                    print(f"\n🌙 Night mode - Sleeping until market open tomorrow...")
                    print(f"⏰ Next market open: {MARKET_OPEN_TIME} IST")

                    # Reset EOD scan flag for next day
                    eod_scan_done_today = False

                    # Sleep for 1 hour
                    time.sleep(3600)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping system...")
            self.is_running = False

    def run_once(self):
        """Run a single scan cycle"""
        signals = self.run_scan()
        self.process_signals(signals)
        self.monitor_positions()

    def run_eod_scan(self, top_n: int = 100, auto: bool = False):
        """
        Run End-of-Day scan on all NSE stocks

        This should be run after market close (3:30 PM IST)
        Scans all NSE stocks and saves top N for next day's live scanning

        Args:
            top_n: Number of top stocks to save for tomorrow
            auto: If True, skip confirmation prompt (for automatic runs)
        """
        print("\n" + "="*70)
        print("🌙 END-OF-DAY SCANNER")
        print("="*70)
        print(f"⏰ Best time to run: After 3:30 PM IST (market close)")
        print(f"📊 Will scan: ALL NSE stocks (~600-800 verified stocks)")
        print(f"⏱️  Expected time: 5-10 minutes")
        print(f"💾 Will save: Top {top_n} stocks ranked in 4 tiers")
        print("="*70)

        # Confirm (skip if automatic)
        if not auto:
            print("\nThis will scan all NSE stocks and may take some time.")
            response = input("Continue? (y/n) [default: y]: ").strip().lower() or 'y'

            if response != 'y':
                print("❌ EOD scan cancelled")
                return

        # Run EOD scan
        results = self.eod_scanner.run_eod_scan(top_n=top_n)

        print("\n" + "="*70)
        print("✅ EOD SCAN COMPLETE!")
        print("="*70)
        print(f"📊 Results saved to: data/eod_scan_results.json")
        print(f"🚀 Tomorrow's live scan will use these {top_n} stocks")
        print("="*70)

        return results

    def _get_ist_time(self) -> str:
        """Get current time in IST"""
        return datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Super Math Trading System')
    parser.add_argument('--mode', choices=['once', 'continuous', 'dashboard', 'comparison', 'eod'],
                       default='once', help='Run mode')
    parser.add_argument('--test-discord', action='store_true',
                       help='Test Discord connection')
    parser.add_argument('--summary', action='store_true',
                       help='Show portfolio summary')
    parser.add_argument('--enable-comparison', action='store_true',
                       help='Enable 3-portfolio comparison (EXCELLENT/MODERATE/ALL)')
    parser.add_argument('--eod-top-n', type=int, default=100,
                       help='Number of top stocks to save from EOD scan (default: 100)')
    parser.add_argument('--eod-tier', choices=['tier1', 'tier2', 'tier3', 'tier4', 'all'],
                       default='tier1',
                       help='EOD tier to load for trading (default: tier1 = Top 50 swing trades)')

    args = parser.parse_args()

    # Test Discord
    if args.test_discord:
        print("\n🧪 Testing Discord connection...")
        discord = DiscordAlerts()
        discord.send_test_alert()
        return

    # Show summary
    if args.summary:
        trader = PaperTrader()
        summary = trader.get_summary()

        print("\n" + "="*60)
        print("📊 PAPER TRADING SUMMARY")
        print("="*60)
        print(f"💼 Portfolio Value: ₹{summary['portfolio_value']:,.0f}")
        print(f"📈 Total Return: {summary['total_return_percent']:+.2f}%")
        print(f"💰 Available Cash: ₹{summary['capital']:,.0f}")
        print(f"📊 Open Positions: {summary['open_positions']}")
        print(f"🎯 Win Rate: {summary['win_rate']:.1f}%")
        print(f"📈 Total Trades: {summary['total_trades']}")
        print(f"✅ Winning Trades: {summary['winning_trades']}")
        print(f"❌ Losing Trades: {summary['losing_trades']}")
        print(f"🏆 Best Trade: ₹{summary['best_trade']:+,.0f}")
        print(f"💔 Worst Trade: ₹{summary['worst_trade']:+,.0f}")
        print("="*60)
        return

    # Dashboard mode
    if args.mode == 'dashboard':
        print("\n🚀 Starting Streamlit Dashboard...")
        print(f"🌐 Open browser to: http://localhost:{DASHBOARD_PORT}")
        import subprocess
        subprocess.run(['streamlit', 'run', 'dashboard.py',
                       '--server.port', str(DASHBOARD_PORT),
                       '--server.headless', 'true'])
        return

    # Comparison Dashboard mode
    if args.mode == 'comparison':
        print("\n🎯 Starting Strategy Comparison Dashboard...")
        print(f"🌐 Open browser to: http://localhost:{DASHBOARD_PORT + 1}")
        print("\n📊 Comparing 3 strategies:")
        print("   🟢 EXCELLENT: Score ≥ 8.5")
        print("   🟡 MODERATE: Score ≥ 8.0")
        print("   🔵 ALL SIGNALS: Score ≥ 7.0")
        import subprocess
        subprocess.run(['streamlit', 'run', 'comparison_dashboard.py',
                       '--server.port', str(DASHBOARD_PORT + 1),
                       '--server.headless', 'true'])
        return

    # EOD Scan mode
    if args.mode == 'eod':
        print("\n🌙 End-of-Day Scanner Mode")
        system = TradingSystem(use_eod_stocks=False)  # Don't load EOD stocks when running EOD scan
        system.run_eod_scan(top_n=args.eod_top_n)
        return

    # Initialize system (enable comparison if requested or in comparison mode)
    enable_comparison = args.enable_comparison or args.mode == 'comparison'
    system = TradingSystem(enable_comparison=enable_comparison, eod_tier=args.eod_tier)

    # Run based on mode
    if args.mode == 'once':
        print("\n🎯 Running single scan cycle...")
        system.run_once()

    elif args.mode == 'continuous':
        print("\n🔄 Running continuous mode...")
        if enable_comparison:
            print("📊 Portfolio comparison enabled - tracking 3 strategies simultaneously")
        print("Press Ctrl+C to stop")
        system.run_continuous()


if __name__ == "__main__":
    main()
