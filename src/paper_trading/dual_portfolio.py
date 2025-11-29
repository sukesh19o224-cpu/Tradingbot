"""
💼 Dual Portfolio Manager
Manages both swing and positional trading portfolios simultaneously
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from src.paper_trading.paper_trader import PaperTrader
import yfinance as yf


class DualPortfolio:
    """
    Manages two separate portfolios:
    - Swing Trading Portfolio (30% capital) - STRICT quality only
    - Positional Trading Portfolio (70% capital) - Main strategy
    """

    def __init__(self, total_capital: float = 100000):
        """
        Initialize dual portfolio system

        Args:
            total_capital: Total capital to split between portfolios
        """
        # Split capital: 30% swing (STRICT quality only), 70% positional (main strategy)
        swing_capital = total_capital * 0.30
        positional_capital = total_capital * 0.70

        # Create two separate portfolios
        self.swing_portfolio = PaperTrader(
            capital=swing_capital,
            data_file='data/swing_trades.json',
            portfolio_file='data/swing_portfolio.json'
        )

        self.positional_portfolio = PaperTrader(
            capital=positional_capital,
            data_file='data/positional_trades.json',
            portfolio_file='data/positional_portfolio.json'
        )

        self.total_initial_capital = total_capital

        print(f"💼 Dual Portfolio Initialized:")
        print(f"   🔥 Swing Portfolio: ₹{swing_capital:,.0f}")
        print(f"   📈 Positional Portfolio: ₹{positional_capital:,.0f}")
        print(f"   💰 Total Capital: ₹{total_capital:,.0f}")

    def execute_swing_signal(self, signal: Dict) -> bool:
        """
        Execute swing trading signal with smart cross-portfolio management

        Args:
            signal: Swing signal dictionary

        Returns:
            True if executed successfully
        """
        # CRITICAL FIX #2: Check cross-portfolio duplicates
        symbol = signal['symbol']
        if symbol in self.positional_portfolio.positions:
            print(f"⚠️ {symbol} already in positional portfolio, skipping swing signal")
            return False

        # Add strategy tag
        signal['strategy'] = 'swing'

        # Try to execute in swing portfolio
        # Smart replacement will handle capital/position limits automatically
        return self.swing_portfolio.execute_signal(signal)

    def execute_positional_signal(self, signal: Dict) -> bool:
        """
        Execute positional trading signal with smart cross-portfolio management

        Args:
            signal: Positional signal dictionary

        Returns:
            True if executed successfully
        """
        # CRITICAL FIX #2: Check cross-portfolio duplicates
        symbol = signal['symbol']
        if symbol in self.swing_portfolio.positions:
            print(f"⚠️ {symbol} already in swing portfolio, skipping positional signal")
            return False

        # Add strategy tag
        signal['strategy'] = 'positional'

        # Try to execute in positional portfolio
        # Smart replacement will handle capital/position limits automatically
        return self.positional_portfolio.execute_signal(signal)

    def monitor_swing_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Monitor swing trading positions

        Swing trades have tighter stops and quicker exits

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            List of exit signals
        """
        return self.swing_portfolio.check_exits(current_prices)

    def monitor_positional_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Monitor positional trading positions

        Positional trades have wider stops and longer holding

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            List of exit signals
        """
        return self.positional_portfolio.check_exits(current_prices)

    def get_combined_summary(self) -> Dict:
        """
        Get combined summary of both portfolios

        Fetches current market prices for accurate portfolio valuation

        Returns:
            Combined portfolio summary
        """
        # Fetch current prices for all open positions
        current_prices = {}

        # Get prices for swing positions
        for symbol in self.swing_portfolio.positions.keys():
            price = self._get_current_price(symbol)
            if price > 0:
                current_prices[symbol] = price

        # Get prices for positional positions
        for symbol in self.positional_portfolio.positions.keys():
            price = self._get_current_price(symbol)
            if price > 0:
                current_prices[symbol] = price

        # Get summaries with current market prices
        swing_summary = self.swing_portfolio.get_summary(current_prices)
        positional_summary = self.positional_portfolio.get_summary(current_prices)

        # Calculate combined metrics
        total_portfolio_value = swing_summary['portfolio_value'] + positional_summary['portfolio_value']
        total_return = total_portfolio_value - self.total_initial_capital
        total_return_pct = (total_return / self.total_initial_capital) * 100

        # Combine trades
        total_trades = swing_summary['total_trades'] + positional_summary['total_trades']
        winning_trades = swing_summary['winning_trades'] + positional_summary['winning_trades']
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_portfolio_value': total_portfolio_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'win_rate': win_rate,

            # Swing portfolio (30% capital - STRICT quality only)
            'swing': {
                'portfolio_value': swing_summary['portfolio_value'],
                'return': swing_summary['portfolio_value'] - (self.total_initial_capital * 0.30),
                'return_pct': swing_summary['total_return_percent'],
                'capital': swing_summary['capital'],
                'positions': swing_summary['open_positions'],
                'trades': swing_summary['total_trades'],
                'win_rate': swing_summary['win_rate'],
                'avg_holding_days': swing_summary.get('avg_holding_days', 0),
            },

            # Positional portfolio (70% capital - Main strategy)
            'positional': {
                'portfolio_value': positional_summary['portfolio_value'],
                'return': positional_summary['portfolio_value'] - (self.total_initial_capital * 0.70),
                'return_pct': positional_summary['total_return_percent'],
                'capital': positional_summary['capital'],
                'positions': positional_summary['open_positions'],
                'trades': positional_summary['total_trades'],
                'win_rate': positional_summary['win_rate'],
                'avg_holding_days': positional_summary.get('avg_holding_days', 0),
            },

            # Timestamp
            'updated': datetime.now().isoformat(),
        }

    def get_swing_summary(self) -> Dict:
        """Get swing portfolio summary"""
        return self.swing_portfolio.get_summary()

    def get_positional_summary(self) -> Dict:
        """Get positional portfolio summary"""
        return self.positional_portfolio.get_summary()

    def get_all_open_positions(self) -> Dict:
        """
        Get all open positions from both portfolios

        Returns:
            Dict with 'swing' and 'positional' positions
        """
        return {
            'swing': self.swing_portfolio.positions,
            'positional': self.positional_portfolio.positions,
        }

    def save_state(self):
        """Save state of both portfolios"""
        # Both portfolios auto-save, but we can trigger explicit save
        self.swing_portfolio._save_portfolio()
        self.swing_portfolio._save_trades()
        self.positional_portfolio._save_portfolio()
        self.positional_portfolio._save_trades()

    def print_summary(self):
        """Print formatted summary of both portfolios"""
        summary = self.get_combined_summary()

        print("\n" + "="*70)
        print("💼 DUAL PORTFOLIO SUMMARY")
        print("="*70)

        print(f"\n📊 COMBINED PERFORMANCE:")
        print(f"   Total Value: ₹{summary['total_portfolio_value']:,.0f}")
        print(f"   Total Return: ₹{summary['total_return']:+,.0f} ({summary['total_return_pct']:+.2f}%)")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Win Rate: {summary['win_rate']:.1f}%")

        print(f"\n🔥 SWING PORTFOLIO:")
        print(f"   Value: ₹{summary['swing']['portfolio_value']:,.0f}")
        print(f"   Return: ₹{summary['swing']['return']:+,.0f} ({summary['swing']['return_pct']:+.2f}%)")
        print(f"   Cash: ₹{summary['swing']['capital']:,.0f}")
        print(f"   Positions: {summary['swing']['positions']}")
        print(f"   Trades: {summary['swing']['trades']} (Win Rate: {summary['swing']['win_rate']:.1f}%)")
        print(f"   Avg Holding: {summary['swing']['avg_holding_days']:.1f} days")

        print(f"\n📈 POSITIONAL PORTFOLIO:")
        print(f"   Value: ₹{summary['positional']['portfolio_value']:,.0f}")
        print(f"   Return: ₹{summary['positional']['return']:+,.0f} ({summary['positional']['return_pct']:+.2f}%)")
        print(f"   Cash: ₹{summary['positional']['capital']:,.0f}")
        print(f"   Positions: {summary['positional']['positions']}")
        print(f"   Trades: {summary['positional']['trades']} (Win Rate: {summary['positional']['win_rate']:.1f}%)")
        print(f"   Avg Holding: {summary['positional']['avg_holding_days']:.1f} days")

    def _get_current_price(self, symbol: str) -> float:
        """
        Fetch current market price for a symbol

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')

        Returns:
            Current price or 0 if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1d')

            if not data.empty:
                return float(data['Close'].iloc[-1])

            return 0

        except Exception:
            # Silent fail - will use entry price as fallback
            return 0
