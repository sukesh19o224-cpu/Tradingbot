"""
V5.5 ULTRA - Advanced Analytics
Comprehensive performance analysis and reporting
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """
    Advanced performance analytics

    Features:
    - Maximum drawdown calculation
    - Sharpe/Sortino ratios
    - Trade analysis (best/worst trades)
    - Monthly performance reports
    - Risk metrics
    - Performance attribution
    """

    def __init__(self, portfolio_manager):
        self.pm = portfolio_manager

    def calculate_drawdown(self) -> Dict:
        """Calculate maximum drawdown and current drawdown"""
        if not self.pm.trade_history:
            return {
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'current_drawdown': 0,
                'current_drawdown_pct': 0,
                'recovery_needed': 0
            }

        # Build equity curve
        equity_curve = [self.pm.capital]
        current_equity = self.pm.capital

        for trade in sorted(self.pm.trade_history, key=lambda x: x.get('exit_date', '')):
            current_equity += trade.get('pnl', 0)
            equity_curve.append(current_equity)

        # Calculate drawdown
        peak = equity_curve[0]
        max_dd = 0
        max_dd_pct = 0

        for value in equity_curve:
            if value > peak:
                peak = value

            dd = peak - value
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        # Current drawdown
        current_peak = max(equity_curve)
        current_value = equity_curve[-1]
        current_dd = current_peak - current_value
        current_dd_pct = (current_dd / current_peak * 100) if current_peak > 0 else 0

        # Recovery needed
        recovery_needed_pct = (current_peak / current_value - 1) * 100 if current_value > 0 else 0

        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'current_drawdown': current_dd,
            'current_drawdown_pct': current_dd_pct,
            'recovery_needed': recovery_needed_pct,
            'peak_equity': current_peak,
            'current_equity': current_value
        }

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.05) -> float:
        """Calculate annualized Sharpe ratio"""
        if not self.pm.trade_history:
            return 0.0

        # Daily returns
        returns = []
        for trade in self.pm.trade_history:
            entry_value = trade['entry_price'] * trade['quantity']
            daily_return = trade.get('pnl', 0) / entry_value
            returns.append(daily_return)

        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)

        sharpe = (np.mean(excess_returns) / np.std(returns_array)) * np.sqrt(252)

        return sharpe

    def calculate_sortino_ratio(self, risk_free_rate: float = 0.05) -> float:
        """Calculate Sortino ratio (uses downside deviation only)"""
        if not self.pm.trade_history:
            return 0.0

        returns = []
        for trade in self.pm.trade_history:
            entry_value = trade['entry_price'] * trade['quantity']
            daily_return = trade.get('pnl', 0) / entry_value
            returns.append(daily_return)

        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)

        # Downside deviation (only negative returns)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else np.std(returns_array)

        sortino = (np.mean(excess_returns) / downside_std) * np.sqrt(252) if downside_std > 0 else 0

        return sortino

    def analyze_trades(self) -> Dict:
        """Comprehensive trade analysis"""
        if not self.pm.trade_history:
            return {}

        trades = self.pm.trade_history

        # Basic stats
        total_trades = len(trades)
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]

        # Win/loss analysis
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0

        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0

        largest_win = max([t['pnl'] for t in wins]) if wins else 0
        largest_loss = min([t['pnl'] for t in losses]) if losses else 0

        # Profit factor
        total_wins = sum(t['pnl'] for t in wins)
        total_losses = abs(sum(t['pnl'] for t in losses))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * abs(avg_loss))

        # Average holding period
        holding_periods = []
        for trade in trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                entry = datetime.fromisoformat(trade['entry_date'])
                exit = datetime.fromisoformat(trade['exit_date'])
                holding_periods.append((exit - entry).days)

        avg_holding = np.mean(holding_periods) if holding_periods else 0

        # Best and worst trades
        best_trades = sorted(wins, key=lambda x: x['pnl'], reverse=True)[:5]
        worst_trades = sorted(losses, key=lambda x: x['pnl'])[:5]

        return {
            'total_trades': total_trades,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_holding_period': avg_holding,
            'best_trades': best_trades,
            'worst_trades': worst_trades
        }

    def generate_monthly_report(self, month: int = None, year: int = None) -> Dict:
        """Generate monthly performance report"""
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        # Filter trades for the month
        monthly_trades = [
            t for t in self.pm.trade_history
            if 'exit_date' in t and
            datetime.fromisoformat(t['exit_date']).month == month and
            datetime.fromisoformat(t['exit_date']).year == year
        ]

        if not monthly_trades:
            return {
                'month': f"{year}-{month:02d}",
                'total_trades': 0,
                'total_pnl': 0,
                'message': 'No trades this month'
            }

        # Calculate stats
        total_pnl = sum(t.get('pnl', 0) for t in monthly_trades)
        wins = sum(1 for t in monthly_trades if t.get('pnl', 0) > 0)
        win_rate = (wins / len(monthly_trades) * 100)

        # Strategy breakdown
        strategy_pnl = {}
        for trade in monthly_trades:
            strategy = trade.get('strategy', 'UNKNOWN')
            strategy_pnl[strategy] = strategy_pnl.get(strategy, 0) + trade.get('pnl', 0)

        return {
            'month': f"{year}-{month:02d}",
            'total_trades': len(monthly_trades),
            'total_pnl': total_pnl,
            'wins': wins,
            'losses': len(monthly_trades) - wins,
            'win_rate': win_rate,
            'strategy_breakdown': strategy_pnl,
            'avg_pnl_per_trade': total_pnl / len(monthly_trades)
        }

    def calculate_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics"""
        return {
            'drawdown': self.calculate_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'value_at_risk_95': self._calculate_var(0.95),
            'value_at_risk_99': self._calculate_var(0.99),
            'calmar_ratio': self._calculate_calmar_ratio()
        }

    def _calculate_var(self, confidence: float) -> float:
        """Calculate Value at Risk"""
        if not self.pm.trade_history:
            return 0.0

        returns = [
            t.get('pnl', 0) / (t['entry_price'] * t['quantity'])
            for t in self.pm.trade_history
        ]

        if not returns:
            return 0.0

        var = np.percentile(returns, (1 - confidence) * 100)
        return var

    def _calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        dd = self.calculate_drawdown()
        max_dd_pct = dd['max_drawdown_pct']

        if max_dd_pct == 0:
            return 0.0

        # Annualized return
        if self.pm.trade_history:
            total_return = sum(t.get('pnl', 0) for t in self.pm.trade_history)
            days = (datetime.now() - datetime.fromisoformat(
                self.pm.trade_history[0].get('entry_date', datetime.now().isoformat())
            )).days

            if days > 0:
                annual_return_pct = (total_return / self.pm.capital) * (365 / days) * 100
                return annual_return_pct / max_dd_pct

        return 0.0

    def generate_comprehensive_report(self) -> str:
        """Generate full analytics report"""
        trade_analysis = self.analyze_trades()
        risk_metrics = self.calculate_risk_metrics()
        monthly = self.generate_monthly_report()

        report = f"""
╔════════════════════════════════════════════════════════════╗
║           ADVANCED ANALYTICS REPORT - V5.5 ULTRA           ║
╚════════════════════════════════════════════════════════════╝

📊 TRADE ANALYSIS
─────────────────────────────────────────────────────────────
Total Trades: {trade_analysis.get('total_trades', 0)}
Wins: {trade_analysis.get('wins', 0)} | Losses: {trade_analysis.get('losses', 0)}
Win Rate: {trade_analysis.get('win_rate', 0):.2f}%

Average Win: ₹{trade_analysis.get('avg_win', 0):,.2f}
Average Loss: ₹{trade_analysis.get('avg_loss', 0):,.2f}
Largest Win: ₹{trade_analysis.get('largest_win', 0):,.2f}
Largest Loss: ₹{trade_analysis.get('largest_loss', 0):,.2f}

Profit Factor: {trade_analysis.get('profit_factor', 0):.2f}
Expectancy: ₹{trade_analysis.get('expectancy', 0):,.2f}
Avg Holding Period: {trade_analysis.get('avg_holding_period', 0):.1f} days

📉 RISK METRICS
─────────────────────────────────────────────────────────────
Max Drawdown: {risk_metrics['drawdown']['max_drawdown_pct']:.2f}%
Current Drawdown: {risk_metrics['drawdown']['current_drawdown_pct']:.2f}%
Recovery Needed: {risk_metrics['drawdown']['recovery_needed']:.2f}%

Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}
Sortino Ratio: {risk_metrics['sortino_ratio']:.2f}
Calmar Ratio: {risk_metrics['calmar_ratio']:.2f}

VaR (95%): {risk_metrics['value_at_risk_95']*100:.2f}%
VaR (99%): {risk_metrics['value_at_risk_99']*100:.2f}%

📅 THIS MONTH ({monthly['month']})
─────────────────────────────────────────────────────────────
Trades: {monthly.get('total_trades', 0)}
P&L: ₹{monthly.get('total_pnl', 0):,.2f}
Win Rate: {monthly.get('win_rate', 0):.1f}%

════════════════════════════════════════════════════════════
        """

        return report
