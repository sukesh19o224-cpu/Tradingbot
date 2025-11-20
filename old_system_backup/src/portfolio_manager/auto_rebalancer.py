"""
V5.5 ULTRA+ - Auto-Rebalancing System
Automatically rebalances portfolio based on performance and allocation
"""
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class AutoRebalancer:
    """
    Automatic portfolio rebalancing
    
    Features:
    - Strategy allocation rebalancing
    - Performance-based adjustments
    - Risk-based rebalancing
    - Scheduled rebalancing triggers
    """
    
    def __init__(self, portfolio_manager):
        self.pm = portfolio_manager
        
        # Rebalancing configuration
        self.REBALANCE_CONFIG = {
            'enabled': True,
            'frequency': 'weekly',  # 'daily', 'weekly', 'monthly'
            'threshold': 0.10,      # Rebalance if drift > 10%
            'method': 'performance_weighted',  # or 'equal_weight', 'risk_parity'
        }
        
        # Target allocations (will be dynamically adjusted)
        self.target_allocations = {
            'MOMENTUM': 0.30,
            'MEAN_REVERSION': 0.25,
            'BREAKOUT': 0.20,
            'POSITIONAL': 0.25
        }
        
        self.last_rebalance = datetime.now()
    
    def should_rebalance(self) -> bool:
        """Check if portfolio should be rebalanced"""
        if not self.REBALANCE_CONFIG['enabled']:
            return False
        
        # Check time-based trigger
        if self._time_trigger():
            return True
        
        # Check drift threshold
        if self._drift_trigger():
            return True
        
        return False
    
    def _time_trigger(self) -> bool:
        """Check if enough time has passed since last rebalance"""
        now = datetime.now()
        days_since = (now - self.last_rebalance).days
        
        freq = self.REBALANCE_CONFIG['frequency']
        
        if freq == 'daily' and days_since >= 1:
            return True
        elif freq == 'weekly' and days_since >= 7:
            return True
        elif freq == 'monthly' and days_since >= 30:
            return True
        
        return False
    
    def _drift_trigger(self) -> bool:
        """Check if actual allocation has drifted from target"""
        current_alloc = self._get_current_allocation()
        
        for strategy in self.target_allocations:
            target = self.target_allocations[strategy]
            current = current_alloc.get(strategy, 0)
            
            drift = abs(current - target)
            
            if drift > self.REBALANCE_CONFIG['threshold']:
                logger.info(f"🔄 Rebalance trigger: {strategy} drift = {drift:.2%}")
                return True
        
        return False
    
    def _get_current_allocation(self) -> Dict[str, float]:
        """Calculate current portfolio allocation by strategy"""
        strategy_values = {}
        total_value = 0
        
        for symbol, position in self.pm.positions.items():
            strategy = position['strategy']
            value = position['quantity'] * position['entry_price']
            
            strategy_values[strategy] = strategy_values.get(strategy, 0) + value
            total_value += value
        
        # Convert to percentages
        if total_value == 0:
            return {s: 0 for s in self.target_allocations}
        
        return {
            strategy: value / total_value
            for strategy, value in strategy_values.items()
        }
    
    def rebalance_portfolio(self) -> Dict:
        """
        Execute portfolio rebalancing
        
        Returns dict with rebalancing actions
        """
        logger.info("🔄 Starting portfolio rebalancing...")
        
        # Calculate new target allocations based on performance
        if self.REBALANCE_CONFIG['method'] == 'performance_weighted':
            new_targets = self._performance_weighted_allocation()
        elif self.REBALANCE_CONFIG['method'] == 'risk_parity':
            new_targets = self._risk_parity_allocation()
        else:  # equal_weight
            new_targets = {s: 0.25 for s in self.target_allocations}
        
        # Update targets
        self.target_allocations = new_targets
        
        # Generate rebalancing actions
        actions = self._generate_rebalance_actions()
        
        self.last_rebalance = datetime.now()
        
        logger.info(f"✅ Rebalancing complete - {len(actions)} actions")
        
        return {
            'new_targets': new_targets,
            'actions': actions,
            'timestamp': datetime.now().isoformat()
        }
    
    def _performance_weighted_allocation(self) -> Dict[str, float]:
        """
        Calculate allocation based on strategy performance
        
        Better performing strategies get more capital
        """
        stats = self.pm.strategy_stats
        
        # Calculate performance scores
        scores = {}
        
        for strategy, stat in stats.items():
            total_trades = stat['wins'] + stat['losses']
            
            if total_trades == 0:
                scores[strategy] = 0.25  # Equal weight if no trades
                continue
            
            # Score based on win rate and average PnL
            win_rate = stat['wins'] / total_trades
            avg_pnl = stat['pnl'] / total_trades if total_trades > 0 else 0
            
            # Combined score (weighted)
            score = (win_rate * 0.6) + (avg_pnl / 1000 * 0.4)  # Normalized
            scores[strategy] = max(0, score)
        
        # Normalize to sum to 1.0
        total_score = sum(scores.values())
        
        if total_score == 0:
            return {s: 0.25 for s in self.target_allocations}
        
        allocations = {
            strategy: score / total_score
            for strategy, score in scores.items()
        }
        
        # Apply constraints (min 10%, max 40% per strategy)
        for strategy in allocations:
            allocations[strategy] = max(0.10, min(0.40, allocations[strategy]))
        
        # Renormalize
        total = sum(allocations.values())
        allocations = {s: v/total for s, v in allocations.items()}
        
        return allocations
    
    def _risk_parity_allocation(self) -> Dict[str, float]:
        """
        Calculate risk parity allocation
        
        Equal risk contribution from each strategy
        """
        # Calculate volatility for each strategy
        volatilities = {}
        
        for strategy, stat in self.pm.strategy_stats.items():
            # Use PnL volatility as risk measure
            trades = [
                t for t in self.pm.trade_history
                if t.get('strategy') == strategy
            ]
            
            if len(trades) < 2:
                volatilities[strategy] = 1.0
                continue
            
            pnls = [t.get('pnl', 0) for t in trades]
            volatilities[strategy] = np.std(pnls) if pnls else 1.0
        
        # Inverse volatility weighting
        inv_vol = {s: 1/v if v > 0 else 1 for s, v in volatilities.items()}
        
        total = sum(inv_vol.values())
        
        return {s: v/total for s, v in inv_vol.items()}
    
    def _generate_rebalance_actions(self) -> List[Dict]:
        """
        Generate specific buy/sell actions to rebalance
        
        Returns list of actions: [{'action': 'BUY'/'SELL', 'strategy': ..., 'amount': ...}]
        """
        actions = []
        
        current_alloc = self._get_current_allocation()
        portfolio_value = self._get_portfolio_value()
        
        for strategy in self.target_allocations:
            target = self.target_allocations[strategy]
            current = current_alloc.get(strategy, 0)
            
            diff = target - current
            
            if abs(diff) > 0.02:  # Only if > 2% difference
                amount = abs(diff * portfolio_value)
                
                if diff > 0:
                    # Need to increase allocation
                    actions.append({
                        'action': 'INCREASE',
                        'strategy': strategy,
                        'amount': amount,
                        'target_pct': target,
                        'current_pct': current
                    })
                else:
                    # Need to decrease allocation
                    actions.append({
                        'action': 'DECREASE',
                        'strategy': strategy,
                        'amount': amount,
                        'target_pct': target,
                        'current_pct': current
                    })
        
        return actions
    
    def _get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        invested = sum(
            pos['quantity'] * pos['entry_price']
            for pos in self.pm.positions.values()
        )
        
        return self.pm.capital + invested
    
    def get_rebalance_recommendation(self) -> str:
        """Get human-readable rebalance recommendation"""
        if not self.should_rebalance():
            return "✅ Portfolio is balanced - no rebalancing needed"
        
        current = self._get_current_allocation()
        
        report = "🔄 Rebalancing Recommended:\n\n"
        
        for strategy in self.target_allocations:
            target = self.target_allocations[strategy]
            curr = current.get(strategy, 0)
            diff = target - curr
            
            report += f"{strategy}:\n"
            report += f"  Current: {curr:.1%}\n"
            report += f"  Target:  {target:.1%}\n"
            report += f"  Diff:    {diff:+.1%}\n\n"
        
        return report
    
    def update_config(self, new_config: Dict):
        """Update rebalancing configuration"""
        self.REBALANCE_CONFIG.update(new_config)
        logger.info("✅ Rebalancing config updated")
