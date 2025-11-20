"""
V5.5 ULTRA - Paper Trading Mode
Test strategies with fake money before risking real capital
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class PaperPortfolio:
    """
    Paper trading portfolio that mirrors real trading without actual money

    Features:
    - Separate portfolio.json for paper trades
    - Parallel execution with real portfolio
    - Performance comparison
    - Risk-free testing
    - Can copy successful paper trades to real portfolio
    """

    def __init__(self, initial_capital: float = 100000, paper_file='data/paper_portfolio.json'):
        self.paper_file = paper_file
        self.initial_capital = initial_capital

        # Load or initialize paper portfolio
        if os.path.exists(paper_file):
            with open(paper_file, 'r') as f:
                data = json.load(f)
                self.capital = data.get('capital', initial_capital)
                self.positions = data.get('positions', {})
                self.trade_history = data.get('trade_history', [])
                self.strategy_stats = data.get('strategy_stats', self._init_strategy_stats())
                self.start_date = data.get('start_date', datetime.now().isoformat())
        else:
            self.capital = initial_capital
            self.positions = {}
            self.trade_history = []
            self.strategy_stats = self._init_strategy_stats()
            self.start_date = datetime.now().isoformat()
            self._save()

        logger.info(f"📄 Paper Trading initialized - Capital: ₹{self.capital:,.2f}")

    def _init_strategy_stats(self) -> Dict:
        """Initialize strategy statistics"""
        return {
            'MOMENTUM': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'MEAN_REVERSION': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'BREAKOUT': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'POSITIONAL': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        }

    def execute_paper_trade(self, action: str, opportunity: Dict, quantity: int,
                           current_price: float, strategy: str) -> bool:
        """
        Execute a paper trade (buy/sell)

        Args:
            action: 'BUY' or 'SELL'
            opportunity: Trade opportunity dict
            quantity: Number of shares
            current_price: Current stock price
            strategy: Strategy name

        Returns:
            bool: Success/failure
        """
        symbol = opportunity['symbol']

        if action == 'BUY':
            return self._paper_buy(symbol, current_price, quantity, strategy, opportunity)
        elif action == 'SELL':
            return self._paper_sell(symbol, current_price, quantity, opportunity)
        else:
            logger.error(f"Invalid action: {action}")
            return False

    def _paper_buy(self, symbol: str, price: float, quantity: int,
                   strategy: str, opportunity: Dict) -> bool:
        """Execute paper buy order"""
        cost = price * quantity

        if cost > self.capital:
            logger.warning(f"📄 PAPER: Insufficient capital for {symbol} - Need ₹{cost:,.2f}, Have ₹{self.capital:,.2f}")
            return False

        # Execute buy
        self.capital -= cost

        self.positions[symbol] = {
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': price,
            'entry_date': datetime.now().isoformat(),
            'strategy': strategy,
            'stop_loss': opportunity.get('stop_loss', price * 0.95),
            'targets': opportunity.get('targets', []),
            'paper': True
        }

        logger.info(f"📄 PAPER BUY: {symbol} x{quantity} @ ₹{price:.2f} ({strategy}) - Cost: ₹{cost:,.2f}")
        self._save()
        return True

    def _paper_sell(self, symbol: str, price: float, quantity: int, reason: Dict) -> bool:
        """Execute paper sell order"""
        if symbol not in self.positions:
            logger.warning(f"📄 PAPER: No position found for {symbol}")
            return False

        position = self.positions[symbol]

        if quantity > position['quantity']:
            logger.warning(f"📄 PAPER: Selling more than owned - {quantity} > {position['quantity']}")
            return False

        # Calculate P&L
        entry_price = position['entry_price']
        proceeds = price * quantity
        cost = entry_price * quantity
        pnl = proceeds - cost
        pnl_pct = (price - entry_price) / entry_price * 100

        # Update capital
        self.capital += proceeds

        # Update strategy stats
        strategy = position['strategy']
        self.strategy_stats[strategy]['trades'] += 1
        self.strategy_stats[strategy]['pnl'] += pnl

        if pnl > 0:
            self.strategy_stats[strategy]['wins'] += 1
        else:
            self.strategy_stats[strategy]['losses'] += 1

        # Record trade history
        trade_record = {
            'symbol': symbol,
            'strategy': strategy,
            'entry_date': position['entry_date'],
            'entry_price': entry_price,
            'exit_date': datetime.now().isoformat(),
            'exit_price': price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason.get('reason', 'MANUAL'),
            'paper': True
        }

        self.trade_history.append(trade_record)

        # Remove or reduce position
        if quantity == position['quantity']:
            del self.positions[symbol]
        else:
            position['quantity'] -= quantity

        logger.info(f"📄 PAPER SELL: {symbol} x{quantity} @ ₹{price:.2f} - P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)")
        self._save()
        return True

    def get_performance_comparison(self, real_portfolio) -> Dict:
        """
        Compare paper trading performance with real portfolio

        Returns dict with comparison metrics
        """
        # Paper portfolio metrics
        paper_total = self.capital + sum(
            pos['quantity'] * pos['entry_price']
            for pos in self.positions.values()
        )
        paper_return = (paper_total - self.initial_capital) / self.initial_capital * 100

        paper_trades = len(self.trade_history)
        paper_wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        paper_win_rate = (paper_wins / paper_trades * 100) if paper_trades > 0 else 0

        # Real portfolio metrics (if available)
        real_total = 0
        real_return = 0
        real_win_rate = 0

        if real_portfolio:
            real_total = real_portfolio.capital + sum(
                pos['quantity'] * pos['entry_price']
                for pos in real_portfolio.positions.values()
            )
            initial_real = getattr(real_portfolio, 'initial_capital', 100000)
            real_return = (real_total - initial_real) / initial_real * 100

            real_trades = len(real_portfolio.trade_history)
            real_wins = sum(1 for t in real_portfolio.trade_history if t.get('pnl', 0) > 0)
            real_win_rate = (real_wins / real_trades * 100) if real_trades > 0 else 0

        return {
            'paper': {
                'total_value': paper_total,
                'capital': self.capital,
                'return_pct': paper_return,
                'total_trades': paper_trades,
                'win_rate': paper_win_rate,
                'open_positions': len(self.positions)
            },
            'real': {
                'total_value': real_total,
                'capital': real_portfolio.capital if real_portfolio else 0,
                'return_pct': real_return,
                'total_trades': len(real_portfolio.trade_history) if real_portfolio else 0,
                'win_rate': real_win_rate,
                'open_positions': len(real_portfolio.positions) if real_portfolio else 0
            },
            'comparison': {
                'paper_vs_real_return': paper_return - real_return,
                'paper_vs_real_winrate': paper_win_rate - real_win_rate,
                'better_performer': 'PAPER' if paper_return > real_return else 'REAL'
            }
        }

    def reset_paper_portfolio(self, new_capital: float = None):
        """Reset paper portfolio to start fresh"""
        if new_capital:
            self.initial_capital = new_capital

        self.capital = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.strategy_stats = self._init_strategy_stats()
        self.start_date = datetime.now().isoformat()

        logger.info(f"📄 Paper portfolio reset - New capital: ₹{self.capital:,.2f}")
        self._save()

    def _save(self):
        """Save paper portfolio to file"""
        os.makedirs(os.path.dirname(self.paper_file), exist_ok=True)

        data = {
            'capital': self.capital,
            'positions': self.positions,
            'trade_history': self.trade_history,
            'strategy_stats': self.strategy_stats,
            'start_date': self.start_date,
            'last_updated': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'mode': 'PAPER_TRADING'
        }

        with open(self.paper_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_summary(self) -> Dict:
        """Get paper trading summary"""
        total_value = self.capital
        invested = 0

        for pos in self.positions.values():
            invested += pos['entry_price'] * pos['quantity']

        total_value += invested

        total_pnl = sum(t['pnl'] for t in self.trade_history)
        total_trades = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        return {
            'mode': 'PAPER',
            'initial_capital': self.initial_capital,
            'current_capital': self.capital,
            'total_value': total_value,
            'invested': invested,
            'total_pnl': total_pnl,
            'total_return_pct': (total_value - self.initial_capital) / self.initial_capital * 100,
            'total_trades': total_trades,
            'wins': wins,
            'losses': total_trades - wins,
            'win_rate': win_rate,
            'open_positions': len(self.positions),
            'start_date': self.start_date
        }


class PaperTradingManager:
    """
    Manager to run paper trading in parallel with real trading
    """

    def __init__(self, enable_paper_trading: bool = True):
        self.enabled = enable_paper_trading
        self.paper_portfolio = PaperPortfolio() if enable_paper_trading else None

    def should_execute_paper_trade(self, opportunity: Dict) -> bool:
        """Decide if this opportunity should also be paper traded"""
        if not self.enabled:
            return False

        # Paper trade everything that the real system trades
        return True

    def sync_paper_trade(self, action: str, opportunity: Dict, quantity: int,
                        price: float, strategy: str):
        """Execute the same trade in paper portfolio"""
        if not self.enabled:
            return

        self.paper_portfolio.execute_paper_trade(
            action, opportunity, quantity, price, strategy
        )

    def get_comparison_report(self, real_portfolio) -> str:
        """Generate comparison report between paper and real trading"""
        if not self.enabled:
            return "Paper trading disabled"

        comp = self.paper_portfolio.get_performance_comparison(real_portfolio)

        report = f"""
╔══════════════════════════════════════════════════════════╗
║         PAPER vs REAL TRADING COMPARISON                 ║
╚══════════════════════════════════════════════════════════╝

📄 PAPER TRADING:
   Portfolio Value: ₹{comp['paper']['total_value']:,.2f}
   Return: {comp['paper']['return_pct']:+.2f}%
   Win Rate: {comp['paper']['win_rate']:.1f}%
   Trades: {comp['paper']['total_trades']}

💰 REAL TRADING:
   Portfolio Value: ₹{comp['real']['total_value']:,.2f}
   Return: {comp['real']['return_pct']:+.2f}%
   Win Rate: {comp['real']['win_rate']:.1f}%
   Trades: {comp['real']['total_trades']}

📊 COMPARISON:
   Better Performer: {comp['comparison']['better_performer']}
   Return Difference: {comp['comparison']['paper_vs_real_return']:+.2f}%
   Win Rate Difference: {comp['comparison']['paper_vs_real_winrate']:+.2f}%

════════════════════════════════════════════════════════════
        """

        return report
