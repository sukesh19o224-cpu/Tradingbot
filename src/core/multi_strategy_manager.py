"""
🎯 MULTI-STRATEGY MANAGER V4.0
The orchestrator that manages all 3 strategies
Auto-switches based on market regime
"""

import sys
import os
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *
from src.analyzers.regime_detector import RegimeDetector
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.breakout_strategy import BreakoutStrategy


class MultiStrategyManager:
    """
    Orchestrates multiple strategies based on market regime
    
    Flow:
    1. Detect market regime
    2. Activate appropriate strategies
    3. Allocate capital to each strategy
    4. Scan for opportunities
    5. Return combined opportunities
    """
    
    def __init__(self):
        print("\n" + "="*70)
        print("🎯 MULTI-STRATEGY MANAGER V4.0 INITIALIZING")
        print("="*70)
        
        # Initialize regime detector
        self.regime_detector = RegimeDetector()
        
        # Initialize all strategies
        self.strategies = {}
        
        if STRATEGIES['MOMENTUM']['enabled']:
            self.strategies['MOMENTUM'] = MomentumStrategy()
        
        if STRATEGIES['MEAN_REVERSION']['enabled']:
            self.strategies['MEAN_REVERSION'] = MeanReversionStrategy()
        
        if STRATEGIES['BREAKOUT']['enabled']:
            self.strategies['BREAKOUT'] = BreakoutStrategy()
        
        # State
        self.current_regime = None
        self.active_strategies = []
        self.capital_allocations = {}
        
        print(f"\n✅ Initialized {len(self.strategies)} strategies:")
        for name in self.strategies.keys():
            print(f"   - {name}")
        print("="*70)
    
    def scan_all_strategies(self, stock_list, total_capital, force_regime=None):
        """
        Main scanning method - runs all appropriate strategies
        
        Args:
            stock_list: List of symbols to scan
            total_capital: Total available capital
            force_regime: Optional - force specific regime (for testing)
        
        Returns:
            dict with opportunities per strategy
        """
        print(f"\n{'='*70}")
        print(f"🎯 MULTI-STRATEGY SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")
        
        # Step 1: Detect regime
        if force_regime:
            regime = force_regime
            confidence = 1.0
            print(f"\n🎯 FORCED REGIME: {regime}")
        else:
            regime, confidence, indicators = self.regime_detector.detect_regime()
        
        self.current_regime = regime
        
        # Step 2: Get active strategies for this regime
        self.active_strategies = self.regime_detector.get_active_strategies(regime)
        
        print(f"\n📊 ACTIVE STRATEGIES FOR {regime}:")
        for strat in self.active_strategies:
            print(f"   ✅ {strat}")
        
        # Step 3: Allocate capital
        self.capital_allocations = self._allocate_capital(total_capital)
        
        print(f"\n💰 CAPITAL ALLOCATION:")
        for strat, amount in self.capital_allocations.items():
            print(f"   {strat}: ₹{amount:,.0f} ({(amount/total_capital)*100:.0f}%)")
        
        # Step 4: Scan with each active strategy
        all_opportunities = {}
        
        for strategy_name in self.active_strategies:
            if strategy_name not in self.strategies:
                continue
            
            strategy = self.strategies[strategy_name]
            capital = self.capital_allocations.get(strategy_name, 0)
            
            if capital == 0:
                continue
            
            print(f"\n{'='*60}")
            opportunities = strategy.scan_opportunities(stock_list)
            
            # Calculate position params for each opportunity
            opportunities_with_params = []
            for opp in opportunities:
                params = strategy.calculate_position_params(opp, capital)
                if params:
                    # Merge opportunity with params
                    full_opp = {**opp, **params}
                    opportunities_with_params.append(full_opp)
            
            all_opportunities[strategy_name] = opportunities_with_params
        
        # Step 5: Display summary
        self._display_summary(all_opportunities)
        
        return all_opportunities
    
    def _allocate_capital(self, total_capital):
        """
        Allocate capital to active strategies
        """
        allocations = {}
        
        # If only one strategy active, give it all
        if len(self.active_strategies) == 1:
            allocations[self.active_strategies[0]] = total_capital
            return allocations
        
        # Multiple strategies - use configured allocations
        total_allocation_pct = 0
        
        for strategy_name in self.active_strategies:
            if strategy_name in STRATEGIES:
                pct = STRATEGIES[strategy_name]['capital_allocation']
                total_allocation_pct += pct
        
        # Normalize if needed
        if total_allocation_pct > 0:
            for strategy_name in self.active_strategies:
                if strategy_name in STRATEGIES:
                    pct = STRATEGIES[strategy_name]['capital_allocation']
                    normalized_pct = pct / total_allocation_pct
                    allocations[strategy_name] = total_capital * normalized_pct
        else:
            # Equal split if no config
            per_strategy = total_capital / len(self.active_strategies)
            for strategy_name in self.active_strategies:
                allocations[strategy_name] = per_strategy
        
        return allocations
    
    def _display_summary(self, all_opportunities):
        """Display summary of all opportunities"""
        print(f"\n{'='*70}")
        print("📊 MULTI-STRATEGY SCAN SUMMARY")
        print(f"{'='*70}")
        
        total_opportunities = 0
        
        for strategy_name, opportunities in all_opportunities.items():
            count = len(opportunities)
            total_opportunities += count
            
            print(f"\n{strategy_name}:")
            print(f"   Opportunities: {count}")
            
            if opportunities:
                # Show top 3
                print(f"   Top 3:")
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"      {i}. {opp['symbol']:10s} "
                          f"Score: {opp['score']:3.0f}  "
                          f"Entry: ₹{opp['entry_price']:.2f}  "
                          f"Shares: {opp['shares']}")
        
        print(f"\n{'='*70}")
        print(f"🎯 TOTAL OPPORTUNITIES: {total_opportunities}")
        print(f"{'='*70}")
    
    def get_combined_opportunities(self, all_opportunities, max_positions=None):
        """
        Combine and rank opportunities from all strategies
        
        Args:
            all_opportunities: Dict from scan_all_strategies
            max_positions: Max positions to return
        
        Returns:
            List of top opportunities across all strategies
        """
        if max_positions is None:
            max_positions = MAX_POSITIONS
        
        combined = []
        
        for strategy_name, opportunities in all_opportunities.items():
            # Limit per strategy
            strategy_max = STRATEGIES.get(strategy_name, {}).get('max_positions', 3)
            combined.extend(opportunities[:strategy_max])
        
        # Sort by score
        combined.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return combined[:max_positions]
    
    def get_strategy_for_symbol(self, symbol):
        """
        Determine which strategy to use for a symbol
        Returns: strategy object or None
        """
        # Check current regime
        if not self.current_regime or not self.active_strategies:
            # Default to momentum
            return self.strategies.get('MOMENTUM')
        
        # Return first active strategy
        # (In practice, you'd scan and see which strategy found it)
        for strategy_name in self.active_strategies:
            if strategy_name in self.strategies:
                return self.strategies[strategy_name]
        
        return None
    
    def update_position_stops(self, position, current_price):
        """
        Update trailing stops using appropriate strategy
        
        Args:
            position: Position dict with 'strategy' key
            current_price: Current market price
        
        Returns:
            new_stop_loss
        """
        strategy_name = position.get('strategy', 'MOMENTUM')
        
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            return strategy.update_trailing_stop(position, current_price)
        
        # Fallback
        return position.get('stop_loss', current_price * 0.93)
    
    def check_exit_conditions(self, position, current_price, days_held):
        """
        Check exit conditions using appropriate strategy
        
        Args:
            position: Position dict with 'strategy' key
            current_price: Current market price
            days_held: Days position has been held
        
        Returns:
            (should_exit, reason, exit_price)
        """
        strategy_name = position.get('strategy', 'MOMENTUM')
        
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            return strategy.check_exit_conditions(position, current_price, days_held)
        
        # Fallback
        return False, None, None
    
    def get_status_report(self):
        """
        Get current status of multi-strategy system
        """
        report = {
            'current_regime': self.current_regime,
            'active_strategies': self.active_strategies,
            'capital_allocations': self.capital_allocations,
            'strategies_enabled': list(self.strategies.keys())
        }
        return report
    
    def display_status(self):
        """Display current status"""
        print(f"\n{'='*70}")
        print("🎯 MULTI-STRATEGY STATUS")
        print(f"{'='*70}")
        
        print(f"\n📊 Current Regime: {self.current_regime or 'Not Detected'}")
        
        print(f"\n✅ Active Strategies: {len(self.active_strategies)}")
        for strat in self.active_strategies:
            capital = self.capital_allocations.get(strat, 0)
            print(f"   - {strat:15s} ₹{capital:,.0f}")
        
        print(f"\n🔧 All Enabled Strategies: {len(self.strategies)}")
        for name in self.strategies.keys():
            status = "ACTIVE" if name in self.active_strategies else "STANDBY"
            print(f"   - {name:15s} [{status}]")
        
        print(f"{'='*70}")


if __name__ == "__main__":
    print("\n🧪 Testing Multi-Strategy Manager\n")
    
    manager = MultiStrategyManager()
    
    # Test with sample stocks
    test_stocks = [
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS',
        'TATAMOTORS.NS', 'TITAN.NS', 'BHARTIARTL.NS'
    ]
    
    # Scan with 100k capital
    all_opps = manager.scan_all_strategies(test_stocks, 100000)
    
    # Get combined top opportunities
    top_opps = manager.get_combined_opportunities(all_opps, max_positions=5)
    
    print(f"\n🏆 TOP 5 COMBINED OPPORTUNITIES:")
    for i, opp in enumerate(top_opps, 1):
        print(f"\n{i}. {opp['symbol']} ({opp['strategy']})")
        print(f"   Score: {opp['score']}")
        print(f"   Entry: ₹{opp['entry_price']:.2f}")
        print(f"   Shares: {opp['shares']}")
        print(f"   Stop: ₹{opp['stop_loss']:.2f}")
        print(f"   Targets: ₹{opp['target1']:.2f}/₹{opp['target2']:.2f}/₹{opp['target3']:.2f}")
    
    # Display status
    manager.display_status()