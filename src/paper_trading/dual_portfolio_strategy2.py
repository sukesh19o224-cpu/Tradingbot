"""
💼 Dual Portfolio Manager for Strategy 2
Manages both swing and positional trading portfolios with custom file paths
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from src.paper_trading.paper_trader import PaperTrader
import yfinance as yf


class DualPortfolioStrategy2:
    """
    Manages two separate portfolios for Strategy 2:
    - Swing Trading Portfolio (50% capital) - ULTRA STRICT
    - Positional Trading Portfolio (50% capital) - VERY STRICT
    """

    def __init__(self, swing_file: str, positional_file: str, initial_capital: float = 100000):
        """
        Initialize dual portfolio system with custom file paths

        Args:
            swing_file: Path to swing portfolio JSON file
            positional_file: Path to positional portfolio JSON file
            initial_capital: Total capital to split between portfolios
        """
        # Split capital: 50% swing, 50% positional
        swing_capital = initial_capital * 0.50
        positional_capital = initial_capital * 0.50

        # Create two separate portfolios with custom file paths
        self.swing_portfolio = PaperTrader(
            capital=swing_capital,
            data_file=swing_file.replace('_portfolio.json', '_trades.json'),
            portfolio_file=swing_file
        )

        self.positional_portfolio = PaperTrader(
            capital=positional_capital,
            data_file=positional_file.replace('_portfolio.json', '_trades.json'),
            portfolio_file=positional_file
        )

        self.total_initial_capital = initial_capital

        print(f"💼 STRATEGY 2 - 50/50 Dual Portfolio Initialized:")
        print(f"   🔥 Swing Portfolio: ₹{swing_capital:,.0f} (50%) - Score ≥9.0, ADX ≥35")
        print(f"   📈 Positional Portfolio: ₹{positional_capital:,.0f} (50%) - Score ≥8.5, ADX ≥30")
        print(f"   💰 Total Capital: ₹{initial_capital:,.0f} • Max 5 positions per portfolio")

    def execute_swing_signal(self, signal: Dict) -> bool:
        """Execute swing trading signal"""
        symbol = signal['symbol']
        
        # Check cross-portfolio duplicates
        if symbol in self.positional_portfolio.positions:
            print(f"⚠️ {symbol} already in positional portfolio, skipping swing signal")
            return False

        signal['strategy'] = 'swing'
        return self.swing_portfolio.execute_signal(signal)

    def execute_positional_signal(self, signal: Dict) -> bool:
        """Execute positional trading signal"""
        symbol = signal['symbol']
        
        # Check cross-portfolio duplicates
        if symbol in self.swing_portfolio.positions:
            print(f"⚠️ {symbol} already in swing portfolio, skipping positional signal")
            return False

        signal['strategy'] = 'positional'
        return self.positional_portfolio.execute_signal(signal)

    def monitor_and_update_swing_positions(self) -> bool:
        """Monitor and update swing positions"""
        try:
            # Get current prices for all swing positions
            current_prices = {}
            for symbol in self.swing_portfolio.positions.keys():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='1d', interval='1m')
                    if not data.empty:
                        current_prices[symbol] = data['Close'].iloc[-1]
                except:
                    continue
            
            if current_prices:
                exits = self.swing_portfolio.monitor_positions(current_prices)
                return len(exits) > 0
            return False
        except Exception as e:
            print(f"❌ Error monitoring swing positions: {e}")
            return False

    def monitor_and_update_positional_positions(self) -> bool:
        """Monitor and update positional positions"""
        try:
            # Get current prices for all positional positions
            current_prices = {}
            for symbol in self.positional_portfolio.positions.keys():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='1d', interval='1m')
                    if not data.empty:
                        current_prices[symbol] = data['Close'].iloc[-1]
                except:
                    continue
            
            if current_prices:
                exits = self.positional_portfolio.monitor_positions(current_prices)
                return len(exits) > 0
            return False
        except Exception as e:
            print(f"❌ Error monitoring positional positions: {e}")
            return False

    def get_swing_portfolio_stats(self) -> Dict:
        """Get swing portfolio statistics"""
        stats = self.swing_portfolio.get_summary()
        stats['portfolio_type'] = 'SWING'
        return stats

    def get_positional_portfolio_stats(self) -> Dict:
        """Get positional portfolio statistics"""
        stats = self.positional_portfolio.get_summary()
        stats['portfolio_type'] = 'POSITIONAL'
        return stats

    def get_combined_stats(self) -> Dict:
        """Get combined statistics from both portfolios"""
        swing_stats = self.get_swing_portfolio_stats()
        pos_stats = self.get_positional_portfolio_stats()

        total_pnl = swing_stats['total_pnl'] + pos_stats['total_pnl']
        total_pnl_pct = (total_pnl / self.total_initial_capital) * 100

        return {
            'total_capital': self.total_initial_capital,
            'swing': swing_stats,
            'positional': pos_stats,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'combined_win_rate': (
                (swing_stats['total_trades'] * swing_stats.get('win_rate', 0) +
                 pos_stats['total_trades'] * pos_stats.get('win_rate', 0)) /
                max(swing_stats['total_trades'] + pos_stats['total_trades'], 1)
            )
        }
