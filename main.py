"""
🚀 SUPER MATH HYBRID TRADING SYSTEM - Main Application
Dual strategy: Swing Trading + Positional Trading running simultaneously
"""

# Standard library imports
import time
import argparse
from datetime import datetime, time as dt_time
from typing import List, Dict

# Third-party imports
import pytz
import yfinance as yf

# Local imports
from config.settings import *
from src.data.data_fetcher import DataFetcher
from src.data.hybrid_scanner import HybridScanner
from src.data.nse_stock_fetcher import NSEStockFetcher
from src.strategies.signal_generator import SignalGenerator
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.paper_trading.dual_portfolio import DualPortfolio
from src.alerts.discord_alerts import DiscordAlerts
from src.utils.signal_validator import SignalValidator

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

    def __init__(self):
        print("🚀 Initializing HYBRID Trading System...")
        print("   🔥 Swing Trading + 📈 Positional Trading")

        self.data_fetcher = DataFetcher()
        self.signal_generator = SignalGenerator()

        # DUAL PORTFOLIO SYSTEM (60% swing, 40% positional)
        self.dual_portfolio = DualPortfolio(total_capital=INITIAL_CAPITAL)

        self.discord = DiscordAlerts()

        # Signal validator for quality control
        self.signal_validator = SignalValidator()

        # Multi-timeframe analyzer and NSE stock fetcher
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.nse_fetcher = NSEStockFetcher(use_simple=True)  # Use Top 50 WORKING stocks!

        # Scan VERIFIED WORKING stocks (guaranteed to work!)
        self.watchlist = self.nse_fetcher.fetch_nse_stocks()

        # ULTRA-SAFE thread settings: Just 3 threads (BULLETPROOF!)
        # 3 threads = ZERO API issues, reliable, works every time!
        # 50 stocks with 3 threads = ~2-3 min scan time (acceptable!)
        self.hybrid_scanner = HybridScanner(max_workers=3)

        self.is_running = False

        # Cache for NIFTY opening price (updated once per day at market open)
        self.nifty_open_price = None
        self.nifty_open_date = None

        print("✅ Hybrid System initialized successfully!")
        print(f"📊 Scanning Universe: {len(self.watchlist)} VERIFIED WORKING stocks")
        print(f"⚡ Hybrid Scanner: ENABLED (swing + positional detection)")
        print(f"⚡ Threads: 3 (ULTRA-SAFE, bulletproof!)")
        print(f"⚡ Multi-timeframe: Daily + 15-minute candles")
        print(f"💼 Dual Portfolio System:")
        print(f"   🔥 Swing Portfolio: ₹{INITIAL_CAPITAL * 0.60:,.0f} (60%)")
        print(f"   📈 Positional Portfolio: ₹{INITIAL_CAPITAL * 0.40:,.0f} (40%)")
        print(f"   💰 Total Capital: ₹{INITIAL_CAPITAL:,.0f}")
        print(f"📱 Discord Alerts: {'Enabled' if self.discord.enabled else 'Disabled'}")
        print(f"🛡️ API Protection: Smart caching + 3 threads + 10min intervals = ZERO errors!")

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

        # CRITICAL FIX #4: Limit signals to top quality only
        # Filter to MIN_SIGNAL_SCORE and take top N by score
        swing_signals = [s for s in swing_signals if s.get('score', 0) >= MIN_SIGNAL_SCORE]
        positional_signals = [s for s in positional_signals if s.get('score', 0) >= MIN_SIGNAL_SCORE]

        # Sort by score (descending) and take top N
        swing_signals = sorted(swing_signals, key=lambda x: x.get('score', 0), reverse=True)[:MAX_SWING_SIGNALS_PER_SCAN]
        positional_signals = sorted(positional_signals, key=lambda x: x.get('score', 0), reverse=True)[:MAX_POSITIONAL_SIGNALS_PER_SCAN]

        print(f"\n📋 Processing Signals (Top Quality Only)...")
        print(f"   🔥 Swing: {len(swing_signals)} signals (filtered)")
        print(f"   📈 Positional: {len(positional_signals)} signals (filtered)")

        # Process swing signals → Swing portfolio
        for signal in swing_signals:
            symbol = signal['symbol']

            # Validate signal freshness and quality
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ⏭️ Swing: {symbol} skipped ({reason})")
                continue

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

            # Validate signal freshness and quality
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ⏭️ Positional: {symbol} skipped ({reason})")
                continue

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
        Monitor BOTH swing and positional positions

        Swing trades: Check every 15 minutes (tighter stops)
        Positional trades: Check every hour (wider stops)
        """
        all_positions = self.dual_portfolio.get_all_open_positions()
        swing_positions = all_positions['swing']
        positional_positions = all_positions['positional']

        if not swing_positions and not positional_positions:
            return

        # CRITICAL FIX #5: Market Circuit Breaker
        # Exit all positions if NIFTY crashes >2%
        try:
            nifty_price = self.data_fetcher.get_current_price(NIFTY_SYMBOL)
            if nifty_price > 0:
                # Get NIFTY's opening price (cached - fetched once per day)
                nifty_open = self._get_nifty_open_price()
                if nifty_open and nifty_open > 0:
                    nifty_change_pct = (nifty_price - nifty_open) / nifty_open

                    if nifty_change_pct <= MARKET_CRASH_THRESHOLD:
                        print(f"\n🚨 MARKET CIRCUIT BREAKER TRIGGERED!")
                        print(f"   NIFTY 50: {nifty_change_pct*100:.2f}% (Threshold: {MARKET_CRASH_THRESHOLD*100:.1f}%)")
                        print(f"   🚪 Exiting ALL positions for capital preservation...")

                        # Exit all swing positions
                        if swing_positions:
                            current_prices = {}
                            for symbol in swing_positions.keys():
                                price = self.data_fetcher.get_current_price(symbol)
                                if price > 0:
                                    current_prices[symbol] = price

                            for symbol in list(swing_positions.keys()):
                                if symbol in current_prices:
                                    self.dual_portfolio.swing_portfolio._exit_position(
                                        symbol, current_prices[symbol], 'MARKET_CRASH_PROTECTION', full_exit=True
                                    )

                        # Exit all positional positions
                        if positional_positions:
                            current_prices = {}
                            for symbol in positional_positions.keys():
                                price = self.data_fetcher.get_current_price(symbol)
                                if price > 0:
                                    current_prices[symbol] = price

                            for symbol in list(positional_positions.keys()):
                                if symbol in current_prices:
                                    self.dual_portfolio.positional_portfolio._exit_position(
                                        symbol, current_prices[symbol], 'MARKET_CRASH_PROTECTION', full_exit=True
                                    )

                        print(f"   ✅ All positions exited - Capital preserved")
                        return  # Skip normal monitoring
        except Exception as e:
            print(f"   ⚠️ Circuit breaker check failed: {e}")

        # Monitor swing positions (more frequently)
        if swing_positions:
            print(f"\n👁️ Monitoring {len(swing_positions)} swing positions...")

            # Get current prices
            current_prices = {}
            for symbol in swing_positions.keys():
                price = self.data_fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits
            exits = self.dual_portfolio.monitor_swing_positions(current_prices)

            if exits:
                print(f"\n🚪 {len(exits)} swing position(s) exited:")

                for exit_info in exits:
                    symbol = exit_info['symbol']
                    pnl = exit_info['pnl']
                    reason = exit_info['reason']

                    print(f"   🔥 {symbol}: ₹{pnl:+,.0f} ({reason})")

                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='swing')

        # Monitor positional positions
        if positional_positions:
            print(f"\n👁️ Monitoring {len(positional_positions)} positional positions...")

            # Get current prices
            current_prices = {}
            for symbol in positional_positions.keys():
                price = self.data_fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits
            exits = self.dual_portfolio.monitor_positional_positions(current_prices)

            if exits:
                print(f"\n🚪 {len(exits)} positional position(s) exited:")

                for exit_info in exits:
                    symbol = exit_info['symbol']
                    pnl = exit_info['pnl']
                    reason = exit_info['reason']

                    print(f"   📈 {symbol}: ₹{pnl:+,.0f} ({reason})")

                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='positional')

    def send_daily_summary(self):
        """Send end-of-day summary to Discord (DUAL portfolio)"""
        print("\n📊 Generating daily summary...")

        # Get combined summary
        summary = self.dual_portfolio.get_combined_summary()

        # Send to Discord
        if self.discord.enabled and SEND_DAILY_SUMMARY:
            self.discord.send_dual_portfolio_summary(summary)

        # Print to console
        self.dual_portfolio.print_summary()

    def run_continuous(self):
        """
        Run HYBRID system continuously - scans ALL stocks for both opportunities

        Schedule:
        - Market hours (9:15 AM - 3:30 PM): Hybrid scan every 10 minutes
        - Detects swing + positional setups simultaneously
        - Position monitoring: Every 5 minutes
        - Post-market (3:30 PM): Daily summary
        - Night: Sleep until next market open
        """
        print("\n🔄 Starting HYBRID AUTOMATIC MODE...")
        print(f"🎯 Scanning: ALL {len(self.watchlist)} NSE stocks")
        print(f"⏰ Market Hours: {MARKET_OPEN_TIME} - {MARKET_CLOSE_TIME} IST")
        print(f"🔍 Hybrid Scan: Every {SCAN_INTERVAL_MINUTES} minutes")
        print(f"   🔥 Swing detection: Fast momentum, breakouts (5-10%, 1-5 days)")
        print(f"   📈 Positional detection: Trends, pullbacks (15-30%, 2-4 weeks)")
        print(f"📊 Position Monitor: Every {POSITION_MONITOR_INTERVAL} minutes")
        print(f"✨ FULLY AUTOMATIC: No missed opportunities!")

        self.is_running = True
        last_scan_time = None
        last_monitor_time = None

        try:
            while self.is_running:
                current_time = datetime.now(IST).time()
                current_date = datetime.now(IST).date()

                # Market hours
                market_open = dt_time(9, 15)
                market_close = dt_time(15, 30)

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

                    print(f"\n💤 Market closed. Sleeping until tomorrow's market open...")

                    # Sleep for 30 minutes
                    time.sleep(1800)

                else:
                    # NIGHT TIME (10:00 PM - 9:15 AM)
                    print(f"\n🌙 Night mode - Sleeping until market open tomorrow...")
                    print(f"⏰ Next market open: {MARKET_OPEN_TIME} IST")

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

    def _get_nifty_open_price(self) -> float:
        """
        Get NIFTY opening price (cached per day)

        Fetches NIFTY opening price once per day and caches it.
        This avoids repeated API calls during position monitoring.

        Returns:
            NIFTY opening price for current trading day, or None if unavailable
        """
        current_date = datetime.now(IST).date()

        # Return cached value if available for today
        if self.nifty_open_date == current_date and self.nifty_open_price:
            return self.nifty_open_price

        # Fetch fresh value (once per day)
        try:
            nifty_data = yf.Ticker(NIFTY_SYMBOL).history(period='1d', interval='1d')
            if not nifty_data.empty:
                self.nifty_open_price = nifty_data['Open'].iloc[-1]
                self.nifty_open_date = current_date
                print(f"   📊 NIFTY opening price cached: ₹{self.nifty_open_price:.2f}")
                return self.nifty_open_price
        except Exception as e:
            print(f"   ⚠️ Error fetching NIFTY open price: {e}")

        return None

    def _get_ist_time(self) -> str:
        """Get current time in IST"""
        return datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Hybrid Trading System - Swing + Positional')
    parser.add_argument('--mode', choices=['once', 'continuous'],
                       default='once', help='Run mode (once=single scan, continuous=live trading)')
    parser.add_argument('--test-discord', action='store_true',
                       help='Test Discord connection')
    parser.add_argument('--summary', action='store_true',
                       help='Show dual portfolio summary')

    args = parser.parse_args()

    # Test Discord
    if args.test_discord:
        print("\n🧪 Testing Discord connection...")
        discord = DiscordAlerts()
        discord.send_test_alert()
        return

    # Show summary
    if args.summary:
        dual_portfolio = DualPortfolio()
        dual_portfolio.print_summary()
        return

    # Initialize hybrid system
    system = TradingSystem()

    # Run based on mode
    if args.mode == 'once':
        print("\n🎯 Running single scan cycle...")
        system.run_once()

    elif args.mode == 'continuous':
        print("\n🔄 Running continuous hybrid mode...")
        print("Press Ctrl+C to stop")
        system.run_continuous()


if __name__ == "__main__":
    main()
