"""
⏱️ POSITION TIMEFRAME CLASSIFIER V5.0
Intelligently classifies stocks into optimal holding timeframes

Solves the problem: "Stock exits at day 5 with loss, but becomes profitable at day 15"

Classifications:
- SHORT_TERM (3-7 days): High volatility, quick moves, swing trades
- MEDIUM_TERM (10-20 days): Moderate trends, positional trades
- LONG_TERM (20-45 days): Strong trends, low volatility, investment trades
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


class PositionTimeframeClassifier:
    """
    Analyzes stock characteristics to determine optimal holding period

    Uses:
    1. Volatility analysis (ATR, Bollinger Bands)
    2. Trend strength and consistency
    3. Historical price pattern analysis
    4. Volume profile
    5. Momentum sustainability
    """

    def __init__(self):
        self.name = "TIMEFRAME_CLASSIFIER"
        print(f"⏱️ {self.name} Initialized")

    def classify_position(self, symbol_ns, current_strategy='MOMENTUM'):
        """
        MASTER FUNCTION: Classify stock into optimal timeframe

        Args:
            symbol_ns: Stock symbol (e.g., 'RELIANCE.NS')
            current_strategy: Current strategy being used

        Returns:
            dict with classification and recommended holding days
        """
        try:
            # Fetch data
            ticker = yf.Ticker(symbol_ns)
            df = ticker.history(period='6mo', interval='1d')

            if df.empty or len(df) < 50:
                return {
                    'timeframe': 'SHORT_TERM',
                    'recommended_hold_days': 5,
                    'confidence': 0,
                    'reason': 'Insufficient data'
                }

            # Calculate all metrics
            volatility_score = self._calculate_volatility_profile(df)
            trend_score = self._calculate_trend_sustainability(df)
            pattern_score = self._calculate_pattern_consistency(df)
            momentum_score = self._calculate_momentum_profile(df)

            # Combine scores
            timeframe, hold_days, confidence, reason = self._determine_timeframe(
                volatility_score,
                trend_score,
                pattern_score,
                momentum_score,
                current_strategy
            )

            return {
                'timeframe': timeframe,
                'recommended_hold_days': hold_days,
                'confidence': confidence,
                'reason': reason,
                'metrics': {
                    'volatility_score': volatility_score,
                    'trend_score': trend_score,
                    'pattern_score': pattern_score,
                    'momentum_score': momentum_score
                }
            }

        except Exception as e:
            return {
                'timeframe': 'SHORT_TERM',
                'recommended_hold_days': 5,
                'confidence': 0,
                'reason': f'Error: {str(e)}'
            }

    def _calculate_volatility_profile(self, df):
        """
        Calculate volatility score (0-100)

        High volatility (70-100): Short-term trades
        Medium volatility (40-70): Medium-term trades
        Low volatility (0-40): Long-term trades
        """
        try:
            # Calculate ATR percent
            atr = self._calculate_atr(df, period=14)
            current_price = df['Close'].iloc[-1]
            atr_percent = (atr / current_price) * 100

            # Calculate Bollinger Band width
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            bb_width = (std20.iloc[-1] / ma20.iloc[-1]) * 100

            # Calculate daily return std
            returns = df['Close'].pct_change().dropna()
            return_std = returns.std() * 100

            # Combine metrics
            volatility_score = (
                atr_percent * 2 * 15 +  # ATR weight
                bb_width * 25 +          # BB width weight
                return_std * 100 * 0.6    # Daily return std weight
            )

            # Normalize to 0-100
            volatility_score = min(100, max(0, volatility_score))

            return round(volatility_score, 1)
        except:
            return 50  # Default medium

    def _calculate_trend_sustainability(self, df):
        """
        Calculate trend sustainability score (0-100)

        High score (70-100): Long sustainable trend → long-term holding
        Medium score (40-70): Moderate trend → medium-term
        Low score (0-40): Weak trend → short-term
        """
        try:
            closes = df['Close']

            # 1. Directional consistency (last 50 days)
            ma10 = closes.rolling(10).mean()
            ma20 = closes.rolling(20).mean()
            ma50 = closes.rolling(50).mean()

            # Check alignment
            current_price = closes.iloc[-1]
            ma10_val = ma10.iloc[-1]
            ma20_val = ma20.iloc[-1]
            ma50_val = ma50.iloc[-1]

            alignment_score = 0
            if current_price > ma10_val > ma20_val > ma50_val:
                alignment_score = 40  # Perfect uptrend alignment
            elif current_price > ma10_val > ma20_val:
                alignment_score = 25
            elif current_price > ma10_val:
                alignment_score = 15

            # 2. Trend strength (ADX-like calculation)
            highs = df['High'].tail(20)
            lows = df['Low'].tail(20)

            higher_highs = sum([highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs))])
            higher_lows = sum([lows.iloc[i] > lows.iloc[i-1] for i in range(1, len(lows))])

            trend_strength = ((higher_highs + higher_lows) / (len(highs) * 2)) * 40

            # 3. Price efficiency (how straight is the trend)
            price_range = closes.tail(50).max() - closes.tail(50).min()
            net_move = abs(closes.iloc[-1] - closes.iloc[-50])
            efficiency = (net_move / price_range * 20) if price_range > 0 else 0

            # Combine
            sustainability_score = alignment_score + trend_strength + efficiency

            return round(min(100, max(0, sustainability_score)), 1)
        except:
            return 50

    def _calculate_pattern_consistency(self, df):
        """
        Calculate pattern consistency score (0-100)

        Consistent patterns → easier to hold longer
        Erratic patterns → exit faster
        """
        try:
            closes = df['Close']

            # 1. Coefficient of Variation (CV)
            mean_price = closes.mean()
            std_price = closes.std()
            cv = (std_price / mean_price) if mean_price > 0 else 1

            # Lower CV = more consistent
            cv_score = max(0, 100 - (cv * 200))  # Normalize

            # 2. Autocorrelation (price predictability)
            returns = closes.pct_change().dropna()
            if len(returns) > 10:
                autocorr = returns.autocorr(lag=1)
                autocorr_score = abs(autocorr) * 50  # Higher autocorr = more predictable
            else:
                autocorr_score = 0

            # 3. Range consistency
            daily_ranges = ((df['High'] - df['Low']) / df['Close'] * 100).tail(20)
            range_std = daily_ranges.std()
            range_score = max(0, 50 - range_std * 10)  # Lower std = more consistent

            # Combine
            pattern_score = cv_score * 0.3 + autocorr_score * 0.4 + range_score * 0.3

            return round(min(100, max(0, pattern_score)), 1)
        except:
            return 50

    def _calculate_momentum_profile(self, df):
        """
        Calculate momentum sustainability score (0-100)

        Strong sustained momentum → hold longer
        Weak/fading momentum → exit faster
        """
        try:
            closes = df['Close']
            current_price = closes.iloc[-1]

            # Multiple timeframe momentum
            mom_5d = ((current_price / closes.iloc[-6]) - 1) * 100 if len(closes) >= 6 else 0
            mom_10d = ((current_price / closes.iloc[-11]) - 1) * 100 if len(closes) >= 11 else 0
            mom_20d = ((current_price / closes.iloc[-21]) - 1) * 100 if len(closes) >= 21 else 0
            mom_50d = ((current_price / closes.iloc[-51]) - 1) * 100 if len(closes) >= 51 else 0

            # Check if momentum is accelerating or decelerating
            if mom_5d > mom_10d > mom_20d > 0:
                acceleration_score = 40  # Accelerating uptrend
            elif mom_10d > mom_20d > 0:
                acceleration_score = 25
            elif mom_20d > 0:
                acceleration_score = 15
            else:
                acceleration_score = 0

            # RSI trend (is momentum sustainable?)
            rsi = self._calculate_rsi(df)
            if 40 < rsi < 60:
                rsi_score = 30  # Healthy middle range
            elif 30 < rsi < 70:
                rsi_score = 20
            else:
                rsi_score = 10  # Extreme levels (reversal risk)

            # Volume confirmation
            volumes = df['Volume'].tail(20)
            avg_volume = volumes.mean()
            recent_volume = volumes.tail(5).mean()
            volume_score = min(30, (recent_volume / avg_volume) * 15) if avg_volume > 0 else 0

            # Combine
            momentum_score = acceleration_score + rsi_score + volume_score

            return round(min(100, max(0, momentum_score)), 1)
        except:
            return 50

    def _determine_timeframe(self, volatility, trend, pattern, momentum, strategy):
        """
        Determine optimal timeframe based on all scores

        Logic:
        - High trend + low volatility = LONG_TERM
        - Medium scores = MEDIUM_TERM
        - High volatility + weak trend = SHORT_TERM
        """
        # Calculate composite scores
        long_term_score = (
            (100 - volatility) * 0.3 +  # Low volatility favors long-term
            trend * 0.4 +                # Strong trend favors long-term
            pattern * 0.2 +              # Consistent pattern favors long-term
            momentum * 0.1               # Sustained momentum
        )

        short_term_score = (
            volatility * 0.4 +           # High volatility favors short-term
            (100 - trend) * 0.3 +        # Weak trend favors short-term
            (100 - pattern) * 0.2 +      # Erratic pattern favors short-term
            momentum * 0.1               # Can still have short-term momentum
        )

        medium_term_score = 100 - abs(long_term_score - short_term_score) / 2

        # Find best classification
        scores = {
            'LONG_TERM': long_term_score,
            'MEDIUM_TERM': medium_term_score,
            'SHORT_TERM': short_term_score
        }

        best_timeframe = max(scores, key=scores.get)
        confidence = scores[best_timeframe]

        # Determine holding days based on classification
        if best_timeframe == 'LONG_TERM':
            hold_days = 30  # 20-45 days
            reason = f"Strong trend ({trend:.0f}), low volatility ({volatility:.0f})"
        elif best_timeframe == 'MEDIUM_TERM':
            hold_days = 15  # 10-20 days
            reason = f"Moderate trend ({trend:.0f}), balanced characteristics"
        else:  # SHORT_TERM
            hold_days = 5  # 3-7 days
            reason = f"High volatility ({volatility:.0f}), quick moves expected"

        # Strategy adjustments
        if strategy == 'BREAKOUT' and best_timeframe == 'SHORT_TERM':
            hold_days = 7  # Breakouts need more time to develop
        elif strategy == 'MEAN_REVERSION':
            hold_days = min(hold_days, 10)  # Mean reversion typically faster

        return best_timeframe, hold_days, round(confidence, 1), reason

    def _calculate_atr(self, df, period=14):
        """Calculate ATR"""
        try:
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean().iloc[-1]
            return atr if not pd.isna(atr) else 0
        except:
            return 0

    def _calculate_rsi(self, df, period=14):
        """Calculate RSI"""
        try:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50

    def should_extend_holding(self, symbol_ns, current_days_held, current_pnl_pct):
        """
        Decide if a losing position should be held longer

        This solves: "Stock at -2% on day 5, but would be +5% on day 15"

        Args:
            symbol_ns: Stock symbol
            current_days_held: Days already held
            current_pnl_pct: Current P&L percentage

        Returns:
            dict with should_extend, recommended_extension_days, reason
        """
        try:
            # Only consider if in loss
            if current_pnl_pct >= 0:
                return {
                    'should_extend': False,
                    'recommended_extension_days': 0,
                    'reason': 'Position in profit'
                }

            # Get classification
            classification = self.classify_position(symbol_ns)

            # Check if stock has long-term potential
            if classification['timeframe'] in ['MEDIUM_TERM', 'LONG_TERM']:
                recommended_hold = classification['recommended_hold_days']

                if current_days_held < recommended_hold:
                    # Check recovery potential using statistical predictor
                    try:
                        from src.analyzers.statistical_predictor import get_statistical_predictor
                        predictor = get_statistical_predictor()

                        ticker = yf.Ticker(symbol_ns)
                        df = ticker.history(period='2mo')

                        if not df.empty:
                            # Get trend prediction
                            prediction = predictor.predict_price_trend(df, periods_ahead=10)

                            # If predicted to recover
                            if prediction['predicted_return'] > abs(current_pnl_pct):
                                extension_days = recommended_hold - current_days_held
                                return {
                                    'should_extend': True,
                                    'recommended_extension_days': extension_days,
                                    'reason': f"Predicted recovery: {prediction['predicted_return']:+.1f}% "
                                             f"(confidence: {prediction['confidence']:.0f}%)",
                                    'classification': classification['timeframe']
                                }
                    except:
                        pass

            # Default: don't extend
            return {
                'should_extend': False,
                'recommended_extension_days': 0,
                'reason': 'No recovery signals detected'
            }

        except Exception as e:
            return {
                'should_extend': False,
                'recommended_extension_days': 0,
                'reason': f'Error: {str(e)}'
            }


# Singleton
_classifier_instance = None

def get_timeframe_classifier():
    """Get singleton instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = PositionTimeframeClassifier()
    return _classifier_instance


