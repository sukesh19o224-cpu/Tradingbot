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

    def __init__(self, initial_capital: float = PAPER_TRADING_CAPITAL):
        self.portfolio_file = PAPER_TRADING_FILE
        self.initial_capital = initial_capital

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
            self.trade_history = data.get('trade_history', [])
            self.performance = data.get('performance', {})
            self.start_date = data.get('start_date', datetime.now().isoformat())

            print(f"📄 Paper Portfolio loaded - Capital: ₹{self.capital:,.0f}")

        except Exception as e:
            print(f"❌ Error loading portfolio: {e}")
            self._initialize_portfolio()

    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)

            data = {
                'capital': self.capital,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'performance': self.performance,
                'start_date': self.start_date,
                'last_updated': datetime.now().isoformat(),
                'mode': 'PAPER_TRADING'
            }

            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving portfolio: {e}")

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

            # Calculate position size (Kelly Criterion based)
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
                'strategy': signal.get('strategy', 'unknown')
            }

            self._save_portfolio()

            print(f"📄 PAPER BUY: {symbol} x{shares} @ ₹{entry_price:.2f} = ₹{cost:,.0f}")
            print(f"   Remaining Capital: ₹{self.capital:,.0f}")

            return True

        except Exception as e:
            print(f"❌ Error executing signal: {e}")
            return False

    def check_exits(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check if any positions should be exited

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

            # Check max holding period (time-based exit)
            if 'entry_date' in position and 'max_holding_days' in position:
                try:
                    entry_date = datetime.fromisoformat(position['entry_date'])
                    days_held = (datetime.now() - entry_date).days
                    max_days = position['max_holding_days']

                    if days_held >= max_days:
                        exit_info = self._exit_position(
                            symbol, current_price, f'MAX_HOLDING_PERIOD ({days_held} days)', full_exit=True
                        )
                        if exit_info:
                            exits.append(exit_info)
                        continue
                except Exception as e:
                    print(f"⚠️ Error checking holding period for {symbol}: {e}")

            # Check stop loss
            if current_price <= position['stop_loss']:
                exit_info = self._exit_position(
                    symbol, current_price, 'STOP_LOSS', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)
                continue

            # Check targets
            if current_price >= position['target3']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_3', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)

            elif current_price >= position['target2']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_2', partial=0.40
                )
                if exit_info:
                    exits.append(exit_info)

            elif current_price >= position['target1']:
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_1', partial=0.40
                )
                if exit_info:
                    exits.append(exit_info)

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
                    return None
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
        Calculate position size using risk management

        Uses:
        - Kelly Criterion (fractional)
        - Max risk per trade limit
        - Available capital
        """
        try:
            # Max capital we can use for this trade
            max_position = self.capital * MAX_POSITION_SIZE

            # Risk-based sizing
            entry = signal['entry_price']
            stop = signal['stop_loss']
            risk_per_share = entry - stop

            # Max shares based on risk limit
            max_risk_amount = self.capital * MAX_RISK_PER_TRADE
            max_shares_by_risk = max_risk_amount / risk_per_share if risk_per_share > 0 else 0

            # Position size
            position_size = min(max_position, max_shares_by_risk * entry)

            return position_size

        except Exception as e:
            print(f"❌ Position sizing error: {e}")
            return 0

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
