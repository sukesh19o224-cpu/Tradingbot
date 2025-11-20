"""
🚀 SUPER MATH TRADING SYSTEM - Main Application
Automated signal generation with paper trading and Discord alerts
"""

import time
from datetime import datetime, time as dt_time
import pytz
from typing import List, Dict
import argparse

from config.settings import *
from src.data.data_fetcher import DataFetcher
from src.data.fast_scanner import FastScanner
from src.strategies.signal_generator import SignalGenerator
from src.paper_trading.paper_trader import PaperTrader
from src.alerts.discord_alerts import DiscordAlerts

IST = pytz.timezone('Asia/Kolkata')


class TradingSystem:
    """
    Main trading system orchestrator

    Responsibilities:
    - Scan stocks for signals
    - Execute paper trades
    - Monitor open positions
    - Send Discord alerts
    - Manage daily operations
    """

    def __init__(self):
        print("🚀 Initializing Super Math Trading System...")

        self.data_fetcher = DataFetcher()
        self.fast_scanner = FastScanner(max_workers=10)  # Multi-threaded scanner
        self.signal_generator = SignalGenerator()
        self.paper_trader = PaperTrader()
        self.discord = DiscordAlerts()

        self.watchlist = DEFAULT_WATCHLIST
        self.is_running = False

        print("✅ System initialized successfully!")
        print(f"📊 Monitoring {len(self.watchlist)} stocks")
        print(f"⚡ Multi-threaded scanning: ENABLED (10x faster)")
        print(f"💰 Paper Trading Capital: ₹{self.paper_trader.capital:,.0f}")
        print(f"📱 Discord Alerts: {'Enabled' if self.discord.enabled else 'Disabled'}")

    def run_scan(self) -> List[Dict]:
        """
        Run complete stock scan and generate signals (Multi-threaded)

        Returns:
            List of signal dictionaries
        """
        print("\n" + "="*70)
        print(f"🔍 FAST MULTI-THREADED STOCK SCAN")
        print(f"⏰ {self._get_ist_time()}")
        print("="*70)

        # Use fast scanner (multi-threaded)
        result = self.fast_scanner.scan_all_stocks(self.watchlist)

        signals = result['signals']
        stats = result['stats']

        # Display top signals
        if signals:
            print(f"🎯 TOP SIGNALS:")
            for i, signal in enumerate(signals[:5], 1):
                print(f"\n{i}. {signal['symbol']} - Score: {signal['score']}/10 ({signal['trade_type']})")
                print(f"   Entry: ₹{signal['entry_price']:.2f}")
                print(f"   Target 2: ₹{signal['target2']:.2f} (+{((signal['target2']/signal['entry_price']-1)*100):.1f}%)")
                print(f"   Stop: ₹{signal['stop_loss']:.2f} | R:R: {signal['risk_reward_ratio']:.1f}:1")
                print(f"   ML Prediction: {signal['predicted_return']:+.1f}% ({signal['ml_confidence']*100:.0f}% confidence)")
        else:
            print(f"\n⚠️ No signals found (Try lowering MIN_SIGNAL_SCORE in config/settings.py)")

        return signals

    def process_signals(self, signals: List[Dict]):
        """
        Process signals: execute paper trades and send alerts

        Args:
            signals: List of signal dictionaries
        """
        if not signals:
            print("\n⚠️ No signals to process")
            return

        print(f"\n📋 Processing {len(signals)} signals...")

        for signal in signals:
            symbol = signal['symbol']

            # Execute paper trade
            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.paper_trader.execute_signal(signal)

                if executed:
                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_buy_signal(signal, paper_trade=True)
                else:
                    print(f"⏭️ Skipped {symbol} (already holding or insufficient capital)")

        print("\n✅ Signal processing complete")

    def monitor_positions(self):
        """
        Monitor open positions and check for exits

        Checks:
        - Target hits
        - Stop loss
        - Time-based exits
        """
        if not self.paper_trader.positions:
            return

        print(f"\n👁️ Monitoring {len(self.paper_trader.positions)} open positions...")

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
        Run system continuously during market hours

        Schedule:
        - Pre-market scan: 9:00 AM
        - Market scans: Every SCAN_INTERVAL_MINUTES
        - Position monitoring: Every 3 minutes
        - Post-market summary: 3:45 PM
        """
        print("\n🔄 Starting continuous mode...")
        print(f"⏰ Market Hours: {MARKET_OPEN_TIME} - {MARKET_CLOSE_TIME} IST")
        print(f"🔍 Scan Interval: {SCAN_INTERVAL_MINUTES} minutes")
        print(f"📊 Position Monitor: Every {POSITION_MONITOR_INTERVAL} minutes")

        self.is_running = True
        last_scan_time = None
        last_monitor_time = None

        try:
            while self.is_running:
                current_time = datetime.now(IST).time()

                # Check if market is open
                market_open = dt_time(9, 15)
                market_close = dt_time(15, 30)

                if market_open <= current_time <= market_close:
                    # Market hours - run scans and monitoring

                    # Run scan
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

                else:
                    # Market closed
                    if current_time > market_close:
                        # Post-market
                        print(f"\n🌙 Market closed. Next scan at {MARKET_OPEN_TIME} IST tomorrow.")

                        # Send daily summary (once per day)
                        if last_scan_time and last_scan_time.date() == datetime.now().date():
                            self.send_daily_summary()
                            last_scan_time = None  # Reset for next day

                        # Sleep until next market open
                        time.sleep(3600)  # 1 hour
                    else:
                        # Pre-market
                        print(f"\n🌅 Pre-market. Waiting for market open at {MARKET_OPEN_TIME} IST...")
                        time.sleep(300)  # 5 minutes

                # Small sleep to prevent CPU overuse
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping system...")
            self.is_running = False

    def run_once(self):
        """Run a single scan cycle"""
        signals = self.run_scan()
        self.process_signals(signals)
        self.monitor_positions()

    def _get_ist_time(self) -> str:
        """Get current time in IST"""
        return datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Super Math Trading System')
    parser.add_argument('--mode', choices=['once', 'continuous', 'dashboard'],
                       default='once', help='Run mode')
    parser.add_argument('--test-discord', action='store_true',
                       help='Test Discord connection')
    parser.add_argument('--summary', action='store_true',
                       help='Show portfolio summary')

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

    # Initialize system
    system = TradingSystem()

    # Run based on mode
    if args.mode == 'once':
        print("\n🎯 Running single scan cycle...")
        system.run_once()

    elif args.mode == 'continuous':
        print("\n🔄 Running continuous mode...")
        print("Press Ctrl+C to stop")
        system.run_continuous()


if __name__ == "__main__":
    main()
