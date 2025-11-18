"""
📊 PERFORMANCE TRACKER
Track daily returns, calculate metrics, compare with benchmark
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import get_logger
    from src.utils.database import get_database
    logger = get_logger('PerformanceTracker')
except:
    logger = None


class PerformanceTracker:
    """
    Track and analyze trading performance
    Calculates advanced metrics like Sharpe, Sortino, Alpha, Beta
    """
    
    def __init__(self):
        self.daily_returns = []
        self.benchmark_returns = []
        self.daily_values = []
        self.dates = []
        
        self.db = None
        try:
            self.db = get_database()
        except:
            pass
    
    def record_daily_performance(self, date, portfolio_value, benchmark_value=None, 
                                  positions_count=0, trades_taken=0, wins=0, losses=0):
        """
        Record daily performance
        
        Args:
            date: Trading date
            portfolio_value: Current portfolio value
            benchmark_value: Benchmark index value (e.g., NIFTY 50)
            positions_count: Number of open positions
            trades_taken: Trades taken today
            wins: Winning trades today
            losses: Losing trades today
        """
        # Calculate returns if we have previous value
        daily_return = 0
        if len(self.daily_values) > 0:
            daily_return = (portfolio_value / self.daily_values[-1]) - 1
            self.daily_returns.append(daily_return)
        
        # Store values
        self.daily_values.append(portfolio_value)
        self.dates.append(date)
        
        # Calculate benchmark return if provided
        if benchmark_value and len(self.benchmark_returns) >= 0:
            if len(self.daily_values) > 1:  # Need previous value
                # Fetch previous benchmark (or estimate)
                prev_benchmark = benchmark_value / (1 + daily_return + 0.001)
                benchmark_return = (benchmark_value / prev_benchmark) - 1
                self.benchmark_returns.append(benchmark_return)
        
        # Save to database
        if self.db and len(self.daily_values) > 1:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    starting_capital = self.daily_values[-2]
                    ending_capital = portfolio_value
                    daily_pnl = ending_capital - starting_capital
                    daily_return_pct = daily_return * 100
                    
                    benchmark_return_pct = None
                    if benchmark_value and len(self.benchmark_returns) > 0:
                        benchmark_return_pct = self.benchmark_returns[-1] * 100
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO daily_performance (
                            date, starting_capital, ending_capital, daily_pnl,
                            daily_return_pct, total_positions, trades_taken,
                            winning_trades, losing_trades, benchmark_return_pct
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date, starting_capital, ending_capital, daily_pnl,
                        daily_return_pct, positions_count, trades_taken,
                        wins, losses, benchmark_return_pct
                    ))
                    conn.commit()
            except Exception as e:
                if logger:
                    logger.error(f"Failed to save daily performance: {e}")
    
    def calculate_sharpe_ratio(self, risk_free_rate=0.05):
        """
        Calculate Sharpe Ratio
        
        Args:
            risk_free_rate: Annual risk-free rate (default 5%)
        
        Returns:
            Sharpe ratio (higher is better)
        """
        if len(self.daily_returns) < 2:
            return 0
        
        returns = np.array(self.daily_returns)
        
        # Annualized excess return
        avg_return = returns.mean() * 252  # 252 trading days
        risk_free_daily = risk_free_rate / 252
        excess_return = avg_return - risk_free_rate
        
        # Annualized volatility
        volatility = returns.std() * np.sqrt(252)
        
        if volatility == 0:
            return 0
        
        sharpe = excess_return / volatility
        return sharpe
    
    def calculate_sortino_ratio(self, risk_free_rate=0.05):
        """
        Calculate Sortino Ratio (like Sharpe but only considers downside volatility)
        
        Args:
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Sortino ratio (higher is better)
        """
        if len(self.daily_returns) < 2:
            return 0
        
        returns = np.array(self.daily_returns)
        
        # Annualized excess return
        avg_return = returns.mean() * 252
        excess_return = avg_return - risk_free_rate
        
        # Downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')  # No losses!
        
        downside_std = downside_returns.std() * np.sqrt(252)
        
        if downside_std == 0:
            return 0
        
        sortino = excess_return / downside_std
        return sortino
    
    def calculate_max_drawdown(self):
        """
        Calculate maximum drawdown
        
        Returns:
            (max_drawdown_pct, duration_days, recovery_days)
        """
        if len(self.daily_values) < 2:
            return 0, 0, 0
        
        values = np.array(self.daily_values)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdown at each point
        drawdown = (values - running_max) / running_max
        
        # Maximum drawdown
        max_dd = drawdown.min()
        max_dd_idx = drawdown.argmin()
        
        # Find peak before max drawdown
        peak_idx = np.argmax(values[:max_dd_idx+1]) if max_dd_idx > 0 else 0
        
        # Find recovery (when value exceeds previous peak)
        recovery_idx = None
        peak_value = values[peak_idx]
        for i in range(max_dd_idx + 1, len(values)):
            if values[i] >= peak_value:
                recovery_idx = i
                break
        
        duration_days = max_dd_idx - peak_idx
        recovery_days = (recovery_idx - max_dd_idx) if recovery_idx else 0
        
        return abs(max_dd), duration_days, recovery_days
    
    def calculate_alpha_beta(self):
        """
        Calculate Alpha and Beta vs benchmark
        
        Returns:
            (alpha, beta)
        """
        if len(self.daily_returns) < 2 or len(self.benchmark_returns) < 2:
            return 0, 1
        
        if len(self.daily_returns) != len(self.benchmark_returns):
            # Align lengths
            min_len = min(len(self.daily_returns), len(self.benchmark_returns))
            portfolio_returns = np.array(self.daily_returns[-min_len:])
            benchmark_returns = np.array(self.benchmark_returns[-min_len:])
        else:
            portfolio_returns = np.array(self.daily_returns)
            benchmark_returns = np.array(self.benchmark_returns)
        
        # Calculate beta (covariance / variance)
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance == 0:
            beta = 1
        else:
            beta = covariance / benchmark_variance
        
        # Calculate alpha (excess return beyond what beta explains)
        portfolio_return = portfolio_returns.mean() * 252
        benchmark_return = benchmark_returns.mean() * 252
        alpha = portfolio_return - (beta * benchmark_return)
        
        return alpha, beta
    
    def get_performance_summary(self):
        """
        Get comprehensive performance summary
        
        Returns:
            dict with all metrics
        """
        if len(self.daily_values) < 2:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'total_days': 0
            }
        
        # Basic metrics
        starting_value = self.daily_values[0]
        current_value = self.daily_values[-1]
        total_return = ((current_value / starting_value) - 1) * 100
        
        # Time period
        total_days = len(self.daily_values)
        
        # Advanced metrics
        sharpe = self.calculate_sharpe_ratio()
        sortino = self.calculate_sortino_ratio()
        max_dd, dd_duration, recovery = self.calculate_max_drawdown()
        
        # Alpha & Beta
        alpha, beta = 0, 1
        if len(self.benchmark_returns) > 0:
            alpha, beta = self.calculate_alpha_beta()
        
        # Win rate
        positive_days = sum(1 for r in self.daily_returns if r > 0)
        negative_days = sum(1 for r in self.daily_returns if r < 0)
        win_rate = (positive_days / len(self.daily_returns) * 100) if self.daily_returns else 0
        
        # Average returns
        avg_win = np.mean([r for r in self.daily_returns if r > 0]) * 100 if any(r > 0 for r in self.daily_returns) else 0
        avg_loss = np.mean([r for r in self.daily_returns if r < 0]) * 100 if any(r < 0 for r in self.daily_returns) else 0
        
        return {
            'starting_value': starting_value,
            'current_value': current_value,
            'total_return': total_return,
            'total_days': total_days,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd * 100,
            'max_drawdown_duration': dd_duration,
            'recovery_days': recovery,
            'alpha': alpha * 100,
            'beta': beta,
            'daily_win_rate': win_rate,
            'avg_winning_day': avg_win,
            'avg_losing_day': avg_loss,
            'positive_days': positive_days,
            'negative_days': negative_days
        }
    
    def display_performance(self):
        """Display performance summary"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*70)
        print("📊 PERFORMANCE SUMMARY")
        print("="*70)
        
        print(f"\n💰 Returns:")
        print(f"   Starting Value: ₹{summary['starting_value']:,.0f}")
        print(f"   Current Value:  ₹{summary['current_value']:,.0f}")
        print(f"   Total Return:   {summary['total_return']:+.2f}%")
        print(f"   Days Tracked:   {summary['total_days']}")
        
        print(f"\n📈 Risk-Adjusted Metrics:")
        print(f"   Sharpe Ratio:   {summary['sharpe_ratio']:.2f}")
        print(f"   Sortino Ratio:  {summary['sortino_ratio']:.2f}")
        print(f"   Alpha:          {summary['alpha']:+.2f}%")
        print(f"   Beta:           {summary['beta']:.2f}")
        
        print(f"\n📉 Drawdown:")
        print(f"   Max Drawdown:   {summary['max_drawdown']:.2f}%")
        print(f"   DD Duration:    {summary['max_drawdown_duration']} days")
        if summary['recovery_days'] > 0:
            print(f"   Recovery:       {summary['recovery_days']} days")
        else:
            print(f"   Recovery:       Not yet recovered")
        
        print(f"\n📊 Daily Statistics:")
        print(f"   Win Rate:       {summary['daily_win_rate']:.1f}%")
        print(f"   Positive Days:  {summary['positive_days']}")
        print(f"   Negative Days:  {summary['negative_days']}")
        print(f"   Avg Win Day:    {summary['avg_winning_day']:+.2f}%")
        print(f"   Avg Loss Day:   {summary['avg_losing_day']:+.2f}%")
        
        print("="*70)


# Global instance
_performance_tracker = None


def get_performance_tracker():
    """Get global performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


if __name__ == "__main__":
    # Test performance tracker
    print("🧪 Testing Performance Tracker...")
    
    tracker = get_performance_tracker()
    
    # Simulate 30 days of trading
    import random
    base_value = 100000
    
    for day in range(30):
        date = (datetime.now() - timedelta(days=30-day)).strftime('%Y-%m-%d')
        
        # Simulate daily return (-2% to +3%)
        daily_return = random.uniform(-0.02, 0.03)
        base_value *= (1 + daily_return)
        
        tracker.record_daily_performance(
            date=date,
            portfolio_value=base_value,
            positions_count=random.randint(3, 10),
            trades_taken=random.randint(0, 3)
        )
    
    # Display results
    tracker.display_performance()
    
    print("\n✅ Performance tracker test complete")