if __name__ == "__main__":
    print("\n🧪 Testing Position Timeframe Classifier\n")

    classifier = PositionTimeframeClassifier()

    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'TATAMOTORS.NS']

    for symbol in test_stocks:
        print(f"\n{'='*60}")
        print(f"Testing: {symbol}")
        print(f"{'='*60}")

        result = classifier.classify_position(symbol)

        print(f"\n⏱️ Classification: {result['timeframe']}")
        print(f"📅 Recommended Hold: {result['recommended_hold_days']} days")
        print(f"🎯 Confidence: {result['confidence']:.1f}%")
        print(f"💡 Reason: {result['reason']}")

        if 'metrics' in result:
            metrics = result['metrics']
            print(f"\n📊 Metrics:")
            print(f"   Volatility: {metrics['volatility_score']:.1f}")
            print(f"   Trend: {metrics['trend_score']:.1f}")
            print(f"   Pattern: {metrics['pattern_score']:.1f}")
            print(f"   Momentum: {metrics['momentum_score']:.1f}")

        # Test extension logic
        print(f"\n🔍 Extension Test (at day 5, -2% loss):")
        extension = classifier.should_extend_holding(symbol, current_days_held=5, current_pnl_pct=-2)
        print(f"   Should Extend: {extension['should_extend']}")
        if extension['should_extend']:
            print(f"   Extension Days: {extension['recommended_extension_days']}")
            print(f"   Reason: {extension['reason']}")
