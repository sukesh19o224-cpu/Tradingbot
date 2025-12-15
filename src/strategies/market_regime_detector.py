"""
📊 MARKET REGIME DETECTOR
Analyzes Nifty 50 to determine current market regime (BULL/SIDEWAYS/BEAR)
Professional feature used by institutional traders
"""

import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, Tuple

from config.settings import MARKET_REGIME_CONFIG, NIFTY_SYMBOL


class MarketRegimeDetector:
    """
    Detect market regime based on Nifty 50 analysis
    
    Regimes:
    - BULL: Strong uptrend (trade aggressively)
    - SIDEWAYS: Choppy/weak trend (be selective)
    - BEAR: Downtrend (preserve capital)
    """
    
    def __init__(self):
        self.config = MARKET_REGIME_CONFIG
        self.current_regime = None
        self.regime_details = {}
        
    def detect_regime(self) -> Tuple[str, Dict]:
        """
        Detect current market regime
        
        Returns:
            Tuple of (regime_name, regime_details)
            regime_name: 'BULL', 'SIDEWAYS', or 'BEAR'
            regime_details: Dict with analysis details
        """
        try:
            # Fetch Nifty 50 data
            nifty = yf.Ticker(NIFTY_SYMBOL)
            df = nifty.history(period=self.config['LOOKBACK_PERIOD'])
            
            if df is None or len(df) < 50:
                print("⚠️ Insufficient Nifty data for regime detection")
                return 'BULL', {'error': 'Insufficient data', 'default': True}
            
            # Calculate indicators
            current_price = float(df['Close'].iloc[-1])
            ema_50 = float(df['Close'].ewm(span=self.config['EMA_SHORT']).mean().iloc[-1])
            ema_200 = float(df['Close'].ewm(span=self.config['EMA_LONG']).mean().iloc[-1])
            adx = self._calculate_adx(df)
            
            # Calculate trend metrics
            price_vs_ema50 = ((current_price - ema_50) / ema_50) * 100
            price_vs_ema200 = ((current_price - ema_200) / ema_200) * 100
            ema50_vs_ema200 = ((ema_50 - ema_200) / ema_200) * 100
            
            # Determine regime
            regime = self._classify_regime(
                current_price, ema_50, ema_200, adx
            )
            
            # Build details
            details = {
                'nifty_price': current_price,
                'ema_50': ema_50,
                'ema_200': ema_200,
                'adx': adx,
                'price_vs_ema50_pct': round(price_vs_ema50, 2),
                'price_vs_ema200_pct': round(price_vs_ema200, 2),
                'ema50_vs_ema200_pct': round(ema50_vs_ema200, 2),
                'regime': regime,
                'description': self.config[regime]['description'],
                'timestamp': datetime.now().isoformat()
            }
            
            self.current_regime = regime
            self.regime_details = details
            
            return regime, details
            
        except Exception as e:
            print(f"❌ Error detecting market regime: {e}")
            # Default to BULL on error (normal operation)
            return 'BULL', {'error': str(e), 'default': True}
    
    def _classify_regime(self, price: float, ema_50: float, ema_200: float, adx: float) -> str:
        """
        Classify market regime based on price position and trend strength
        
        Logic:
        - BULL: Price > EMA50 > EMA200 AND ADX > 25 (strong uptrend)
        - BEAR: Price < EMA50 < EMA200 AND ADX > 25 (strong downtrend)
        - SIDEWAYS: Everything else (weak trend or choppy)
        """
        adx_strong = self.config['ADX_STRONG_TREND']
        adx_weak = self.config['ADX_WEAK_TREND']
        
        # BULL: Strong uptrend
        if price > ema_50 > ema_200 and adx > adx_strong:
            return 'BULL'
        
        # BEAR: Strong downtrend
        elif price < ema_50 < ema_200 and adx > adx_strong:
            return 'BEAR'
        
        # SIDEWAYS: Weak trend or choppy
        else:
            return 'SIDEWAYS'
    
    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """Calculate ADX (Average Directional Index)"""
        try:
            period = self.config['ADX_PERIOD']
            
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # ATR
            atr = tr.rolling(window=period).mean()
            
            # +DI and -DI
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            
            # DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return float(adx.iloc[-1])
            
        except Exception as e:
            print(f"⚠️ ADX calculation error: {e}")
            return 20.0  # Default to neutral
    
    def get_regime_adjustments(self, regime: str = None) -> Dict:
        """
        Get trading adjustments for current regime
        
        Args:
            regime: Regime name (uses current if None)
            
        Returns:
            Dict with adjustment multipliers
        """
        if regime is None:
            regime = self.current_regime or 'BULL'
        
        return self.config.get(regime, self.config['BULL'])
    
    def print_regime_summary(self):
        """Print current regime summary"""
        if not self.regime_details:
            print("⚠️ No regime detected yet")
            return
        
        details = self.regime_details
        regime = details['regime']
        
        # Color coding
        regime_emoji = {
            'BULL': '🟢',
            'SIDEWAYS': '🟡',
            'BEAR': '🔴'
        }
        
        print(f"\n{'='*70}")
        print(f"📊 MARKET REGIME ANALYSIS")
        print(f"{'='*70}")
        print(f"\n{regime_emoji.get(regime, '⚪')} Current Regime: {regime}")
        print(f"   {details['description']}")
        print(f"\n📈 Nifty 50 Analysis:")
        print(f"   Price: {details['nifty_price']:.2f}")
        print(f"   vs 50-EMA: {details['price_vs_ema50_pct']:+.2f}%")
        print(f"   vs 200-EMA: {details['price_vs_ema200_pct']:+.2f}%")
        print(f"   ADX: {details['adx']:.1f}")
        
        # Show adjustments
        adjustments = self.get_regime_adjustments(regime)
        print(f"\n⚙️ Trading Adjustments:")
        print(f"   Quality Threshold: {adjustments['quality_multiplier']:.1f}x")
        print(f"   Max Positions: {adjustments['max_positions_multiplier']:.1f}x")
        print(f"   Position Size: {adjustments['position_size_multiplier']:.1f}x")
        
        if 'min_rs_rating' in adjustments:
            print(f"   Min RS Rating: {adjustments['min_rs_rating']}")
        
        print(f"{'='*70}\n")


def test_regime_detector():
    """Test the market regime detector"""
    print("🧪 Testing Market Regime Detector...\n")
    
    detector = MarketRegimeDetector()
    regime, details = detector.detect_regime()
    
    detector.print_regime_summary()
    
    print(f"✅ Regime detection complete!")
    print(f"   Detected: {regime}")
    print(f"   Timestamp: {details.get('timestamp', 'N/A')}")


if __name__ == "__main__":
    test_regime_detector()
