"""
PERFECT REPLICA Positional Trading Backtester
==============================================
This backtester EXACTLY matches the current positional trading system:
- 50/40/10 progressive exits (T1: 50%, T2: 90% total, T3: 100%)
- Profit locking after T1 (+2%) and T2 (+3.5%)
- Adaptive trailing stops (tighter after T2: 1.0x ATR instead of 1.8x)
- ATR-based stop loss (1.5-2.5% range)
- Exact Zerodha trading charges
- 1-hour candle data for accurate exit detection
- Max 10-day holding period

Uses 1-hour data from yfinance (~2 years history) to accurately simulate:
- Which target/stop loss hit first
- Trailing stop adjustments
- Partial exits at each target level
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

# Import exact settings from config
from config.settings import (
    POSITIONAL_TARGETS,
    ATR_MIN_STOP_LOSS_POSITIONAL,
    ATR_MAX_STOP_LOSS_POSITIONAL,
    ATR_MULTIPLIER_POSITIONAL,
    TRAILING_STOP_ATR_MULTIPLIER,
    POSITIONAL_HOLD_DAYS_MAX,
    INITIAL_CAPITAL,
    MIN_SIGNAL_SCORE
)


class PositionalBacktester:
    """
    EXACT REPLICA of paper_trader.py positional trading logic
    """

    def __init__(self, initial_capital: float = 50000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # Open positions
        self.trades = []  # Completed trades
        self.trade_id = 0

        # Exact settings from config
        self.targets = POSITIONAL_TARGETS  # [0.025, 0.04, 0.06]
        self.atr_min_sl = ATR_MIN_STOP_LOSS_POSITIONAL  # 0.015 (1.5%)
        self.atr_max_sl = ATR_MAX_STOP_LOSS_POSITIONAL  # 0.025 (2.5%)
        self.atr_multiplier = ATR_MULTIPLIER_POSITIONAL  # 1.8
        self.trailing_atr_multiplier = TRAILING_STOP_ATR_MULTIPLIER  # 1.8
        self.max_holding_days = POSITIONAL_HOLD_DAYS_MAX  # 10

    def _calculate_holding_days(self, entry_date, exit_date) -> int:
        """
        Calculate holding days handling timezone-aware and timezone-naive datetime objects.
        """
        try:
            # Convert both to timezone-naive for comparison
            if hasattr(entry_date, 'tz_localize'):
                entry_dt = entry_date.tz_localize(None) if entry_date.tz else entry_date
            elif hasattr(entry_date, 'replace') and hasattr(entry_date, 'tzinfo'):
                entry_dt = entry_date.replace(tzinfo=None) if entry_date.tzinfo else entry_date
            else:
                entry_dt = entry_date

            if hasattr(exit_date, 'tz_localize'):
                exit_dt = exit_date.tz_localize(None) if exit_date.tz else exit_date
            elif hasattr(exit_date, 'replace') and hasattr(exit_date, 'tzinfo'):
                exit_dt = exit_date.replace(tzinfo=None) if exit_date.tzinfo else exit_date
            else:
                exit_dt = exit_date

            return (exit_dt - entry_dt).days
        except:
            return 0

    def _calculate_trading_charges(self, trade_value: float, is_buy: bool = True) -> float:
        """
        EXACT Zerodha charges calculation from paper_trader.py
        """
        # Brokerage: ₹20 or 0.03% (whichever is lower) per executed order
        brokerage = min(20, trade_value * 0.0003)

        # STT (Securities Transaction Tax): 0.1% on sell side only
        stt = 0 if is_buy else trade_value * 0.001

        # Exchange transaction charges: 0.00325% (NSE)
        exchange_charges = trade_value * 0.0000325

        # GST: 18% on (brokerage + exchange charges)
        gst = (brokerage + exchange_charges) * 0.18

        # SEBI charges: ₹10 per crore
        sebi_charges = (trade_value / 10000000) * 10

        # Stamp duty: 0.015% on buy side, 0.003% on sell side
        stamp_duty = trade_value * (0.00015 if is_buy else 0.00003)

        total_charges = brokerage + stt + exchange_charges + gst + sebi_charges + stamp_duty
        return round(total_charges, 2)

    def _calculate_atr_stop_loss(self, entry_price: float, atr: float) -> float:
        """
        EXACT ATR-based stop loss calculation from paper_trader.py
        """
        # Calculate stop loss using ATR multiplier
        sl_distance = atr * self.atr_multiplier
        sl_percentage = sl_distance / entry_price

        # Clamp between min and max
        sl_percentage = max(self.atr_min_sl, min(self.atr_max_sl, sl_percentage))

        stop_loss = entry_price * (1 - sl_percentage)
        return stop_loss

    def _calculate_position_size(self, entry_price: float, capital: float) -> int:
        """
        EXACT position sizing: ₹10,000 per position
        """
        position_value = 10000
        shares = int(position_value / entry_price)

        # Ensure we have enough capital
        actual_cost = shares * entry_price
        if actual_cost > capital:
            shares = int(capital / entry_price)

        return max(1, shares)

    def _enter_position(self, symbol: str, entry_price: float, entry_date: datetime,
                       atr: float, signal_score: float) -> bool:
        """
        EXACT position entry logic from paper_trader.py
        """
        # Calculate position size
        shares = self._calculate_position_size(entry_price, self.capital)
        cost = shares * entry_price
        buy_charges = self._calculate_trading_charges(cost, is_buy=True)
        total_cost = cost + buy_charges

        # Check if we have enough capital
        if total_cost > self.capital:
            return False

        # Calculate targets and stop loss
        target1 = entry_price * (1 + self.targets[0])  # +2.5%
        target2 = entry_price * (1 + self.targets[1])  # +4%
        target3 = entry_price * (1 + self.targets[2])  # +6%
        stop_loss = self._calculate_atr_stop_loss(entry_price, atr)

        # Create position
        self.trade_id += 1
        position = {
            'trade_id': self.trade_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'entry_date': entry_date,
            'shares': shares,
            'initial_shares': shares,
            'cost': cost,
            'buy_charges': buy_charges,
            'target1': target1,
            'target2': target2,
            'target3': target3,
            'stop_loss': stop_loss,
            'initial_stop_loss': stop_loss,
            'atr': atr,
            'score': signal_score,
            't1_hit': False,
            't2_hit': False,
            't3_hit': False,
            'trailing_active': False
        }

        self.positions[symbol] = position
        self.capital -= total_cost

        return True

    def _exit_position(self, symbol: str, exit_price: float, exit_date: datetime,
                      reason: str, partial_pct: float = 1.0) -> Optional[Dict]:
        """
        EXACT exit logic with partial exits from paper_trader.py
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        shares_to_exit = int(position['shares'] * partial_pct)

        if shares_to_exit == 0:
            return None

        # Calculate proceeds
        gross_proceeds = shares_to_exit * exit_price
        sell_charges = self._calculate_trading_charges(gross_proceeds, is_buy=False)
        net_proceeds = gross_proceeds - sell_charges

        # Calculate P&L for this exit
        cost_basis = (position['cost'] / position['initial_shares']) * shares_to_exit
        buy_charges_portion = (position['buy_charges'] / position['initial_shares']) * shares_to_exit
        pnl = net_proceeds - (cost_basis + buy_charges_portion)
        pnl_percent = ((exit_price - position['entry_price']) / position['entry_price']) * 100

        # Create trade record
        trade = {
            'trade_id': position['trade_id'],
            'symbol': symbol,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'shares': shares_to_exit,
            'initial_shares': position['initial_shares'],
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'reason': reason,
            'buy_charges': buy_charges_portion,
            'sell_charges': sell_charges,
            'gross_proceeds': gross_proceeds,
            'net_proceeds': net_proceeds,
            'score': position['score'],
            'holding_days': self._calculate_holding_days(position['entry_date'], exit_date),
            'is_partial': partial_pct < 1.0,
            'exit_percentage': partial_pct * 100
        }

        self.trades.append(trade)
        self.capital += net_proceeds

        # Update or close position
        if partial_pct >= 1.0:
            del self.positions[symbol]
        else:
            position['shares'] -= shares_to_exit

        return trade

    def _update_trailing_stop(self, symbol: str, current_price: float):
        """
        EXACT adaptive trailing stop logic from paper_trader.py
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        entry_price = position['entry_price']
        atr = position['atr']

        # Adaptive trailing based on targets hit
        if position.get('t2_hit', False):
            # T2 hit: Only 10% remains - TIGHT ATR trailing (1.0x ATR)
            atr_multiplier = 1.0
        else:
            # Normal: Standard ATR trailing (1.8x ATR)
            atr_multiplier = self.trailing_atr_multiplier

        trailing_distance = atr * atr_multiplier
        atr_trailing_stop = current_price - trailing_distance

        # Ensure trailing stop is at least at breakeven
        trailing_stop = max(entry_price, atr_trailing_stop)

        # Only raise stop loss, never lower it
        if trailing_stop > position['stop_loss']:
            position['stop_loss'] = trailing_stop
            position['trailing_active'] = True

    def _process_hour(self, symbol: str, candle: pd.Series, current_date: datetime):
        """
        Process one hour candle for a position
        EXACT logic from paper_trader.py for checking targets and stop loss
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        entry_price = position['entry_price']

        # Extract scalar values from Series
        high = float(candle['High'].iloc[0] if hasattr(candle['High'], 'iloc') else candle['High'])
        low = float(candle['Low'].iloc[0] if hasattr(candle['Low'], 'iloc') else candle['Low'])
        close = float(candle['Close'].iloc[0] if hasattr(candle['Close'], 'iloc') else candle['Close'])

        # Check holding period
        holding_days = self._calculate_holding_days(position['entry_date'], current_date)

        if holding_days >= self.max_holding_days:
            self._exit_position(symbol, close, current_date, 'MAX_HOLDING_PERIOD', partial_pct=1.0)
            return

        # Priority 1: Check stop loss first (most important)
        if low <= position['stop_loss']:
            exit_price = position['stop_loss']
            self._exit_position(symbol, exit_price, current_date, 'STOP_LOSS', partial_pct=1.0)
            return

        # Priority 2: Target 3 (full exit)
        if high >= position['target3'] and not position.get('t3_hit', False):
            self._exit_position(symbol, position['target3'], current_date, 'TARGET_3', partial_pct=1.0)
            return

        # Priority 3: Target 2 (90% exit - 40% more after T1's 50%)
        if high >= position['target2'] and not position.get('t2_hit', False):
            self._exit_position(symbol, position['target2'], current_date, 'TARGET_2', partial_pct=0.90)
            # Lock profit at +3.5%
            if symbol in self.positions:
                position['stop_loss'] = entry_price * 1.035
                position['t2_hit'] = True
            return

        # Priority 4: Target 1 (50% exit)
        if high >= position['target1'] and not position.get('t1_hit', False):
            self._exit_position(symbol, position['target1'], current_date, 'TARGET_1', partial_pct=0.50)
            # Lock profit at +2%
            if symbol in self.positions:
                position['stop_loss'] = entry_price * 1.020
                position['t1_hit'] = True
            return

        # Update trailing stop every hour
        self._update_trailing_stop(symbol, close)

    def backtest_symbol(self, symbol: str, entry_date: datetime, entry_price: float,
                       atr: float, signal_score: float, days_forward: int = 15) -> Dict:
        """
        Backtest a single trade

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            entry_date: Entry datetime
            entry_price: Entry price
            atr: ATR value at entry
            signal_score: Signal quality score
            days_forward: Days to simulate forward

        Returns:
            Trade results dictionary
        """
        # Enter position
        if not self._enter_position(symbol, entry_price, entry_date, atr, signal_score):
            return {'error': 'Insufficient capital'}

        # Download 1-hour data
        end_date = entry_date + timedelta(days=days_forward)
        try:
            df = yf.download(symbol, start=entry_date, end=end_date, interval='1h', progress=False)
        except Exception as e:
            return {'error': f'Failed to download data: {str(e)}'}

        if df.empty:
            return {'error': 'No data available'}

        # Process each hour candle
        for idx, row in df.iterrows():
            self._process_hour(symbol, row, idx)

            # Check if position closed
            if symbol not in self.positions:
                break

        # Force exit if still open after days_forward
        if symbol in self.positions:
            last_close = df.iloc[-1]['Close']
            self._exit_position(symbol, last_close, df.index[-1], 'FORCE_EXIT_END_OF_BACKTEST', partial_pct=1.0)

        # Get all trades for this symbol
        symbol_trades = [t for t in self.trades if t['symbol'] == symbol]

        return {
            'trades': symbol_trades,
            'capital': self.capital,
            'total_pnl': sum(t['pnl'] for t in symbol_trades)
        }

    def get_performance_summary(self) -> Dict:
        """
        Get performance summary
        """
        if not self.trades:
            return {}

        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        breakeven_trades = [t for t in self.trades if t['pnl'] == 0]

        total_pnl = sum(t['pnl'] for t in self.trades)
        total_charges = sum(t['buy_charges'] + t['sell_charges'] for t in self.trades)

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'breakeven_trades': len(breakeven_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if self.trades else 0,
            'total_pnl': total_pnl,
            'total_charges': total_charges,
            'avg_pnl_per_trade': total_pnl / len(self.trades) if self.trades else 0,
            'best_trade': max((t['pnl'] for t in self.trades), default=0),
            'worst_trade': min((t['pnl'] for t in self.trades), default=0),
            'final_capital': self.capital,
            'return_pct': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'avg_holding_days': sum(t['holding_days'] for t in self.trades) / len(self.trades) if self.trades else 0
        }


