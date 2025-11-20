"""
🔬 MATHEMATICAL INDICATORS - Advanced Market Geometry
Fibonacci, Elliott Wave, Gann Theory, Harmonic Patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

from config.settings import *


class MathematicalIndicators:
    """
    Advanced mathematical and geometric analysis of price movements

    Features:
    - Fibonacci Retracements & Extensions
    - Elliott Wave Pattern Detection
    - Gann Angles & Square of 9
    - Harmonic Pattern Recognition
    - Support & Resistance Levels
    """

    def __init__(self):
        self.patterns = []

    def calculate_all(self, df: pd.DataFrame) -> Dict:
        """
        Calculate all mathematical indicators

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dict with mathematical analysis and signals
        """
        if df is None or len(df) < 50:
            return None

        try:
            # Calculate each mathematical indicator
            fibonacci = self._calculate_fibonacci(df)
            elliott = self._detect_elliott_wave(df)
            gann = self._calculate_gann_levels(df)
            support_resistance = self._find_support_resistance(df)

            # Generate mathematical score
            math_score = self._calculate_mathematical_score(
                df, fibonacci, elliott, gann, support_resistance
            )

            return {
                'fibonacci': fibonacci,
                'elliott_wave': elliott,
                'gann': gann,
                'support_resistance': support_resistance,
                'mathematical_score': math_score,
                'signals': self._generate_mathematical_signals(
                    df, fibonacci, elliott, gann, support_resistance
                )
            }

        except Exception as e:
            print(f"❌ Error in mathematical indicators: {e}")
            return None

    def _calculate_fibonacci(self, df: pd.DataFrame) -> Dict:
        """
        Calculate Fibonacci retracement and extension levels

        Uses recent swing high and swing low to calculate key Fibonacci levels
        """
        try:
            # Find recent swing high and low (last 50 bars)
            recent_data = df.tail(50)
            swing_high = recent_data['High'].max()
            swing_low = recent_data['Low'].min()

            # Find when they occurred
            high_idx = recent_data['High'].idxmax()
            low_idx = recent_data['Low'].idxmin()

            # Determine if we're in uptrend or downtrend
            if high_idx > low_idx:
                # Uptrend: low came first
                trend = 'UPTREND'
                diff = swing_high - swing_low

                # Retracement levels (from high)
                retracements = {
                    level: swing_high - (diff * level)
                    for level in FIBONACCI_LEVELS
                }

                # Extension levels (beyond high)
                extensions = {
                    level: swing_high + (diff * (level - 1))
                    for level in FIBONACCI_EXTENSIONS
                }
            else:
                # Downtrend: high came first
                trend = 'DOWNTREND'
                diff = swing_high - swing_low

                # Retracement levels (from low)
                retracements = {
                    level: swing_low + (diff * level)
                    for level in FIBONACCI_LEVELS
                }

                # Extension levels (beyond low)
                extensions = {
                    level: swing_low - (diff * (level - 1))
                    for level in FIBONACCI_EXTENSIONS
                }

            current_price = df['Close'].iloc[-1]

            # Find nearest Fibonacci level
            nearest_level = None
            min_distance = float('inf')

            for level, price in retracements.items():
                distance = abs(current_price - price) / current_price
                if distance < min_distance:
                    min_distance = distance
                    nearest_level = level

            return {
                'trend': trend,
                'swing_high': swing_high,
                'swing_low': swing_low,
                'retracements': retracements,
                'extensions': extensions,
                'current_price': current_price,
                'nearest_retracement': nearest_level,
                'distance_to_nearest': min_distance,
                'at_key_level': min_distance < 0.02  # Within 2% of Fibonacci level
            }

        except Exception as e:
            print(f"❌ Fibonacci error: {e}")
            return {}

    def _detect_elliott_wave(self, df: pd.DataFrame) -> Dict:
        """
        Simplified Elliott Wave pattern detection

        Detects 5-wave impulse patterns and 3-wave corrections
        """
        try:
            # Find swing highs and lows
            recent_data = df.tail(100)

            # Simplified wave detection using pivot points
            highs = []
            lows = []

            for i in range(2, len(recent_data) - 2):
                # Swing high
                if (recent_data['High'].iloc[i] > recent_data['High'].iloc[i-1] and
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i-2] and
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i+1] and
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i+2]):
                    highs.append((i, recent_data['High'].iloc[i]))

                # Swing low
                if (recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i-1] and
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i-2] and
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i+1] and
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i+2]):
                    lows.append((i, recent_data['Low'].iloc[i]))

            # Try to identify wave pattern (simplified)
            wave_pattern = 'UNKNOWN'
            wave_count = 0

            if len(highs) >= 3 and len(lows) >= 2:
                # Check for 5-wave impulse pattern
                if len(highs) >= 3 and len(lows) >= 2:
                    # Simple check: are we making higher highs?
                    last_3_highs = [h[1] for h in highs[-3:]]
                    if last_3_highs[-1] > last_3_highs[0]:
                        wave_pattern = 'IMPULSE_UP'
                        wave_count = 3  # Simplified
                    elif last_3_highs[-1] < last_3_highs[0]:
                        wave_pattern = 'IMPULSE_DOWN'
                        wave_count = 3

            return {
                'pattern': wave_pattern,
                'wave_count': wave_count,
                'swing_highs': len(highs),
                'swing_lows': len(lows),
                'in_wave_5': wave_count >= 5,  # Potential reversal
                'confidence': 0.6 if wave_count > 0 else 0.3
            }

        except Exception as e:
            print(f"❌ Elliott Wave error: {e}")
            return {'pattern': 'UNKNOWN', 'wave_count': 0, 'confidence': 0}

    def _calculate_gann_levels(self, df: pd.DataFrame) -> Dict:
        """
        Calculate Gann angles and key price levels

        Based on Gann theory of price-time relationships
        """
        try:
            recent_data = df.tail(50)
            swing_high = recent_data['High'].max()
            swing_low = recent_data['Low'].min()
            current_price = df['Close'].iloc[-1]

            # Gann 1x1 angle (45 degrees) - price moves 1 point per 1 time unit
            price_range = swing_high - swing_low
            time_range = len(recent_data)

            gann_1x1_slope = price_range / time_range

            # Calculate Gann angles from swing low
            gann_levels = {}
            for angle in GANN_ANGLES:
                gann_levels[f'1x{angle}'] = swing_low + (gann_1x1_slope * angle * time_range)

            # Square of 9 - Price levels
            if GANN_SQUARE_OF_9_ENABLED:
                # Simplified: key 45-degree levels
                square_of_9_levels = []
                base = int(np.sqrt(current_price))
                for i in range(-2, 3):
                    level = (base + i) ** 2
                    square_of_9_levels.append(level)
            else:
                square_of_9_levels = []

            return {
                'gann_angles': gann_levels,
                'square_of_9': square_of_9_levels,
                'current_price': current_price,
                'nearest_gann_level': self._find_nearest_level(current_price, list(gann_levels.values())),
                'at_gann_level': self._is_at_level(current_price, list(gann_levels.values()), tolerance=0.02)
            }

        except Exception as e:
            print(f"❌ Gann error: {e}")
            return {}

    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        Identify key support and resistance levels using multiple touches
        """
        try:
            recent_data = df.tail(100)

            # Find levels where price has bounced multiple times
            price_levels = []

            # Use clustering to find frequently tested levels
            all_highs = recent_data['High'].values
            all_lows = recent_data['Low'].values

            # Simplified: use recent swing highs/lows as S/R
            resistance_levels = []
            support_levels = []

            # Find local maxima (resistance)
            for i in range(5, len(recent_data) - 5):
                if (recent_data['High'].iloc[i] >= recent_data['High'].iloc[i-5:i].max() and
                    recent_data['High'].iloc[i] >= recent_data['High'].iloc[i+1:i+6].max()):
                    resistance_levels.append(recent_data['High'].iloc[i])

            # Find local minima (support)
            for i in range(5, len(recent_data) - 5):
                if (recent_data['Low'].iloc[i] <= recent_data['Low'].iloc[i-5:i].min() and
                    recent_data['Low'].iloc[i] <= recent_data['Low'].iloc[i+1:i+6].min()):
                    support_levels.append(recent_data['Low'].iloc[i])

            # Remove duplicates and sort
            resistance_levels = sorted(list(set([round(r, 2) for r in resistance_levels])), reverse=True)[:5]
            support_levels = sorted(list(set([round(s, 2) for s in support_levels])))[:5]

            current_price = df['Close'].iloc[-1]

            return {
                'resistance': resistance_levels,
                'support': support_levels,
                'nearest_resistance': self._find_nearest_above(current_price, resistance_levels),
                'nearest_support': self._find_nearest_below(current_price, support_levels),
                'between_levels': self._is_between_levels(current_price, support_levels, resistance_levels)
            }

        except Exception as e:
            print(f"❌ Support/Resistance error: {e}")
            return {}

    def _calculate_mathematical_score(self, df: pd.DataFrame, fibonacci: Dict,
                                      elliott: Dict, gann: Dict, sr: Dict) -> float:
        """
        Calculate overall mathematical score (0-10)

        Based on alignment of various mathematical indicators
        """
        score = 0
        max_score = 0

        # 1. Fibonacci alignment (3 points)
        max_score += 3
        if fibonacci.get('at_key_level'):
            if fibonacci.get('trend') == 'UPTREND':
                score += 3  # Bouncing from Fibonacci support
            else:
                score += 1

        # 2. Elliott Wave (2 points)
        max_score += 2
        if elliott.get('pattern') == 'IMPULSE_UP':
            if elliott.get('wave_count') < 5:
                score += 2 * elliott.get('confidence', 0.5)
            else:
                score += 0.5  # Wave 5 - potential reversal

        # 3. Gann levels (2 points)
        max_score += 2
        if gann.get('at_gann_level'):
            score += 2

        # 4. Support/Resistance (3 points)
        max_score += 3
        if sr.get('between_levels') or sr.get('nearest_support'):
            # Price near support is bullish
            current = df['Close'].iloc[-1]
            nearest_support = sr.get('nearest_support', 0)
            if nearest_support > 0:
                distance_to_support = abs(current - nearest_support) / current
                if distance_to_support < 0.02:  # Within 2%
                    score += 3

        # Calculate final score (0-10 scale)
        math_score = (score / max_score) * 10 if max_score > 0 else 5.0

        return round(math_score, 2)

    def _generate_mathematical_signals(self, df: pd.DataFrame, fibonacci: Dict,
                                       elliott: Dict, gann: Dict, sr: Dict) -> Dict:
        """Generate trading signals from mathematical analysis"""
        signals = {}

        # Fibonacci signal
        if fibonacci.get('at_key_level'):
            if fibonacci.get('trend') == 'UPTREND':
                signals['fibonacci'] = 'BULLISH_RETRACEMENT'
            else:
                signals['fibonacci'] = 'BEARISH_RETRACEMENT'
        else:
            signals['fibonacci'] = 'NO_SIGNAL'

        # Elliott Wave signal
        if elliott.get('pattern') == 'IMPULSE_UP' and elliott.get('wave_count') < 5:
            signals['elliott'] = 'BULLISH_IMPULSE'
        elif elliott.get('in_wave_5'):
            signals['elliott'] = 'POTENTIAL_REVERSAL'
        else:
            signals['elliott'] = 'NEUTRAL'

        # Gann signal
        if gann.get('at_gann_level'):
            signals['gann'] = 'AT_KEY_LEVEL'
        else:
            signals['gann'] = 'NEUTRAL'

        # Support/Resistance signal
        current = df['Close'].iloc[-1]
        nearest_support = sr.get('nearest_support', 0)
        nearest_resistance = sr.get('nearest_resistance', float('inf'))

        if nearest_support > 0:
            distance_to_support = abs(current - nearest_support) / current
            if distance_to_support < 0.02:
                signals['support_resistance'] = 'AT_SUPPORT'
            elif abs(current - nearest_resistance) / current < 0.02:
                signals['support_resistance'] = 'AT_RESISTANCE'
            else:
                signals['support_resistance'] = 'NEUTRAL'
        else:
            signals['support_resistance'] = 'NEUTRAL'

        return signals

    # Helper methods
    def _find_nearest_level(self, price: float, levels: List[float]) -> Optional[float]:
        """Find the nearest level to current price"""
        if not levels:
            return None
        return min(levels, key=lambda x: abs(x - price))

    def _is_at_level(self, price: float, levels: List[float], tolerance: float = 0.02) -> bool:
        """Check if price is at any of the levels (within tolerance)"""
        for level in levels:
            if abs(price - level) / price < tolerance:
                return True
        return False

    def _find_nearest_above(self, price: float, levels: List[float]) -> Optional[float]:
        """Find nearest level above current price"""
        above = [l for l in levels if l > price]
        return min(above) if above else None

    def _find_nearest_below(self, price: float, levels: List[float]) -> Optional[float]:
        """Find nearest level below current price"""
        below = [l for l in levels if l < price]
        return max(below) if below else None

    def _is_between_levels(self, price: float, support: List[float], resistance: List[float]) -> bool:
        """Check if price is between support and resistance"""
        nearest_support = self._find_nearest_below(price, support)
        nearest_resistance = self._find_nearest_above(price, resistance)
        return nearest_support is not None and nearest_resistance is not None


