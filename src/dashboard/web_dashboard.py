"""
V5.5 ULTRA - Real-time Performance Dashboard
Flask web application for monitoring portfolio performance
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)


class PerformanceDashboard:
    """
    Real-time web dashboard for portfolio monitoring

    Features:
    - Live portfolio value and P&L
    - Current positions with real-time prices
    - Strategy performance comparison
    - Recent trade history
    - Risk metrics and analytics
    - Chart visualizations
    """

    def __init__(self, portfolio_manager, market_data_fetcher):
        self.portfolio_manager = portfolio_manager
        self.market_data = market_data_fetcher
        self.port = 5000

    def start_server(self, host='0.0.0.0', port=5000, debug=False):
        """Start the dashboard server"""
        self.port = port
        logger.info(f"🚀 Starting dashboard server at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug, use_reloader=False)

    def get_dashboard_data(self) -> dict:
        """Compile all data for the dashboard"""
        pm = self.portfolio_manager

        # Portfolio overview
        total_value = pm.capital
        invested = 0
        unrealized_pnl = 0
        unrealized_pnl_pct = 0

        positions_data = []

        # Get current position values
        for symbol, pos in pm.positions.items():
            try:
                current_price = self.market_data.get_current_price(symbol)
                quantity = pos['quantity']
                entry_price = pos['entry_price']

                current_value = current_price * quantity
                invested += entry_price * quantity
                position_pnl = (current_price - entry_price) * quantity
                position_pnl_pct = (current_price - entry_price) / entry_price * 100

                unrealized_pnl += position_pnl

                positions_data.append({
                    'symbol': symbol,
                    'strategy': pos['strategy'],
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'quantity': quantity,
                    'invested': entry_price * quantity,
                    'current_value': current_value,
                    'pnl': position_pnl,
                    'pnl_pct': position_pnl_pct,
                    'entry_date': pos['entry_date'],
                    'days_held': (datetime.now() - datetime.fromisoformat(pos['entry_date'])).days
                })

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")

        total_value = pm.capital + invested + unrealized_pnl
        if invested > 0:
            unrealized_pnl_pct = (unrealized_pnl / invested) * 100

        # Strategy statistics
        strategy_stats = []
        for strategy, stats in pm.strategy_stats.items():
            total_trades = stats['wins'] + stats['losses']
            win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = stats['pnl'] / total_trades if total_trades > 0 else 0

            strategy_stats.append({
                'name': strategy,
                'trades': total_trades,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': win_rate,
                'total_pnl': stats['pnl'],
                'avg_pnl': avg_pnl
            })

        # Recent trades (last 20)
        recent_trades = sorted(
            pm.trade_history,
            key=lambda x: x.get('exit_date', x.get('entry_date', '')),
            reverse=True
        )[:20]

        # Calculate daily P&L
        today = datetime.now().date().isoformat()
        daily_pnl = sum(
            trade['pnl']
            for trade in pm.trade_history
            if trade.get('exit_date', '').startswith(today)
        )

        # Risk metrics
        risk_metrics = self._calculate_risk_metrics(pm)

        return {
            'overview': {
                'total_value': total_value,
                'capital': pm.capital,
                'invested': invested,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'daily_pnl': daily_pnl,
                'total_positions': len(pm.positions),
                'last_updated': datetime.now().isoformat()
            },
            'positions': positions_data,
            'strategy_stats': strategy_stats,
            'recent_trades': recent_trades,
            'risk_metrics': risk_metrics
        }

    def _calculate_risk_metrics(self, pm) -> dict:
        """Calculate portfolio risk metrics"""
        if not pm.trade_history:
            return {
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        # Calculate returns
        returns = [trade['pnl'] / trade['entry_price'] / trade['quantity']
                  for trade in pm.trade_history if 'pnl' in trade]

        if not returns:
            return {'max_drawdown': 0, 'sharpe_ratio': 0, 'win_rate': 0}

        # Max drawdown
        cumulative = [sum(returns[:i+1]) for i in range(len(returns))]
        running_max = [max(cumulative[:i+1]) for i in range(len(cumulative))]
        drawdowns = [cumulative[i] - running_max[i] for i in range(len(cumulative))]
        max_drawdown = min(drawdowns) if drawdowns else 0

        # Sharpe ratio (assuming risk-free rate = 5%)
        import numpy as np
        returns_array = np.array(returns)
        sharpe = (np.mean(returns_array) - 0.05/252) / np.std(returns_array) * np.sqrt(252) if len(returns_array) > 1 else 0

        # Win rate and profit factor
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]

        win_rate = len(wins) / len(returns) * 100 if returns else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 0

        return {
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'avg_win': avg_win * 100,
            'avg_loss': avg_loss * 100,
            'profit_factor': profit_factor
        }


# Flask Routes

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    try:
        data = dashboard_instance.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio')
def api_portfolio():
    """API endpoint for portfolio overview"""
    try:
        data = dashboard_instance.get_dashboard_data()
        return jsonify(data['overview'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions')
def api_positions():
    """API endpoint for current positions"""
    try:
        data = dashboard_instance.get_dashboard_data()
        return jsonify(data['positions'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategy_performance')
def api_strategy_performance():
    """API endpoint for strategy statistics"""
    try:
        data = dashboard_instance.get_dashboard_data()
        return jsonify(data['strategy_stats'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades')
def api_trades():
    """API endpoint for recent trades"""
    try:
        data = dashboard_instance.get_dashboard_data()
        return jsonify(data['recent_trades'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Global dashboard instance (set by main application)
dashboard_instance = None


def init_dashboard(portfolio_manager, market_data_fetcher):
    """Initialize dashboard with portfolio manager"""
    global dashboard_instance
    dashboard_instance = PerformanceDashboard(portfolio_manager, market_data_fetcher)
    return dashboard_instance
