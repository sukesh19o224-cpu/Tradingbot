"""
🛡️ RISK MANAGER V4.0
Updated for multi-strategy system
Per-strategy risk limits and tracking
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *

# Import trading days calculator
try:
    from src.utils.trading_days_calculator import count_trading_days
    TRADING_DAYS_AVAILABLE = True
except:
    TRADING_DAYS_AVAILABLE = False



class RiskManager:
    """
    Manages risk with multi-strategy support
    
    V4.0 NEW:
    - Per-strategy risk limits
    - Strategy-specific position sizing
    - Combined risk monitoring
    """
    
    def __init__(self, capital=INITIAL_CAPITAL):
        self.capital = capital
        self.available_capital = capital
        self.open_positions = []
        self.daily_pnl = 0
        self.trade_count = 0
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        
        # Win rate tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0
        self.win_rate = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.position_size_multiplier = 1.0
        
        # Drawdown protection
        self.peak_capital = capital
        self.current_drawdown = 0.0
        self.trading_paused = False
        self.pause_until = None
        self.pause_reason = ""
        
        # V4.0 NEW: Per-strategy tracking
        self.strategy_risk = {
            'MOMENTUM': {
                'capital_used': 0,
                'open_positions': 0,
                'risk_exposure': 0
            },
            'MEAN_REVERSION': {
                'capital_used': 0,
                'open_positions': 0,
                'risk_exposure': 0
            },
            'BREAKOUT': {
                'capital_used': 0,
                'open_positions': 0,
                'risk_exposure': 0
            }
        }
        
        print("🛡️ Risk Manager V4.0 Initialized")
        print(f"💰 Capital: ₹{self.capital:,.0f}")
        print(f"⚠️ Risk/Trade: {MAX_RISK_PER_TRADE*100:.1f}%")
        print(f"📊 Multi-Strategy Tracking: Enabled")
        
        # Sync with existing portfolio
        self._sync_with_portfolio()
    
    def _sync_with_portfolio(self):
        """Sync risk manager with existing portfolio.json"""
        try:
            import json
            portfolio_file = 'data/portfolio.json'
            
            if not os.path.exists(portfolio_file):
                return
            
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
            
            # Load existing positions
            positions = portfolio.get('positions', {})
            
            if positions:
                print(f"\n🔄 Syncing with portfolio: {len(positions)} positions found")
                
                for symbol, pos in positions.items():
                    if pos.get('status') == 'OPEN':
                        entry_price = pos['entry_price']
                        shares = pos['shares']
                        stop_loss = pos['stop_loss']
                        strategy = pos.get('strategy', 'MOMENTUM')
                        
                        # Add to risk manager
                        self.add_position(symbol, entry_price, shares, stop_loss, strategy)
                
                print(f"✅ Synced {len(self.open_positions)} open positions")
        
        except Exception as e:
            print(f"⚠️ Portfolio sync failed: {e}")
    
    def update_capital(self, new_capital):
        """Update capital and check drawdown"""
        self.capital = new_capital
        self._recalculate_available_capital()
        
        if new_capital > self.peak_capital:
            self.peak_capital = new_capital
            print(f"🎉 New peak: ₹{self.peak_capital:,.0f}")
        
        self._check_drawdown()
    
    def _recalculate_available_capital(self):
        """Recalculate available capital"""
        invested = sum(pos.get('position_value', 0) for pos in self.open_positions)
        self.available_capital = self.capital - invested
    
    def calculate_position_size(self, entry_price, stop_loss_price, strategy='MOMENTUM'):
        """
        Calculate position size with strategy awareness
        
        V4.0 UPDATED: Consider strategy-specific limits
        """
        # Base risk
        base_risk = self.available_capital * MAX_RISK_PER_TRADE
        adjusted_risk = base_risk * self.position_size_multiplier
        
        # Risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            return 0
        
        # Calculate shares
        shares = int(adjusted_risk / risk_per_share)
        
        # Max position limit
        max_position_value = self.available_capital * MAX_PER_STOCK
        max_shares = int(max_position_value / entry_price) if entry_price > 0 else 0
        
        final_shares = min(shares, max_shares)
        
        # V4.0 NEW: Check strategy-specific limits
        if strategy in STRATEGIES:
            strategy_max_positions = STRATEGIES[strategy]['max_positions']
            current_positions = self.strategy_risk[strategy]['open_positions']
            
            if current_positions >= strategy_max_positions:
                print(f"⚠️ {strategy} max positions reached ({current_positions}/{strategy_max_positions})")
                return 0
        
        # Minimum check
        if final_shares * entry_price < 5000:
            return 0
        
        return final_shares
    
    def calculate_stop_loss(self, entry_price, atr_value=None, strategy='MOMENTUM'):
        """
        Calculate stop loss (strategy-aware)
        
        V4.0 UPDATED: Use strategy-specific stop %
        """
        # Get strategy-specific stop if available
        if strategy in ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT']:
            config_map = {
                'MOMENTUM': MOMENTUM,
                'MEAN_REVERSION': MEAN_REVERSION,
                'BREAKOUT': BREAKOUT
            }
            stop_pct = config_map[strategy]['STOP_LOSS']
        else:
            stop_pct = STOP_LOSS_PERCENT
        
        if atr_value and atr_value > 0:
            atr_stop = entry_price - (2.0 * atr_value)
            pct_stop = entry_price * (1 - stop_pct)
            stop_loss = max(atr_stop, pct_stop)  # Use tighter stop
        else:
            stop_loss = entry_price * (1 - stop_pct)
        
        return round(stop_loss, 2)
    
    def calculate_target(self, entry_price, stop_loss, strategy='MOMENTUM', target_num=1):
        """
        Calculate targets (strategy-specific)
        
        V4.0 NEW: Different targets per strategy
        """
        config_map = {
            'MOMENTUM': MOMENTUM,
            'MEAN_REVERSION': MEAN_REVERSION,
            'BREAKOUT': BREAKOUT
        }
        
        if strategy in config_map:
            targets = config_map[strategy]['TARGETS']
            target_pct = targets[target_num - 1] if target_num <= len(targets) else targets[-1]
            target = entry_price * (1 + target_pct)
        else:
            # Default
            risk = entry_price - stop_loss
            target = entry_price + (risk * 2)
        
        return round(target, 2)
    
    def check_trade_allowed(self, strategy='MOMENTUM'):
        """
        Check if trade is allowed
        
        V4.0 UPDATED: Check strategy-specific limits
        """
        # Check pause
        if self.trading_paused:
            if self.pause_until and datetime.now() < self.pause_until:
                time_left = (self.pause_until - datetime.now()).total_seconds() / 3600
                print(f"⛔ PAUSED - {self.pause_reason} ({time_left:.1f}h left)")
                return False, {'trading_paused': True}
            else:
                self.trading_paused = False
                self.pause_until = None
                self.pause_reason = ""
                print("✅ Pause ended")
        
        checks = {
            'daily_loss_ok': self.daily_pnl > -(self.capital * MAX_DAILY_LOSS),
            'positions_available': len(self.open_positions) < MAX_POSITIONS,
            'no_consecutive_losses': self.consecutive_losses < 3,
            'capital_available': self.available_capital > self.capital * 0.2,
            'not_paused': not self.trading_paused
        }
        
        # V4.0 NEW: Strategy-specific check
        if strategy in STRATEGIES:
            strategy_max = STRATEGIES[strategy]['max_positions']
            strategy_current = self.strategy_risk[strategy]['open_positions']
            checks['strategy_positions_ok'] = strategy_current < strategy_max
        
        all_ok = all(checks.values())
        
        if not all_ok:
            print(f"\n⛔ TRADE BLOCKED ({strategy}):")
            for check, status in checks.items():
                if not status:
                    print(f"  ❌ {check}")
        
        return all_ok, checks
    
    def add_position(self, symbol, entry_price, shares, stop_loss, strategy='MOMENTUM'):
        """
        Add position with strategy tracking
        
        V4.0 UPDATED: Track per-strategy
        """
        if shares <= 0:
            print(f"❌ Invalid shares: {shares}")
            return False
        
        position = {
            'symbol': symbol,
            'entry_price': entry_price,
            'shares': shares,
            'stop_loss': stop_loss,
            'position_value': entry_price * shares,
            'entry_time': datetime.now(),
            'status': 'OPEN',
            'strategy': strategy  # V4.0
        }
        
        self.open_positions.append(position)
        self.available_capital -= position['position_value']
        self.trade_count += 1
        
        # V4.0: Update strategy risk
        if strategy in self.strategy_risk:
            self.strategy_risk[strategy]['capital_used'] += position['position_value']
            self.strategy_risk[strategy]['open_positions'] += 1
            self.strategy_risk[strategy]['risk_exposure'] += (entry_price - stop_loss) * shares
        
        print(f"✅ Position added: {symbol} ({strategy})")
        print(f"   Shares: {shares} @ ₹{entry_price}")
        return True
    
    def record_trade_outcome(self, symbol, pnl, strategy='MOMENTUM'):
        """
        Record trade with strategy tracking
        
        V4.0 UPDATED: Track per-strategy
        """
        self.total_trades += 1
        
        if pnl > 0:
            self.winning_trades += 1
            self.total_profit += pnl
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            print(f"✅ Win: {symbol} ({strategy}), Streak: {self.consecutive_wins}")
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnl)
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            print(f"⚠️ Loss: {symbol} ({strategy}), Streak: {self.consecutive_losses}")
        
        # Calculate stats
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.winning_trades > 0:
            self.avg_win = self.total_profit / self.winning_trades
        
        if self.losing_trades > 0:
            self.avg_loss = self.total_loss / self.losing_trades
        
        self.daily_pnl += pnl
        
        # V4.0: Remove from strategy tracking
        if strategy in self.strategy_risk:
            self.strategy_risk[strategy]['open_positions'] = max(0, self.strategy_risk[strategy]['open_positions'] - 1)
        
        self._auto_adjust_position_size()
    
    def _auto_adjust_position_size(self):
        """Auto-adjust position sizing"""
        if self.total_trades < 10:
            return
        
        if self.win_rate < 45:
            self.position_size_multiplier = 0.7
            print("⚠️ Win rate <45%. Reducing size to 70%")
        elif self.consecutive_losses >= 2:
            self.position_size_multiplier = 0.8
            print("⚠️ 2 losses. Reducing size to 80%")
        elif self.win_rate > 70 and self.consecutive_wins >= 3 and self.total_trades >= 15:
            self.position_size_multiplier = 1.1
            print("✅ Strong! Increasing size to 110%")
        elif 55 <= self.win_rate <= 70:
            self.position_size_multiplier = 1.0
    
    def get_performance_summary(self):
        """Get performance stats"""
        summary = {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 1),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'total_profit': round(self.total_profit, 2),
            'total_loss': round(self.total_loss, 2),
            'net_pnl': round(self.total_profit - self.total_loss, 2),
            'position_size_multiplier': self.position_size_multiplier,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses
        }
        
        if self.total_trades > 0:
            expectancy = (self.win_rate / 100 * self.avg_win) - ((100 - self.win_rate) / 100 * self.avg_loss)
            summary['expectancy'] = round(expectancy, 2)
        else:
            summary['expectancy'] = 0
        
        return summary
    
    def _check_drawdown(self):
        """Check drawdown and pause if needed"""
        if self.capital < self.peak_capital:
            self.current_drawdown = (self.peak_capital - self.capital) / self.peak_capital * 100
        else:
            self.current_drawdown = 0.0
        
        if self.current_drawdown >= (MAX_DRAWDOWN_PERCENT * 100):
            if not self.trading_paused:
                self.trading_paused = True
                self.pause_until = datetime.now() + timedelta(hours=DRAWDOWN_PAUSE_HOURS)
                self.pause_reason = f"Drawdown {self.current_drawdown:.1f}% > {MAX_DRAWDOWN_PERCENT*100}%"
                
                print("\n" + "="*60)
                print("🚨 TRADING PAUSED - DRAWDOWN LIMIT!")
                print("="*60)
                print(f"   Peak: ₹{self.peak_capital:,.0f}")
                print(f"   Current: ₹{self.capital:,.0f}")
                print(f"   Drawdown: {self.current_drawdown:.1f}%")
                print(f"   Resume: {self.pause_until.strftime('%Y-%m-%d %H:%M')}")
                print("="*60)
    
    def calculate_portfolio_heat(self):
        """Calculate total risk exposure"""
        total_risk = 0
        
        for position in self.open_positions:
            risk = (position['entry_price'] - position['stop_loss']) * position['shares']
            total_risk += risk
        
        if self.capital == 0:
            return 0, "⚪ NO CAPITAL"
        
        portfolio_heat = (total_risk / self.capital) * 100
        
        if portfolio_heat < 4:
            status = "🟢 SAFE"
        elif portfolio_heat < 6:
            status = "🟡 CAUTION"
        else:
            status = "🔴 DANGER"
        
        return portfolio_heat, status
    
    def get_trade_summary(self, symbol, price, atr_value=None, strategy='MOMENTUM'):
        """
        Get complete trade plan
        
        V4.0 UPDATED: Strategy-aware
        """
        stop_loss = self.calculate_stop_loss(price, atr_value, strategy)
        shares = self.calculate_position_size(price, stop_loss, strategy)
        
        if shares == 0:
            return None
        
        position_value = shares * price
        risk_amount = (price - stop_loss) * shares
        
        target1 = self.calculate_target(price, stop_loss, strategy, 1)
        target2 = self.calculate_target(price, stop_loss, strategy, 2)
        target3 = self.calculate_target(price, stop_loss, strategy, 3)
        
        # Blended reward
        reward_t1 = (target1 - price) * shares * PARTIAL_EXIT_T1
        reward_t2 = (target2 - price) * shares * PARTIAL_EXIT_T2
        reward_t3 = (target3 - price) * shares * PARTIAL_EXIT_T3
        reward_amount = reward_t1 + reward_t2 + reward_t3
        
        risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0
        
        allowed, checks = self.check_trade_allowed(strategy)
        
        summary = {
            'symbol': symbol,
            'strategy': strategy,
            'price': price,
            'entry_price': price,
            'stop_loss': stop_loss,
            'target': target2,
            'target1': target1,
            'target2': target2,
            'target3': target3,
            'shares': shares,
            'position_value': round(position_value, 2),
            'risk_amount': round(risk_amount, 2),
            'reward_amount': round(reward_amount, 2),
            'risk_reward': round(risk_reward, 2),
            'risk_percent': round((risk_amount/self.capital)*100, 2),
            'trade_allowed': allowed,
            'checks': checks
        }
        
        return summary
    
    def display_risk_status(self):
        """Display complete risk status"""
        heat, status = self.calculate_portfolio_heat()
        perf = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 RISK MANAGEMENT STATUS V4.0")
        print("="*60)
        
        print(f"💰 Peak: ₹{self.peak_capital:,.0f}")
        print(f"💰 Current: ₹{self.capital:,.0f}")
        print(f"💵 Available: ₹{self.available_capital:,.0f}")
        
        if self.current_drawdown > 0:
            dd_status = "🔴" if self.current_drawdown > 8 else "🟡" if self.current_drawdown > 5 else "🟢"
            print(f"📉 Drawdown: {self.current_drawdown:.1f}% {dd_status}")
        
        print(f"📈 Positions: {len(self.open_positions)}/{MAX_POSITIONS}")
        print(f"🔥 Heat: {heat:.1f}% {status}")
        print(f"📊 Daily P&L: ₹{self.daily_pnl:,.0f}")
        
        # V4.0 NEW: Per-strategy risk
        print(f"\n📊 STRATEGY RISK BREAKDOWN:")
        for strategy, risk_data in self.strategy_risk.items():
            if risk_data['open_positions'] > 0:
                print(f"   {strategy:15s}: {risk_data['open_positions']} pos, "
                      f"₹{risk_data['capital_used']:,.0f} used, "
                      f"₹{risk_data['risk_exposure']:,.0f} risk")
        
        if self.total_trades > 0:
            print("\n" + "-"*60)
            print("📈 PERFORMANCE")
            print("-"*60)
            print(f"Trades: {perf['total_trades']} (W: {perf['winning_trades']}, L: {perf['losing_trades']})")
            print(f"Win Rate: {perf['win_rate']:.1f}%")
            print(f"Avg Win: ₹{perf['avg_win']:,.0f} | Avg Loss: ₹{perf['avg_loss']:,.0f}")
            print(f"Net P&L: ₹{perf['net_pnl']:,.0f}")
            print(f"Expectancy: ₹{perf['expectancy']:,.0f}/trade")
            print(f"Size: {perf['position_size_multiplier']:.1f}x")
        
        print("\n" + "-"*60)
        print(f"✅ Wins: {self.consecutive_wins} | ⚠️ Losses: {self.consecutive_losses}")
        
        if self.trading_paused:
            print("\n🚨 STATUS: PAUSED")
            print(f"Reason: {self.pause_reason}")
            if self.pause_until:
                print(f"Resume: {self.pause_until.strftime('%Y-%m-%d %H:%M')}")
        
        print("="*60)


if __name__ == "__main__":
    print("\n🧪 Testing Risk Manager V4.0\n")
    
    rm = RiskManager(100000)
    rm.display_risk_status()
    
    # Test with different strategies
    print("\n🧪 TEST CALCULATIONS:")
    
    for strategy in ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT']:
        print(f"\n{strategy}:")
        summary = rm.get_trade_summary('TEST', 1000, atr_value=30, strategy=strategy)
        if summary:
            print(f"  Shares: {summary['shares']}")
            print(f"  Stop: ₹{summary['stop_loss']}")
            print(f"  Targets: ₹{summary['target1']:.0f}/₹{summary['target2']:.0f}/₹{summary['target3']:.0f}")
            print(f"  R:R = 1:{summary['risk_reward']:.1f}")