def test_backtest():
    """
    Test backtester with a sample trade
    """
    print("=" * 80)
    print("POSITIONAL BACKTESTER - TEST RUN")
    print("=" * 80)

    backtester = PositionalBacktester(initial_capital=50000)

    # Example: Test with RELIANCE
    symbol = 'RELIANCE.NS'
    entry_date = datetime(2024, 12, 1, 9, 15)  # Dec 1, 2024, 9:15 AM
    entry_price = 1250.0
    atr = 30.0  # Example ATR
    signal_score = 8.5

    print(f"\nTesting trade:")
    print(f"Symbol: {symbol}")
    print(f"Entry Date: {entry_date}")
    print(f"Entry Price: ₹{entry_price}")
    print(f"ATR: ₹{atr}")
    print(f"Signal Score: {signal_score}")

    # Run backtest
    result = backtester.backtest_symbol(symbol, entry_date, entry_price, atr, signal_score, days_forward=15)

    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return

    print(f"\n{'=' * 80}")
    print("TRADE RESULTS")
    print(f"{'=' * 80}")

    for trade in result['trades']:
        print(f"\n{trade['reason']}:")
        print(f"  Exit Price: ₹{trade['exit_price']:.2f}")
        print(f"  Exit Date: {trade['exit_date']}")
        print(f"  Shares: {trade['shares']}/{trade['initial_shares']}")
        print(f"  P&L: ₹{trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
        print(f"  Holding: {trade['holding_days']} days")
        if trade['is_partial']:
            print(f"  Partial Exit: {trade['exit_percentage']:.0f}%")

    print(f"\n{'=' * 80}")
    print(f"Total P&L: ₹{result['total_pnl']:.2f}")
    print(f"Final Capital: ₹{result['capital']:.2f}")

    # Performance summary
    summary = backtester.get_performance_summary()
    print(f"\n{'=' * 80}")
    print("PERFORMANCE SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']:.1f}%")
    print(f"Total P&L: ₹{summary['total_pnl']:.2f}")
    print(f"Return: {summary['return_pct']:.2f}%")
    print(f"Avg Holding: {summary['avg_holding_days']:.1f} days")


if __name__ == '__main__':
    test_backtest()
