"""
📊 Multi-Timeframe Analyzer
Uses both Daily and 15-minute candles for better entry/exit timing
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime

from src.data.data_fetcher import DataFetcher
from src.indicators.technical_indicators import TechnicalIndicators
from src.indicators.mathematical_indicators import MathematicalIndicators


class MultiTimeframeAnalyzer:
    """
    Analyze stocks using multiple timeframes

    Strategy:
    - Daily timeframe: Overall trend and signal quality
    - 15-minute timeframe: Precise entry/exit timing
    """

    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.technical_indicators = TechnicalIndicators()
        self.mathematical_indicators = MathematicalIndicators()

    def analyze(self, symbol: str) -> Optional[Dict]:
        """
        Perform multi-timeframe analysis

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with analysis results or None
        """
        try:
            # Fetch daily data (6 months for trend)
            df_daily = self.data_fetcher.get_stock_data(symbol, period='6mo', interval='1d')

            if df_daily is None or len(df_daily) < 100:
                return None

            # Fetch 15-minute data (5 days for entry/exit timing)
            df_15m = self.data_fetcher.get_stock_data(symbol, period='5d', interval='15m')

            if df_15m is None or len(df_15m) < 20:
                # If 15m data not available, use daily only
                df_15m = None

            # Analyze daily timeframe (trend confirmation)
            daily_analysis = self._analyze_daily(df_daily)

            # Analyze 15-minute timeframe (entry/exit timing)
            intraday_analysis = self._analyze_intraday(df_15m) if df_15m is not None else None

            # Combine analyses
            combined = self._combine_timeframes(daily_analysis, intraday_analysis)

            return combined

        except Exception as e:
            print(f"⚠️ Error analyzing {symbol}: {e}")
            return None

    def analyze_stock(self, symbol: str, daily_df: pd.DataFrame, intraday_df: Optional[pd.DataFrame] = None) -> Optional[Dict]:
        """
        Perform multi-timeframe analysis with pre-fetched data

        This method is used by sequential scanner which already fetched the data

        Args:
            symbol: Stock symbol
            daily_df: Pre-fetched daily OHLCV data
            intraday_df: Pre-fetched 15-min OHLCV data (optional)

        Returns:
            Dictionary with analysis results or None
        """
        try:
            if daily_df is None or len(daily_df) < 30:
                return None

            # Analyze daily timeframe (trend confirmation)
            daily_analysis = self._analyze_daily(daily_df)

            # Analyze 15-minute timeframe (entry/exit timing) if available
            intraday_analysis = self._analyze_intraday(intraday_df) if intraday_df is not None and len(intraday_df) > 10 else None

            # Combine analyses
            combined = self._combine_timeframes(daily_analysis, intraday_analysis)
            combined['symbol'] = symbol

            return combined

        except Exception as e:
            # Silent fail for individual stocks
            return None

    def _analyze_daily(self, df: pd.DataFrame) -> Dict:
        """
        Analyze daily timeframe for trend and signal quality

        Args:
            df: Daily OHLCV data

        Returns:
            Daily analysis results
        """
        # Calculate technical indicators
        indicators = self.technical_indicators.calculate_all(df)

        # Check if indicators failed
        if indicators is None:
            current_price = float(df['Close'].iloc[-1])
            return {
                'timeframe': 'DAILY',
                'current_price': current_price,
                'trend': 'UNKNOWN',
                'trend_score': 5,
                'rsi': 50,
                'adx': 0,  # No trend strength
                'macd': 0,
                'macd_signal': 'HOLD',
                'macd_histogram': 0,
                'ema_alignment': False,
                'support_level': current_price * 0.95,
                'resistance_level': current_price * 1.05,
                'fibonacci_levels': {},
                'volume_trend': 'NORMAL',
            }

        # Calculate mathematical indicators
        math_indicators = self.mathematical_indicators.calculate_all(df)

        # If math_indicators is None, use empty dict
        if math_indicators is None:
            math_indicators = {
                'fibonacci': {},
                'elliott_wave': {'pattern': 'UNKNOWN', 'wave_count': 0},
                'mathematical_score': 5.0,
                'signals': {}
            }

        # Determine trend
        current_price = float(df['Close'].iloc[-1])
        ema_50 = indicators['ema_50']
        ema_200 = indicators['ema_200']

        if current_price > ema_50 > ema_200:
            trend = 'STRONG_UPTREND'
            trend_score = 10
        elif current_price > ema_50:
            trend = 'UPTREND'
            trend_score = 8
        elif current_price > ema_200:
            trend = 'WEAK_UPTREND'
            trend_score = 6
        elif current_price < ema_50 < ema_200:
            trend = 'STRONG_DOWNTREND'
            trend_score = 2
        else:
            trend = 'SIDEWAYS'
            trend_score = 5

        # Extract REAL mathematical indicators
        fibonacci = math_indicators.get('fibonacci', {})
        elliott_wave = math_indicators.get('elliott_wave', {})
        math_signals = math_indicators.get('signals', {})
        math_score = math_indicators.get('mathematical_score', 5.0)

        # Extract support/resistance from math indicators
        sr = math_indicators.get('support_resistance', {})
        nearest_support = sr.get('nearest_support', current_price * 0.95)
        nearest_resistance = sr.get('nearest_resistance', current_price * 1.05)

        return {
            'timeframe': 'DAILY',
            'current_price': current_price,
            'trend': trend,
            'trend_score': trend_score,
            'rsi': indicators['rsi'],
            'adx': indicators['adx'],  # REAL ADX from technical indicators
            'macd': indicators['macd'],
            'macd_signal': indicators['macd_signal'],
            'macd_histogram': indicators['macd_histogram'],
            'ema_alignment': current_price > ema_50,
            'support_level': nearest_support,
            'resistance_level': nearest_resistance,
            'fibonacci_levels': fibonacci,
            'volume_trend': indicators['signals']['volume_signal'],

            # REAL Mathematical indicators
            'mathematical_score': math_score,
            'fibonacci_signal': math_signals.get('fibonacci', 'NO_SIGNAL'),
            'elliott_wave_pattern': elliott_wave.get('pattern', 'UNKNOWN'),
            'elliott_wave_count': elliott_wave.get('wave_count', 0),
            'elliott_signal': math_signals.get('elliott', 'NEUTRAL'),
            'technical_signals': indicators['signals'],  # All technical signals
            
            # ADD MISSING EMAs for signal classification
            'ema_20': indicators.get('ema_20', 0),
            'ema_50': ema_50,
            'ema_200': ema_200,
        }

    def _analyze_intraday(self, df: pd.DataFrame) -> Dict:
        """
        Analyze 15-minute timeframe for entry/exit timing

        Args:
            df: 15-minute OHLCV data

        Returns:
            Intraday analysis results
        """
        # Calculate technical indicators on 15m timeframe
        indicators = self.technical_indicators.calculate_all(df)

        # If indicators failed (not enough data), return minimal analysis
        if indicators is None:
            current_price = float(df['Close'].iloc[-1])
            return {
                'timeframe': '15MIN',
                'current_price': current_price,
                'entry_signals': {},
                'exit_signals': {},
                'entry_quality': 5.0,  # Neutral
                'rsi': 50,  # Neutral
                'macd_histogram': 0,
                'recent_high': float(df['High'].tail(min(20, len(df))).max()),
                'recent_low': float(df['Low'].tail(min(20, len(df))).min()),
            }

        current_price = float(df['Close'].iloc[-1])

        # Entry signals (15m timeframe)
        entry_signals = {
            'rsi_oversold': indicators['rsi'] < 35,  # More aggressive on 15m
            'macd_bullish': indicators['macd_signal'] == 'BUY',
            'price_above_vwap': current_price > df['Close'].rolling(min(20, len(df))).mean().iloc[-1],
            'recent_breakout': self._detect_breakout(df),
        }

        # Exit signals (15m timeframe)
        exit_signals = {
            'rsi_overbought': indicators['rsi'] > 65,  # Earlier exit on 15m
            'macd_bearish': indicators['macd_signal'] == 'SELL',
            'price_below_vwap': current_price < df['Close'].rolling(min(20, len(df))).mean().iloc[-1],
            'momentum_weakening': self._check_momentum(df),
        }

        # Calculate entry quality score
        entry_score = sum(entry_signals.values()) / len(entry_signals) * 10

        return {
            'timeframe': '15MIN',
            'current_price': current_price,
            'entry_signals': entry_signals,
            'exit_signals': exit_signals,
            'entry_quality': entry_score,
            'rsi': indicators['rsi'],
            'macd_histogram': indicators['macd_histogram'],
            'recent_high': float(df['High'].tail(min(20, len(df))).max()),
            'recent_low': float(df['Low'].tail(min(20, len(df))).min()),
        }

    def _detect_breakout(self, df: pd.DataFrame) -> bool:
        """
        Detect recent breakout on 15m chart
        
        Breakout = Price breaking above recent consolidation/resistance
        Industry standard: Last 3-5 candles must be above prior 10-20 candle high
        """
        if len(df) < 15:
            return False

        current_price = float(df['Close'].iloc[-1])
        
        # Check last 3 candles (current + 2 prior) - must all be elevated
        recent_3_candles_low = float(df['Low'].iloc[-3:].min())
        
        # Get consolidation high from prior 10 candles (before the breakout)
        consolidation_high = float(df['High'].iloc[-13:-3].max())
        
        # BREAKOUT CONDITIONS:
        # 1. Current price above consolidation (0.2%+ breakout - more lenient)
        # 2. Last 3 candles mostly stayed above consolidation (2 out of 3 is okay)
        breakout_threshold = consolidation_high * 1.002  # 0.2% above consolidation (was 0.3%)
        
        is_above_consolidation = current_price > breakout_threshold
        
        # Check how many of last 3 candles held above consolidation (need 2 out of 3)
        candles_above = sum(1 for price in df['Low'].iloc[-3:] if price > consolidation_high)
        sustained_breakout = candles_above >= 2  # At least 2 out of 3 candles held
        
        return is_above_consolidation and sustained_breakout

    def _check_momentum(self, df: pd.DataFrame) -> bool:
        """Check if momentum is weakening"""
        if len(df) < 10:
            return False

        # Compare recent candles
        recent_closes = df['Close'].tail(10)
        momentum_weakening = recent_closes.iloc[-1] < recent_closes.iloc[-3]

        return momentum_weakening

    def _combine_timeframes(self, daily: Dict, intraday: Optional[Dict]) -> Dict:
        """
        Combine daily and intraday analysis

        Strategy:
        - Daily: Determines IF we should trade (trend + signal quality)
        - 15-minute: Determines WHEN to enter/exit (timing)

        Args:
            daily: Daily analysis results
            intraday: Intraday analysis results (or None)

        Returns:
            Combined analysis
        """
        # Start with daily analysis
        combined = {
            'symbol': None,  # Will be set by caller
            'daily_trend': daily['trend'],
            'daily_trend_score': daily['trend_score'],
            'current_price': daily['current_price'],
            'support': daily['support_level'],
            'resistance': daily['resistance_level'],
            'fibonacci': daily['fibonacci_levels'],
        }

        if intraday:
            # Add intraday timing signals
            combined.update({
                'has_intraday_data': True,
                'intraday_entry_quality': intraday['entry_quality'],
                'intraday_entry_signals': intraday['entry_signals'],
                'intraday_exit_signals': intraday['exit_signals'],
                'intraday_rsi': intraday['rsi'],
                'recent_high_15m': intraday['recent_high'],
                'recent_low_15m': intraday['recent_low'],
            })

            # Determine optimal entry timing
            entry_signals_count = sum(intraday['entry_signals'].values())

            if entry_signals_count >= 3:
                combined['entry_timing'] = 'EXCELLENT'  # 3+ signals = enter now
                combined['entry_timing_score'] = 10
            elif entry_signals_count >= 2:
                combined['entry_timing'] = 'GOOD'  # 2 signals = good entry
                combined['entry_timing_score'] = 7.5
            elif entry_signals_count >= 1:
                combined['entry_timing'] = 'FAIR'  # 1 signal = wait for more confirmation
                combined['entry_timing_score'] = 5
            else:
                combined['entry_timing'] = 'POOR'  # No signals = wait
                combined['entry_timing_score'] = 2

            # Determine exit urgency
            exit_signals_count = sum(intraday['exit_signals'].values())

            if exit_signals_count >= 3:
                combined['exit_urgency'] = 'URGENT'  # Exit now
            elif exit_signals_count >= 2:
                combined['exit_urgency'] = 'HIGH'  # Consider exiting
            else:
                combined['exit_urgency'] = 'LOW'  # Hold

        else:
            # No intraday data - use daily only
            combined.update({
                'has_intraday_data': False,
                'entry_timing': 'DAILY_ONLY',
                'entry_timing_score': daily['trend_score'] * 0.7,  # Reduced confidence without 15m
                'exit_urgency': 'DAILY_ONLY',
            })

        # Calculate COMPREHENSIVE quality score using ALL indicators
        # INDUSTRY STANDARD: Technical indicators (RSI/ADX/MACD/Volume) are primary edge (50%)
        # Math indicators (Fibonacci/S/R) are context only (10%)
        technical_score = daily.get('technical_signals', {}).get('technical_score', 5.0)
        mathematical_score = daily.get('mathematical_score', 5.0)

        if intraday:
            # With intraday: Technical indicators as primary edge
            combined['overall_quality'] = (
                technical_score * 0.50 +             # Technical (RSI, MACD, ADX, Volume) - PRIMARY EDGE (50%)
                daily['trend_score'] * 0.30 +        # EMA trend structure (30%)
                intraday['entry_quality'] * 0.10 +   # Intraday timing precision (10%)
                mathematical_score * 0.10            # Mathematical (Fibonacci, S/R) - context only (10%)
            )
        else:
            # Without intraday: Focus on technical + trend
            combined['overall_quality'] = (
                technical_score * 0.50 +             # Technical indicators - PRIMARY EDGE (50%)
                daily['trend_score'] * 0.40 +        # EMA trend structure (40%)
                mathematical_score * 0.10            # Mathematical - context only (10%)
            )

        # ADD MISSING FIELDS for sequential_scanner compatibility
        combined['uptrend'] = daily['trend'] in ['UPTREND', 'STRONG_UPTREND', 'WEAK_UPTREND']
        
        # Signal score with strategic boost for mean reversion (if valid quality)
        base_signal_score = combined['overall_quality']
        
        # Add signal type classification BEFORE scoring adjustment
        signal_type = self._classify_signal_type(daily, intraday)
        combined['signal_type'] = signal_type
        
        # STRATEGIC BOOST: Mean reversion signals get bonus if they pass quality checks
        # This helps them compete with momentum while maintaining quality standards
        if signal_type == 'MEAN_REVERSION':
            mr_quality = self._check_mean_reversion_quality(daily)
            if mr_quality['is_valid'] and mr_quality['score'] >= 60:
                # High quality mean reversion: +0.5 boost
                base_signal_score = min(10.0, base_signal_score + 0.5)
            elif mr_quality['is_valid'] and mr_quality['score'] >= 50:
                # Good quality mean reversion: +0.3 boost
                base_signal_score = min(10.0, base_signal_score + 0.3)
        
        combined['signal_score'] = base_signal_score  # Comprehensive score with boost
        combined['technical_score'] = technical_score  # Add technical score
        combined['trend_only_score'] = daily['trend_score']  # Keep trend-only for reference
        combined['current_price'] = daily['current_price']
        combined['trend_strength'] = daily['trend']

        # Add indicators dict for compatibility (using REAL values from daily analysis)
        combined['indicators'] = {
            'rsi': daily.get('rsi', 50),
            'adx': daily.get('adx', 0),  # REAL ADX from technical indicators
            'macd': daily.get('macd', 0),  # REAL MACD from technical indicators
            'macd_histogram': daily.get('macd_histogram', 0),
            'volume_ratio': 1.5 if daily.get('volume_trend') == 'STRONG' else 1.0
        }

        # Add REAL mathematical indicators (NOT placeholders!)
        combined['mathematical_score'] = daily.get('mathematical_score', 5.0)
        combined['fibonacci_signal'] = daily.get('fibonacci_signal', 'NO_SIGNAL')
        combined['elliott_wave_pattern'] = daily.get('elliott_wave_pattern', 'UNKNOWN')
        combined['elliott_wave_count'] = daily.get('elliott_wave_count', 0)
        combined['elliott_signal'] = daily.get('elliott_signal', 'NEUTRAL')

        # Add REAL trend signals from technical analysis
        tech_signals = daily.get('technical_signals', {})
        combined['ema_trend'] = tech_signals.get('ema_trend', 'NEUTRAL')
        combined['macd_signal'] = tech_signals.get('macd_signal', 'NEUTRAL')

        # Add quality metrics (signal_type already added above during scoring)
        combined['mean_reversion_quality'] = self._check_mean_reversion_quality(daily)
        combined['momentum_quality'] = self._check_momentum_quality(daily)
        combined['breakout_quality'] = self._check_breakout_quality(daily, intraday)

        return combined

    def _classify_signal_type(self, daily: Dict, intraday: Optional[Dict]) -> str:
        """
        Classify signal as BREAKOUT, MOMENTUM, or MEAN_REVERSION
        BALANCED approach - not too strict, not too lenient
        
        RESTORED: Back to working configuration that catches real pullbacks
        """
        rsi = daily.get('rsi', 50)
        price = daily.get('current_price', 0)
        ema_20 = daily.get('ema_20', 0)
        ema_50 = daily.get('ema_50', 0)
        ema_200 = daily.get('ema_200', 0)
        volume_ratio = daily.get('volume_ratio', 1.0)
        macd_histogram = daily.get('macd_histogram', 0)

        # BREAKOUT: Breaking resistance with volume surge (15-min chart)
        # Breakouts are powerful - they combine momentum + fresh demand
        if intraday and intraday.get('recent_breakout'):
            if volume_ratio > 1.5:  # Good volume (was 1.8 - too strict)
                return 'BREAKOUT'

        # MEAN_REVERSION: Pullback in uptrend (Industry Standard)
        # RSI 30-45 = true pullback zone (professional range)
        if 30 <= rsi <= 45:
            # Must be in uptrend (above 50-MA - STRICT)
            if ema_50 > 0 and price > ema_50:
                # Must be pulling back (below 20-MA - STRICT)
                if ema_20 > 0 and price < ema_20:
                    return 'MEAN_REVERSION'
                # Fallback: If no 20-MA, RSI check is enough
                elif ema_20 <= 0:
                    return 'MEAN_REVERSION'
            # Alternative: Above 200-MA if 50-MA not available
            elif ema_200 > 0 and price > ema_200:
                if ema_20 > 0 and price < ema_20:
                    return 'MEAN_REVERSION'
                elif ema_20 <= 0:
                    return 'MEAN_REVERSION'

        # MOMENTUM: RSI 60-70, strong trend, above EMAs (Industry Standard)
        if 60 <= rsi <= 70:
            if price > ema_50:  # Above 50-day MA
                return 'MOMENTUM'
        
        # Default: If nothing else matched, classify as momentum
        # (will be filtered by quality scoring)
        return 'MOMENTUM'

    def _check_mean_reversion_quality(self, daily: Dict) -> Dict:
        """
        Check if mean reversion setup has good entry confirmation
        Returns quality metrics for filtering
        """
        from config.settings import MEAN_REVERSION_CONFIG

        quality = {
            'is_valid': False,
            'score': 0,
            'reasons': []
        }

        rsi = daily.get('rsi', 50)
        price = daily.get('current_price', 0)
        ema_50 = daily.get('ema_50', 0)
        volume_ratio = daily.get('volume_ratio', 1.0)
        macd_histogram = daily.get('macd_histogram', 0)
        rs_rating = daily.get('rs_rating', 100)  # RS vs Nifty 50

        score = 0

        # 1. RSI in mean reversion zone (30-45 = professional range)
        if 30 <= rsi <= 40:
            score += 30
            quality['reasons'].append(f'RSI in strong reversal zone ({rsi:.1f})')
        elif 40 < rsi <= 45:
            score += 20
            quality['reasons'].append(f'RSI in pullback zone ({rsi:.1f})')

        # 2. Still in uptrend (MUST be above 50-MA - STRICT)
        if ema_50 > 0 and price > ema_50:
            score += 25
            quality['reasons'].append('Above 50-day MA (uptrend intact)')

        # 3. Volume pickup (buying interest - minimum 1.0x)
        if volume_ratio >= MEAN_REVERSION_CONFIG['VOLUME_SPIKE_MIN']:
            score += 20
            quality['reasons'].append(f'Volume spike {volume_ratio:.1f}x')
        elif volume_ratio >= 1.0:
            score += 10
            quality['reasons'].append(f'Volume average {volume_ratio:.1f}x')

        # 4. MACD showing reversal signs (histogram turning positive)
        if macd_histogram > 0:
            score += 15
            quality['reasons'].append('MACD turning bullish')
        elif macd_histogram > -0.5:
            score += 10
            quality['reasons'].append('MACD close to turning')

        # 5. Relative Strength vs Nifty 50 (O'Neil method)
        if rs_rating >= 110:  # Strongly outperforming
            score += 15
            quality['reasons'].append(f'RS {rs_rating:.0f} (strong outperformer)')
        elif rs_rating >= 100:  # Outperforming
            score += 10
            quality['reasons'].append(f'RS {rs_rating:.0f} (outperforming)')

        quality['score'] = score
        quality['is_valid'] = score >= 50  # Industry Standard: 50+ score minimum

        return quality

    def _check_momentum_quality(self, daily: Dict) -> Dict:
        """
        Check if momentum setup has good entry confirmation
        Avoids overbought entries and ensures strong trend
        Returns quality metrics for filtering
        """
        from config.settings import MOMENTUM_CONFIG

        quality = {
            'is_valid': False,
            'score': 0,
            'reasons': []
        }

        rsi = daily.get('rsi', 50)
        price = daily.get('current_price', 0)
        ema_20 = daily.get('ema_20', 0)
        ema_50 = daily.get('ema_50', 0)
        volume_ratio = daily.get('volume_ratio', 1.0)
        macd_histogram = daily.get('macd_histogram', 0)
        adx = daily.get('adx', 0)
        rs_rating = daily.get('rs_rating', 100)  # RS vs Nifty 50

        score = 0

        # 1. RSI in momentum zone (60-68 = strong but not overbought)
        if 60 <= rsi <= 68:
            score += 25
            quality['reasons'].append(f'RSI in momentum zone ({rsi:.1f})')
        elif rsi < 60:
            score += 5  # Weak momentum
            quality['reasons'].append('RSI below momentum threshold')

        # 2. Strong trend (above 50 MA)
        if ema_50 > 0 and price > ema_50:
            score += 20
            quality['reasons'].append('Above 50-day MA (strong uptrend)')

        # 3. ADX check - CRITICAL for momentum (Industry Standard)
        if adx >= MOMENTUM_CONFIG['MIN_ADX']:
            if adx >= 40:
                score += 30
                quality['reasons'].append(f'ADX {adx:.1f} (very strong trend)')
            else:
                score += 25
                quality['reasons'].append(f'ADX {adx:.1f} (strong trend)')
        else:
            # No ADX means weak trend - give minimal points
            score += 5
            quality['reasons'].append(f'ADX {adx:.1f} (weak trend)')

        # 4. Not too extended (within 10% of 20-day MA)
        if ema_20 > 0:
            distance_from_ma20 = (price - ema_20) / ema_20 * 100
            if distance_from_ma20 <= 10:
                score += 15
                quality['reasons'].append(f'{distance_from_ma20:.1f}% from 20-MA (not extended)')

        # 5. Volume confirmation (minimum 1.3x for momentum)
        if volume_ratio >= 1.5:
            score += 20
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (very strong)')
        elif volume_ratio >= 1.3:
            score += 15
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (strong)')
        elif volume_ratio >= 1.0:
            score += 5
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (average)')

        # 6. MACD positive (momentum intact)
        if macd_histogram > 0:
            score += 10
            quality['reasons'].append('MACD bullish')

        # 7. Relative Strength vs Nifty 50 (O'Neil method - CRITICAL for momentum)
        if rs_rating >= 120:  # Very strongly outperforming
            score += 20
            quality['reasons'].append(f'RS {rs_rating:.0f} (very strong outperformer)')
        elif rs_rating >= 110:  # Strongly outperforming
            score += 15
            quality['reasons'].append(f'RS {rs_rating:.0f} (strong outperformer)')
        elif rs_rating >= 100:  # Outperforming
            score += 10
            quality['reasons'].append(f'RS {rs_rating:.0f} (outperforming)')

        quality['score'] = score
        quality['is_valid'] = score >= 60  # Industry Standard: 60+ for momentum

        return quality

    def _check_breakout_quality(self, daily: Dict, intraday: Optional[Dict]) -> Dict:
        """
        Check quality of BREAKOUT setup
        
        BREAKOUT = Momentum + Fresh breakout from consolidation
        Minimum: 65/100 (slightly higher than momentum since breakouts are powerful)
        """
        quality = {
            'score': 0,
            'is_valid': False,
            'reasons': []
        }

        score = 0
        rsi = daily.get('rsi', 50)
        adx = daily.get('adx', 0)
        price = daily.get('current_price', 0)
        ema_20 = daily.get('ema_20', 0)
        ema_50 = daily.get('ema_50', 0)
        volume_ratio = 1.5 if daily.get('volume_trend') == 'STRONG' else 1.0
        macd_histogram = daily.get('macd_histogram', 0)

        # 1. RSI in breakout zone (55-70 - momentum building but not overbought)
        if 55 <= rsi <= 70:
            if 60 <= rsi <= 68:
                score += 25
                quality['reasons'].append(f'RSI {rsi:.1f} (optimal breakout zone)')
            else:
                score += 20
                quality['reasons'].append(f'RSI {rsi:.1f} (good for breakout)')

        # 2. Above 50-MA (must be in uptrend)
        if ema_50 > 0 and price > ema_50:
            score += 25
            quality['reasons'].append(f'Above 50-MA (uptrend confirmed)')

        # 3. ADX showing strong trend (≥25)
        if adx >= 30:
            score += 30
            quality['reasons'].append(f'ADX {adx:.1f} (explosive trend)')
        elif adx >= 25:
            score += 25
            quality['reasons'].append(f'ADX {adx:.1f} (strong trend)')

        # 4. EXPLOSIVE volume (2x+ required for breakouts)
        if volume_ratio >= 2.5:
            score += 25
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (institutional buying)')
        elif volume_ratio >= 2.0:
            score += 20
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (strong interest)')
        elif volume_ratio >= 1.5:
            score += 15
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (good volume)')

        # 5. MACD positive (momentum confirmation)
        if macd_histogram > 0:
            score += 15
            quality['reasons'].append('MACD positive (bullish momentum)')

        # 6. RS Rating (if available)
        rs_rating = daily.get('rs_rating', 0)
        if rs_rating >= 120:
            score += 20
            quality['reasons'].append(f'RS {rs_rating:.0f} (exceptional vs market)')
        elif rs_rating >= 110:
            score += 15
            quality['reasons'].append(f'RS {rs_rating:.0f} (strong vs market)')
        elif rs_rating >= 100:
            score += 10
            quality['reasons'].append(f'RS {rs_rating:.0f} (outperforming market)')

        quality['score'] = score
        quality['is_valid'] = score >= 60  # Breakouts need 60+ (same as momentum - rare but powerful)

        return quality


if __name__ == "__main__":
    # Test multi-timeframe analyzer
    analyzer = MultiTimeframeAnalyzer()

    test_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']

    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing: {symbol}")
        print('='*60)

        result = analyzer.analyze(symbol)

        if result:
            print(f"\n📊 Daily Trend: {result['daily_trend']} (Score: {result['daily_trend_score']}/10)")
            print(f"💰 Current Price: ₹{result['current_price']:.2f}")
            print(f"📈 Support: ₹{result['support']:.2f}")
            print(f"📉 Resistance: ₹{result['resistance']:.2f}")

            if result['has_intraday_data']:
                print(f"\n⏱️  Entry Timing: {result['entry_timing']} (Score: {result['entry_timing_score']}/10)")
                print(f"🚪 Exit Urgency: {result['exit_urgency']}")
                print(f"\n15m Entry Signals:")
                for signal, active in result['intraday_entry_signals'].items():
                    status = '✅' if active else '❌'
                    print(f"   {status} {signal}")

            print(f"\n✨ Overall Quality: {result['overall_quality']:.1f}/10")
        else:
            print("❌ Analysis failed")
