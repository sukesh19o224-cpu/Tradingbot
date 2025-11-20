#!/usr/bin/env python3
"""
🚀 MULTI-STRATEGY TRADING SYSTEM V4.0
Target: 8-12% Monthly Returns (All Market Conditions)
Strategies: Momentum + Mean Reversion + Breakout

COMPLETE SYSTEM:
- Auto regime detection
- 3 strategies running in parallel
- Smart capital allocation
- All V3.0 features preserved
"""

import sys, os, time, schedule
from datetime import datetime, timedelta
import pandas as pd
import pytz

# Force IST timezone (Indian Standard Time)
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

# Initialize data caching (speeds up scans)
try:
    from src.data_collector.data_cache import get_cache
    CACHE_ENABLED = True
    print("✅ Data caching enabled")
except:
    CACHE_ENABLED = False
    print("⚠️ Data caching not available")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import *

# Core V4.0 components
from src.core.multi_strategy_manager import MultiStrategyManager
from src.portfolio_manager.portfolio_manager import PortfolioManager
from src.risk_guardian.risk_manager import RiskManager
from src.analyzers.sector_tracker import SectorTracker
from src.analyzers.correlation_checker import CorrelationChecker

# NEW: Dynamic Capital Allocator
try:
    from src.core.dynamic_capital_allocator import DynamicCapitalAllocator
    DYNAMIC_ALLOCATOR_AVAILABLE = True
    print("✅ Dynamic capital allocator enabled")
except ImportError:
    DYNAMIC_ALLOCATOR_AVAILABLE = False
    print("⚠️ Dynamic allocator not available")

# NEW: EOD Manager for watchlist handling
try:
    from src.data_collector.eod_manager import EODManager
    EOD_MANAGER_AVAILABLE = True
except ImportError:
    EOD_MANAGER_AVAILABLE = False
    print("⚠️ EOD Manager not available")

# V3.0 components
try:
    from src.alert_dispatcher.discord_alerts import DiscordAlerts
    ALERTER_AVAILABLE = True
except ImportError:
    ALERTER_AVAILABLE = False
    print("⚠️ Discord alerts not available")

try:
    from src.scanners.morning_checker import MorningChecker
    MORNING_AVAILABLE = True
except ImportError:
    MORNING_AVAILABLE = False

try:
    from src.scanners.intraday_scanner import IntradayScanner
    INTRADAY_AVAILABLE = True
except ImportError:
    INTRADAY_AVAILABLE = False

try:
    from src.data_collector.full_nse_scanner import FullNSEScanner
    FULL_SCANNER_AVAILABLE = True
except ImportError:
    FULL_SCANNER_AVAILABLE = False