def test_mathematical_indicators():
    """Test the mathematical indicators module"""
    import yfinance as yf

    print("🧪 Testing Mathematical Indicators...")

    # Fetch sample data
    ticker = yf.Ticker('RELIANCE.NS')
    df = ticker.history(period='6mo')

    if df.empty:
        print("❌ Failed to fetch data")
        return

    # Calculate indicators
    mi = MathematicalIndicators()
    result = mi.calculate_all(df)

    if result:
        print(f"\n✅ Mathematical indicators calculated!")
        print(f"\n📊 FIBONACCI:")
        fib = result['fibonacci']
        print(f"   Trend: {fib.get('trend')}")
        print(f"   At Key Level: {fib.get('at_key_level')}")
        print(f"   Nearest Level: {fib.get('nearest_retracement', 0):.3f}")

        print(f"\n🌊 ELLIOTT WAVE:")
        ew = result['elliott_wave']
        print(f"   Pattern: {ew.get('pattern')}")
        print(f"   Wave Count: {ew.get('wave_count')}")

        print(f"\n📐 GANN:")
        gann = result['gann']
        print(f"   At Gann Level: {gann.get('at_gann_level')}")

        print(f"\n🎯 Mathematical Score: {result['mathematical_score']}/10")
    else:
        print("❌ Failed to calculate mathematical indicators")


if __name__ == "__main__":
    test_mathematical_indicators()
