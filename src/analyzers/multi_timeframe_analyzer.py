"""
V5.5 ULTRA - Multi-Timeframe Analysis
Analyzes stocks across multiple timeframes for stronger signals
"""
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MultiTimeframeAnalyzer:
    """
    Analyze stocks across multiple timeframes

    Features:
    - Hourly, Daily, Weekly chart analysis
    - Trend alignment detection
    - Multi-timeframe confirmation
    - Stronger signals when all timeframes align
    """

    def __init__(self):
        self.timeframes = {
            'hourly': '1h',
            'daily': '1d',
            'weekly': '1wk'
        }

    def analyze_multi_timeframe(self, symbol: str) -> Dict:
        """
        Analyze symbol across all timeframes

        Returns:
        {
            'alignment_score': 0-100,
            'timeframe_signals': {timeframe: signal},
            'overall_trend': 'BULLISH'/'BEARISH'/'NEUTRAL',
            'confidence': 0-100
        }
        """
        logger.info(f"🔍 Multi-timeframe analysis for {symbol}")

        timeframe_data = {}
        timeframe_signals = {}

        # Fetch data for each timeframe
        for tf_name, tf_period in self.timeframes.items():
            try:
                data = self._fetch_timeframe_data(symbol, tf_period, tf_name)
                if data is not None and len(data) > 0:
                    signal = self._analyze_timeframe(data, tf_name)
                    timeframe_data[tf_name] = data
                    timeframe_signals[tf_name] = signal
            except Exception as e:
                logger.warning(f"Failed to analyze {tf_name} for {symbol}: {e}")
                timeframe_signals[tf_name] = {'trend': 'NEUTRAL', 'strength': 0}

        # Calculate alignment
        alignment = self._calculate_alignment(timeframe_signals)

        return {
            'alignment_score': alignment['score'],
            'timeframe_signals': timeframe_signals,
            'overall_trend': alignment['trend'],
            'confidence': alignment['confidence'],
            'aligned': alignment['aligned']
        }

    def _fetch_timeframe_data(self, symbol: str, interval: str, tf_name: str) -> pd.DataFrame:
        """Fetch data for specific timeframe"""
        periods = {
            'hourly': '5d',   # Last 5 days of hourly data
            'daily': '90d',   # Last 90 days
            'weekly': '2y'    # Last 2 years
        }

        period = periods.get(tf_name, '90d')

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            return data
        except Exception as e:
            logger.error(f"Error fetching {tf_name} data for {symbol}: {e}")
            return None

    def _analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze trend and strength for a timeframe"""
        if df is None or len(df) < 10:
            return {'trend': 'NEUTRAL', 'strength': 0, 'details': 'Insufficient data'}

        # Calculate indicators
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()

        current_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else current_price
        sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else current_price

        # Trend determination
        trend = 'NEUTRAL'
        strength = 50

        if current_price > sma_20 > sma_50:
            trend = 'BULLISH'
            # Strength based on price distance from SMA_20
            strength = min(100, 60 + (current_price - sma_20) / sma_20 * 200)

        elif current_price < sma_20 < sma_50:
            trend = 'BEARISH'
            strength = min(100, 60 + (sma_20 - current_price) / current_price * 200)

        else:
            # Mixed signals
            if current_price > sma_20:
                trend = 'BULLISH'
                strength = 55
            elif current_price < sma_20:
                trend = 'BEARISH'
                strength = 55

        # Volume confirmation
        avg_volume = df['Volume'].tail(20).mean()
        recent_volume = df['Volume'].tail(5).mean()
        volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1

        if volume_surge > 1.5:
            strength = min(100, strength + 10)

        return {
            'trend': trend,
            'strength': strength,
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'volume_surge': volume_surge
        }

    def _calculate_alignment(self, signals: Dict) -> Dict:
        """Calculate alignment between timeframes"""
        if not signals:
            return {
                'score': 0,
                'trend': 'NEUTRAL',
                'confidence': 0,
                'aligned': False
            }

        trends = [s['trend'] for s in signals.values()]
        strengths = [s['strength'] for s in signals.values()]

        # Count bullish/bearish signals
        bullish_count = trends.count('BULLISH')
        bearish_count = trends.count('BEARISH')
        total_count = len(trends)

        # Determine overall trend
        if bullish_count >= 2:
            overall_trend = 'BULLISH'
            alignment_pct = bullish_count / total_count
        elif bearish_count >= 2:
            overall_trend = 'BEARISH'
            alignment_pct = bearish_count / total_count
        else:
            overall_trend = 'NEUTRAL'
            alignment_pct = 0.5

        # Alignment score (0-100)
        alignment_score = alignment_pct * 100

        # Average strength
        avg_strength = sum(strengths) / len(strengths) if strengths else 50

        # Confidence: Higher when aligned and strong
        confidence = (alignment_score * 0.6 + avg_strength * 0.4)

        # Fully aligned if all timeframes agree
        aligned = (bullish_count == total_count) or (bearish_count == total_count)

        return {
            'score': alignment_score,
            'trend': overall_trend,
            'confidence': confidence,
            'aligned': aligned
        }

    def should_trade_based_on_timeframes(self, mtf_result: Dict, strategy: str) -> bool:
        """
        Decide if trade should be taken based on multi-timeframe analysis
        """
        # For swing trading, require at least daily + hourly alignment
        if strategy in ['MOMENTUM', 'BREAKOUT']:
            return mtf_result['alignment_score'] >= 66.6

        # For positional trading, require all timeframes aligned
        elif strategy == 'POSITIONAL':
            return mtf_result['aligned']

        # For mean reversion, we want misalignment
        elif strategy == 'MEAN_REVERSION':
            signals = mtf_result['timeframe_signals']
            daily_bearish = signals.get('daily', {}).get('trend') == 'BEARISH'
            weekly_bullish = signals.get('weekly', {}).get('trend') == 'BULLISH'
            return daily_bearish and weekly_bullish

        return True

    def get_enhanced_opportunity_score(self, base_score: float, mtf_result: Dict) -> float:
        """Enhance opportunity score based on multi-timeframe alignment"""
        alignment_boost = mtf_result['alignment_score'] / 10
        confidence_boost = mtf_result['confidence'] / 20
        alignment_bonus = 5 if mtf_result['aligned'] else 0

        enhanced_score = base_score + alignment_boost + confidence_boost + alignment_bonus

        return min(100, enhanced_score)
