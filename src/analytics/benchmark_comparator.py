"""V5.5 ULTRA+ - Performance Benchmarking"""
import yfinance as yf
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class BenchmarkComparator:
    """Compare portfolio performance against market indices"""
    
    def __init__(self):
        self.benchmarks = {'NIFTY50': '^NSEI', 'SENSEX': '^BSESN'}
    
    def compare_performance(self, portfolio_return: float, period_days: int = 30) -> Dict:
        """Compare portfolio return vs benchmarks"""
        results = {}
        for name, symbol in self.benchmarks.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f'{period_days}d')
                if len(hist) > 1:
                    bench_return = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
                    results[name] = {'return': bench_return, 'outperformance': portfolio_return - bench_return}
            except:
                results[name] = {'return': 0, 'outperformance': 0}
        return results
