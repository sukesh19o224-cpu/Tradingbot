"""
🚀 EOD + INTRADAY TRADING SYSTEM
End-of-Day ranking + Intraday sequential scanning

FLOW:
1. EOD (3:45 PM daily): Generate Top 1000 NSE stocks (ranked by market cap)
2. INTRADAY (every 10 mins): Scan Top 1000 sequentially, send alerts for qualified stocks
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
    - EOD ranking (3:45 PM): Top 1000 NSE stocks
    - Intraday scanning (every 10 mins): Sequential, safe, no API ban
    - Discord alerts for qualified stocks
    - Dual portfolio (swing + positional)
    """

    def __init__(self):
        print("🚀 Initializing EOD + INTRADAY System...")
        print("=" * 70)

        # Sequential scanner (NO threads!) - Maximum speed: 0.08s delay (very fast, monitor rate limits)
        self.scanner = SequentialScanner(api_delay=0.08)

        # Dual portfolio (uses settings values: INITIAL_CAPITAL=50K, SWING_CAPITAL=25K)
        self.dual_portfolio = DualPortfolio()

        # Discord alerts
        self.discord = DiscordAlerts()

        # Signal validator
        self.signal_validator = SignalValidator()

        # Stock list (will be loaded from config)
        self.stocks = self._load_stock_list()

        self.is_running = False
        self.eod_done_today = False  # Track if EOD ranking done today
        self.last_swing_monitor_time = None  # Track last swing monitoring time
        self.last_positional_monitor_time = None  # Track last positional monitoring time

        print(f"✅ System Initialized!")
        print(f"📊 Stock Universe: {len(self.stocks)} stocks")
        print(f"🐌 Sequential Scanning: ONE BY ONE (safe, no threads)")
        print(f"⏱️ API Delay: 0.1s between stocks (FAST - monitor for rate limits)")
        print(f"⏰ Scan Interval: Every {SCAN_INTERVAL_MINUTES} minutes")
        print(f"💼 Dual Portfolio: Positional (70%) + Swing (30%)")
        print(f"📱 Discord: {'Enabled' if self.discord.enabled else 'Disabled'}")
        print("=" * 70)

    def _load_stock_list(self) -> List[str]:
        """
        Load stock list from config

        Priority:
        1. nse_top_1000_live.py (if exists and not empty - from EOD ranking)
        2. nse_top_50_working.py (fallback)
        """
        try:
            # Try to load NSE Top 1000 (from EOD ranking)
            from config.nse_top_1000_live import NSE_TOP_1000, GENERATED_DATE

            # Check if list is not empty (not placeholder)
            if NSE_TOP_1000 and len(NSE_TOP_1000) > 0:
                print(f"📊 Loaded NSE Top 1000 (Generated: {GENERATED_DATE})")
                return NSE_TOP_1000
            else:
                # Empty list - use fallback
                raise ImportError("Top 1000 list is empty (placeholder)")

        except ImportError:
            # Fallback to Top 50
            try:
                from config.nse_top_50_working import NSE_TOP_50_WORKING
                print(f"⚠️ Using NSE Top 50 (fallback)")
                print(f"💡 Run EOD ranking to generate Top 1000 list!")
                return NSE_TOP_50_WORKING
            except ImportError:
                print("❌ No stock list found!")
                return []

    def run_eod_ranking(self):
        """
        Run End-of-Day ranking to generate Top 1000 list

        This should run ONCE per day at market close (3:45 PM)
        Takes ~20-30 minutes to complete
        """
        print("\n" + "=" * 70)
        print("🌆 END-OF-DAY RANKING - Generating Top 1000 List")
        print("=" * 70)
        print(f"⏰ Time: {self._get_ist_time()}")
        print("⏳ This will take ~20-30 minutes...")
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
                print("📊 config/nse_top_1000_live.py generated")
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
        Run intraday scan (sequential, up to 1000 stocks)
        
        CRITICAL: Monitors positions during scan (every 2 minutes)
        This ensures positions are checked even during long scans (7+ minutes)

        Returns:
            Dict with swing and positional signals
        """
        print("\n" + "=" * 70)
        print("🎯 INTRADAY SCAN - Sequential Scanning")
        print("=" * 70)
        print(f"⏰ Time: {self._get_ist_time()}")
        print(f"📊 Stocks: {len(self.stocks)}")
        print(f"👁️ Position monitoring: Every 2 minutes during scan")
        print()

        # Track monitoring times for during-scan monitoring
        last_swing_check = self.last_swing_monitor_time
        last_positional_check = self.last_positional_monitor_time
        scan_start_time = datetime.now()
        
        # Run sequential scan with periodic position monitoring
        # Monitor positions every 2 minutes during the scan
        result = self.scanner.scan_all_stocks(
            self.stocks,
            monitor_callback=self._monitor_positions_during_scan,
            monitor_callback_data={
                'last_swing_check': last_swing_check,
                'last_positional_check': last_positional_check,
                'scan_start_time': scan_start_time
            }
        )
        
        # Update monitor times after scan
        self.last_swing_monitor_time = datetime.now()
        self.last_positional_monitor_time = datetime.now()

        return result
    
    def _monitor_positions_during_scan(self, callback_data: Dict):
        """
        Callback function to monitor positions during scan
        
        Called periodically by the scanner to check positions
        even while scanning is in progress
        """
        current_time = datetime.now()
        last_swing_check = callback_data.get('last_swing_check')
        last_positional_check = callback_data.get('last_positional_check')
        
        # Check if 2 minutes have passed since last swing monitoring
        if (last_swing_check is None or 
            (current_time - last_swing_check).seconds >= SWING_MONITOR_INTERVAL * 60):
            self.monitor_swing_positions_only()
            callback_data['last_swing_check'] = current_time
            self.last_swing_monitor_time = current_time
        
        # Check if 2 minutes have passed since last positional monitoring
        if (last_positional_check is None or 
            (current_time - last_positional_check).seconds >= POSITIONAL_MONITOR_INTERVAL * 60):
            self.monitor_positional_positions_only()
            callback_data['last_positional_check'] = current_time
            self.last_positional_monitor_time = current_time

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

        # Filter by minimum score (FIX: Use correct threshold for swing)
        swing_signals = [s for s in swing_signals if s.get('score', 0) >= MIN_SWING_SIGNAL_SCORE]
        positional_signals = [s for s in positional_signals if s.get('score', 0) >= MIN_SIGNAL_SCORE]

        # Sort by score (primary) and quality score (secondary tiebreaker) - take top N
        def get_sort_key(signal):
            """Sort by signal score first, then quality score as tiebreaker"""
            score = signal.get('score', 0)
            signal_type = signal.get('signal_type', 'MOMENTUM')
            
            # Get quality score based on signal type
            if signal_type == 'MEAN_REVERSION':
                quality = signal.get('mean_reversion_score', 0)
            elif signal_type == 'MOMENTUM':
                quality = signal.get('momentum_score', 0)
            elif signal_type == 'BREAKOUT':
                quality = signal.get('breakout_score', 0)
            else:
                quality = 0
            
            # Return tuple: (signal_score, quality_score) for sorting
            # This ensures signals with same score are sorted by quality
            return (score, quality)
        
        swing_signals = sorted(swing_signals, key=get_sort_key, reverse=True)[:MAX_SWING_SIGNALS_PER_SCAN]
        positional_signals = sorted(positional_signals, key=get_sort_key, reverse=True)[:MAX_POSITIONAL_SIGNALS_PER_SCAN]

        print(f"\n📊 Qualified Signals:")
        print(f"   🔥 Swing: {len(swing_signals)}")
        print(f"   📈 Positional: {len(positional_signals)}")

        # Process swing signals
        print(f"\n{'='*70}")
        print(f"🌊 PROCESSING {len(swing_signals)} SWING SIGNALS")
        print(f"{'='*70}\n")
        
        for i, signal in enumerate(swing_signals, 1):
            symbol = signal['symbol']
            signal_type = signal.get('signal_type', 'SWING')
            score = signal.get('score', 0)
            
            print(f"{i}. {symbol} - {signal_type} (Score: {score:.1f}/10)")

            # SWING: MOMENTUM ONLY - Reject Mean Reversion and Breakout
            if signal_type != 'MOMENTUM':
                print(f"   ❌ REJECTED - Swing trades are MOMENTUM ONLY (got {signal_type})")
                    print()
                    continue
            
            # Check momentum quality for swing trades
            if signal_type == 'MOMENTUM':
                momentum_score = signal.get('momentum_score', 0)
                is_valid = signal.get('momentum_valid', False)
                
                print(f"   📊 Momentum Quality: {momentum_score}/100")
                
                # Swing: Accept score >= 25 (optimized for 1-2% quick moves)
                if momentum_score < 25:
                    print(f"   ❌ REJECTED - Weak momentum (need ≥25 for swing)")
                    print()
                    continue
                else:
                    print(f"   ✅ PASSED - Good momentum swing (optimized for 1-2% quick moves)")

            # Validate signal freshness
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ❌ REJECTED - {reason}")
                print()
                continue

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_swing_signal(signal)

                if executed:
                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_swing_signal(signal)
                    print(f"   🔥 Swing trade executed")
                    print()
                else:
                    print(f"   ⏭️ Skipped (already holding or insufficient capital)")
                    print()

        # Process positional signals
        print(f"\n{'='*70}")
        print(f"📊 PROCESSING {len(positional_signals)} POSITIONAL SIGNALS")
        print(f"{'='*70}\n")
        
        for i, signal in enumerate(positional_signals, 1):
            symbol = signal['symbol']
            signal_type = signal.get('signal_type', 'MOMENTUM')
            score = signal.get('score', 0)
            
            print(f"{i}. {symbol} - {signal_type} (Score: {score:.1f}/10)")

            # Check quality filters based on signal type
            if signal_type == 'MEAN_REVERSION':
                mean_rev_score = signal.get('mean_reversion_score', 0)
                is_valid = signal.get('mean_reversion_valid', False)
                
                print(f"   📊 Mean Reversion Quality: {mean_rev_score}/100")
                
                if not is_valid:
                    print(f"   ❌ REJECTED - Weak mean reversion setup (need ≥40 score)")
                    print()
                    continue
                else:
                    print(f"   ✅ PASSED - Good mean reversion setup")
            
            elif signal_type == 'MOMENTUM':
                momentum_score = signal.get('momentum_score', 0)
                is_valid = signal.get('momentum_valid', False)
                
                print(f"   📊 Momentum Quality: {momentum_score}/100")
                
                if not is_valid:
                    print(f"   ❌ REJECTED - Weak momentum setup (need ≥50 score)")
                    print()
                    continue
                else:
                    print(f"   ✅ PASSED - Good momentum setup")
            elif signal_type == 'BREAKOUT':
                breakout_score = signal.get('breakout_score', 0)
                is_valid = signal.get('breakout_valid', False)
                
                print(f"   📊 Breakout Quality: {breakout_score}/100")
                
                if not is_valid:
                    print(f"   ❌ REJECTED - Weak breakout setup (need ≥50 score)")
                    print()
                    continue
                else:
                    print(f"   ✅ PASSED - Good breakout setup")
            else:
                print(f"   ⚠️ Unknown signal type: {signal_type}")

            # Validate signal freshness
            is_valid, reason = self.signal_validator.validate_signal_freshness(
                signal, signal.get('current_price', signal.get('entry_price', 0))
            )

            if not is_valid:
                print(f"   ❌ REJECTED - {reason}")
                print()
                continue

            if PAPER_TRADING_AUTO_EXECUTE:
                executed = self.dual_portfolio.execute_positional_signal(signal)

                if executed:
                    # Send Discord alert
                    if self.discord.enabled:
                        self.discord.send_positional_signal(signal)
                    print(f"   📈 Positional trade executed")
                    print()
                else:
                    print(f"   ⏭️ Skipped (already holding or insufficient capital)")
                    print()

    def monitor_positions(self):
        """Monitor open positions and check for exits (legacy method - kept for compatibility)"""
        self.monitor_swing_positions_only()
        self.monitor_positional_positions_only()

    def monitor_swing_positions_only(self):
        """Monitor swing positions only (called every 2 minutes)"""
        all_positions = self.dual_portfolio.get_all_open_positions()
        swing_positions = all_positions['swing']

        if not swing_positions:
            return

        print(f"\n👁️ Monitoring Swing Positions ({len(swing_positions)} positions):")

            # Get current prices
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher(api_delay=0.2)

            current_prices = {}
            for symbol in swing_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits and trailing stop activations
            exits, trailing_activations = self.dual_portfolio.monitor_swing_positions(current_prices)

            # Send trailing stop activation alerts
            if trailing_activations:
                for activation in trailing_activations:
                    print(f"   🔒 {activation['symbol']}: Trailing stop activated (Profit: +{activation['profit_pct']*100:.2f}%)")
                    if self.discord.enabled:
                        self.discord.send_trailing_stop_alert(activation, paper_trade=True)

        # Send exit alerts for ALL exits (partial and full)
        # User wants to see all exits: T1 (60%), T2 (40%), Stop Loss (full), etc.
            if exits:
                for exit_info in exits:
                exit_type = exit_info.get('exit_type', 'FULL')
                print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']}) [{exit_type}]")
                
                # Send Discord alert for ALL exits (partial and full)
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='swing', paper_trade=True)

    def monitor_positional_positions_only(self):
        """Monitor positional positions only (called every 2 minutes)"""
        all_positions = self.dual_portfolio.get_all_open_positions()
        positional_positions = all_positions['positional']

        if not positional_positions:
            return

        print(f"\n👁️ Monitoring Positional Positions ({len(positional_positions)} positions):")

        # Get current prices
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher(api_delay=0.2)

            current_prices = {}
            for symbol in positional_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    current_prices[symbol] = price

            # Check for exits and trailing stop activations
            exits, trailing_activations = self.dual_portfolio.monitor_positional_positions(current_prices)

            # Send trailing stop activation alerts
            if trailing_activations:
                for activation in trailing_activations:
                    print(f"   🔒 {activation['symbol']}: Trailing stop activated (Profit: +{activation['profit_pct']*100:.2f}%)")
                    if self.discord.enabled:
                        self.discord.send_trailing_stop_alert(activation, paper_trade=True)

        # Send exit alerts for ALL exits (partial and full)
        # User wants to see all exits: T1 (30%), T2 (40%), Stop Loss (full), etc.
            if exits:
                for exit_info in exits:
                exit_type = exit_info.get('exit_type', 'FULL')
                print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']}) [{exit_type}]")
                
                # Send Discord alert for ALL exits (partial and full)
                    if self.discord.enabled:
                        self.discord.send_exit_alert(exit_info, strategy='positional', paper_trade=True)

    def run_continuous(self):
        """
        Run system continuously

        Schedule:
        - Before Market: Heartbeat every 5 minutes
        - 9:15 AM - 3:30 PM: Intraday scans (every 10 minutes)
        - 3:45 PM: EOD ranking (generate Top 1000)
        - After Market: Heartbeat every 5 minutes
        """
        print("\n🔄 Starting EOD + INTRADAY System...")
        print("=" * 70)
        print(f"📊 Stock Universe: {len(self.stocks)} stocks")
        print(f"⏰ Intraday Scan: Every {SCAN_INTERVAL_MINUTES} minutes (9:30 AM - 3:30 PM)")
        print(f"🌆 EOD Ranking: 3:45 PM (generates Top 1000 for next day)")
        print(f"👁️ Position Monitor:")
        print(f"   🔥 Swing: Every {SWING_MONITOR_INTERVAL} minutes (high-frequency, quick exits)")
        print(f"   📈 Positional: Every {POSITIONAL_MONITOR_INTERVAL} minutes (faster monitoring)")
        print(f"💓 Heartbeat: Every 5 minutes (when market closed)")
        print("=" * 70)
        print("\nPress Ctrl+C to stop\n")

        self.is_running = True
        last_scan_time = None
        last_swing_monitor_time = None
        last_positional_monitor_time = None
        last_heartbeat_time = None
        last_summary_date = None  # Track if summary sent today

        try:
            while self.is_running:
                current_time = datetime.now(IST).time()
                current_date = datetime.now(IST).date()

                # Define market hours
                market_open = dt_time(9, 30)  # Start at 9:30 AM to avoid opening volatility
                market_close = dt_time(15, 30)
                eod_start = dt_time(15, 45)
                eod_end = dt_time(16, 0)
                summary_time = dt_time(15, 35)  # Send summary at 3:35 PM (after market close)

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

                        # Remove old signal file before scanning
                        if os.path.exists('data/.strategy1_complete'):
                            os.remove('data/.strategy1_complete')
                        
                        scan_result = self.run_intraday_scan()
                        self.process_signals(scan_result)
                        last_scan_time = datetime.now()
                        
                        # Signal Strategy 2 that scan is complete
                        with open('data/.strategy1_complete', 'w') as f:
                            f.write(datetime.now().isoformat())

                    # CRITICAL FIX: Monitor swing and positional positions separately with different intervals
                    # Swing: 2 minutes (high-frequency, small margins need quick exits)
                    # Positional: 2 minutes (faster monitoring for better exits)
                    current_time_sec = datetime.now()
                    
                    # Monitor swing positions (every 2 minutes)
                    if (last_swing_monitor_time is None or
                            (current_time_sec - last_swing_monitor_time).seconds >= SWING_MONITOR_INTERVAL * 60):
                        self.monitor_swing_positions_only()
                        last_swing_monitor_time = current_time_sec
                    
                    # Monitor positional positions (every 2 minutes)
                    if (last_positional_monitor_time is None or
                            (current_time_sec - last_positional_monitor_time).seconds >= POSITIONAL_MONITOR_INTERVAL * 60):
                        self.monitor_positional_positions_only()
                        last_positional_monitor_time = current_time_sec

                    # Small sleep
                    time.sleep(30)

                # OUTSIDE MARKET HOURS - Heartbeat Mode
                else:
                    # Send daily summary once after market close (3:35 PM)
                    if (summary_time <= current_time < dt_time(16, 0) and 
                        last_summary_date != current_date):
                        print(f"\n📊 Market CLOSED - Sending daily summary...")
                        self.send_daily_summary()
                        last_summary_date = current_date
                    
                    # Show heartbeat every 5 minutes
                    if (last_heartbeat_time is None or
                            (datetime.now() - last_heartbeat_time).seconds >= 300):  # 5 minutes

                        print(f"\n💤 Market CLOSED - System Active")
                        print(f"⏰ {self._get_ist_time()}")
                        print(f"📊 Loaded: {len(self.stocks)} stocks")
                        print(f"🔄 Next market open: 9:30 AM IST")
                        print(f"💓 Heartbeat: System running normally...")

                        last_heartbeat_time = datetime.now()

                    # Sleep for 60 seconds before next check
                    time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping system...")
            self.is_running = False

    def send_daily_summary(self):
        """Send end-of-day summary to Discord with position analysis"""
        print("\n📊 Generating daily summary with position analysis...")
        
        try:
            # Get combined summary
            summary = self.dual_portfolio.get_combined_summary()
            
            # Get all open positions with current prices
            all_positions = self.dual_portfolio.get_all_open_positions()
            swing_positions = all_positions.get('swing', {})
            positional_positions = all_positions.get('positional', {})
            
            # Fetch current prices for all positions
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher(api_delay=0.1)
            
            swing_prices = {}
            for symbol in swing_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    swing_prices[symbol] = price
            
            positional_prices = {}
            for symbol in positional_positions.keys():
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    positional_prices[symbol] = price
            
            # Prepare positions data for analysis
            positions_data = {
                'swing': {
                    'positions': swing_positions,
                    'current_prices': swing_prices
                },
                'positional': {
                    'positions': positional_positions,
                    'current_prices': positional_prices
                }
            }
            
            # Send to Discord
            if self.discord.enabled and SEND_DAILY_SUMMARY:
                self.discord.send_dual_portfolio_summary(summary, positions_data)
            
            # Print to console
            self.dual_portfolio.print_summary()
            
        except Exception as e:
            print(f"❌ Error generating daily summary: {e}")
            import traceback
            traceback.print_exc()

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
    parser.add_argument('--daily-summary', action='store_true',
                        help='Send daily summary with position analysis to Discord (can run anytime)')

    args = parser.parse_args()

    # Show summary
    if args.summary:
        dual_portfolio = DualPortfolio()
        dual_portfolio.print_summary()
        return

    # Send daily summary with position analysis
    if args.daily_summary:
        print("📊 Generating daily summary with position analysis...")
        system = EODIntradaySystem()
        system.send_daily_summary()
        print("\n✅ Daily summary sent to Discord!")
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
