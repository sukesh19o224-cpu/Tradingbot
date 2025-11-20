"""
📊 PORTFOLIO COMPARISON - Live Strategy Testing
Run 3 strategies simultaneously and compare performance

Strategy A: EXCELLENT (score ≥ 8.5)
Strategy B: MODERATE+ (score ≥ 8.0)
Strategy C: ALL SIGNALS (score ≥ 7.0)
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd

from config.settings import PAPER_TRADING_CAPITAL


class PortfolioComparison:
    """
    Manage and compare 3 different trading strategies

    Each strategy has its own virtual portfolio with same starting capital
    """

    def __init__(self, initial_capital: float = PAPER_TRADING_CAPITAL):
        self.comparison_file = 'data/portfolio_comparison.json'
        self.initial_capital = initial_capital

        # Load or initialize
        if os.path.exists(self.comparison_file):
            self._load()
        else:
            self._initialize()

    def _initialize(self):
        """Initialize 3 portfolios with same capital"""
        self.portfolios = {
            'EXCELLENT': {
                'name': 'Excellent Signals Only',
                'description': 'Score ≥ 8.5',
                'capital': self.initial_capital,
                'positions': {},
                'trade_history': [],
                'stats': self._init_stats()
            },
            'MODERATE': {
                'name': 'Moderate + Excellent',
                'description': 'Score ≥ 8.0',
                'capital': self.initial_capital,
                'positions': {},
                'trade_history': [],
                'stats': self._init_stats()
            },
            'ALL': {
                'name': 'All Discord Signals',
                'description': 'Score ≥ 7.0 (all alerts)',
                'capital': self.initial_capital,
                'positions': {},
                'trade_history': [],
                'stats': self._init_stats()
            }
        }

        self.start_date = datetime.now().isoformat()
        self.days_running = 0

        self._save()

        print("✅ 3 Virtual Portfolios Initialized!")
        print(f"   Portfolio A: Excellent (≥8.5) - ₹{self.initial_capital:,.0f}")
        print(f"   Portfolio B: Moderate (≥8.0) - ₹{self.initial_capital:,.0f}")
        print(f"   Portfolio C: All Signals (≥7.0) - ₹{self.initial_capital:,.0f}")

    def _init_stats(self) -> Dict:
        """Initialize statistics"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'total_return_pct': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_drawdown': 0
        }

    def process_signal(self, signal: Dict):
        """
        Process signal for each portfolio based on their criteria

        Args:
            signal: Signal from the scanner
        """
        score = signal.get('score', 0)

        # Portfolio A: EXCELLENT (≥8.5)
        if score >= 8.5:
            self._execute_trade('EXCELLENT', signal)

        # Portfolio B: MODERATE (≥8.0)
        if score >= 8.0:
            self._execute_trade('MODERATE', signal)

        # Portfolio C: ALL (≥7.0)
        if score >= 7.0:
            self._execute_trade('ALL', signal)

        self._save()

    def _execute_trade(self, portfolio_name: str, signal: Dict):
        """Execute trade in specific portfolio"""
        portfolio = self.portfolios[portfolio_name]
        symbol = signal['symbol']

        # Check if already holding
        if symbol in portfolio['positions']:
            return

        # Calculate position size (simple: 10% of capital)
        position_value = portfolio['capital'] * 0.10
        entry_price = signal['entry_price']
        shares = int(position_value / entry_price)

        if shares <= 0:
            return

        cost = shares * entry_price

        # Check if enough capital
        if cost > portfolio['capital']:
            return

        # Execute buy
        portfolio['capital'] -= cost

        portfolio['positions'][symbol] = {
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
            'portfolio': portfolio_name
        }

        print(f"   📊 {portfolio_name}: BUY {symbol} x{shares} @ ₹{entry_price:.2f}")

    def check_exits(self, current_prices: Dict[str, float]):
        """Check exits for all portfolios"""
        exits = {
            'EXCELLENT': [],
            'MODERATE': [],
            'ALL': []
        }

        for portfolio_name, portfolio in self.portfolios.items():
            for symbol, position in list(portfolio['positions'].items()):
                current_price = current_prices.get(symbol, 0)

                if current_price == 0:
                    continue

                # Check stop loss or targets
                exit_info = self._check_position_exit(position, current_price)

                if exit_info:
                    # Execute exit
                    self._execute_exit(portfolio_name, symbol, current_price, exit_info['reason'])
                    exits[portfolio_name].append(exit_info)

        self._save()
        return exits

    def _check_position_exit(self, position: Dict, current_price: float) -> Dict:
        """Check if position should be exited"""
        entry_price = position['entry_price']

        # Stop loss
        if current_price <= position['stop_loss']:
            return {
                'symbol': position['symbol'],
                'reason': 'STOP_LOSS',
                'exit_price': current_price
            }

        # Targets
        if current_price >= position['target3']:
            return {
                'symbol': position['symbol'],
                'reason': 'TARGET_3',
                'exit_price': current_price
            }
        elif current_price >= position['target2']:
            # Exit 50% at target 2
            return {
                'symbol': position['symbol'],
                'reason': 'TARGET_2',
                'exit_price': current_price,
                'partial': 0.5
            }

        return None

    def _execute_exit(self, portfolio_name: str, symbol: str, exit_price: float, reason: str):
        """Execute exit for a position"""
        portfolio = self.portfolios[portfolio_name]
        position = portfolio['positions'][symbol]

        entry_price = position['entry_price']
        shares = position['shares']

        proceeds = shares * exit_price
        cost = shares * entry_price
        pnl = proceeds - cost
        pnl_pct = (exit_price - entry_price) / entry_price * 100

        # Update capital
        portfolio['capital'] += proceeds

        # Record trade
        trade_record = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'entry_date': position['entry_date'],
            'exit_date': datetime.now().isoformat(),
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason,
            'portfolio': portfolio_name
        }

        portfolio['trade_history'].append(trade_record)

        # Update stats
        stats = portfolio['stats']
        stats['total_trades'] += 1
        stats['total_pnl'] += pnl

        if pnl > 0:
            stats['winning_trades'] += 1
            if pnl > stats['best_trade']:
                stats['best_trade'] = pnl
        else:
            stats['losing_trades'] += 1
            if pnl < stats['worst_trade']:
                stats['worst_trade'] = pnl

        # Remove position
        del portfolio['positions'][symbol]

        print(f"   📊 {portfolio_name}: EXIT {symbol} @ ₹{exit_price:.2f} - P&L: ₹{pnl:+,.0f}")

    def get_comparison_summary(self, current_prices: Dict[str, float] = None) -> Dict:
        """
        Get comparison summary for all portfolios

        Returns:
            Dict with performance metrics for each portfolio
        """
        if current_prices is None:
            current_prices = {}

        summary = {}

        for portfolio_name, portfolio in self.portfolios.items():
            # Calculate portfolio value
            capital = portfolio['capital']
            invested = 0
            unrealized_pnl = 0

            for symbol, position in portfolio['positions'].items():
                current_price = current_prices.get(symbol, position['entry_price'])
                invested += position['entry_price'] * position['shares']
                unrealized_pnl += (current_price - position['entry_price']) * position['shares']

            total_value = capital + invested + unrealized_pnl

            # Calculate stats
            stats = portfolio['stats']
            total_trades = stats['total_trades']

            if total_trades > 0:
                win_rate = (stats['winning_trades'] / total_trades) * 100

                winning_trades = [t for t in portfolio['trade_history'] if t['pnl'] > 0]
                losing_trades = [t for t in portfolio['trade_history'] if t['pnl'] <= 0]

                avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
                avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
            else:
                win_rate = 0
                avg_win = 0
                avg_loss = 0

            total_return_pct = ((total_value - self.initial_capital) / self.initial_capital) * 100

            summary[portfolio_name] = {
                'name': portfolio['name'],
                'description': portfolio['description'],
                'initial_capital': self.initial_capital,
                'current_capital': capital,
                'invested': invested,
                'unrealized_pnl': unrealized_pnl,
                'total_value': total_value,
                'total_return_pct': total_return_pct,
                'total_pnl': stats['total_pnl'] + unrealized_pnl,
                'total_trades': total_trades,
                'winning_trades': stats['winning_trades'],
                'losing_trades': stats['losing_trades'],
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'best_trade': stats['best_trade'],
                'worst_trade': stats['worst_trade'],
                'open_positions': len(portfolio['positions']),
                'rank': 0  # Will be set below
            }

        # Rank by total return
        sorted_portfolios = sorted(
            summary.items(),
            key=lambda x: x[1]['total_return_pct'],
            reverse=True
        )

        for rank, (name, data) in enumerate(sorted_portfolios, 1):
            summary[name]['rank'] = rank

        return summary

    def reset_all(self):
        """Reset all portfolios"""
        self._initialize()
        print("🗑️ All portfolios reset!")

    def _save(self):
        """Save to file"""
        os.makedirs(os.path.dirname(self.comparison_file), exist_ok=True)

        data = {
            'portfolios': self.portfolios,
            'start_date': self.start_date,
            'days_running': self.days_running,
            'initial_capital': self.initial_capital,
            'last_updated': datetime.now().isoformat()
        }

        with open(self.comparison_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from file"""
        with open(self.comparison_file, 'r') as f:
            data = json.load(f)

        self.portfolios = data['portfolios']
        self.start_date = data['start_date']
        self.days_running = data['days_running']
        self.initial_capital = data['initial_capital']

        print("✅ Loaded existing portfolio comparison")


if __name__ == "__main__":
    # Test
    print("🧪 Testing Portfolio Comparison...")

    comp = PortfolioComparison()

    summary = comp.get_comparison_summary()

    print(f"\n📊 Comparison Summary:")
    for name, data in summary.items():
        print(f"\n{name}: {data['name']}")
        print(f"   Return: {data['total_return_pct']:+.2f}%")
        print(f"   Trades: {data['total_trades']}")
        print(f"   Win Rate: {data['win_rate']:.1f}%")
        print(f"   Rank: #{data['rank']}")
