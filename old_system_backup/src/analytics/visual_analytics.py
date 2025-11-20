"""V5.5 ULTRA+ - Visual Analytics"""
import numpy as np
import pandas as pd
from typing import Dict, List
import json

class VisualAnalytics:
    """Generate visual analytics data"""
    
    def __init__(self, portfolio_manager):
        self.pm = portfolio_manager
    
    def generate_equity_curve(self) -> List[Dict]:
        """Generate equity curve data"""
        curve = []
        equity = self.pm.capital
        
        for trade in sorted(self.pm.trade_history, key=lambda x: x.get('exit_date', '')):
            equity += trade.get('pnl', 0)
            curve.append({
                'date': trade.get('exit_date'),
                'equity': equity
            })
        
        return curve
    
    def generate_correlation_matrix(self) -> Dict:
        """Generate correlation matrix for positions"""
        import yfinance as yf
        
        symbols = list(self.pm.positions.keys())
        if len(symbols) < 2:
            return {}
        
        returns_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='3mo')
                returns_data[symbol] = hist['Close'].pct_change().dropna()
            except:
                pass
        
        if len(returns_data) < 2:
            return {}
        
        df = pd.DataFrame(returns_data)
        corr_matrix = df.corr()
        
        return corr_matrix.to_dict()
    
    def generate_strategy_distribution(self) -> Dict:
        """Generate strategy distribution chart data"""
        distribution = {}
        for symbol, pos in self.pm.positions.items():
            strategy = pos['strategy']
            value = pos['quantity'] * pos['entry_price']
            distribution[strategy] = distribution.get(strategy, 0) + value
        return distribution
