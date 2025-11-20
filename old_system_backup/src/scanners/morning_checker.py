"""
🌅 MORNING CHECKER V4.0 - FRESH SCANS
Now does FULL regime-based scan at morning, not just gap checks!
"""

import sys, os
from datetime import datetime
import yfinance as yf
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *


class MorningChecker:
    """
    V4.0 Morning Checker - Does FRESH scans
    
    OLD: Used yesterday's scores, just checked gaps
    NEW: Full regime detection + strategy scan + filters
    """
    
    def __init__(self, multi_strategy_manager=None, discord_alerts=None):
        self.multi_strategy_manager = multi_strategy_manager
        self.discord_alerts = discord_alerts
        self.sent_alerts = set()
        print("🌅 Morning Checker V4.0 initialized (FRESH SCANS)")
    
    def run_morning_check(self, watchlist, check_time="09:15"):
        """
        V4.0: Do FRESH regime-based scan
        
        Args:
            watchlist: Yesterday's watchlist (used as stock pool)
            check_time: "09:15" or "09:45"
        
        Returns:
            List of qualified opportunities with full strategy analysis
        """
        if not ENABLE_MORNING_CHECK:
            return []
        
        print(f"\n{'='*70}")
        print(f"🌅 MORNING CHECK V4.0 @ {check_time}")
        print(f"{'='*70}")
        
        # Skip 9:15 - too early for reliable data
        if check_time == "09:15":
            print("⏰ First check - Scanning watchlist for gaps...")
            return self._quick_gap_check(watchlist)
        
        # 9:45 - DO FRESH FULL SCAN
        if check_time == "09:45":
            print("⏰ Final check - Running FRESH regime-based scan...")
            return self._fresh_multi_strategy_scan(watchlist)
        
        return []
    
    def _quick_gap_check(self, watchlist):
        """
        9:15 AM - Quick gap filter only
        Just removes stocks with bad gaps
        """
        print(f"\n📊 Checking {len(watchlist)} stocks for gaps...")
        
        filtered = []
        
        for stock in watchlist:
            symbol = stock['symbol']
            
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                current_data = ticker.history(period='1d', interval='1m')
                
                if current_data.empty:
                    print(f"   ❌ {symbol}: No data")
                    continue
                
                current_price = current_data['Close'].iloc[-1]
                yesterday_close = stock.get('price', current_price)
                gap_percent = ((current_price - yesterday_close) / yesterday_close) * 100
                
                # Reject bad gaps
                if gap_percent > 3.0:
                    print(f"   ❌ {symbol}: Gap up {gap_percent:.1f}% (too high)")
                    continue
                
                if gap_percent < -3.0:
                    print(f"   ❌ {symbol}: Gap down {gap_percent:.1f}% (too low)")
                    continue
                
                # Passed gap check
                print(f"   ✅ {symbol}: Gap {gap_percent:+.1f}% (OK)")
                filtered.append(stock)
                
                time.sleep(0.3)
            
            except Exception as e:
                print(f"   ⚠️ {symbol}: Error - {e}")
                continue
        
        print(f"\n📊 Gap Filter: {len(filtered)}/{len(watchlist)} passed")
        print(f"⏰ Will do FRESH scan at 9:45 AM...")
        
        return []  # Don't enter yet, wait for 9:45
    
    def _fresh_multi_strategy_scan(self, watchlist):
        """
        9:45 AM - FRESH FULL SCAN with regime detection
        This is identical to intraday scans!
        """
        if not self.multi_strategy_manager:
            print("❌ Multi-strategy manager not available!")
            return []
        
        # Extract just symbols from watchlist
        stock_list = [f"{stock['symbol']}.NS" for stock in watchlist]
        
        print(f"\n📊 Running FRESH scan on {len(stock_list)} stocks...")
        print("   (This uses current regime + fresh data + multi-timeframe)")
        
        try:
            # Get available capital
            try:
                import json
                with open('data/portfolio.json', 'r') as f:
                    portfolio = json.load(f)
                    capital = portfolio.get('capital', INITIAL_CAPITAL)
                    invested = sum(pos['position_value'] for pos in portfolio.get('positions', {}).values())
                    available_capital = capital - invested
            except:
                available_capital = INITIAL_CAPITAL * 0.8  # Assume 80% available
            
            print(f"💰 Available capital: ₹{available_capital:,.0f}")
            
            # Run FRESH multi-strategy scan (same as intraday!)
            all_opportunities = self.multi_strategy_manager.scan_all_strategies(
                stock_list,
                available_capital
            )
            
            # Get top opportunities
            top_opportunities = self.multi_strategy_manager.get_combined_opportunities(
                all_opportunities,
                max_positions=5  # Morning: max 5 positions
            )
            
            if not top_opportunities:
                print("\n⚠️ No opportunities found in morning scan")
                return []
            
            print(f"\n✅ Found {len(top_opportunities)} opportunities!")
            
            # Display
            print(f"\n{'='*70}")
            print(f"🎯 MORNING OPPORTUNITIES")
            print(f"{'='*70}")
            
            for i, opp in enumerate(top_opportunities, 1):
                print(f"\n{i}. {opp['symbol']} ({opp['strategy']})")
                print(f"   Score: {opp['score']}")
                print(f"   Entry: ₹{opp['entry_price']:.2f}")
                print(f"   Shares: {opp['shares']}")
                print(f"   Stop: ₹{opp['stop_loss']:.2f}")
                print(f"   Targets: ₹{opp['target1']:.2f}/₹{opp['target2']:.2f}/₹{opp['target3']:.2f}")
                
                # Show MTF signal if available
                if 'mtf_signal' in opp:
                    print(f"   15-min: {opp['mtf_signal']} (confidence: {opp.get('mtf_confidence', 0)}%)")
            
            return top_opportunities
        
        except Exception as e:
            print(f"❌ Fresh scan failed: {e}")
            import traceback
            traceback.print_exc()
            return []


if __name__ == "__main__":
    # Test
    checker = MorningChecker()
    
    # Dummy watchlist
    test_watchlist = [
        {'symbol': 'RELIANCE', 'price': 2500, 'score': 80},
        {'symbol': 'TCS', 'price': 3400, 'score': 75},
        {'symbol': 'INFY', 'price': 1450, 'score': 70}
    ]
    
    print("\n📊 Testing Morning Checker V4.0...")
    
    # Test 9:15
    print("\n1️⃣ Testing 9:15 AM check...")
    result = checker.run_morning_check(test_watchlist, "09:15")
    
    print(f"\n✅ Test complete!")