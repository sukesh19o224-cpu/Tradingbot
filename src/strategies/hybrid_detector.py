"""
🎯 Hybrid Signal Detector
Detects BOTH swing and positional trading opportunities for each stock
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

from config.settings import (
    SWING_MEAN_REVERSION_STOP, SWING_MOMENTUM_STOP, SWING_BREAKOUT_STOP,
    POSITIONAL_MEAN_REVERSION_STOP, POSITIONAL_MOMENTUM_STOP, POSITIONAL_BREAKOUT_STOP
)


class HybridDetector:
    """
    Detects both swing and positional trading setups

    A stock can be:
    - Swing only
    - Positional only
    - Both swing AND positional
    - Neither (no signal)
    """

    def __init__(self):
        self.swing_signals = []
        self.positional_signals = []

    def detect_opportunities(self, symbol: str, df_daily: pd.DataFrame,
                           df_15m: pd.DataFrame, base_signal: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Detect both swing and positional opportunities for a stock

        Args:
            symbol: Stock symbol
            df_daily: Daily timeframe data
            df_15m: 15-minute timeframe data
            base_signal: Base signal from signal generator

        Returns:
            (swing_signal, positional_signal) - either can be None
        """
        swing_signal = None
        positional_signal = None

        # Check for swing trading opportunity
        if self._is_swing_setup(df_daily, df_15m, base_signal):
            swing_signal = self._create_swing_signal(symbol, df_daily, df_15m, base_signal)

        # Check for positional trading opportunity
        if self._is_positional_setup(df_daily, base_signal):
            positional_signal = self._create_positional_signal(symbol, df_daily, base_signal)

        return swing_signal, positional_signal

    def _classify_signal_type(self, df_daily: pd.DataFrame, df_15m: pd.DataFrame,
                              signal: Dict, strategy: str) -> str:
        """
        Classify signal as MEAN_REVERSION, MOMENTUM, or BREAKOUT

        Mean Reversion: Price pullback to support/EMA, oversold bounce
        Momentum: Trend continuation, riding strong trends
        Breakout: Breaking resistance, high volume surge
        """
        try:
            latest = df_daily.iloc[-1]
            price = latest['close']
            prev = df_daily.iloc[-2]

            # BREAKOUT signals (highest priority for classification)
            # Criteria: Breaking above resistance with high volume
            if 'resistance' in signal:
                if price > signal['resistance'] * 1.005:  # Broke above resistance
                    avg_volume = df_daily['volume'].tail(20).mean()
                    if latest['volume'] > avg_volume * 1.5:
                        return 'BREAKOUT'

            # Check 20-day range breakout
            if len(df_daily) >= 20:
                high_20d = df_daily['high'].tail(20).max()
                if price > high_20d * 0.998:  # At/near 20-day high
                    avg_volume = df_daily['volume'].tail(20).mean()
                    if latest['volume'] > avg_volume * 1.2:
                        return 'BREAKOUT'

            # MEAN REVERSION signals
            # Criteria 1: Price at/near EMA support
            if all(key in latest.index for key in ['ema_21', 'ema_50']):
                ema_21 = latest['ema_21']
                ema_50 = latest['ema_50']

                # Price within 3% of EMA (at support)
                if (0.97 < price / ema_21 < 1.03) or (0.97 < price / ema_50 < 1.03):
                    # Check if coming from oversold
                    if 'rsi' in latest.index and latest['rsi'] < 50:
                        return 'MEAN_REVERSION'

            # Criteria 2: RSI oversold bounce
            if 'rsi' in latest.index:
                rsi = latest['rsi']
                if 30 < rsi < 45:  # Bouncing from oversold
                    return 'MEAN_REVERSION'

            # Criteria 3: Fibonacci retracement
            if 'fibonacci_0.618' in signal:
                fib_618 = signal['fibonacci_0.618']
                if 0.98 < price / fib_618 < 1.02:  # At Fib 0.618
                    return 'MEAN_REVERSION'

            # Criteria 4: Recent pullback in uptrend
            if len(df_daily) >= 10:
                high_10d = df_daily['high'].tail(10).max()
                pullback_pct = (high_10d / price - 1) * 100
                if 3 < pullback_pct < 10:  # 3-10% pullback
                    # But still in uptrend
                    if 'ema_50' in latest.index and price > latest['ema_50']:
                        return 'MEAN_REVERSION'

            # MOMENTUM signals (default if not MR or BO)
            # Criteria 1: Strong intraday momentum (for swing)
            if df_15m is not None and len(df_15m) >= 10:
                recent_15m = df_15m.tail(10)
                close_change = (recent_15m['close'].iloc[-1] / recent_15m['close'].iloc[0] - 1) * 100
                if close_change > 2.0:
                    return 'MOMENTUM'

            # Criteria 2: Price above all EMAs with momentum
            if all(key in latest.index for key in ['ema_9', 'ema_21', 'ema_50']):
                if (price > latest['ema_9'] and
                    price > latest['ema_21'] and
                    price > latest['ema_50']):
                    price_change = (price / prev['close'] - 1) * 100
                    if price_change > 1.0:  # Gaining >1%
                        return 'MOMENTUM'

            # Criteria 3: RSI trending up (50-70 range)
            if 'rsi' in latest.index and 'rsi' in prev.index:
                rsi = latest['rsi']
                rsi_prev = prev['rsi']
                if 50 < rsi < 75 and rsi > rsi_prev:
                    return 'MOMENTUM'

            # Default: Classify based on RSI
            if 'rsi' in latest.index:
                rsi = latest['rsi']
                if rsi < 50:
                    return 'MEAN_REVERSION'
                else:
                    return 'MOMENTUM'

            # Fallback
            return 'MOMENTUM'

        except Exception as e:
            print(f"⚠️  Error classifying signal type: {e}")
            return 'MOMENTUM'  # Safe default

    def _is_swing_setup(self, df_daily: pd.DataFrame, df_15m: pd.DataFrame, signal: Dict) -> bool:
        """
        Detect swing trading setup

        Swing characteristics:
        - Fast momentum (RSI spike, MACD crossover)
        - Breakout above resistance
        - High volume surge
        - Quick move expected (5-10% in 1-5 days)
        """
        if len(df_daily) < 20 or len(df_15m) < 50:
            return False

        try:
            latest_daily = df_daily.iloc[-1]
            latest_15m = df_15m.iloc[-1]
            prev_daily = df_daily.iloc[-2]

            # Criteria 1: Recent breakout (within last 1-2 days)
            if 'resistance' in signal:
                if latest_daily['close'] > signal['resistance'] * 1.005:  # Broke above resistance
                    # Check volume confirmation
                    avg_volume = df_daily['volume'].tail(20).mean()
                    if latest_daily['volume'] > avg_volume * 1.5:  # 50% above average volume
                        return True

            # Criteria 2: Momentum spike (RSI entering overbought from below)
            if 'rsi' in latest_daily.index:
                rsi_current = latest_daily['rsi']
                rsi_prev = prev_daily['rsi']
                if 55 < rsi_current < 75 and rsi_prev < 60:  # RSI spiking up
                    return True

            # Criteria 3: MACD bullish crossover (recent)
            if 'macd' in latest_daily.index and 'macd_signal' in latest_daily.index:
                macd = latest_daily['macd']
                macd_signal = latest_daily['macd_signal']
                macd_prev = prev_daily['macd']
                macd_signal_prev = prev_daily['macd_signal']

                # Bullish crossover in last 1-2 days
                if macd > macd_signal and macd_prev <= macd_signal_prev:
                    return True

            # Criteria 4: Strong intraday momentum (15m timeframe)
            if len(df_15m) >= 10:
                # Check last 2-3 hours (8-12 candles)
                recent_15m = df_15m.tail(10)
                close_change = (recent_15m['close'].iloc[-1] / recent_15m['close'].iloc[0] - 1) * 100

                # Strong intraday move (>2% in last 2-3 hours)
                if close_change > 2.0:
                    return True

            # Criteria 5: Price above all key EMAs with strong momentum
            if all(key in latest_daily.index for key in ['ema_9', 'ema_21', 'ema_50']):
                price = latest_daily['close']
                if (price > latest_daily['ema_9'] and
                    price > latest_daily['ema_21'] and
                    price > latest_daily['ema_50']):
                    # Check momentum
                    price_change_1d = (price / prev_daily['close'] - 1) * 100
                    if price_change_1d > 1.5:  # >1.5% gain today
                        return True

            return False

        except Exception as e:
            print(f"⚠️  Error detecting swing setup for {signal.get('symbol', 'unknown')}: {e}")
            return False

    def _is_positional_setup(self, df_daily: pd.DataFrame, signal: Dict) -> bool:
        """
        Detect positional trading setup

        Positional characteristics:
        - Strong established trend (EMA alignment)
        - Pullback to support/Fibonacci
        - Trend continuation pattern
        - Bigger move expected (15-30% in 2-4 weeks)
        """
        if len(df_daily) < 50:
            return False

        try:
            latest = df_daily.iloc[-1]
            price = latest['close']

            # Criteria 1: Strong uptrend (EMA alignment)
            if all(key in latest.index for key in ['ema_21', 'ema_50', 'ema_200']):
                ema_21 = latest['ema_21']
                ema_50 = latest['ema_50']
                ema_200 = latest['ema_200']

                # Perfect EMA alignment (21 > 50 > 200)
                if ema_21 > ema_50 > ema_200:
                    # Price near 21 EMA (pullback to support)
                    if 0.97 < price / ema_21 < 1.03:  # Within 3% of EMA
                        return True

            # Criteria 2: Pullback to Fibonacci level
            if 'fibonacci_0.618' in signal:
                fib_618 = signal['fibonacci_0.618']
                if 0.98 < price / fib_618 < 1.02:  # At Fibonacci 0.618
                    # Check trend is still intact
                    if 'ema_50' in latest.index and latest['ema_50'] > df_daily.iloc[-10]['ema_50']:
                        return True

            # Criteria 3: Consolidation breakout (3+ weeks)
            high_20d = df_daily['high'].tail(20).max()
            low_20d = df_daily['low'].tail(20).min()
            range_pct = (high_20d / low_20d - 1) * 100

            # Tight consolidation (< 8% range over 20 days)
            if range_pct < 8:
                # Breaking above consolidation with volume
                if price > high_20d * 0.998:  # Near/above range high
                    avg_volume = df_daily['volume'].tail(20).mean()
                    if latest['volume'] > avg_volume * 1.2:
                        return True

            # Criteria 4: Strong trend + pullback pattern
            # Trend strength: price significantly above 200 EMA
            if 'ema_200' in latest.index:
                ema_200 = latest['ema_200']
                if price > ema_200 * 1.10:  # >10% above 200 EMA (strong uptrend)
                    # Recent pullback (last 5 days)
                    high_5d = df_daily['high'].tail(5).max()
                    pullback_pct = (high_5d / price - 1) * 100

                    # Pulled back 3-8% (healthy retracement)
                    if 3 < pullback_pct < 8:
                        # Now showing signs of resumption
                        if latest['close'] > df_daily.iloc[-2]['close']:
                            return True

            # Criteria 5: Higher highs and higher lows (trending)
            if len(df_daily) >= 30:
                # Check last 30 days for clear trend
                highs = df_daily['high'].tail(30)
                lows = df_daily['low'].tail(30)

                # Divide into 3 periods
                h1, h2, h3 = highs.iloc[:10].max(), highs.iloc[10:20].max(), highs.iloc[20:].max()
                l1, l2, l3 = lows.iloc[:10].min(), lows.iloc[10:20].min(), lows.iloc[20:].min()

                # Higher highs and higher lows
                if h3 > h2 > h1 and l3 > l2 > l1:
                    # ADX confirms trend
                    if 'adx' in latest.index and latest['adx'] > 25:
                        return True

            return False

        except Exception as e:
            print(f"⚠️  Error detecting positional setup for {signal.get('symbol', 'unknown')}: {e}")
            return False

    def _create_swing_signal(self, symbol: str, df_daily: pd.DataFrame,
                            df_15m: pd.DataFrame, base_signal: Dict) -> Dict:
        """Create swing trading signal with appropriate parameters"""
        latest = df_daily.iloc[-1]
        entry_price = latest['close']

        # Swing trading targets: 5-10%
        target1 = entry_price * 1.05  # 5%
        target2 = entry_price * 1.08  # 8%
        target3 = entry_price * 1.10  # 10%

        # CRITICAL FIX #9: Use settings.py values instead of hardcoded
        stop_loss = entry_price * (1 - SWING_STOP_LOSS)

        # Calculate risk-reward
        risk = entry_price - stop_loss
        reward = target2 - entry_price
        risk_reward = reward / risk if risk > 0 else 0

        # DYNAMIC ALLOCATOR: Classify signal type
        signal_type = self._classify_signal_type(df_daily, df_15m, base_signal, 'swing')

        signal = {
            'symbol': symbol,
            'trade_type': '🔥 SWING TRADE',
            'strategy': 'swing',
            'signal_type': signal_type,  # 'MEAN_REVERSION', 'MOMENTUM', or 'BREAKOUT'
            'entry_price': entry_price,
            'target1': target1,
            'target2': target2,
            'target3': target3,
            'stop_loss': stop_loss,
            'risk_reward_ratio': risk_reward,
            'expected_holding': 'Same day (intraday only)',
            'max_holding_days': 1,  # ONE DAY TRADER - same day exit only (force exit at 3:25 PM)
            'expected_return': 2.5,  # 2.5% target (same day)
            'score': base_signal.get('score', 8.0),
            'timestamp': datetime.now().isoformat(),

            # Copy relevant indicators
            'rsi': base_signal.get('rsi'),
            'macd': base_signal.get('macd'),
            'volume_ratio': base_signal.get('volume_ratio'),
            'predicted_return': base_signal.get('predicted_return', 0),
            'ml_confidence': base_signal.get('ml_confidence', 0),
        }

        return signal

    def _create_positional_signal(self, symbol: str, df_daily: pd.DataFrame,
                                  base_signal: Dict) -> Dict:
        """Create positional trading signal with appropriate parameters"""
        latest = df_daily.iloc[-1]
        entry_price = latest['close']

        # Positional trading targets: 15-30%
        target1 = entry_price * 1.15  # 15%
        target2 = entry_price * 1.22  # 22%
        target3 = entry_price * 1.30  # 30%

        # CRITICAL FIX #9: Use settings.py values instead of hardcoded
        stop_loss = entry_price * (1 - POSITIONAL_STOP_LOSS)

        # Calculate risk-reward
        risk = entry_price - stop_loss
        reward = target2 - entry_price
        risk_reward = reward / risk if risk > 0 else 0

        # DYNAMIC ALLOCATOR: Classify signal type
        signal_type = self._classify_signal_type(df_daily, None, base_signal, 'positional')

        signal = {
            'symbol': symbol,
            'trade_type': '📈 POSITIONAL TRADE',
            'strategy': 'positional',
            'signal_type': signal_type,  # 'MEAN_REVERSION', 'MOMENTUM', or 'BREAKOUT'
            'entry_price': entry_price,
            'target1': target1,
            'target2': target2,
            'target3': target3,
            'stop_loss': stop_loss,
            'risk_reward_ratio': risk_reward,
            'expected_holding': '2-4 weeks',
            'max_holding_days': 30,  # Auto-exit after 30 days
            'expected_return': 22.0,  # 22% target
            'score': base_signal.get('score', 7.5),
            'timestamp': datetime.now().isoformat(),

            # Copy relevant indicators
            'rsi': base_signal.get('rsi'),
            'macd': base_signal.get('macd'),
            'trend_strength': base_signal.get('trend_strength'),
            'predicted_return': base_signal.get('predicted_return', 0),
            'ml_confidence': base_signal.get('ml_confidence', 0),
        }

        return signal
