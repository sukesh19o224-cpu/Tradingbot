"""
📄 PAPER TRADING SYSTEM - Virtual Portfolio with Auto-Execution
Test strategies with fake money before risking real capital
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from config.settings import *


class PaperTrader:
    """
    Paper trading portfolio that automatically executes signals

    Features:
    - Auto-execute all generated signals
    - Track performance in real-time
    - Compare with manual trading
    - Calculate realistic P&L
    - Position management (targets & stop loss)
    """

    def __init__(self, capital: float = None, data_file: str = None, portfolio_file: str = None):
        """
        Initialize paper trader

        Args:
            capital: Initial capital (if starting fresh)
            data_file: Path to trades history file
            portfolio_file: Path to portfolio state file
        """
        # Use provided files or defaults
        self.trades_file = data_file if data_file else 'data/trades.json'
        self.portfolio_file = portfolio_file if portfolio_file else PAPER_TRADING_FILE
        self.initial_capital = capital if capital else PAPER_TRADING_CAPITAL

        # Load or initialize portfolio
        if os.path.exists(self.portfolio_file):
            self._load_portfolio()
        else:
            self._initialize_portfolio()

    def _initialize_portfolio(self):
        """Initialize new paper portfolio"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0
        }
        self.start_date = datetime.now().isoformat()
        self._save_portfolio()

        print(f"📄 Paper Trading initialized - Capital: ₹{self.capital:,.0f}")

    def _load_portfolio(self):
        """Load existing portfolio from file"""
        try:
            with open(self.portfolio_file, 'r') as f:
                data = json.load(f)

            self.capital = data.get('capital', self.initial_capital)
            self.positions = data.get('positions', {})
            self.performance = data.get('performance', {})
            self.start_date = data.get('start_date', datetime.now().isoformat())

            # Load initial capital from saved data
            saved_initial = data.get('initial_capital')
            if saved_initial:
                self.initial_capital = saved_initial

            # Load trade history from separate file
            self._load_trades()

            print(f"📄 Paper Portfolio loaded - Capital: ₹{self.capital:,.0f}")

        except Exception as e:
            print(f"❌ Error loading portfolio: {e}")
            self._initialize_portfolio()

    def _load_trades(self):
        """Load trade history from separate file"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    self.trade_history = json.load(f)
            else:
                self.trade_history = []
        except Exception as e:
            print(f"❌ Error loading trades: {e}")
            self.trade_history = []

    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)

            data = {
                'capital': self.capital,
                'positions': self.positions,
                'performance': self.performance,
                'start_date': self.start_date,
                'last_updated': datetime.now().isoformat(),
                'initial_capital': self.initial_capital,
                'mode': 'PAPER_TRADING'
            }

            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving portfolio: {e}")

    def _save_trades(self):
        """Save trade history to separate file"""
        try:
            os.makedirs(os.path.dirname(self.trades_file), exist_ok=True)

            with open(self.trades_file, 'w') as f:
                json.dump(self.trade_history, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving trades: {e}")

    def execute_signal(self, signal: Dict) -> bool:
        """
        Auto-execute a trading signal

        Args:
            signal: Signal dictionary from SignalGenerator

        Returns:
            bool: True if executed successfully
        """
        if not PAPER_TRADING_AUTO_EXECUTE:
            return False

        try:
            symbol = signal['symbol']

            # Don't buy if already holding
            if symbol in self.positions:
                print(f"📄 Already holding {symbol}, skipping")
                return False

            # CRITICAL FIX #1: Enforce MAX_POSITIONS limit
            if len(self.positions) >= MAX_POSITIONS:
                print(f"📄 Max positions ({MAX_POSITIONS}) reached, skipping {symbol}")
                return False

            # DYNAMIC ALLOCATOR: Check signal type capacity
            if DYNAMIC_ALLOCATION_ENABLED:
                signal_type = signal.get('signal_type', 'MOMENTUM')
                if not self._has_signal_type_capacity(signal_type, signal):
                    print(f"📄 No capacity for {signal_type} signals, skipping {symbol}")
                    return False

            # Calculate position size (Kelly Criterion based + quality multiplier)
            position_size = self._calculate_position_size(signal)

            if position_size <= 0:
                print(f"📄 Insufficient capital for {symbol}")
                return False

            entry_price = signal['entry_price']
            shares = int(position_size / entry_price)

            if shares <= 0:
                print(f"📄 Cannot afford even 1 share of {symbol}")
                return False

            cost = shares * entry_price

            # Deduct capital
            self.capital -= cost

            # Add position
            self.positions[symbol] = {
                'symbol': symbol,
                'shares': shares,
                'entry_price': entry_price,
                'entry_date': datetime.now().isoformat(),
                'trade_type': signal['trade_type'],
                'target1': signal['target1'],
                'target2': signal['target2'],
                'target3': signal['target3'],
                'stop_loss': signal['stop_loss'],
                'score': signal['score'],
                'cost': cost,
                'max_holding_days': signal.get('max_holding_days', 30),  # Default 30 days
                'strategy': signal.get('strategy', 'unknown'),
                'signal_type': signal.get('signal_type', 'MOMENTUM')  # MEAN_REVERSION, MOMENTUM, or BREAKOUT
            }

            self._save_portfolio()
            # No need to save trades here - no trade completed yet

            print(f"📄 PAPER BUY: {symbol} x{shares} @ ₹{entry_price:.2f} = ₹{cost:,.0f}")
            print(f"   Remaining Capital: ₹{self.capital:,.0f}")

            return True

        except Exception as e:
            print(f"❌ Error executing signal: {e}")
            return False

    def check_exits(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check if any positions should be exited

        CRITICAL FIX #3: Exit priority corrected
        1. Check TARGETS first (lock in profits)
        2. Check STOP LOSS second (cut losses)
        3. Check TIME last (only if not profitable)

        NEW FEATURE: Trailing stops to lock in profits

        Args:
            current_prices: Dict mapping symbol to current price

        Returns:
            List of exit notifications
        """
        exits = []

        for symbol, position in list(self.positions.items()):
            current_price = current_prices.get(symbol, 0)

            if current_price == 0:
                continue

            entry_price = position['entry_price']
            shares = position['shares']

            # NEW FEATURE #7: Trailing stop - raise stop loss when in profit
            # If price is up 5% or more, move stop to breakeven or higher
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct >= 0.05:  # If up 5%+
                # Trail stop at 3% below current price or breakeven, whichever is higher
                trailing_stop = max(entry_price, current_price * 0.97)
                if trailing_stop > position['stop_loss']:
                    position['stop_loss'] = trailing_stop
                    # Note: Don't save here, will save if exit happens

            # CRITICAL FIX #3: Check TARGETS FIRST (not time!)
            # Priority 1: Target 3 (highest profit)
            if current_price >= position['target3']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_3', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)
                continue  # Move to next position

            # Priority 2: Target 2 (good profit)
            elif current_price >= position['target2']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_2', partial=0.40
                )
                if exit_info:
                    exits.append(exit_info)
                # Don't continue, check other exits too

            # Priority 3: Target 1 (minimum profit)
            elif current_price >= position['target1']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_1', partial=0.40
                )
                if exit_info:
                    exits.append(exit_info)
                # Don't continue, check other exits too

            # Priority 4: STOP LOSS (including trailing stop)
            if current_price <= position['stop_loss']:
                exit_info = self._exit_position(
                    symbol, current_price, 'STOP_LOSS', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)
                continue  # Position closed

            # Priority 5: TIME-BASED exit (LAST resort, only if not profitable)
            # Only exit on max days if NOT making good profit
            if 'entry_date' in position and 'max_holding_days' in position:
                try:
                    entry_date = datetime.fromisoformat(position['entry_date'])
                    days_held = (datetime.now() - entry_date).days
                    max_days = position['max_holding_days']

                    # Only exit on time if:
                    # 1. Max days reached AND
                    # 2. Not in profit (or profit < 3%)
                    if days_held >= max_days and profit_pct < 0.03:
                        exit_info = self._exit_position(
                            symbol, current_price, f'MAX_HOLDING_PERIOD ({days_held} days)', full_exit=True
                        )
                        if exit_info:
                            exits.append(exit_info)
                        continue
                except Exception as e:
                    print(f"⚠️ Error checking holding period for {symbol}: {e}")

        return exits

    def _exit_position(self, symbol: str, exit_price: float, reason: str,
                      full_exit: bool = False, partial: float = 0) -> Optional[Dict]:
        """Exit position (full or partial)"""
        try:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]
            entry_price = position['entry_price']

            if partial > 0 and not full_exit:
                # Partial exit
                shares_to_sell = int(position['shares'] * partial)
                if shares_to_sell <= 0:
                    # CRITICAL FIX #8: If partial exit too small, exit full position
                    shares_to_sell = position['shares']
                    full_exit = True
            else:
                # Full exit
                shares_to_sell = position['shares']

            proceeds = shares_to_sell * exit_price
            cost = shares_to_sell * entry_price

            pnl = proceeds - cost
            pnl_percent = (exit_price - entry_price) / entry_price * 100

            # Update capital
            self.capital += proceeds

            # Update position
            if shares_to_sell >= position['shares']:
                # Full exit
                del self.positions[symbol]
            else:
                # Partial exit
                position['shares'] -= shares_to_sell

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'shares': shares_to_sell,
                'entry_date': position['entry_date'],
                'exit_date': datetime.now().isoformat(),
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'reason': reason,
                'trade_type': position['trade_type']
            }

            self.trade_history.append(trade_record)

            # Update performance stats
            self.performance['total_trades'] += 1
            self.performance['total_pnl'] += pnl

            if pnl > 0:
                self.performance['winning_trades'] += 1
                if pnl > self.performance.get('best_trade', 0):
                    self.performance['best_trade'] = pnl
            else:
                self.performance['losing_trades'] += 1
                if pnl < self.performance.get('worst_trade', 0):
                    self.performance['worst_trade'] = pnl

            self._save_portfolio()
            self._save_trades()  # Save trade history when trade completes

            exit_type = 'PARTIAL' if shares_to_sell < position['shares'] else 'FULL'

            print(f"📄 PAPER EXIT ({exit_type}): {symbol} x{shares_to_sell} @ ₹{exit_price:.2f}")
            print(f"   P&L: ₹{pnl:+,.0f} ({pnl_percent:+.2f}%)")

            return {
                'symbol': symbol,
                'exit_type': exit_type,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'reason': reason,
                'shares': shares_to_sell
            }

        except Exception as e:
            print(f"❌ Error exiting position: {e}")
            return None

    def _calculate_position_size(self, signal: Dict) -> float:
        """
        Calculate position size using risk management + quality-based sizing

        Uses:
        - Portfolio value (not just cash) for fair sizing
        - Kelly Criterion (fractional)
        - Max risk per trade limit
        - Quality multiplier based on signal score
        """
        try:
            # CRITICAL FIX #6: Use portfolio value, not just remaining cash
            # This ensures all positions get fair sizing
            portfolio_value = self.capital + sum(p['shares'] * p['entry_price'] for p in self.positions.values())

            # Base position size
            max_position = portfolio_value * MAX_POSITION_SIZE

            # Risk-based sizing
            entry = signal['entry_price']
            stop = signal['stop_loss']
            risk_per_share = entry - stop

            # Max shares based on risk limit
            max_risk_amount = portfolio_value * MAX_RISK_PER_TRADE
            max_shares_by_risk = max_risk_amount / risk_per_share if risk_per_share > 0 else 0

            # Base position size
            base_position_size = min(max_position, max_shares_by_risk * entry)

            # NEW FEATURE: Quality-based position sizing
            # Score 9-10: 1.5x size (high confidence)
            # Score 8-9: 1.0x size (normal)
            # Score 7-8: 0.5x size (low confidence)
            # Score <7: 0x (skip)
            score = signal.get('score', 7.0)
            if score < 7.0:
                return 0  # Skip low quality signals

            # Linear multiplier: 0.5x at score 7, 1.0x at score 8, 1.5x at score 9, 2.0x at score 10
            quality_multiplier = 0.5 + (score - 7) * 0.5
            quality_multiplier = min(quality_multiplier, 2.0)  # Cap at 2x

            # Adjusted position size
            position_size = base_position_size * quality_multiplier

            # Don't exceed available capital
            position_size = min(position_size, self.capital)

            return position_size

        except Exception as e:
            print(f"❌ Position sizing error: {e}")
            return 0

    def _has_signal_type_capacity(self, signal_type: str, signal: Dict) -> bool:
        """
        Check if we have capacity to take this signal type

        DYNAMIC ALLOCATOR:
        - Mean Reversion: 70% of portfolio capital
        - Momentum: 20% of portfolio capital
        - Breakout: 10% of portfolio capital

        If Momentum/Breakout signal is high quality (score >= 8.5):
        - Auto-exit weakest mean reversion position to free capital
        """
        if not DYNAMIC_ALLOCATION_ENABLED:
            return True  # No restriction

        # Calculate total portfolio value
        portfolio_value = self.capital + sum(p['shares'] * p['entry_price'] for p in self.positions.values())

        # Calculate capital allocated by signal type
        mr_allocated = sum(
            p['shares'] * p['entry_price']
            for p in self.positions.values()
            if p.get('signal_type', 'MOMENTUM') == 'MEAN_REVERSION'
        )
        momentum_allocated = sum(
            p['shares'] * p['entry_price']
            for p in self.positions.values()
            if p.get('signal_type', 'MOMENTUM') == 'MOMENTUM'
        )
        breakout_allocated = sum(
            p['shares'] * p['entry_price']
            for p in self.positions.values()
            if p.get('signal_type', 'MOMENTUM') == 'BREAKOUT'
        )

        # Calculate limits
        mr_limit = portfolio_value * MEAN_REVERSION_CAPITAL_PCT
        momentum_limit = portfolio_value * MOMENTUM_CAPITAL_PCT
        breakout_limit = portfolio_value * BREAKOUT_CAPITAL_PCT

        # Check if we have capacity
        if signal_type == 'MEAN_REVERSION':
            has_capacity = mr_allocated < mr_limit
        elif signal_type == 'MOMENTUM':
            has_capacity = momentum_allocated < momentum_limit
        elif signal_type == 'BREAKOUT':
            has_capacity = breakout_allocated < breakout_limit
        else:
            has_capacity = True  # Unknown type, allow

        # If no capacity but signal is high-quality momentum/breakout, exit weakest MR
        if not has_capacity and AUTO_EXIT_MR_FOR_MOMENTUM:
            if signal_type in ['MOMENTUM', 'BREAKOUT']:
                if signal.get('score', 0) >= MR_EXIT_THRESHOLD_SCORE:
                    # Try to exit weakest mean reversion position
                    exited = self._exit_weakest_mean_reversion()
                    if exited:
                        print(f"   💡 Exited weak MR position to free capital for {signal_type} signal!")
                        return True  # Now we have capacity

        return has_capacity

    def _exit_weakest_mean_reversion(self) -> bool:
        """
        Exit the weakest (lowest score) mean reversion position
        to free capital for high-quality momentum/breakout signals

        Returns:
            True if a position was exited
        """
        # Find all mean reversion positions
        mr_positions = [
            (symbol, pos)
            for symbol, pos in self.positions.items()
            if pos.get('signal_type', 'MOMENTUM') == 'MEAN_REVERSION'
        ]

        if not mr_positions:
            return False

        # Find weakest (lowest score)
        weakest = min(mr_positions, key=lambda x: x[1].get('score', 7.0))
        symbol, position = weakest

        # Exit at current price (assume entry price as proxy for current)
        # In real implementation, would fetch current price
        exit_price = position['entry_price'] * 1.02  # Assume small profit

        exit_info = self._exit_position(
            symbol,
            exit_price,
            'AUTO_EXIT_FOR_MOMENTUM',
            full_exit=True
        )

        return exit_info is not None

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        total = self.capital

        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position['entry_price'])
            total += position['shares'] * current_price

        return total

    def get_summary(self, current_prices: Dict[str, float] = None) -> Dict:
        """Get portfolio summary"""
        if current_prices is None:
            current_prices = {}

        # Calculate unrealized P&L
        unrealized_pnl = 0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position['entry_price'])
            unrealized_pnl += (current_price - position['entry_price']) * position['shares']

        # Total portfolio value
        portfolio_value = self.get_portfolio_value(current_prices)

        # Calculate metrics
        total_return = ((portfolio_value - self.initial_capital) / self.initial_capital * 100)

        win_rate = 0
        if self.performance['total_trades'] > 0:
            win_rate = (self.performance['winning_trades'] / self.performance['total_trades'] * 100)

        return {
            'capital': self.capital,
            'portfolio_value': portfolio_value,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': self.performance['total_pnl'],
            'total_return_percent': total_return,
            'open_positions': len(self.positions),
            'total_trades': self.performance['total_trades'],
            'winning_trades': self.performance['winning_trades'],
            'losing_trades': self.performance['losing_trades'],
            'win_rate': win_rate,
            'best_trade': self.performance.get('best_trade', 0),
            'worst_trade': self.performance.get('worst_trade', 0)
        }

    def reset(self):
        """Reset paper portfolio"""
        self._initialize_portfolio()
        print("🗑️ Paper portfolio reset")


if __name__ == "__main__":
    # Test paper trader
    print("🧪 Testing Paper Trader...")

    trader = PaperTrader()
    summary = trader.get_summary()

    print(f"\n📄 Paper Portfolio Summary:")
    print(f"   Capital: ₹{summary['capital']:,.0f}")
    print(f"   Portfolio Value: ₹{summary['portfolio_value']:,.0f}")
    print(f"   Total Return: {summary['total_return_percent']:+.2f}%")
    print(f"   Win Rate: {summary['win_rate']:.1f}%")
