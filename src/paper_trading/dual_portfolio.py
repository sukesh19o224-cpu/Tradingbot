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
from config.settings import INITIAL_CAPITAL, SWING_CAPITAL, MAX_POSITIONS, MAX_POSITIONS_SWING


class DualPortfolio:
    """
    Manages two separate portfolios:
    - Positional Trading Portfolio (₹50K) - Real money, balanced strategies
    - Swing Trading Portfolio (₹25K) - Paper test, A+ only
    """

    def __init__(self, positional_capital: float = INITIAL_CAPITAL, swing_capital: float = SWING_CAPITAL):
        """
        Initialize dual portfolio system

        Args:
            positional_capital: Capital for positional portfolio (default: ₹50,000)
            swing_capital: Capital for swing portfolio (default: ₹25,000)
        """
        # Use FIXED allocations from settings (not percentages)
        # This allows independent scaling of each portfolio

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

        self.total_initial_capital = positional_capital + swing_capital

        print(f"💼 INTERMEDIATE Positional Strategy - Dual Portfolio Initialized:")
        print(f"   📈 Positional Portfolio (MAIN): ₹{positional_capital:,.0f} (70%) - 5-14 days, targets 5/10/15%")
        print(f"   🔥 Swing Portfolio (STRICT): ₹{swing_capital:,.0f} (30%) - Score ≥8.0, ADX ≥30")
        print(f"   💰 Total Capital: ₹{self.total_initial_capital:,.0f} • Max {MAX_POSITIONS}/{MAX_POSITIONS_SWING} positions")

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

    def get_strategy_allocation_status(self) -> Dict:
        """
        Get current allocation status for mean reversion vs momentum

        ADAPTIVE Target: Prefer 1 MR + 5 Momentum, but allow 6 Momentum if no MR available

        Returns:
            Dict with allocation counts and what's needed next
        """
        positions = self.positional_portfolio.positions

        # Count current positions by signal type
        mean_reversion_count = sum(1 for p in positions.values() if p.get('signal_type') == 'MEAN_REVERSION')
        momentum_count = sum(1 for p in positions.values() if p.get('signal_type') == 'MOMENTUM')
        total_count = len(positions)

        # MOMENTUM ONLY: 6 positions, all momentum (no mean reversion)
        target_mr = 0  # No mean reversion
        target_momentum = 6  # All 6 momentum
        max_total = MAX_POSITIONS  # 6

        # Calculate total slots available
        total_slots_available = max_total - total_count

        # Momentum only - simple calculation
        mr_slots_available = 0  # No MR slots
        momentum_slots_available = total_slots_available

        # Priority is always momentum (or full)
        if total_slots_available == 0:
            priority = 'FULL'
        else:
            priority = 'MOMENTUM'

        return {
            'current_mr': mean_reversion_count,
            'current_momentum': momentum_count,
            'current_total': total_count,
            'target_mr': target_mr,
            'target_momentum': target_momentum,
            'max_total': max_total,
            'mr_slots_available': mr_slots_available,
            'momentum_slots_available': momentum_slots_available,
            'total_slots_available': total_slots_available,
            'priority': priority,
            'mr_filled': mean_reversion_count >= target_mr,
            'momentum_filled': momentum_count >= target_momentum,
            'portfolio_full': total_slots_available == 0
        }

    def execute_positional_signals_smart(self, signals: List[Dict]) -> List[bool]:
        """
        Execute positional signals with smart 1:5 allocation (1 MR + 5 Momentum)

        Intelligently fills slots based on current allocation:
        - Prioritize filling momentum up to 5 positions
        - Then fill mean reversion up to 1 position
        - Maintains balance dynamically as positions exit

        Args:
            signals: List of positional signals (mixed MR and Momentum)

        Returns:
            List of execution results (True/False for each signal) - MATCHES INPUT ORDER
        """
        # CRITICAL FIX: Create results dict to map symbol -> execution status
        # This ensures Discord alerts match the executed signals correctly
        execution_map = {signal['symbol']: False for signal in signals}

        # Separate signals by type
        mr_signals = [s for s in signals if s.get('signal_type') == 'MEAN_REVERSION']
        momentum_signals = [s for s in signals if s.get('signal_type') == 'MOMENTUM']

        # Sort each by score (highest first)
        mr_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        momentum_signals.sort(key=lambda x: x.get('score', 0), reverse=True)

        # CRITICAL: Add context flag to ALL signals indicating if MR is available
        # This tells paper_trader whether to reserve the 6th slot or allow 6 momentum
        mr_available = len(mr_signals) > 0
        for signal in signals:
            signal['_mr_signals_available'] = mr_available

        print(f"\n📊 Allocation Status (MOMENTUM ONLY):")
        allocation = self.get_strategy_allocation_status()
        print(f"   Current: {allocation['current_momentum']} Momentum = {allocation['current_total']}/6")
        print(f"   Target: 6 Momentum")
        print(f"   Available: {allocation['momentum_slots_available']} Momentum slots")
        print(f"   Priority: {allocation['priority']}")

        # Execute signals - MOMENTUM ONLY
        executed_count = 0

        # Fill all 6 slots with momentum
        if allocation['momentum_slots_available'] > 0 and momentum_signals:
            slots_to_fill = allocation['momentum_slots_available']
            print(f"\n🎯 Filling {slots_to_fill} MOMENTUM slots...")
            for signal in momentum_signals[:slots_to_fill]:
                symbol = signal['symbol']
                print(f"\n   Attempting to execute {symbol} (MOMENTUM)...")
                if self.execute_positional_signal(signal):
                    executed_count += 1
                    execution_map[signal['symbol']] = True
                    print(f"   ✅ {symbol} executed successfully")
                else:
                    print(f"   ❌ {symbol} execution failed (check logs above)")

                # Update allocation after each execution
                allocation = self.get_strategy_allocation_status()
                if allocation['portfolio_full']:
                    print(f"   Portfolio full (6/6), stopping execution")
                    break

        print(f"\n✅ Smart allocation complete: {executed_count} signals executed")
        final_allocation = self.get_strategy_allocation_status()
        print(f"   Final: {final_allocation['current_mr']} MR + {final_allocation['current_momentum']} Momentum = {final_allocation['current_total']}/6")

        # CRITICAL FIX: Return results in SAME ORDER as input signals
        # This ensures zip() in main_eod_system.py correctly pairs signals with execution status
        results = [execution_map[signal['symbol']] for signal in signals]
        return results

    def monitor_swing_positions(self, current_prices: Dict[str, float]) -> tuple[List[Dict], List[Dict]]:
        """
        Monitor swing trading positions

        Swing trades have tighter stops and quicker exits

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            Tuple of (exit signals, trailing stop activations)
        """
        return self.swing_portfolio.check_exits(current_prices)

    def monitor_positional_positions(self, current_prices: Dict[str, float]) -> tuple[List[Dict], List[Dict]]:
        """
        Monitor positional trading positions

        Positional trades have wider stops and longer holding

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            Tuple of (exit signals, trailing stop activations)
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
        print("💼 INTERMEDIATE POSITIONAL STRATEGY - PORTFOLIO SUMMARY")
        print("="*70)

        print(f"\n📊 COMBINED PERFORMANCE:")
        print(f"   Total Value: ₹{summary['total_portfolio_value']:,.0f}")
        print(f"   Total Return: ₹{summary['total_return']:+,.0f} ({summary['total_return_pct']:+.2f}%)")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Win Rate: {summary['win_rate']:.1f}%")

        print(f"\n📈 POSITIONAL PORTFOLIO (MAIN - 70% Capital):")
        print(f"   Value: ₹{summary['positional']['portfolio_value']:,.0f}")
        print(f"   Return: ₹{summary['positional']['return']:+,.0f} ({summary['positional']['return_pct']:+.2f}%)")
        print(f"   Cash: ₹{summary['positional']['capital']:,.0f}")
        print(f"   Positions: {summary['positional']['positions']}/7 • Holding: {summary['positional']['avg_holding_days']:.1f} days (Target: 5-14)")
        print(f"   Trades: {summary['positional']['trades']} (Win Rate: {summary['positional']['win_rate']:.1f}%)")
        print(f"   Strategy: Score ≥7.0 • Targets: 5%, 10%, 15%")

        print(f"\n🔥 SWING PORTFOLIO (STRICT - 30% Capital):")
        print(f"   Value: ₹{summary['swing']['portfolio_value']:,.0f}")
        print(f"   Return: ₹{summary['swing']['return']:+,.0f} ({summary['swing']['return_pct']:+.2f}%)")
        print(f"   Cash: ₹{summary['swing']['capital']:,.0f}")
        print(f"   Positions: {summary['swing']['positions']}/7 • Holding: {summary['swing']['avg_holding_days']:.1f} days (Max: 10)")
        print(f"   Trades: {summary['swing']['trades']} (Win Rate: {summary['swing']['win_rate']:.1f}%)")
        print(f"   Strategy: Score ≥8.0 • ADX ≥30 • Targets: 2.5%, 5%, 7.5%")

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
