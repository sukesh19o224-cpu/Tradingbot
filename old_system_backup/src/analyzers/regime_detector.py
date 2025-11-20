"""
🎯 REGIME DETECTOR V4.0
Detects market conditions to select best strategy
Returns: TRENDING_UP, CHOPPY, CONSOLIDATION, TRENDING_DOWN, etc.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *


class RegimeDetector:
    """
    Detects market regime to switch strategies automatically
    
    Regimes:
    - STRONG_BULL: Strong uptrend (use momentum)
    - TRENDING_UP: Moderate uptrend (use momentum)
    - CHOPPY: Sideways/volatile (use mean reversion)
    - RANGING: Tight range (use mean reversion)
    - CONSOLIDATION: Consolidating (use breakout)
    - WEAK: Weak/uncertain (use mean reversion)
    - TRENDING_DOWN: Downtrend (use mean reversion on quality stocks)
    """
    
    def __init__(self):
        print("🎯 Regime Detector Initialized")
        self.current_regime = None
        self.last_check = None
        self.regime_history = []
    
    def detect_regime(self, symbol="^NSEI", lookback_days=REGIME_LOOKBACK_DAYS):
        """
        Main regime detection method
        Returns: (regime_name, confidence, details)
        """
        print(f"\n{'='*60}")
        print(f"🎯 DETECTING MARKET REGIME")
        print(f"{'='*60}")
        
        try:
            # Get market data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{lookback_days*2}d", interval="1d")
            
            if df.empty or len(df) < lookback_days:
                print("⚠️ Insufficient data, defaulting to NEUTRAL")
                return 'NEUTRAL', 0.5, {}
            
            # Calculate indicators
            indicators = self._calculate_indicators(df)
            
            # Detect regime
            regime, confidence = self._classify_regime(indicators)
            
            # Store
            self.current_regime = regime
            self.last_check = datetime.now()
            self.regime_history.append({
                'timestamp': datetime.now(),
                'regime': regime,
                'confidence': confidence
            })
            
            # Display
            self._display_regime(regime, confidence, indicators)
            
            return regime, confidence, indicators
        
        except Exception as e:
            print(f"❌ Error detecting regime: {e}")
            return 'NEUTRAL', 0.5, {}
    
    def _calculate_indicators(self, df):
        """Calculate all regime indicators"""
        indicators = {}
        
        # 1. TREND INDICATORS
        # Moving averages
        indicators['ma20'] = df['Close'].rolling(20).mean().iloc[-1]
        indicators['ma50'] = df['Close'].rolling(50).mean().iloc[-1]
        indicators['price'] = df['Close'].iloc[-1]
        
        # Price position relative to MAs
        indicators['above_ma20'] = indicators['price'] > indicators['ma20']
        indicators['above_ma50'] = indicators['price'] > indicators['ma50']
        indicators['ma20_above_ma50'] = indicators['ma20'] > indicators['ma50']
        
        # Distance from MA
        indicators['dist_from_ma20'] = ((indicators['price'] - indicators['ma20']) / indicators['ma20']) * 100
        indicators['dist_from_ma50'] = ((indicators['price'] - indicators['ma50']) / indicators['ma50']) * 100
        
        # 2. MOMENTUM INDICATORS
        # Rate of change
        if len(df) >= 21:
            indicators['roc_20'] = ((df['Close'].iloc[-1] / df['Close'].iloc[-20]) - 1) * 100
        else:
            indicators['roc_20'] = 0
        
        if len(df) >= 6:
            indicators['roc_5'] = ((df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1) * 100
        else:
            indicators['roc_5'] = 0
        
        # 3. VOLATILITY INDICATORS
        # ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        indicators['atr'] = true_range.rolling(14).mean().iloc[-1]
        indicators['atr_percent'] = (indicators['atr'] / indicators['price']) * 100
        
        # Standard deviation
        indicators['volatility'] = df['Close'].pct_change().std() * 100
        
        # Recent volatility vs historical
        recent_vol = df['Close'].tail(5).pct_change().std() * 100
        historical_vol = df['Close'].iloc[-20:-5].pct_change().std() * 100
        indicators['vol_ratio'] = recent_vol / historical_vol if historical_vol > 0 else 1
        
        # 4. ADX (Trend Strength)
        indicators['adx'] = self._calculate_adx(df)
        
        # 5. RANGE/CONSOLIDATION DETECTION
        # Price range over last N days
        recent_high = df['High'].tail(BREAKOUT['CONSOLIDATION_DAYS']).max()
        recent_low = df['Low'].tail(BREAKOUT['CONSOLIDATION_DAYS']).min()
        indicators['consolidation_range'] = ((recent_high - recent_low) / indicators['price']) * 100
        
        # 6. VOLUME
        indicators['volume_avg'] = df['Volume'].tail(20).mean()
        indicators['volume_recent'] = df['Volume'].tail(5).mean()
        indicators['volume_ratio'] = indicators['volume_recent'] / indicators['volume_avg'] if indicators['volume_avg'] > 0 else 1
        
        return indicators
    
    def _calculate_adx(self, df, period=14):
        """Calculate ADX for trend strength"""
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            # +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Smoothed TR
            atr = tr.rolling(period).mean()
            
            # +DI and -DI
            plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
            
            # DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(period).mean().iloc[-1]
            
            return adx if not pd.isna(adx) else 0
        except:
            return 0
    
    def _classify_regime(self, ind):
        """
        Classify regime based on indicators
        Returns: (regime_name, confidence)
        """
        regime_scores = {
            'STRONG_BULL': 0,
            'TRENDING_UP': 0,
            'CHOPPY': 0,
            'RANGING': 0,
            'CONSOLIDATION': 0,
            'WEAK': 0,
            'TRENDING_DOWN': 0
        }
        
        # STRONG_BULL signals
        if ind['above_ma20'] and ind['above_ma50'] and ind['ma20_above_ma50']:
            regime_scores['STRONG_BULL'] += 30
        if ind['roc_20'] > 10:
            regime_scores['STRONG_BULL'] += 25
        if ind['roc_5'] > 5:
            regime_scores['STRONG_BULL'] += 20
        if ind['adx'] > 30:
            regime_scores['STRONG_BULL'] += 25
        
        # TRENDING_UP signals
        if ind['above_ma20'] and ind['ma20_above_ma50']:
            regime_scores['TRENDING_UP'] += 25
        if ind['roc_20'] > 5 and ind['roc_20'] <= 10:
            regime_scores['TRENDING_UP'] += 20
        if ind['adx'] > 20 and ind['adx'] <= 30:
            regime_scores['TRENDING_UP'] += 20
        if ind['dist_from_ma20'] > 0 and ind['dist_from_ma20'] < 5:
            regime_scores['TRENDING_UP'] += 15
        
        # CHOPPY signals
        if ind['vol_ratio'] > 1.5:
            regime_scores['CHOPPY'] += 30
        if ind['adx'] < 20:
            regime_scores['CHOPPY'] += 25
        if abs(ind['roc_5']) < 2:
            regime_scores['CHOPPY'] += 20
        if ind['atr_percent'] > 3:
            regime_scores['CHOPPY'] += 15
        
        # RANGING signals
        if ind['consolidation_range'] < 3:
            regime_scores['RANGING'] += 30
        if abs(ind['dist_from_ma20']) < 2:
            regime_scores['RANGING'] += 25
        if ind['volatility'] < 1.5:
            regime_scores['RANGING'] += 20
        if ind['above_ma50']:
            regime_scores['RANGING'] += 15
        
        # CONSOLIDATION signals
        if ind['consolidation_range'] < 5:
            regime_scores['CONSOLIDATION'] += 25
        if ind['volume_ratio'] < 0.8:  # Low volume during consolidation
            regime_scores['CONSOLIDATION'] += 20
        if ind['atr_percent'] < 2:
            regime_scores['CONSOLIDATION'] += 20
        if ind['adx'] < 20:
            regime_scores['CONSOLIDATION'] += 15
        if ind['above_ma50']:
            regime_scores['CONSOLIDATION'] += 10
        
        # WEAK signals
        if not ind['above_ma20'] and ind['above_ma50']:
            regime_scores['WEAK'] += 25
        if ind['roc_5'] < 0 and ind['roc_5'] > -3:
            regime_scores['WEAK'] += 20
        if ind['adx'] < 15:
            regime_scores['WEAK'] += 20
        
        # TRENDING_DOWN signals
        if not ind['above_ma20'] and not ind['above_ma50']:
            regime_scores['TRENDING_DOWN'] += 30
        if ind['roc_20'] < -5:
            regime_scores['TRENDING_DOWN'] += 25
        if ind['roc_5'] < -3:
            regime_scores['TRENDING_DOWN'] += 20
        if ind['adx'] > 25:
            regime_scores['TRENDING_DOWN'] += 25
        
        # Find winner
        best_regime = max(regime_scores, key=regime_scores.get)
        best_score = regime_scores[best_regime]
        max_possible = 100
        confidence = min(best_score / max_possible, 1.0)
        
        return best_regime, confidence
    
    def _display_regime(self, regime, confidence, indicators):
        """Display regime with details"""
        print(f"\n🎯 DETECTED REGIME: {regime}")
        print(f"   Confidence: {confidence*100:.0f}%")
        print(f"\n📊 KEY INDICATORS:")
        print(f"   Price: ₹{indicators['price']:.2f}")
        print(f"   MA20: ₹{indicators['ma20']:.2f} ({'Above' if indicators['above_ma20'] else 'Below'})")
        print(f"   MA50: ₹{indicators['ma50']:.2f} ({'Above' if indicators['above_ma50'] else 'Below'})")
        print(f"   ROC(20d): {indicators['roc_20']:+.1f}%")
        print(f"   ROC(5d): {indicators['roc_5']:+.1f}%")
        print(f"   ADX: {indicators['adx']:.1f} ({'Trending' if indicators['adx'] > 25 else 'Weak'})")
        print(f"   Volatility: {indicators['volatility']:.2f}%")
        print(f"   Consolidation Range: {indicators['consolidation_range']:.1f}%")
        
        print(f"\n💡 RECOMMENDED STRATEGIES:")
        strategies = self.get_recommended_strategies(regime)
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")
        
        print(f"{'='*60}")
    
    def get_recommended_strategies(self, regime):
        """Get recommended strategies for regime"""
        recommendations = {
            'STRONG_BULL': ['MOMENTUM (Primary)', 'BREAKOUT (Secondary)'],
            'TRENDING_UP': ['MOMENTUM (Primary)', 'BREAKOUT (Secondary)'],
            'CHOPPY': ['MEAN_REVERSION (Primary)', 'No Momentum'],
            'RANGING': ['MEAN_REVERSION (Primary)', 'BREAKOUT (Watch)'],
            'CONSOLIDATION': ['BREAKOUT (Primary)', 'MEAN_REVERSION (Secondary)'],
            'WEAK': ['MEAN_REVERSION (Primary)', 'Wait for clarity'],
            'TRENDING_DOWN': ['MEAN_REVERSION (Quality only)', 'Stay defensive']
        }
        return recommendations.get(regime, ['NEUTRAL - Mixed strategies'])
    
    def get_active_strategies(self, regime=None):
        """
        Return list of strategies that should be active in current regime
        """
        if regime is None:
            regime = self.current_regime
        
        if regime is None:
            return ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT']  # All active
        
        active = []
        for strategy_name, config in STRATEGIES.items():
            if regime in config['market_regimes']:
                active.append(strategy_name)
        
        # If no match, return all
        if not active:
            active = ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT']
        
        return active
    
    def should_check_regime(self):
        """Check if it's time to re-check regime"""
        if self.last_check is None:
            return True
        
        minutes_since = (datetime.now() - self.last_check).total_seconds() / 60
        return minutes_since >= REGIME_CHECK_INTERVAL


if __name__ == "__main__":
    print("\n🧪 Testing Regime Detector\n")
    
    detector = RegimeDetector()
    regime, confidence, indicators = detector.detect_regime()
    
    print(f"\n✅ Active Strategies: {detector.get_active_strategies(regime)}")