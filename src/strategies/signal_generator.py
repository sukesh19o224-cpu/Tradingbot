"""
⚡ SIGNAL GENERATION ENGINE - Hybrid Swing + Positional Trading
Combines Technical, Mathematical, and ML indicators for high-probability signals
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import *
from src.indicators.technical_indicators import TechnicalIndicators
from src.indicators.mathematical_indicators import MathematicalIndicators
from src.ml_models.lstm_predictor import LSTMPredictor


class SignalGenerator:
    """
    Generate trading signals by combining all analysis methods

    Scoring System (0-10):
    - Technical Indicators: 40%
    - Mathematical Patterns: 30%
    - ML Prediction: 20%
    - Volume Analysis: 10%

    Signals generated only if score >= MIN_SIGNAL_SCORE (default 7.0)
    """

    def __init__(self):
        self.technical = TechnicalIndicators()
        self.mathematical = MathematicalIndicators()
        self.ml_predictor = LSTMPredictor()

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """
        Generate complete trading signal for a stock

        Args:
            symbol: Stock symbol
            df: Historical OHLCV data

        Returns:
            Signal dict with all analysis, or None if no signal
        """
        if df is None or len(df) < 50:
            return None

        try:
            # 1. Calculate Technical Indicators
            technical_result = self.technical.calculate_all(df)
            if technical_result is None:
                return None

            # 2. Calculate Mathematical Indicators
            mathematical_result = self.mathematical.calculate_all(df)
            if mathematical_result is None:
                mathematical_result = {
                    'mathematical_score': 5.0,
                    'signals': {},
                    'fibonacci': {},
                    'elliott_wave': {},
                    'gann': {},
                    'support_resistance': {}
                }

            # 3. ML Prediction
            ml_prediction = self.ml_predictor.predict(df, technical_result)

            # 4. Calculate Overall Signal Score
            signal_score = self._calculate_signal_score(
                technical_result,
                mathematical_result,
                ml_prediction
            )

            # 5. Determine Trade Type (Swing vs Positional)
            trade_type = self._determine_trade_type(
                technical_result,
                mathematical_result,
                ml_prediction
            )

            # 6. Calculate Entry, Targets, and Stop Loss
            # Use strategy-specific config based on signal type (MEAN_REVERSION, MOMENTUM, BREAKOUT)
            from config.settings import MEAN_REVERSION_CONFIG, MOMENTUM_CONFIG, BREAKOUT_CONFIG
            
            current_price = technical_result['price']
            entry_price = current_price
            
            # Get signal type from technical analysis (MEAN_REVERSION, MOMENTUM, or BREAKOUT)
            signal_classification = technical_result.get('signal_type', 'MOMENTUM')

            if trade_type == 'SWING':
                # SWING: Use config values (NO HARDCODED DUPLICATES)
                if signal_classification == 'MEAN_REVERSION':
                    # Mean reversion swing: Use config stop loss
                    targets = self._calculate_targets(entry_price, [0.04, 0.07, 0.10])
                    stop_loss = entry_price * (1 - SWING_STOP_LOSS)  # From config
                elif signal_classification == 'BREAKOUT':
                    # Breakout swing: Use config stop loss
                    targets = self._calculate_targets(entry_price, [0.05, 0.08, 0.12])
                    stop_loss = entry_price * (1 - SWING_STOP_LOSS)  # From config
                else:  # MOMENTUM
                    # Momentum swing: Use config stop loss
                    targets = self._calculate_targets(entry_price, [0.04, 0.07, 0.10])
                    stop_loss = entry_price * (1 - SWING_STOP_LOSS)  # From config
                hold_days = (SWING_HOLD_DAYS_MIN + SWING_HOLD_DAYS_MAX) // 2
            else:  # POSITIONAL
                # For positional trades, use strategy-specific config
                if signal_classification == 'MEAN_REVERSION':
                    strategy_config = MEAN_REVERSION_CONFIG
                elif signal_classification == 'BREAKOUT':
                    strategy_config = BREAKOUT_CONFIG
                else:  # MOMENTUM or default
                    strategy_config = MOMENTUM_CONFIG
                
                targets = self._calculate_targets(entry_price, strategy_config['TARGETS'])
                stop_loss = entry_price * (1 - strategy_config['STOP_LOSS'])
                hold_days = POSITIONAL_HOLD_DAYS_MAX  # Use max days for faster exits (15 days)

            # 7. Build complete signal
            # Include strategy classification (MEAN_REVERSION, MOMENTUM, BREAKOUT)
            mean_reversion_quality = technical_result.get('mean_reversion_quality', {})
            momentum_quality = technical_result.get('momentum_quality', {})
            
            signal = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'signal_type': signal_classification,  # MEAN_REVERSION, MOMENTUM, or BREAKOUT
                'trade_type': trade_type,
                'score': round(signal_score, 2),
                'strategy': 'swing' if trade_type == 'SWING' else 'positional',

                # Price & Targets
                'current_price': round(current_price, 2),
                'entry_price': round(entry_price, 2),
                'target1': round(targets[0], 2),
                'target2': round(targets[1], 2),
                'target3': round(targets[2], 2),
                'stop_loss': round(stop_loss, 2),

                # Strategy Quality (for filtering weak setups)
                'mean_reversion_valid': mean_reversion_quality.get('is_valid', True),
                'mean_reversion_score': mean_reversion_quality.get('score', 0),
                'momentum_valid': momentum_quality.get('is_valid', True),
                'momentum_score': momentum_quality.get('score', 0),

                # Technical Analysis
                'technical_score': technical_result['signals']['technical_score'],
                'rsi': round(technical_result['rsi'], 2),
                'macd_signal': technical_result['signals'].get('macd_signal'),
                'ema_trend': technical_result['signals'].get('ema_trend'),
                'adx': round(technical_result['adx'], 2),
                'volume_ratio': round(technical_result['volume_ratio'], 2),

                # Mathematical Analysis
                'mathematical_score': mathematical_result['mathematical_score'],
                'fibonacci_signal': mathematical_result['signals'].get('fibonacci'),
                'elliott_wave': mathematical_result['elliott_wave'].get('pattern'),
                'at_support': mathematical_result['support_resistance'].get('nearest_support', 0),

                # ML Prediction
                'predicted_return': ml_prediction['predicted_return'],
                'ml_confidence': ml_prediction['confidence'],
                'ml_direction': ml_prediction['direction'],

                # Trade Parameters
                'recommended_hold_days': hold_days,
                'risk_reward_ratio': round((targets[1] - entry_price) / (entry_price - stop_loss), 2),

                # Risk Assessment
                'risk_level': self._assess_risk_level(signal_score, technical_result, mathematical_result),

                # Full Details (for analysis)
                '_technical_details': technical_result,
                '_mathematical_details': mathematical_result,
                '_ml_details': ml_prediction
            }

            # Only return signal if score meets minimum threshold
            # ULTRA STRICT: Swing requires 8.5+, Positional requires 7.0
            min_required_score = MIN_SWING_SIGNAL_SCORE if trade_type == 'SWING' else MIN_SIGNAL_SCORE

            if signal_score < min_required_score:
                return None  # Score too low for this trade type
            
            # ADDITIONAL SWING VALIDATION: Double-check 5-day profit criteria
            if trade_type == 'SWING':
                rsi = signal.get('rsi', 0)
                adx = signal.get('adx', 0)
                volume_ratio = signal.get('volume_ratio', 1.0)
                
                # Must meet ALL swing criteria for 5-day profit potential
                if not (50 <= rsi <= 70 and adx >= 35 and volume_ratio >= 2.0):
                    print(f"   ⚠️ {symbol}: Swing rejected (RSI:{rsi:.1f}, ADX:{adx:.1f}, Vol:{volume_ratio:.1f}x)")
                    return None
            
            return signal

        except Exception as e:
            print(f"❌ Signal generation error for {symbol}: {e}")
            return None

    def _calculate_signal_score(self, technical: Dict, mathematical: Dict, ml: Dict) -> float:
        """
        Calculate overall signal score (0-10) using weighted combination

        Weights:
        - Technical: 40%
        - Mathematical: 30%
        - ML: 20%
        - Volume: 10%
        """
        try:
            # Technical score (0-10)
            tech_score = technical['signals']['technical_score']

            # Mathematical score (0-10)
            math_score = mathematical['mathematical_score']

            # ML score (convert to 0-10 scale)
            ml_return = ml['predicted_return']
            ml_conf = ml['confidence']

            # ML score: positive return * confidence
            if ml_return > 0:
                ml_score = min(10, (ml_return / 10) * 10 * ml_conf)  # Normalize to 0-10
            else:
                ml_score = 0

            # Volume score (0-10)
            volume_ratio = technical.get('volume_ratio', 1.0)
            volume_score = min(10, volume_ratio * 5)  # 2x volume = 10 points

            # Weighted combination
            overall_score = (
                tech_score * WEIGHTS['technical'] +
                math_score * WEIGHTS['mathematical'] +
                ml_score * WEIGHTS['ml_prediction'] +
                volume_score * WEIGHTS['volume']
            ) / sum(WEIGHTS.values())

            return round(overall_score, 2)

        except Exception as e:
            print(f"❌ Score calculation error: {e}")
            return 0

    def _determine_trade_type(self, technical: Dict, mathematical: Dict, ml: Dict) -> str:
        """
        Determine if this should be a SWING or POSITIONAL trade

        Criteria:
        - SWING (5-day profit): RSI 50-70, ADX ≥35, Volume ≥2x, Strong momentum
        - POSITIONAL: Strong trends, Elliott Wave impulse, long-term momentum
        """
        try:
            # SWING QUALIFICATION (ULTRA STRICT - 5-day profit potential)
            rsi = technical.get('rsi', 0)
            adx = technical.get('adx', 0)
            volume_ratio = technical.get('volume_ratio', 1.0)
            
            # SWING must meet ALL these criteria for 5-day profit:
            # 1. RSI 50-70: Strong momentum but not overbought
            # 2. ADX ≥35: Explosive trend strength
            # 3. Volume ≥2x: Strong buying pressure
            # 4. MACD bullish crossover: Recent momentum shift
            swing_qualified = (
                50 <= rsi <= 70 and
                adx >= 35 and
                volume_ratio >= 2.0 and
                technical.get('signals', {}).get('macd_signal') == 'BULLISH'
            )
            
            if swing_qualified and SWING_ENABLED:
                return 'SWING'
            
            # Otherwise, check for POSITIONAL
            positional_score = 0

            # 1. Strong ADX indicates trend following (positional)
            if adx > 25:
                positional_score += 2

            # 2. Price above long-term EMA
            if technical.get('ema_200', 0) > 0 and technical.get('price', 0) > technical.get('ema_200', 0):
                positional_score += 1

            # 3. Elliott Wave impulse pattern
            if mathematical.get('elliott_wave', {}).get('pattern') == 'IMPULSE_UP':
                positional_score += 2

            # 4. ML predicts long-term gains
            if ml.get('predicted_return', 0) > 10:
                positional_score += 2

            # 5. Strong 20-day momentum
            if technical.get('momentum_20d', 0) > 8:
                positional_score += 1

            # If positional score >= 5, it's a POSITIONAL trade
            if positional_score >= 5 and POSITIONAL_ENABLED:
                return 'POSITIONAL'
            elif SWING_ENABLED:
                return 'SWING'
            else:
                return 'SWING'  # Default

        except Exception as e:
            print(f"❌ Trade type determination error: {e}")
            return 'SWING'

    def _calculate_targets(self, entry_price: float, target_percentages: List[float]) -> List[float]:
        """Calculate target prices based on entry and percentage targets"""
        return [entry_price * (1 + pct) for pct in target_percentages]

    def _assess_risk_level(self, score: float, technical: Dict, mathematical: Dict) -> str:
        """
        Assess risk level of the trade

        Returns: 'LOW', 'MEDIUM', 'HIGH'
        """
        try:
            # High score + confirming signals = LOW risk
            if score >= HIGH_QUALITY_SCORE:
                if (technical['signals'].get('ema_trend') == 'BULLISH' and
                    technical.get('adx', 0) > 25):
                    return 'LOW'

            # Medium score or mixed signals = MEDIUM risk
            if score >= 7.5:
                return 'MEDIUM'

            # Low score or weak signals = HIGH risk
            return 'HIGH'

        except:
            return 'MEDIUM'

    def scan_multiple_stocks(self, symbols: List[str], stock_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Scan multiple stocks and return all valid signals

        Args:
            symbols: List of stock symbols
            stock_data: Dict mapping symbol to DataFrame

        Returns:
            List of signal dicts, sorted by score (highest first)
        """
        signals = []

        print(f"\n🔍 Scanning {len(symbols)} stocks for signals...")

        for i, symbol in enumerate(symbols, 1):
            print(f"   [{i}/{len(symbols)}] {symbol}...", end=' ')

            df = stock_data.get(symbol)
            if df is None:
                print("⚠️ No data")
                continue

            signal = self.generate_signal(symbol, df)

            if signal:
                signals.append(signal)
                print(f"✅ SIGNAL! Score: {signal['score']}/10")
            else:
                print("⏭️")

        # Sort by score (highest first)
        signals.sort(key=lambda x: x['score'], reverse=True)

        print(f"\n✅ Found {len(signals)} signals (score >= {MIN_SIGNAL_SCORE})")

        return signals


def test_signal_generator():
    """Test the signal generation engine"""
    from src.data.data_fetcher import DataFetcher

    print("🧪 Testing Signal Generator...")

    # Fetch data
    fetcher = DataFetcher()
    test_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']

    print("\n📡 Fetching stock data...")
    stock_data = fetcher.get_multiple_stocks(test_symbols)

    # Generate signals
    generator = SignalGenerator()
    signals = generator.scan_multiple_stocks(test_symbols, stock_data)

    if signals:
        print(f"\n🎯 Top Signal:")
        top = signals[0]
        print(f"   Symbol: {top['symbol']}")
        print(f"   Score: {top['score']}/10")
        print(f"   Type: {top['trade_type']}")
        print(f"   Entry: ₹{top['entry_price']:.2f}")
        print(f"   Target 2: ₹{top['target2']:.2f} ({((top['target2']/top['entry_price']-1)*100):.1f}%)")
        print(f"   Stop Loss: ₹{top['stop_loss']:.2f}")
        print(f"   Risk/Reward: {top['risk_reward_ratio']:.1f}:1")
    else:
        print("\n⚠️ No signals found (try lowering MIN_SIGNAL_SCORE in settings)")


if __name__ == "__main__":
    test_signal_generator()
