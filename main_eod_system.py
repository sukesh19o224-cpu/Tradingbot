"""
🚀 EOD + INTRADAY TRADING SYSTEM
End-of-Day ranking + Intraday sequential scanning

FLOW:
1. EOD (3:45 PM daily): Generate Top 500 NSE stocks (ranked by market cap)
2. INTRADAY (every 10 mins): Scan Top 500 sequentially, send alerts for qualified stocks
"""

import time
import subprocess
import os
from datetime import datetime, time as dt_time
from typing import List, Dict
import pytz

# Local imports
from config.settings import *
from src.data.sequential_scanner import SequentialScanner
from src.paper_trading.dual_portfolio import DualPortfolio
from src.alerts.discord_alerts import DiscordAlerts
from src.utils.signal_validator import SignalValidator

IST = pytz.timezone('Asia/Kolkata')


class EODIntradaySystem:
    """
    EOD + Intraday Trading System

    Features:
    - EOD ranking (3:45 PM): Top 500 NSE stocks
    - Intraday scanning (every 10 mins): Sequential, safe, no API ban
    - Discord alerts for qualified stocks
    - Dual portfolio (swing + positional)
    """

    def __init__(self):
        print("🚀 Initializing EOD + INTRADAY System...")
        print("=" * 70)

        # Sequential scanner (NO threads!)
        self.scanner = SequentialScanner(api_delay=0.3)

        # Dual portfolio
        self.dual_portfolio = DualPortfolio(total_capital=INITIAL_CAPITAL)

        # Discord alerts
        self.discord = DiscordAlerts()

        # Signal validator
        self.signal_validator = SignalValidator()

        # Stock list (will be loaded from config)
        self.stocks = self._load_stock_list()

        self.is_running = False
        self.eod_done_today = False  # Track if EOD ranking done today

        print(f"✅ System Initialized!")
        print(f"📊 Stock Universe: {len(self.stocks)} stocks")
        print(f"🐌 Sequential Scanning: ONE BY ONE (safe, no threads)")
        print(f"⏱️ API Delay: 0.3s between stocks")
        print(f"⏰ Scan Interval: Every {SCAN_INTERVAL_MINUTES} minutes")
        print(f"💼 Dual Portfolio: Swing (60%) + Positional (40%)")
        print(f"📱 Discord: {'Enabled' if self.discord.enabled else 'Disabled'}")
        print("=" * 70)

    def _load_stock_list(self) -> List[str]:
        """
        Load stock list from config

        Priority:
        1. nse_top_500_live.py (if exists and not empty - from EOD ranking)
        2. nse_top_50_working.py (fallback)
        """
        try:
            # Try to load NSE Top 500 (from EOD ranking)
            from config.nse_top_500_live import NSE_TOP_500, GENERATED_DATE

            # Check if list is not empty (not placeholder)
            if NSE_TOP_500 and len(NSE_TOP_500) > 0:
                print(f"📊 Loaded NSE Top 500 (Generated: {GENERATED_DATE})")
                return NSE_TOP_500
            else:
                # Empty list - use fallback
                raise ImportError("Top 500 list is empty (placeholder)")

        except ImportError:
            # Fallback to Top 50
            try:
                from config.nse_top_50_working import NSE_TOP_50_WORKING
                print(f"⚠️ Using NSE Top 50 (fallback)")
                print(f"💡 Run EOD ranking to generate Top 500 list!")
                return NSE_TOP_50_WORKING
            except ImportError:
                print("❌ No stock list found!")
                return []

    def run_eod_ranking(self):
        """
        Run End-of-Day ranking to generate Top 500 list

        This should run ONCE per day at market close (3:45 PM)
        Takes ~10-15 minutes to complete
        """
        print("\n" + "=" * 70)
        print("🌆 END-OF-DAY RANKING - Generating Top 500 List")
        print("=" * 70)
        print(f"⏰ Time: {self._get_ist_time()}")
        print("⏳ This will take ~10-15 minutes...")
        print()

        try:
            # Run the fetch script with REAL-TIME output (no buffering)
            result = subprocess.run(
                ['python', 'scripts/fetch_nse_top_500.py'],
                text=True,
                bufsize=0  # No buffering - show output immediately
            )

            if result.returncode == 0:
                print("\n✅ EOD Ranking Complete!")
                print("📊 config/nse_top_500_live.py generated")
                print("💡 This list will be used for tomorrow's intraday scans")

                # Reload stock list
                self.stocks = self._load_stock_list()
                self.eod_done_today = True

            else:
                print(f"❌ EOD Ranking Failed!")
                print("Check the output above for errors")

        except Exception as e:
            print(f"❌ Error running EOD ranking: {e}")

    def run_intraday_scan(self) -> Dict:
        """
        Run intraday scan (sequential, 500 stocks)

        Returns:
            Dict with swing and positional signals
        """
        print("\n" + "=" * 70)
        print("🎯 INTRADAY SCAN - Sequential Scanning")
        print("=" * 70)
        print(f"⏰ Time: {self._get_ist_time()}")
        print(f"📊 Stocks: {len(self.stocks)}")
        print()

        # Run sequential scan
        result = self.scanner.scan_all_stocks(self.stocks)

        return result

    def process_signals(self, scan_result: Dict):
        """
        Process signals and send Discord alerts

        Args:
            scan_result: Dict with swing_signals and positional_signals
        """
        swing_signals = scan_result.get('swing_signals', [])
        positional_signals = scan_result.get('positional_signals', [])

        if not swing_signals and not positional_signals:
            print("\n⚠️ No signals found")
            return

        # Filter by minimum score
        swing_signals = [s for s in swing_signals if s.get('score', 0) >= MIN_SIGNAL_SCORE]
        positional_signals = [s for s in positional_signals if s.get('score', 0) >= MIN_SIGNAL_SCORE]

        # Sort by score and take top N
        swing_signals = sorted(swing_signals, key=lambda x: x.get('score', 0), reverse=True)[:MAX_SWING_SIGNALS_PER_SCAN]
        positional_signals = sorted(positional_signals, key=lambda x: x.get('score', 0), reverse=True)[:MAX_POSITIONAL_SIGNALS_PER_SCAN]

        print(f"\n📊 Qualified Signals:")
        print(f"   🔥 Swing: {len(swing_signals)}")
        print(f"   📈 Positional: {len(positional_signals)}")

        # Process swing signals
        for signal in swing_signals:
            symbol = signal['symbol']

            # Validate signal freshness
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ⏭️ {symbol}: Skipped ({reason})")
                continue

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_swing_signal(signal)

                if executed:
                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_swing_signal(signal)
                    print(f"   🔥 {symbol}: Swing trade executed")
                else:
                    print(f"   ⏭️ {symbol}: Skipped (already holding or insufficient capital)")

        # Process positional signals
        for signal in positional_signals:
            symbol = signal['symbol']

            # Validate signal freshness
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ⏭️ {symbol}: Skipped ({reason})")
                continue

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_positional_signal(signal)

                if executed:
                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_positional_signal(signal)
                    print(f"   📈 {symbol}: Positional trade executed")
                else:
                    print(f"   ⏭️ {symbol}: Skipped (already holding or insufficient capital)")

    def monitor_positions(self):
        """Monitor open positions and check for exits"""
        all_positions = self.dual_portfolio.get_all_open_positions()
        swing_positions = all_positions['swing']
        positional_positions = all_positions['positional']

        if not swing_positions and not positional_positions:
            return

        print(f"\n👁️ Monitoring Positions:")
        print(f"   🔥 Swing: {len(swing_positions)}")
        print(f"   📈 Positional: {len(positional_positions)}")

        # Monitor swing positions
        if swing_positions:
            # Get current prices
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher(api_delay=0.2)

            current_prices = {}
            for symbol in swing_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits
            exits = self.dual_portfolio.monitor_swing_positions(current_prices)

            if exits:
                for exit_info in exits:
                    print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']})")
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='swing')

        # Monitor positional positions
        if positional_positions:
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher(api_delay=0.2)

            current_prices = {}
            for symbol in positional_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits
            exits = self.dual_portfolio.monitor_positional_positions(current_prices)

            if exits:
                for exit_info in exits:
                    print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']})")
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='positional')

    def run_continuous(self):
        """
        Run system continuously

        Schedule:
        - Before Market: Heartbeat every 5 minutes
        - 9:15 AM - 3:30 PM: Intraday scans (every 10 minutes)
        - 3:45 PM: EOD ranking (generate Top 500)
        - After Market: Heartbeat every 5 minutes
        """
        print("\n🔄 Starting EOD + INTRADAY System...")
        print("=" * 70)
        print(f"📊 Stock Universe: {len(self.stocks)} stocks")
        print(f"⏰ Intraday Scan: Every {SCAN_INTERVAL_MINUTES} minutes (9:15 AM - 3:30 PM)")
        print(f"🌆 EOD Ranking: 3:45 PM (generates Top 500 for next day)")
        print(f"👁️ Position Monitor: Every {POSITION_MONITOR_INTERVAL} minutes")
        print(f"💓 Heartbeat: Every 5 minutes (when market closed)")
        print("=" * 70)
        print("\nPress Ctrl+C to stop\n")

        self.is_running = True
        last_scan_time = None
        last_monitor_time = None
        last_heartbeat_time = None

        try:
            while self.is_running:
                current_time = datetime.now(IST).time()
                current_date = datetime.now(IST).date()

                # Define market hours
                market_open = dt_time(9, 15)
                market_close = dt_time(15, 30)
                eod_start = dt_time(15, 45)
                eod_end = dt_time(16, 0)

                # EOD RANKING (3:45 PM - once per day)
                if eod_start <= current_time < eod_end:
                    if not self.eod_done_today:
                        self.run_eod_ranking()
                        self.eod_done_today = True

                # Reset EOD flag at midnight
                if current_time < dt_time(0, 5):
                    self.eod_done_today = False

                # MARKET HOURS - Active Trading
                if market_open <= current_time <= market_close:
                    # Run intraday scan
                    if (last_scan_time is None or
                            (datetime.now() - last_scan_time).seconds >= SCAN_INTERVAL_MINUTES * 60):

                        scan_result = self.run_intraday_scan()
                        self.process_signals(scan_result)
                        last_scan_time = datetime.now()

                    # Monitor positions
                    if (last_monitor_time is None or
                            (datetime.now() - last_monitor_time).seconds >= POSITION_MONITOR_INTERVAL * 60):

                        self.monitor_positions()
                        last_monitor_time = datetime.now()

                    # Small sleep
                    time.sleep(30)

                # OUTSIDE MARKET HOURS - Heartbeat Mode
                else:
                    # Show heartbeat every 5 minutes
                    if (last_heartbeat_time is None or
                            (datetime.now() - last_heartbeat_time).seconds >= 300):  # 5 minutes

                        print(f"\n💤 Market CLOSED - System Active")
                        print(f"⏰ {self._get_ist_time()}")
                        print(f"📊 Loaded: {len(self.stocks)} stocks")
                        print(f"🔄 Next market open: 9:15 AM IST")
                        print(f"💓 Heartbeat: System running normally...")

                        last_heartbeat_time = datetime.now()

                    # Sleep for 60 seconds before next check
                    time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping system...")
            self.is_running = False

    def run_once(self):
        """Run a single scan cycle (for testing)"""
        scan_result = self.run_intraday_scan()
        self.process_signals(scan_result)
        self.monitor_positions()

    def _get_ist_time(self) -> str:
        """Get current IST time as string"""
        return datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='EOD + Intraday Trading System')
    parser.add_argument('--mode', choices=['once', 'continuous', 'eod'],
                        default='once', help='Run mode')
    parser.add_argument('--summary', action='store_true',
                        help='Show portfolio summary')

    args = parser.parse_args()

    # Show summary
    if args.summary:
        dual_portfolio = DualPortfolio()
        dual_portfolio.print_summary()
        return

    # Initialize system
    system = EODIntradaySystem()

    # Run based on mode
    if args.mode == 'eod':
        print("\n🌆 Running EOD ranking only...")
        system.run_eod_ranking()

    elif args.mode == 'once':
        print("\n🎯 Running single intraday scan...")
        system.run_once()

    elif args.mode == 'continuous':
        print("\n🔄 Running continuous mode...")
        system.run_continuous()


if __name__ == "__main__":
    main()
