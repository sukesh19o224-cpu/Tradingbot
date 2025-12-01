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
from src.strategies.signal_generator import SignalGenerator
from src.paper_trading.dual_portfolio_strategy2 import DualPortfolioStrategy2
from src.alerts.discord_alerts import DiscordAlerts

class Strategy2TradingSystem:
    """Strategy 2: 50/50 Stricter Trading System (Above Strategy 1 strictness)"""
    
    def __init__(self):
        self.stock_fetcher = NSEStockFetcher()
        self.signal_generator = SignalGenerator()
        self.portfolio = DualPortfolioStrategy2(
            swing_file='data/strategy2_swing_portfolio.json',
            positional_file='data/strategy2_positional_portfolio.json',
            initial_capital=settings.INITIAL_CAPITAL
        )
        self.discord = None  # No Discord alerts for Strategy 2
        self.timezone = pytz.timezone(settings.TIMEZONE)
        
        print("="*70)
        print("🎯 STRATEGY 2 - STRICTER TRADING SYSTEM")
        print("="*70)
        print(f"📊 50% Swing (≥8.3 score) + 50% Positional (≥7.5 score)")
        print(f"💰 Capital: ₹{settings.INITIAL_CAPITAL:,}")
        print(f"📈 Max Positions: {settings.MAX_POSITIONS} per portfolio")
        print(f"🎯 Higher quality than Strategy 1")
        print(f"📱 Discord: ❌ | Dashboard: Port {settings.DASHBOARD_PORT}")
        print("="*70)
    
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
            # Get stock list
            stocks = self.stock_fetcher.get_stocks()
            print(f"📊 Scanning {len(stocks)} stocks...")
            
            swing_signals = []
            positional_signals = []
            
            for i, symbol in enumerate(stocks, 1):
                try:
                    print(f"[{i}/{len(stocks)}] Analyzing {symbol}...", end='\r')
                    
                    # Generate signal
                    signal = self.signal_generator.generate_signal(symbol)
                    
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
            print(f"📊 Found {len(swing_signals)} SWING signals, {len(positional_signals)} POSITIONAL signals")
            
            # Sort by score and take only the best
            swing_signals.sort(key=lambda x: x['signal_score'], reverse=True)
            positional_signals.sort(key=lambda x: x['signal_score'], reverse=True)
            
            # Limit to max signals per scan
            swing_signals = swing_signals[:settings.MAX_SWING_SIGNALS_PER_SCAN]
            positional_signals = positional_signals[:settings.MAX_POSITIONAL_SIGNALS_PER_SCAN]
            
            print(f"🎯 Selected: {len(swing_signals)} SWING (top-rated), {len(positional_signals)} POSITIONAL (top-rated)")
            
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
            except Exception as e:
                print(f"❌ Failed to execute SWING {signal['symbol']}: {e}")
        
        # Execute positional signals
        for signal in positional_signals:
            try:
                result = self.portfolio.execute_positional_signal(signal)
                if result:
                    print(f"✅ POSITIONAL: {signal['symbol']} @ ₹{signal['entry_price']:.2f} (Score: {signal['signal_score']:.1f})")
            except Exception as e:
                print(f"❌ Failed to execute POSITIONAL {signal['symbol']}: {e}")
    
    def monitor_positions(self):
        """Monitor and manage open positions"""
        try:
            swing_updated = self.portfolio.monitor_and_update_swing_positions()
            positional_updated = self.portfolio.monitor_and_update_positional_positions()
            
            if swing_updated or positional_updated:
                print(f"✅ Positions monitored at {datetime.now(self.timezone).strftime('%I:%M %p')}")
        except Exception as e:
            print(f"❌ Position monitoring error: {e}")
    
    def display_status(self):
        """Display current system status"""
        now = datetime.now(self.timezone)
        market_status = "OPEN 🟢" if self.is_market_open() else "CLOSED 🔴"
        
        print("\n" + "="*70)
        print(f"💓 STRATEGY 2 - System Status")
        print("="*70)
        print(f"⏰ {now.strftime('%d %b %Y, %I:%M %p IST')}")
        print(f"📊 Market: {market_status}")
        
        # Get portfolio stats
        swing_stats = self.portfolio.get_swing_portfolio_stats()
        pos_stats = self.portfolio.get_positional_portfolio_stats()
        
        # Calculate used capital
        swing_used = 50000 - swing_stats.get('capital', 50000)
        pos_used = 50000 - pos_stats.get('capital', 50000)
        
        # Calculate total P&L
        swing_pnl = swing_stats.get('realized_pnl', 0) + swing_stats.get('unrealized_pnl', 0)
        pos_pnl = pos_stats.get('realized_pnl', 0) + pos_stats.get('unrealized_pnl', 0)
        swing_pnl_pct = (swing_pnl / 50000 * 100) if swing_used > 0 else 0
        pos_pnl_pct = (pos_pnl / 50000 * 100) if pos_used > 0 else 0
        
        print(f"\n💼 SWING Portfolio: {swing_stats.get('open_positions', 0)}/5 positions")
        print(f"   Capital: ₹{swing_used:,.0f} / ₹50,000")
        print(f"   P&L: ₹{swing_pnl:,.0f} ({swing_pnl_pct:.2f}%)")
        
        print(f"\n💼 POSITIONAL Portfolio: {pos_stats.get('open_positions', 0)}/5 positions")
        print(f"   Capital: ₹{pos_used:,.0f} / ₹50,000")
        print(f"   P&L: ₹{pos_pnl:,.0f} ({pos_pnl_pct:.2f}%)")
        
        total_pnl = swing_pnl + pos_pnl
        print(f"\n💰 TOTAL P&L: ₹{total_pnl:,.0f}")
        print("="*70)
    
    def run(self):
        """Main system loop - runs AFTER Strategy 1 completes"""
        print("\n🚀 Starting Strategy 2 Trading System...")
        print("⏳ Waits for Strategy 1 scan → Then runs Strategy 2 scan")
        print("✅ ZERO API conflicts - Sequential execution")
        
        # Clean up any old signal file on startup
        if os.path.exists('data/.strategy1_complete'):
            print("🧹 Cleaning up old signal file...")
            os.remove('data/.strategy1_complete')
        
        last_scan_minute = -1
        last_monitor_minute = -1
        
        while True:
            try:
                now = datetime.now(self.timezone)
                current_minute = now.minute
                
                if self.is_market_open():
                    # Scan every 10 minutes (waits for Strategy 1 to complete)
                    if current_minute % settings.SCAN_INTERVAL_MINUTES == 0 and current_minute != last_scan_minute:
                        # Wait for Strategy 1 to complete and signal
                        print(f"\n⏳ Waiting for Strategy 1 to complete scan...")
                        max_wait = 300  # Max 5 minutes
                        wait_time = 0
                        while not os.path.exists('data/.strategy1_complete') and wait_time < max_wait:
                            time.sleep(5)
                            wait_time += 5
                            if wait_time % 30 == 0:
                                print(f"   Still waiting... ({wait_time}s)")
                        
                        if os.path.exists('data/.strategy1_complete'):
                            # Double-check market is still open before scanning
                            if self.is_market_open():
                                print(f"✅ Strategy 1 complete! Starting Strategy 2 scan...")
                                self.scan_and_generate_signals()
                                last_scan_minute = current_minute
                            else:
                                print(f"⚠️  Market closed while waiting. Skipping scan.")
                                os.remove('data/.strategy1_complete')  # Clean up signal file
                        else:
                            print(f"⚠️  Timeout waiting for Strategy 1. Skipping this cycle.")
                    
                    # Monitor positions every 5 minutes
                    if current_minute % settings.POSITION_MONITOR_INTERVAL == 0 and current_minute != last_monitor_minute:
                        self.monitor_positions()
                        last_monitor_minute = current_minute
                else:
                    # Market closed - just show status every 5 minutes
                    if current_minute % 5 == 0 and current_minute != last_monitor_minute:
                        self.display_status()
                        last_monitor_minute = current_minute
                
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                print("\n\n🛑 Strategy 2 shutting down...")
                break
            except Exception as e:
                print(f"\n❌ System error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    system = Strategy2TradingSystem()
    system.run()
