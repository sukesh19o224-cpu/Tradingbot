"""
🧪 MULTI-STRATEGY BACKTESTER V4.0
Test all 3 strategies together
Compare individual vs combined performance
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *
from src.core.multi_strategy_manager import MultiStrategyManager
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.breakout_strategy import BreakoutStrategy


class MultiStrategyBacktester:
    """
    Backtest multi-strategy system
    
    Features:
    - Test each strategy individually
    - Test combined multi-strategy
    - Compare performance
    - Regime-aware testing
    """
    
    def __init__(self, initial_capital=INITIAL_CAPITAL):
        print("\n" + "="*70)
        print("🧪 MULTI-STRATEGY BACKTESTER V4.0")
        print("="*70)
        
        self.initial_capital = initial_capital
        self.multi_strategy_manager = MultiStrategyManager()
        
        # Individual strategies
        self.momentum_strategy = MomentumStrategy()
        self.mean_reversion_strategy = MeanReversionStrategy()
        self.breakout_strategy = BreakoutStrategy()
        
        print("✅ Backtester initialized")
    
    def run_backtest(self, start_date, end_date, test_stocks):
        """
        Run complete backtest
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            test_stocks: List of stock symbols
        
        Returns:
            dict with results
        """
        print(f"\n{'='*70}")
        print(f"🧪 BACKTESTING PERIOD: {start_date} to {end_date}")
        print(f"📊 Testing {len(test_stocks)} stocks")
        print(f"💰 Initial Capital: ₹{self.initial_capital:,.0f}")
        print(f"{'='*70}")
        
        # Test individual strategies
        print("\n1️⃣ Testing MOMENTUM strategy...")
        momentum_results = self._backtest_single_strategy(
            self.momentum_strategy, 
            start_date, 
            end_date, 
            test_stocks
        )
        
        print("\n2️⃣ Testing MEAN REVERSION strategy...")
        mean_rev_results = self._backtest_single_strategy(
            self.mean_reversion_strategy,
            start_date,
            end_date,
            test_stocks
        )
        
        print("\n3️⃣ Testing BREAKOUT strategy...")
        breakout_results = self._backtest_single_strategy(
            self.breakout_strategy,
            start_date,
            end_date,
            test_stocks
        )
        
        # Test multi-strategy
        print("\n4️⃣ Testing MULTI-STRATEGY system...")
        multi_results = self._backtest_multi_strategy(
            start_date,
            end_date,
            test_stocks
        )
        
        # Compare results
        results = {
            'MOMENTUM': momentum_results,
            'MEAN_REVERSION': mean_rev_results,
            'BREAKOUT': breakout_results,
            'MULTI_STRATEGY': multi_results
        }
        
        self._display_comparison(results)
        
        return results
    
    def _backtest_single_strategy(self, strategy, start_date, end_date, test_stocks):
        """Backtest a single strategy"""
        capital = self.initial_capital
        positions = {}
        trades = []
        daily_capital = []
        
        # Convert dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current_date = start
        
        while current_date <= end:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Scan for opportunities
            opportunities = strategy.scan_opportunities(test_stocks)
            
            # Enter new positions (limit 3 per strategy)
            available_capital = capital - sum(p['position_value'] for p in positions.values())
            
            for opp in opportunities[:3]:
                if len(positions) >= 3:
                    break
                
                if opp['symbol'] in positions:
                    continue
                
                # Calculate position
                params = strategy.calculate_position_params(opp, available_capital)
                
                if not params:
                    continue
                
                # Enter position
                positions[opp['symbol']] = {
                    'entry_price': params['entry_price'],
                    'shares': params['shares'],
                    'stop_loss': params['stop_loss'],
                    'target1': params['target1'],
                    'target2': params['target2'],
                    'target3': params.get('target3', params['target2'] * 1.5),
                    'position_value': params['position_value'],
                    'entry_date': current_date,
                    'days_held': 0,
                    'strategy': strategy.name
                }
            
            # Update existing positions
            to_exit = []
            
            for symbol, pos in positions.items():
                # Get current price
                try:
                    ticker = yf.Ticker(f"{symbol}.NS")
                    hist = ticker.history(start=current_date, end=current_date + timedelta(days=1))
                    
                    if hist.empty:
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    pos['days_held'] += 1
                    
                    # Check exits
                    should_exit, reason, exit_price = strategy.check_exit_conditions(
                        pos, current_price, pos['days_held']
                    )
                    
                    if should_exit:
                        # Exit position
                        pnl = (exit_price - pos['entry_price']) * pos['shares']
                        capital += pnl
                        
                        trades.append({
                            'symbol': symbol,
                            'strategy': strategy.name,
                            'entry': pos['entry_price'],
                            'exit': exit_price,
                            'shares': pos['shares'],
                            'pnl': pnl,
                            'pnl_pct': (pnl / pos['position_value']) * 100,
                            'days_held': pos['days_held'],
                            'reason': reason
                        })
                        
                        to_exit.append(symbol)
                
                except Exception as e:
                    continue
            
            # Remove exited positions
            for symbol in to_exit:
                positions.pop(symbol)
            
            # Track capital
            invested = sum(p['position_value'] for p in positions.values())
            daily_capital.append({
                'date': current_date,
                'capital': capital,
                'invested': invested,
                'total': capital + invested
            })
            
            current_date += timedelta(days=1)
        
        # Close remaining positions
        for symbol, pos in positions.items():
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(period='1d')
                if not hist.empty:
                    exit_price = hist['Close'].iloc[-1]
                    pnl = (exit_price - pos['entry_price']) * pos['shares']
                    capital += pnl
                    
                    trades.append({
                        'symbol': symbol,
                        'strategy': strategy.name,
                        'entry': pos['entry_price'],
                        'exit': exit_price,
                        'shares': pos['shares'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / pos['position_value']) * 100,
                        'days_held': pos['days_held'],
                        'reason': 'End of backtest'
                    })
            except:
                pass
        
        # Calculate statistics
        results = self._calculate_statistics(trades, capital, daily_capital)
        results['strategy_name'] = strategy.name
        
        return results
    
    def _backtest_multi_strategy(self, start_date, end_date, test_stocks):
        """Backtest multi-strategy system"""
        capital = self.initial_capital
        positions = {}
        trades = []
        daily_capital = []
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        current_date = start
        
        while current_date <= end:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Multi-strategy scan
            available = capital - sum(p['position_value'] for p in positions.values())
            
            all_opps = self.multi_strategy_manager.scan_all_strategies(
                test_stocks,
                available
            )
            
            # Get combined opportunities
            combined = self.multi_strategy_manager.get_combined_opportunities(
                all_opps,
                max_positions=6
            )
            
            # Enter positions
            for opp in combined:
                if len(positions) >= 6:
                    break
                
                if opp['symbol'] in positions:
                    continue
                
                positions[opp['symbol']] = {
                    'entry_price': opp['entry_price'],
                    'shares': opp['shares'],
                    'stop_loss': opp['stop_loss'],
                    'target1': opp['target1'],
                    'target2': opp['target2'],
                    'target3': opp.get('target3', opp['target2'] * 1.5),
                    'position_value': opp['position_value'],
                    'entry_date': current_date,
                    'days_held': 0,
                    'strategy': opp['strategy']
                }
            
            # Update positions
            to_exit = []
            
            for symbol, pos in positions.items():
                try:
                    ticker = yf.Ticker(f"{symbol}.NS")
                    hist = ticker.history(start=current_date, end=current_date + timedelta(days=1))
                    
                    if hist.empty:
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    pos['days_held'] += 1
                    
                    # Use strategy-specific exit
                    should_exit, reason, exit_price = self.multi_strategy_manager.check_exit_conditions(
                        pos, current_price, pos['days_held']
                    )
                    
                    if should_exit:
                        pnl = (exit_price - pos['entry_price']) * pos['shares']
                        capital += pnl
                        
                        trades.append({
                            'symbol': symbol,
                            'strategy': pos['strategy'],
                            'entry': pos['entry_price'],
                            'exit': exit_price,
                            'shares': pos['shares'],
                            'pnl': pnl,
                            'pnl_pct': (pnl / pos['position_value']) * 100,
                            'days_held': pos['days_held'],
                            'reason': reason
                        })
                        
                        to_exit.append(symbol)
                
                except Exception as e:
                    continue
            
            for symbol in to_exit:
                positions.pop(symbol)
            
            invested = sum(p['position_value'] for p in positions.values())
            daily_capital.append({
                'date': current_date,
                'capital': capital,
                'invested': invested,
                'total': capital + invested
            })
            
            current_date += timedelta(days=1)
        
        # Close remaining
        for symbol, pos in positions.items():
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(period='1d')
                if not hist.empty:
                    exit_price = hist['Close'].iloc[-1]
                    pnl = (exit_price - pos['entry_price']) * pos['shares']
                    capital += pnl
                    
                    trades.append({
                        'symbol': symbol,
                        'strategy': pos['strategy'],
                        'entry': pos['entry_price'],
                        'exit': exit_price,
                        'shares': pos['shares'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / pos['position_value']) * 100,
                        'days_held': pos['days_held'],
                        'reason': 'End of backtest'
                    })
            except:
                pass
        
        results = self._calculate_statistics(trades, capital, daily_capital)
        results['strategy_name'] = 'MULTI_STRATEGY'
        
        return results
    
    def _calculate_statistics(self, trades, final_capital, daily_capital):
        """Calculate backtest statistics"""
        if not trades:
            return {
                'final_capital': final_capital,
                'total_return': 0,
                'total_trades': 0,
                'winners': 0,
                'losers': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0
            }
        
        df = pd.DataFrame(trades)
        
        winners = df[df['pnl'] > 0]
        losers = df[df['pnl'] <= 0]
        
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        win_rate = (len(winners) / len(trades)) * 100 if len(trades) > 0 else 0
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = abs(losers['pnl'].mean()) if len(losers) > 0 else 0
        
        total_profit = winners['pnl'].sum() if len(winners) > 0 else 0
        total_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 1
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # Max drawdown
        if daily_capital:
            cap_series = pd.Series([d['total'] for d in daily_capital])
            running_max = cap_series.cummax()
            drawdown = (cap_series - running_max) / running_max * 100
            max_drawdown = drawdown.min()
        else:
            max_drawdown = 0
        
        return {
            'final_capital': final_capital,
            'total_return': total_return,
            'total_trades': len(trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'trades': trades
        }
    
    def _display_comparison(self, results):
        """Display comparison of all strategies"""
        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS COMPARISON")
        print("="*70)
        
        # Create comparison table
        comparison = []
        
        for name, result in results.items():
            comparison.append({
                'Strategy': name,
                'Return': f"{result['total_return']:.2f}%",
                'Trades': result['total_trades'],
                'Win Rate': f"{result['win_rate']:.1f}%",
                'Profit Factor': f"{result['profit_factor']:.2f}",
                'Max DD': f"{result['max_drawdown']:.2f}%",
                'Final': f"₹{result['final_capital']:,.0f}"
            })
        
        df = pd.DataFrame(comparison)
        print("\n" + df.to_string(index=False))
        
        # Winner
        best = max(results.items(), key=lambda x: x[1]['total_return'])
        
        print(f"\n{'='*70}")
        print(f"🏆 BEST PERFORMER: {best[0]}")
        print(f"   Return: {best[1]['total_return']:.2f}%")
        print(f"   Win Rate: {best[1]['win_rate']:.1f}%")
        print(f"   Profit Factor: {best[1]['profit_factor']:.2f}")
        print(f"{'='*70}")


if __name__ == "__main__":
    print("\n🧪 RUNNING MULTI-STRATEGY BACKTEST\n")
    
    # Test stocks
    test_stocks = [
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 
        'ICICIBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'TATAMOTORS.NS', 'MARUTI.NS',
        'SUNPHARMA.NS', 'TATASTEEL.NS', 'HINDALCO.NS', 'TITAN.NS'
    ]
    
    # Run backtest
    backtester = MultiStrategyBacktester(100000)
    
    results = backtester.run_backtest(
        start_date='2025-09-01',
        end_date='2025-11-01',
        test_stocks=test_stocks
    )
    
    print("\n✅ Backtest complete!")
    print("\n💡 TIP: Multi-strategy should outperform individual strategies")
    print("   by working in different market conditions!")