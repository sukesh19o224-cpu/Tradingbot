"""V5.5 ULTRA+ - Market Regime Detector"""
import yfinance as yf
import numpy as np
from typing import Dict

class MarketRegimeDetector:
    """Detect bull/bear/sideways market regimes"""
    
    def detect_regime(self, index_symbol: str = '^NSEI') -> Dict:
        """Detect current market regime"""
        ticker = yf.Ticker(index_symbol)
        hist = ticker.history(period='90d')
        
        if len(hist) < 50:
            return {'regime': 'UNKNOWN', 'confidence': 0}
        
        # Calculate trend
        prices = hist['Close'].values
        sma_50 = np.mean(prices[-50:])
        sma_20 = np.mean(prices[-20:])
        current = prices[-1]
        
        # Determine regime
        if current > sma_20 > sma_50:
            regime = 'BULL_MARKET'
            confidence = 80
        elif current < sma_20 < sma_50:
            regime = 'BEAR_MARKET'
            confidence = 80
        else:
            regime = 'SIDEWAYS'
            confidence = 60
        
        # Calculate volatility
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) * 100
        
        return {
            'regime': regime,
            'confidence': confidence,
            'volatility': volatility,
            'trend_strength': abs((current - sma_50) / sma_50 * 100)
        }
