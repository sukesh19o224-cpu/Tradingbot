"""
🔄 DYNAMIC CAPITAL REALLOCATION
Intelligently shifts capital between strategies based on regime changes
"""

from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *


class DynamicCapitalAllocator:
    """
    Manages capital reallocation when regime changes
    Exits weak positions to fund higher-priority strategies
    """
    
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        self.strategy_priority = {
            'TRENDING_UP': ['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION'],
            'STRONG_BULL': ['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION'],
            'RANGING': ['MEAN_REVERSION', 'BREAKOUT', 'MOMENTUM'],
            'CHOPPY': ['MEAN_REVERSION', 'MOMENTUM', 'BREAKOUT'],
            'CONSOLIDATION': ['BREAKOUT', 'MEAN_REVERSION', 'MOMENTUM'],
            'WEAK': ['MEAN_REVERSION', 'MOMENTUM', 'BREAKOUT']
        }
        
        # Configuration
        self.max_capital_utilization = 0.90  # Use 90% max
        self.reallocation_threshold = 0.15   # Reallocate if 15%+ capital needed
        self.min_profit_to_keep = 0.02       # Keep positions with 2%+ profit
        self.max_loss_to_exit = -0.02        # Exit if losing 2%+
        
        print("🔄 Dynamic Capital Allocator initialized")
    
    def check_and_reallocate(self, new_regime, required_capital, current_strategy):
        """
        Check if reallocation needed and execute
        
        Args:
            new_regime: New market regime detected
            required_capital: Capital needed for new opportunities
            current_strategy: Strategy needing capital
        
        Returns:
            freed_capital: Amount of capital freed up
        """
        print(f"\n{'='*70}")
        print(f"🔄 CAPITAL REALLOCATION CHECK")
        print(f"{'='*70}")
        print(f"New Regime: {new_regime}")
        print(f"Strategy Needing Capital: {current_strategy}")
        print(f"Capital Required: ₹{required_capital:,.0f}")
        
        # Get available capital
        available = self.portfolio_manager.available_capital
        print(f"Available Capital: ₹{available:,.0f}")
        
        # Check if we need to reallocate
        if available >= required_capital:
            print("✅ Sufficient capital available, no reallocation needed")
            return 0
        
        capital_shortage = required_capital - available
        
        if capital_shortage < (self.portfolio_manager.capital * self.reallocation_threshold):
            print(f"⚠️ Shortage (₹{capital_shortage:,.0f}) below threshold, keeping positions")
            return 0
        
        print(f"\n🎯 Need to free up: ₹{capital_shortage:,.0f}")
        
        # Get strategy priorities for this regime
        priority_order = self.strategy_priority.get(new_regime, 
                                                    ['MOMENTUM', 'BREAKOUT', 'MEAN_REVERSION'])
        
        print(f"📊 Strategy Priority: {' > '.join(priority_order)}")
        
        # Find positions to exit
        positions_to_exit = self._identify_exit_candidates(
            priority_order, 
            current_strategy,
            capital_shortage
        )
        
        if not positions_to_exit:
            print("⚠️ No suitable positions to exit")
            return 0
        
        # Execute exits
        freed_capital = self._execute_exits(positions_to_exit)
        
        print(f"\n✅ Freed up ₹{freed_capital:,.0f} for {current_strategy}")
        return freed_capital
    
    def _identify_exit_candidates(self, priority_order, requesting_strategy, needed_capital):
        """
        Identify which positions to exit to free capital
        
        Priority:
        1. Losing positions in low-priority strategies
        2. Break-even positions in low-priority strategies  
        3. Small winners in low-priority strategies
        """
        candidates = []
        
        # Get all open positions
        positions = self.portfolio_manager.get_open_positions()
        
        if not positions:
            return []
        
        # Score each position for exit
        scored_positions = []
        
        for symbol, pos in positions.items():
            strategy = pos.get('strategy', 'MOMENTUM')
            
            # Don't exit positions in the requesting strategy
            if strategy == requesting_strategy:
                continue
            
            # Calculate metrics
            entry = pos['entry_price']
            
            # Get current price
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{symbol}.NS")
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
            except:
                current_price = entry
            
            profit_pct = (current_price - entry) / entry
            days_held = pos.get('days_held', 0)
            
            # Calculate exit score (higher = better to exit)
            exit_score = 0
            
            # Priority: Low priority strategies
            strategy_rank = priority_order.index(strategy) if strategy in priority_order else 999
            exit_score += strategy_rank * 30  # 0, 30, 60 points
            
            # Losses: High priority to exit
            if profit_pct < self.max_loss_to_exit:
                exit_score += 50
            
            # Break-even: Medium priority
            elif abs(profit_pct) < 0.01:
                exit_score += 30
            
            # Small profits: Lower priority
            elif profit_pct < self.min_profit_to_keep:
                exit_score += 20
            
            # Good profits: Don't exit
            else:
                exit_score -= 50  # Negative score = keep
            
            # Age: Older positions easier to exit
            if days_held >= 3:
                exit_score += 10
            
            # Position size
            cost_per_share = pos['position_value'] / pos['initial_shares']
            remaining_value = cost_per_share * pos['shares']
            
            scored_positions.append({
                'symbol': symbol,
                'position': pos,
                'exit_score': exit_score,
                'profit_pct': profit_pct,
                'value': remaining_value,
                'current_price': current_price,
                'strategy': strategy
            })
        
        # Sort by exit score (highest first)
        scored_positions.sort(key=lambda x: x['exit_score'], reverse=True)
        
        # Select positions to exit
        total_freed = 0
        
        print(f"\n📋 Exit Candidates:")
        for i, item in enumerate(scored_positions[:10], 1):  # Show top 10
            print(f"   {i}. {item['symbol']} ({item['strategy']})")
            print(f"      Score: {item['exit_score']}, P&L: {item['profit_pct']*100:+.1f}%, Value: ₹{item['value']:,.0f}")
        
        for item in scored_positions:
            if item['exit_score'] > 20:  # Only exit if score > 20
                candidates.append(item)
                total_freed += item['value']
                
                if total_freed >= needed_capital * 1.1:  # Get 10% extra buffer
                    break
        
        return candidates
    
    def _execute_exits(self, exit_list):
        """Execute the exits and return freed capital"""
        freed_capital = 0
        
        print(f"\n🔄 Executing {len(exit_list)} exits:")
        
        for item in exit_list:
            symbol = item['symbol']
            current_price = item['current_price']
            strategy = item['strategy']
            profit_pct = item['profit_pct']
            
            # Execute exit
            success, alert_data = self.portfolio_manager.remove_position(
                symbol,
                current_price,
                f"Reallocated ({profit_pct*100:+.1f}% P&L)"
            )
            
            if success:
                cost_per_share = item['position']['position_value'] / item['position']['initial_shares']
                exit_value = current_price * item['position']['shares']
                freed_capital += exit_value
                
                print(f"   ✅ Exited {symbol}: ₹{exit_value:,.0f} freed ({profit_pct*100:+.1f}%)")
        
        # Recalculate available capital
        self.portfolio_manager._recalculate_capital()
        
        return freed_capital
    
    def get_dynamic_allocation(self, regime):
        """
        Get dynamic position limits based on regime
        
        When in mean reversion regime: Allow more positions
        When switching to momentum/breakout: Will reallocate
        """
        if regime in ['RANGING', 'CHOPPY', 'WEAK']:
            # Mean reversion dominant - allow more positions
            return {
                'MEAN_REVERSION': {
                    'max_positions': 12,  # Use most capital
                    'capital_pct': 0.85
                },
                'MOMENTUM': {
                    'max_positions': 2,
                    'capital_pct': 0.10
                },
                'BREAKOUT': {
                    'max_positions': 2,
                    'capital_pct': 0.05
                }
            }
        
        elif regime in ['TRENDING_UP', 'STRONG_BULL']:
            # Momentum dominant - will reallocate automatically
            return {
                'MOMENTUM': {
                    'max_positions': 10,
                    'capital_pct': 0.70
                },
                'BREAKOUT': {
                    'max_positions': 4,
                    'capital_pct': 0.20
                },
                'MEAN_REVERSION': {
                    'max_positions': 2,
                    'capital_pct': 0.10
                }
            }
        
        elif regime in ['CONSOLIDATION']:
            # Breakout dominant
            return {
                'BREAKOUT': {
                    'max_positions': 8,
                    'capital_pct': 0.60
                },
                'MEAN_REVERSION': {
                    'max_positions': 4,
                    'capital_pct': 0.25
                },
                'MOMENTUM': {
                    'max_positions': 3,
                    'capital_pct': 0.15
                }
            }
        
        # Default
        return {
            'MOMENTUM': {'max_positions': 5, 'capital_pct': 0.40},
            'MEAN_REVERSION': {'max_positions': 5, 'capital_pct': 0.35},
            'BREAKOUT': {'max_positions': 3, 'capital_pct': 0.25}
        }


if __name__ == "__main__":
    print("🔄 Dynamic Capital Allocator - Test Mode")
    print("\nThis module handles intelligent capital reallocation")
    print("when market regime changes.\n")