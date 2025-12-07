#!/usr/bin/env python3
"""
🎯 STRATEGY 2 - Main Trading System
50% Swing / 50% Positional - STRICTER Quality

This runs AFTER Strategy 1 completes to avoid API conflicts
Uses SAME analysis engine as Strategy 1, just MODERATELY STRICTER filtering
"""

import sys
import time
import os
from datetime import datetime
import pytz

# Import Strategy 2 settings
sys.path.insert(0, '/media/sukesh-k/Storage/new Tr/TraDc')
from config import settings_strategy2 as settings

from src.data.nse_stock_fetcher import NSEStockFetcher
from src.data.data_fetcher import DataFetcher
from src.strategies.signal_generator import SignalGenerator
from src.paper_trading.dual_portfolio_strategy2 import DualPortfolioStrategy2
from src.alerts.discord_alerts import DiscordAlerts

class Strategy2TradingSystem:
    """Strategy 2: 50/50 Stricter Trading System (Above Strategy 1 strictness)"""
    
    def __init__(self):
        # Load same stock list as Strategy 1 (Top 500)
        self.stocks = self._load_stock_list()
        self.data_fetcher = DataFetcher()
        self.signal_generator = SignalGenerator()
        self.portfolio = DualPortfolioStrategy2(
            swing_file='data/strategy2_swing_portfolio.json',
            positional_file='data/strategy2_positional_portfolio.json',
            initial_capital=settings.INITIAL_CAPITAL
        )
        self.discord = DiscordAlerts() if settings.DISCORD_ENABLED else None
        self.timezone = pytz.timezone(settings.TIMEZONE)
        
        print("="*70)
        print("🎯 STRATEGY 2 - STRICTER TRADING SYSTEM")
        print("="*70)
        print(f"📊 50% Swing (≥8.3 score) + 50% Positional (≥7.5 score)")
        print(f"💰 Capital: ₹{settings.INITIAL_CAPITAL:,}")
        print(f"📈 Max Positions: {settings.MAX_POSITIONS} per portfolio")
        print(f"🎯 Higher quality than Strategy 1")
        discord_status = "✅" if self.discord and self.discord.enabled else "❌"
        print(f"📱 Discord: {discord_status} (STRATEGY 2) | Dashboard: Port {settings.DASHBOARD_PORT}")
        print("="*70)
    
    def _load_stock_list(self):
        """Load same stock list as Strategy 1 (Top 500 from EOD ranking)"""
        try:
            # Try to load NSE Top 500 (from EOD ranking)
            from config.nse_top_500_live import NSE_TOP_500, GENERATED_DATE
            
            if NSE_TOP_500 and len(NSE_TOP_500) > 0:
                print(f"📊 Loaded NSE Top 500 (Generated: {GENERATED_DATE})")
                return NSE_TOP_500
            else:
                raise ImportError("Top 500 list is empty")
        except ImportError:
            # Fallback to Top 50
            from config.nse_top_50_working import NSE_TOP_50_WORKING
            print(f"⚠️ Using NSE Top 50 (fallback)")
            print(f"💡 Run EOD ranking to generate Top 500 list!")
            return NSE_TOP_50_WORKING
    
    def is_market_open(self):
        """Check if market is currently open"""
        now = datetime.now(self.timezone)
        
        # Weekend check
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours check
        market_open = datetime.strptime(settings.MARKET_OPEN_TIME, '%H:%M').time()
        market_close = datetime.strptime(settings.MARKET_CLOSE_TIME, '%H:%M').time()
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    def scan_and_generate_signals(self):
        """Scan stocks and generate trading signals"""
        print("\n" + "="*70)
        print(f"📊 STRATEGY 2 - SCANNING FOR SIGNALS")
        print("="*70)
        print(f"⏰ {datetime.now(self.timezone).strftime('%d %b %Y, %I:%M %p IST')}")
        print("="*70)
        
        try:
            # Get stock list (same 500 as Strategy 1)
            stocks = self.stocks
            print(f"📊 Scanning {len(stocks)} stocks...")
            
            swing_signals = []
            positional_signals = []
            
            for i, symbol in enumerate(stocks, 1):
                try:
                    print(f"[{i}/{len(stocks)}] Analyzing {symbol}...", end='\r')
                    
                    # Fetch data for the symbol
                    df = self.data_fetcher.get_stock_data(symbol, period="1mo", interval="1d")
                    
                    if df is None or len(df) < 20:
                        continue
                    
                    # Generate signal
                    signal = self.signal_generator.generate_signal(symbol, df)
                    
                    if signal:
                        if signal['trade_type'] == 'SWING':
                            swing_signals.append(signal)
                        else:
                            positional_signals.append(signal)
                    
                    time.sleep(settings.API_REQUEST_DELAY)
                    
                except Exception as e:
                    print(f"\n⚠️ Error analyzing {symbol}: {e}")
                    continue
            
            print(f"\n{'='*70}")
            print(f"✅ Scan Complete!")
            print(f"📊 Raw signals: {len(swing_signals)} SWING, {len(positional_signals)} POSITIONAL")
            
            # Apply Strategy 2's STRICTER filters
            # Swing: score >= 8.3, ADX >= 32
            # Positional: score >= 7.5, ADX >= 27
            swing_signals = [s for s in swing_signals if s['signal_score'] >= settings.MIN_SWING_SIGNAL_SCORE 
                           and s.get('_technical_details', {}).get('indicators', {}).get('adx', 0) >= settings.ADX_MIN_TREND]
            positional_signals = [s for s in positional_signals if s['signal_score'] >= settings.MIN_SIGNAL_SCORE
                                and s.get('_technical_details', {}).get('indicators', {}).get('adx', 0) >= settings.ADX_STRONG_TREND]
            
            print(f"🎯 After Strategy 2 filters: {len(swing_signals)} SWING (≥{settings.MIN_SWING_SIGNAL_SCORE} score, ≥{settings.ADX_MIN_TREND} ADX)")
            print(f"                             {len(positional_signals)} POSITIONAL (≥{settings.MIN_SIGNAL_SCORE} score, ≥{settings.ADX_STRONG_TREND} ADX)")
            
            # Sort by score and take only the best
            swing_signals.sort(key=lambda x: x['signal_score'], reverse=True)
            positional_signals.sort(key=lambda x: x['signal_score'], reverse=True)
            
            # Limit to max signals per scan
            swing_signals = swing_signals[:settings.MAX_SWING_SIGNALS_PER_SCAN]
            positional_signals = positional_signals[:settings.MAX_POSITIONAL_SIGNALS_PER_SCAN]
            
            print(f"📋 Final selection: {len(swing_signals)} SWING (top-rated), {len(positional_signals)} POSITIONAL (top-rated)")
            
            # Execute signals
            self.execute_signals(swing_signals, positional_signals)
            
        except Exception as e:
            print(f"❌ Scan error: {e}")
    def execute_signals(self, swing_signals, positional_signals):
        """Execute trading signals"""
        
        # Execute swing signals
        for signal in swing_signals:
            try:
                result = self.portfolio.execute_swing_signal(signal)
                if result:
                    print(f"✅ SWING: {signal['symbol']} @ ₹{signal['entry_price']:.2f} (Score: {signal['signal_score']:.1f})")
                    
                    # Send Discord alert for Strategy 2
                    if self.discord and self.discord.enabled:
                        # Mark as Strategy 2
                        signal['trade_type'] = '🎯 STRATEGY 2 - SWING TRADE'
                        signal['strategy_name'] = 'Strategy 2 (Stricter)'
                        self.discord.send_buy_signal(signal, paper_trade=True)
            except Exception as e:
                print(f"❌ Failed to execute SWING {signal['symbol']}: {e}")
        
        # Execute positional signals
        for signal in positional_signals:
            try:
                result = self.portfolio.execute_positional_signal(signal)
                if result:
                    print(f"✅ POSITIONAL: {signal['symbol']} @ ₹{signal['entry_price']:.2f} (Score: {signal['signal_score']:.1f})")
                    
                    # Send Discord alert for Strategy 2
                    if self.discord and self.discord.enabled:
                        # Mark as Strategy 2
                        signal['trade_type'] = '🎯 STRATEGY 2 - POSITIONAL TRADE'
                        signal['strategy_name'] = 'Strategy 2 (Stricter)'
                        self.discord.send_buy_signal(signal, paper_trade=True)
            except Exception as e:
                print(f"❌ Failed to execute POSITIONAL {signal['symbol']}: {e}")
                print(f"❌ Failed to execute POSITIONAL {signal['symbol']}: {e}")
    
    def monitor_positions(self):
        """Monitor open positions and check for exits"""
        try:
            # Get all open positions
            swing_stats = self.portfolio.get_swing_portfolio_stats()
            pos_stats = self.portfolio.get_positional_portfolio_stats()
            
            swing_positions = swing_stats.get('open_positions', 0)
            positional_positions = pos_stats.get('open_positions', 0)
            
            if swing_positions == 0 and positional_positions == 0:
                return
            
            print(f"\n👁️ Monitoring Positions:")
            print(f"   🔥 Swing: {swing_positions}")
            print(f"   📈 Positional: {positional_positions}")
            
            # Monitor swing positions - returns list of exit_info dicts
            swing_exits = self.portfolio.monitor_and_update_swing_positions()
            
            # Send Discord alerts for swing exits
            if swing_exits and self.discord and self.discord.enabled:
                for exit_info in swing_exits:
                    print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']})")
                    # Mark as Strategy 2
                    exit_info['strategy_name'] = 'Strategy 2 (Stricter)'
                    exit_info['trade_type'] = '🎯 STRATEGY 2 - SWING TRADE'
                    self.discord.send_exit_alert(exit_info, paper_trade=True, strategy='swing')
            
            # Monitor positional positions - returns list of exit_info dicts
            positional_exits = self.portfolio.monitor_and_update_positional_positions()
            
            # Send Discord alerts for positional exits
            if positional_exits and self.discord and self.discord.enabled:
                for exit_info in positional_exits:
                    print(f"   🚪 {exit_info['symbol']}: ₹{exit_info['pnl']:+,.0f} ({exit_info['reason']})")
                    # Mark as Strategy 2
                    exit_info['strategy_name'] = 'Strategy 2 (Stricter)'
                    exit_info['trade_type'] = '🎯 STRATEGY 2 - POSITIONAL TRADE'
                    self.discord.send_exit_alert(exit_info, paper_trade=True, strategy='positional')
                    
        except Exception as e:
            print(f"❌ Position monitoring error: {e}")
    
    def display_status(self):
        """Display current system status"""
        now = datetime.now(self.timezone)
        
        print(f"\n💤 Market CLOSED - System Active")
        print(f"⏰ {now.strftime('%d %b %Y, %I:%M %p IST')}")
        print(f"📊 Loaded: {len(self.stocks)} stocks")
        print(f"🔄 Next market open: 9:15 AM IST")
        print(f"💓 Heartbeat: System running normally...")
    
    def run(self):
        """Main system loop - runs AFTER Strategy 1 completes"""
        print("\n🚀 Starting Strategy 2 Trading System...")
        print("⏳ Waits for Strategy 1 scan → Then runs Strategy 2 scan")
        print("✅ ZERO API conflicts - Sequential execution")
        
        last_scan_time = None
        last_monitor_minute = -1
        signal_file = 'data/.strategy1_complete'
        
        while True:
            try:
                now = datetime.now(self.timezone)
                
                if self.is_market_open():
                    # Check for Strategy 1 completion signal (file-based trigger)
                    if os.path.exists(signal_file):
                        # Check if we haven't scanned in last 5 minutes (avoid duplicate scans)
                        if last_scan_time is None or (now - last_scan_time).seconds >= 300:
                            print(f"\n✅ Strategy 1 signal detected! Starting Strategy 2 scan...")
                            
                            # Remove signal file immediately to avoid re-triggering
                            try:
                                os.remove(signal_file)
                            except:
                                pass
                            
                            # Run Strategy 2 scan
                            self.scan_and_generate_signals()
                            last_scan_time = now
                        else:
                            # Signal file exists but we just scanned - remove it
                            try:
                                os.remove(signal_file)
                            except:
                                pass
                    
                    # Monitor positions every 5 minutes
                    current_minute = now.minute
                    if current_minute % settings.POSITION_MONITOR_INTERVAL == 0 and current_minute != last_monitor_minute:
                        self.monitor_positions()
                        last_monitor_minute = current_minute
                else:
                    # Market closed - just show status every 5 minutes
                    current_minute = now.minute
                    if current_minute % 5 == 0 and current_minute != last_monitor_minute:
                        self.display_status()
                        last_monitor_minute = current_minute
                
                time.sleep(10)  # Check every 10 seconds (faster response to signal file)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Strategy 2 shutting down...")
                break
            except Exception as e:
                print(f"\n❌ System error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    system = Strategy2TradingSystem()
    system.run()