class MultiStrategyTradingSystem:
    """
    V4.0 - Multi-Strategy System
    All V3.0 features + regime detection + 3 strategies
    """
    
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 MULTI-STRATEGY TRADING SYSTEM V4.0")
        print("="*70)
        
        # V4.0 CORE: Multi-Strategy Manager
        self.multi_strategy_manager = MultiStrategyManager()
        
        # V3.0 Components
        self.portfolio_manager = PortfolioManager()
        self.risk_manager = RiskManager(INITIAL_CAPITAL)
        self.sector_tracker = SectorTracker()
        self.correlation_checker = CorrelationChecker()
        
        # NEW: Dynamic Capital Allocator
        if DYNAMIC_ALLOCATOR_AVAILABLE and ENABLE_DYNAMIC_ALLOCATION:
            self.dynamic_allocator = DynamicCapitalAllocator(self.portfolio_manager)
            print("🔄 Dynamic capital allocation: ENABLED")
        else:
            self.dynamic_allocator = None
            print("📊 Static capital allocation: ENABLED")
        
        # Alerter
        if ALERTER_AVAILABLE:
            self.alerter = DiscordAlerts()
        else:
            self.alerter = None
        
        # NEW: EOD Manager
        if EOD_MANAGER_AVAILABLE:
            self.eod_manager = EODManager()
        else:
            self.eod_manager = None
        
        # V3.0 Scanners
        if MORNING_AVAILABLE:
            self.morning_checker = MorningChecker(self.multi_strategy_manager, self.alerter)
        else:
            self.morning_checker = None
        
        if INTRADAY_AVAILABLE:
            # Note: Intraday scanner needs the multi-strategy manager
            self.intraday_scanner = IntradayScanner(self.multi_strategy_manager, self.alerter)
        else:
            self.intraday_scanner = None
        
        if FULL_SCANNER_AVAILABLE:
            self.market_scanner = FullNSEScanner()
        else:
            self.market_scanner = None
        
        # State
        self.watchlist = []
        self.yesterday_watchlist = []
        self.daily_trades = 0
        self.auto_mode_running = False
        
        print("\n✅ All systems ready!")
        print(f"💰 Capital: ₹{INITIAL_CAPITAL:,.0f}")
        print(f"🎯 Target: 8-12% monthly (multi-strategy)")
        print(f"⚠️ Risk/Trade: {MAX_RISK_PER_TRADE*100:.1f}%")
        print(f"🎯 Max Positions: {MAX_POSITIONS}")
        print(f"\n🎯 ACTIVE STRATEGIES:")
        for name, config in STRATEGIES.items():
            if config['enabled']:
                print(f"   ✅ {name}: {config['capital_allocation']*100:.0f}% allocation")
        print("="*70)
    
    def run_eod_scan(self):
        """
        EOD scan - V4.0 UPDATED
        Runs full NSE scan and processes 3-tier watchlist
        """
        print(f"\n{'='*70}")
        print(f"🌙 EOD SCAN V4.0 - {get_ist_now().strftime('%Y-%m-%d %H:%M')} IST")
        print(f"{'='*70}")
        
        try:
            # Step 1: Run your existing full NSE scanner
            if self.market_scanner:
                print("\n📊 Running Full NSE Scan...")
                self.market_scanner.run_end_of_day_screening()
                print("\n✅ EOD Screening Complete")
            else:
                print("\n⚠️ Full scanner not available")
            
            # Step 2: Process results with EOD Manager
            if self.eod_manager:
                print("\n📊 Processing watchlist files...")
                success = self.eod_manager.process_eod_results()
                
                if success:
                    print("\n✅ All files created successfully!")
                else:
                    print("\n⚠️ Some files missing - using fallback")
            else:
                print("\n⚠️ EOD Manager not available")
                
                # Fallback: Load from combined file if exists
                if os.path.exists('data/daily_watchlist.csv'):
                    df = pd.read_csv('data/daily_watchlist.csv')
                    symbols = df['symbol'].tolist()
                    self.yesterday_watchlist = [{'symbol': s, 'score': 50} for s in symbols[:TOP_STOCKS]]
                    print(f"✅ Loaded {len(self.yesterday_watchlist)} from daily_watchlist.csv")
                    
                    # Save for morning
                    import json
                    os.makedirs('data', exist_ok=True)
                    with open('data/yesterday_watchlist.json', 'w') as f:
                        json.dump(self.yesterday_watchlist, f)
        
        except Exception as e:
            print(f"\n❌ EOD Scan Failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_strategy_limits(self, dynamic_limits):
        """Update strategy position limits dynamically"""
        for strategy_name, limits in dynamic_limits.items():
            if strategy_name in self.multi_strategy_manager.strategies:
                strategy = self.multi_strategy_manager.strategies[strategy_name]
                # Update max positions
                if hasattr(strategy, 'config'):
                    strategy.config['max_positions'] = limits['max_positions']
    
    def run_multi_strategy_scan(self):
        """
        V4.0 NEW: Multi-strategy scan with dynamic allocation
        """
        print(f"\n{'='*70}")
        print(f"🎯 MULTI-STRATEGY SCAN - {get_ist_now().strftime('%Y-%m-%d %H:%M')} IST")
        print(f"{'='*70}")
        
        # Get stock list
        stock_list = self._get_stock_list()
        
        if not stock_list:
            print("❌ No stock list available")
            return
        
        # Recalculate capital to get latest values
        self.portfolio_manager._recalculate_capital()
        
        # Check if dynamic allocation active
        if self.dynamic_allocator:
            # Get current regime
            current_regime = self.multi_strategy_manager.current_regime if hasattr(self.multi_strategy_manager, 'current_regime') else 'RANGING'
            
            # Get dynamic limits
            dynamic_limits = self.dynamic_allocator.get_dynamic_allocation(current_regime)
            
            print(f"\n🔄 DYNAMIC ALLOCATION FOR {current_regime}:")
            for strategy, limits in dynamic_limits.items():
                print(f"   {strategy}: Max {limits['max_positions']} positions, {limits['capital_pct']*100:.0f}% capital")
            
            # Update strategy limits dynamically
            self._update_strategy_limits(dynamic_limits)
        
        # V4.0: Run multi-strategy scan
        all_opportunities = self.multi_strategy_manager.scan_all_strategies(
            stock_list,
            self.portfolio_manager.available_capital
        )
        
        # Filter through sector, correlation, etc.
        filtered_opportunities = self._apply_filters(all_opportunities)
        
        # Get combined top opportunities
        top_opportunities = self.multi_strategy_manager.get_combined_opportunities(
            filtered_opportunities,
            max_positions=MAX_ENTRIES_PER_DAY
        )
        
        if not top_opportunities:
            print("\n⚠️ No opportunities after filtering")
            print(f"   💡 Scanned strategies: {', '.join(all_opportunities.keys())}")
            print(f"   📊 Total candidates before filtering: {sum(len(v) for v in all_opportunities.values())}")
            return
        
        print(f"\n✅ Found {len(top_opportunities)} actionable opportunities")
        
        # Display
        self._display_opportunities(top_opportunities)
        
        # Enter positions
        self._enter_positions(top_opportunities)
    
    def _get_stock_list(self):
        """Get stock list for scanning"""
        # Try to load daily watchlist
        if os.path.exists('data/daily_watchlist.csv'):
            df = pd.read_csv('data/daily_watchlist.csv')
            symbols = df['symbol'].tolist()
            return [f"{s}.NS" for s in symbols]
        
        # Fallback
        fallback = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 
                   'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'AXISBANK']
        return [f"{s}.NS" for s in fallback]
    
    def _apply_filters(self, all_opportunities):
        """
        Apply sector, correlation, and other filters
        """
        filtered = {}
        
        # CRITICAL: Recalculate capital to get fresh position data
        self.portfolio_manager._recalculate_capital()
        
        # Get FRESH open positions after recalculation
        open_positions = self.portfolio_manager.get_open_positions()
        total_capital = self.portfolio_manager.capital
        
        print(f"\n🔍 FILTERING CANDIDATES:")
        print(f"   📊 Current open positions: {len(open_positions)}")
        rejection_reasons = {}
        
        for strategy_name, opportunities in all_opportunities.items():
            filtered_list = []
            
            for opp in opportunities:
                symbol = opp['symbol']
                
                # Check if already trading this symbol
                if symbol in open_positions:
                    print(f"   ⚪ {symbol}: Already have position")
                    continue
                
                # Sector check (if enabled)
                if ENABLE_SECTOR_CHECK:
                    sector_ok, sector_reason = self.sector_tracker.check_sector_limit(
                        symbol, open_positions, total_capital
                    )
                    if not sector_ok:
                        rejection_reasons[symbol] = f"Sector: {sector_reason}"
                        print(f"   ❌ {symbol}: {sector_reason}")
                        continue
                
                # Correlation check (if enabled)
                if ENABLE_CORRELATION_CHECK:
                    corr_ok, corr_reason, _ = self.correlation_checker.check_correlation_limit(
                        symbol, open_positions
                    )
                    if not corr_ok:
                        rejection_reasons[symbol] = f"Correlation: {corr_reason}"
                        print(f"   ❌ {symbol}: {corr_reason}")
                        continue
                
                print(f"   ✅ {symbol}: Passed all filters")
                filtered_list.append(opp)
            
            filtered[strategy_name] = filtered_list
        
        return filtered
    
    def _display_opportunities(self, opportunities):
        """Display opportunities"""
        print(f"\n{'='*60}")
        print("🎯 TOP OPPORTUNITIES (MULTI-STRATEGY)")
        print(f"{'='*60}")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n{i}. {opp['symbol']} ({opp['strategy']})")
            print(f"   Score: {opp['score']}")
            print(f"   Entry: ₹{opp['entry_price']:.2f}")
            print(f"   Shares: {opp['shares']}")
            print(f"   Stop: ₹{opp['stop_loss']:.2f}")
            print(f"   Targets: ₹{opp['target1']:.2f}/₹{opp['target2']:.2f}/₹{opp['target3']:.2f}")
            print(f"   Value: ₹{opp['position_value']:,.0f}")
    
    def _enter_positions(self, opportunities):
        """Enter positions with dynamic reallocation"""
        # Check if we need to reallocate capital
        if self.dynamic_allocator and opportunities:
            total_needed = sum(opp['position_value'] for opp in opportunities)
            available = self.portfolio_manager.available_capital
            
            if total_needed > available:
                # Get current regime
                current_regime = self.multi_strategy_manager.current_regime if hasattr(self.multi_strategy_manager, 'current_regime') else 'RANGING'
                
                # Get primary strategy needing capital
                primary_strategy = opportunities[0]['strategy']
                
                # Attempt reallocation
                freed = self.dynamic_allocator.check_and_reallocate(
                    current_regime,
                    total_needed - available,
                    primary_strategy
                )
                
                if freed > 0:
                    print(f"✅ Freed ₹{freed:,.0f} through smart reallocation")
                    # Recalculate after reallocation
                    self.portfolio_manager._recalculate_capital()
        
        # Now enter positions
        for opp in opportunities:
            # Check if allowed
            allowed, _ = self.risk_manager.check_trade_allowed(opp['strategy'])
            if not allowed:
                continue
            
            # Add to portfolio
            success = self.portfolio_manager.add_position(
                symbol=opp['symbol'],
                entry_price=opp['entry_price'],
                shares=opp['shares'],
                stop_loss=opp['stop_loss'],
                target1=opp['target1'],
                target2=opp['target2'],
                strategy=opp['strategy'],
                target3=opp.get('target3', opp['target2'] * 1.5)
            )
            
            if success:
                # Add to risk manager
                self.risk_manager.add_position(
                    opp['symbol'],
                    opp['entry_price'],
                    opp['shares'],
                    opp['stop_loss'],
                    strategy=opp['strategy']
                )
                
                # Send alert (add current_price for alert compatibility)
                if self.alerter:
                    alert_data = opp.copy()
                    alert_data['current_price'] = opp['entry_price']  # For alert compatibility
                    try:
                        self.alerter.send_buy_alert(alert_data)
                    except Exception as e:
                        print(f"   ⚠️ BUY alert failed: {e}")
                
                time.sleep(1)
    
    def run_position_monitoring(self):
        """
        Monitor and update positions
        V4.0 UPDATED: Use multi-strategy manager for exits
        """
        if not self.check_market_open():
            return
        
        print(f"\n{'='*70}")
        print(f"📊 POSITION MONITORING - {get_ist_now().strftime('%H:%M')} IST")
        print(f"{'='*70}")
        
        open_positions = self.portfolio_manager.get_open_positions()
        print(f"📊 Monitoring {len(open_positions)} open positions...")
        
        if not open_positions:
            print("   ⚪ No positions to monitor")
            return
        
        # Update positions with multi-strategy exit logic
        exit_alerts = self.portfolio_manager.update_positions_from_live_data(
            self.multi_strategy_manager
        )
        
        # Process exits
        for alert in exit_alerts:
            pnl = alert.get('profit_loss', 0)
            symbol = alert.get('symbol', '')
            strategy = alert.get('strategy', 'MOMENTUM')
            
            self.risk_manager.record_trade_outcome(symbol, pnl, strategy)
            
            if self.alerter:
                self.alerter.send_exit_alert(alert)
            
            time.sleep(1)
        
        # Update risk manager capital
        self.risk_manager.update_capital(self.portfolio_manager.capital)
    
    def check_market_open(self):
        """Check if market is open - USING IST"""
        now = get_ist_now()
        if now.weekday() > 4:
            return False
        
        market_open = datetime.strptime(MARKET_OPEN, "%H:%M").time()
        market_close = datetime.strptime(MARKET_CLOSE, "%H:%M").time()
        
        return market_open <= now.time() <= market_close
    
    def run_morning_check(self):
        """V3.0: Morning verification"""
        if not self.morning_checker or not ENABLE_MORNING_CHECK:
            return []
        
        try:
            import json
            if os.path.exists('data/yesterday_watchlist.json'):
                with open('data/yesterday_watchlist.json', 'r') as f:
                    watchlist = json.load(f)
            else:
                watchlist = self.yesterday_watchlist
        except:
            watchlist = self.yesterday_watchlist
        
        if not watchlist:
            print("⚠️ No watchlist - Run EOD scan first or system will use fallback stocks")
            # Use fallback watchlist
            fallback = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
            watchlist = [{'symbol': s, 'score': 50} for s in fallback]
        
        current_time = get_ist_now().strftime("%H:%M")
        return self.morning_checker.run_morning_check(watchlist, current_time)
    
    def run_full_auto_mode(self):
        """
        V4.0: Full automation with multi-strategy
        """
        print("\n🚀 FULL AUTO MODE V4.0 - MULTI-STRATEGY")
        print("  ✅ Regime detection")
        print("  ✅ 3 strategies active")
        print("  ✅ Morning check at 9:15 & 9:45")
        print("  ✅ Live scanning")
        print("  ✅ Position monitoring")
        print("  ✅ EOD scan at 3:45 PM")
        print("Press Ctrl+C to stop\n")
        
        self.auto_mode_running = True
        last_morning = last_scan = last_monitor = last_eod = None
        last_heartbeat = None
        
        try:
            while self.auto_mode_running:
                now = get_ist_now()  # Use IST time
                current_time = now.strftime("%H:%M")
                
                # Heartbeat (every 5 min to show it's alive)
                if (now.minute % 5) == 0 and last_heartbeat != current_time:
                    print(f"💓 {current_time} IST - System running... (Market: {'OPEN' if self.check_market_open() else 'CLOSED'})")
                    last_heartbeat = current_time
                
                # Morning check
                if current_time in MORNING_CHECK_TIMES and last_morning != current_time:
                    print(f"\n⏰ {current_time} - Morning check...")
                    self.run_morning_check()
                    last_morning = current_time
                
                # Live scanning (every 10 min during market) - UPDATED
                if self.check_market_open():
                    if (now.minute % 10) == 0 and last_scan != current_time:
                        print(f"\n⏰ {current_time} IST - Multi-strategy scan...")
                        self.run_multi_strategy_scan()
                        last_scan = current_time
                    
                    # Position monitoring (every 3 min) - UPDATED
                    if (now.minute % 3) == 0 and last_monitor != current_time:
                        print(f"\n⏰ {current_time} IST - Position monitoring...")
                        self.run_position_monitoring()
                        last_monitor = current_time
                
                # EOD scan
                if current_time == SCAN_TIME and last_eod != current_time:
                    print(f"\n⏰ {current_time} - EOD scan...")
                    self.run_eod_scan()
                    last_eod = current_time
                
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n⏹️ Full auto stopped")
            self.auto_mode_running = False
    
    def manual_menu(self):
        """Manual control menu"""
        while True:
            print("\n" + "="*70)
            print("🚀 MULTI-STRATEGY SYSTEM V4.0 - MANUAL CONTROL")
            print("="*70)
            
            print("\n--- Scanning ---")
            print("1. Run EOD Screening")
            print("2. Run Multi-Strategy Scan NOW")
            print("3. Display Regime Status")
            
            print("\n--- Portfolio ---")
            print("4. View Portfolio")
            print("5. View Strategy Performance")
            print("6. View Risk Status")
            print("7. Monitor Positions")
            
            print("\n--- Analysis ---")
            print("8. View Sector Allocation")
            print("9. View Correlation Status")
            
            print("\n--- Automation ---")
            print("10. Start FULL AUTO MODE")
            if MORNING_AVAILABLE:
                print("11. Run Morning Check NOW")
            
            print("\n--- System ---")
            print("12. Send Test Alert")
            print("13. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if not choice:
                continue  # Skip empty input
            
            if choice == "1":
                self.run_eod_scan()
            
            elif choice == "2":
                self.run_multi_strategy_scan()
            
            elif choice == "3":
                self.multi_strategy_manager.display_status()
                self.multi_strategy_manager.regime_detector.detect_regime()
            
            elif choice == "4":
                self.portfolio_manager.display_summary()
            
            elif choice == "5":
                self.portfolio_manager.display_strategy_stats()
            
            elif choice == "6":
                self.risk_manager.update_capital(self.portfolio_manager.capital)
                self.risk_manager.display_risk_status()
            
            elif choice == "7":
                self.run_position_monitoring()
            
            elif choice == "8":
                pos = self.portfolio_manager.get_open_positions()
                self.sector_tracker.display_sector_allocation(pos, self.portfolio_manager.capital)
            
            elif choice == "9":
                pos = self.portfolio_manager.get_open_positions()
                self.correlation_checker.display_correlation_status(pos)
            
            elif choice == "10":
                self.run_full_auto_mode()
            
            elif choice == "11" and MORNING_AVAILABLE:
                self.run_morning_check()
            
            elif choice == "12":
                if self.alerter:
                    self.alerter.send_test_alert()
                else:
                    print("❌ Alerter not available")
            
            elif choice == "13":
                print("\n👋 Goodbye!")
                break
            
            else:
                if choice:  # Only print if there was actual input
                    print("❌ Invalid option")
                time.sleep(0.1)  # Prevent rapid looping


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════╗
    ║  MULTI-STRATEGY TRADING SYSTEM V4.0           ║
    ║  Target: 8-12% Monthly Returns                ║
    ║                                               ║
    ║  🆕 V4.0 FEATURES:                            ║
    ║  🎯 Auto Regime Detection                     ║
    ║  🚀 3 Strategies (Momentum, Mean Rev, Break)  ║
    ║  💰 Smart Capital Allocation                  ║
    ║  📊 Per-Strategy Performance Tracking         ║
    ║                                               ║
    ║  ✅ ALL V3.0 FEATURES PRESERVED               ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    system = MultiStrategyTradingSystem()
    
    print("\n" + "="*70)
    print("📊 CURRENT STATUS")
    print("="*70)
    print(f"Market: {'✅ OPEN' if system.check_market_open() else '🔒 CLOSED'}")
    system.portfolio_manager.display_summary()
    system.multi_strategy_manager.display_status()
    
    system.manual_menu()