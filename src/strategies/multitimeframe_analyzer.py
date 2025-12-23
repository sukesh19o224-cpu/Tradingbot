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

    def analyze_stock(self, symbol: str, daily_df: pd.DataFrame, intraday_df: Optional[pd.DataFrame] = None, market_regime: Optional[str] = None) -> Optional[Dict]:
        """
        Perform multi-timeframe analysis with pre-fetched data

        This method is used by sequential scanner which already fetched the data

        Args:
            symbol: Stock symbol
            daily_df: Pre-fetched daily OHLCV data
            intraday_df: Pre-fetched 15-min OHLCV data (optional)
            market_regime: Current market regime ('BULL', 'SIDEWAYS', 'BEAR') for adaptive classification

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

            # Combine analyses (pass market regime for adaptive classification)
            combined = self._combine_timeframes(daily_analysis, intraday_analysis, market_regime=market_regime)
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
            
            # Return full indicators dict for downstream use
            'indicators': indicators,
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
    
    def _detect_daily_breakout(self, daily: Dict) -> bool:
        """
        Detect breakout on DAILY chart (NEW - catches daily breakouts)
        
        Breakout = Price breaking above recent 20-day high with volume
        Industry standard: Price above 20-day high + volume surge
        """
        try:
            # Simple check: RSI in breakout zone + good volume + price above resistance
            rsi = daily.get('rsi', 50)
            volume_ratio = daily.get('volume_ratio', 1.0)
            price = daily.get('current_price', 0)
            ema_20 = daily.get('ema_20', 0)
            ema_50 = daily.get('ema_50', 0)
            
            # Breakout conditions:
            # 1. Price above 20-MA (breaking above short-term resistance)
            # 2. RSI 55-75 (momentum building, not overbought)
            # 3. Volume 1.3x+ (volume surge)
            if ema_20 > 0 and price > ema_20 * 1.01:  # 1% above 20-MA (breaking resistance)
                if 55 <= rsi <= 75:  # Momentum zone
                    if volume_ratio >= 1.3:  # Volume surge
                        return True
            
            # Alternative: Price above 50-MA with strong momentum
            if ema_50 > 0 and price > ema_50:
                if 60 <= rsi <= 70:  # Strong momentum
                    if volume_ratio >= 1.5:  # Strong volume
                        return True
            
            return False
        except Exception:
            return False

    def _check_momentum(self, df: pd.DataFrame) -> bool:
        """Check if momentum is weakening"""
        if len(df) < 10:
            return False

        # Compare recent candles
        recent_closes = df['Close'].tail(10)
        momentum_weakening = recent_closes.iloc[-1] < recent_closes.iloc[-3]

        return momentum_weakening

    def _combine_timeframes(self, daily: Dict, intraday: Optional[Dict], market_regime: Optional[str] = None) -> Dict:
        """
        Combine daily and intraday analysis

        Strategy:
        - Daily: Determines IF we should trade (trend + signal quality)
        - 15-minute: Determines WHEN to enter/exit (timing)

        Args:
            daily: Daily analysis results
            intraday: Intraday analysis results (or None)
            market_regime: Current market regime for adaptive classification (optional)

        Returns:
            Combined analysis
        """
        # Start with daily analysis
        combined = {
            'symbol': None,  # Will be set by caller
            'daily_trend': daily['trend'],
            'daily_trend_score': daily['trend_score'],
            'current_price': daily['current_price'],  # Fallback to daily price
            'support': daily['support_level'],
            'resistance': daily['resistance_level'],
            'fibonacci': daily['fibonacci_levels'],
        }

        if intraday:
            # CRITICAL FIX: Use REAL-TIME intraday price instead of stale daily price
            # Intraday data has the most recent 15-min candle close = current market price
            combined['current_price'] = intraday['current_price']  # Override with fresh price

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
        
        # Add signal type classification BEFORE scoring adjustment (with market regime awareness)
        signal_type = self._classify_signal_type(daily, intraday, market_regime=market_regime)
        combined['signal_type'] = signal_type
        
        # STRATEGIC BOOST: Mean reversion signals get bonus if they pass quality checks
        # This helps them compete with momentum while maintaining quality standards
        # UPDATED FOR BALANCED SCORING: MR now scores 0-209 (was 0-100)
        if signal_type == 'MEAN_REVERSION':
            mr_quality = self._check_mean_reversion_quality(daily)
            base_boost = 0
            if mr_quality['is_valid'] and mr_quality['score'] >= 160:
                base_boost = 1.5  # Excellent mean reversion (77% of max 209)
            elif mr_quality['is_valid'] and mr_quality['score'] >= 130:
                base_boost = 1.2  # High quality mean reversion (62% of max)
            elif mr_quality['is_valid'] and mr_quality['score'] >= 100:
                base_boost = 1.0  # Good quality mean reversion (48% of max)
            elif mr_quality['is_valid']:
                base_boost = 0.7  # Acceptable mean reversion (45-100 pts)

            # STOCK-SPECIFIC TREND ADJUSTMENT: Use the stock's own trend, not market regime
            stock_trend = daily.get('trend', 'SIDEWAYS')

            # If the STOCK ITSELF is in pullback/weak uptrend → extra boost for mean reversion
            if stock_trend in ['WEAK_UPTREND', 'UPTREND']:
                base_boost += 0.7  # Stock in pullback/weak uptrend = ideal for MR
            elif stock_trend == 'SIDEWAYS':
                base_boost += 0.5  # Sideways stock = good for MR

            # Market regime as SECONDARY factor (smaller adjustment)
            if market_regime == 'SIDEWAYS':
                base_boost += 0.2  # Minor extra boost if market also sideways

            base_signal_score = min(10.0, base_signal_score + base_boost)

        # STOCK-SPECIFIC MOMENTUM ADJUSTMENT: Use the stock's own trend
        elif signal_type == 'MOMENTUM':
            stock_trend = daily.get('trend', 'SIDEWAYS')

            # If the STOCK ITSELF is in strong uptrend → boost momentum
            if stock_trend == 'STRONG_UPTREND':
                base_signal_score = min(10.0, base_signal_score + 0.5)  # Boost for strong momentum
            # If the STOCK ITSELF is weak/sideways → penalize momentum
            elif stock_trend in ['WEAK_UPTREND', 'SIDEWAYS']:
                base_signal_score = max(0, base_signal_score - 0.5)  # Weak stock momentum

            # Market regime as SECONDARY factor
            if market_regime == 'SIDEWAYS' and stock_trend != 'STRONG_UPTREND':
                # Penalize momentum if both market AND stock are not strong
                base_signal_score = max(0, base_signal_score - 0.3)

        combined['signal_score'] = base_signal_score  # Comprehensive score with boost/penalty
        combined['technical_score'] = technical_score  # Add technical score
        combined['trend_only_score'] = daily['trend_score']  # Keep trend-only for reference
        combined['current_price'] = daily['current_price']
        combined['trend_strength'] = daily['trend']

        # Add indicators dict for compatibility (using REAL values from daily analysis)
        # Get ATR from daily indicators dict (calculated by technical_indicators)
        daily_indicators = daily.get('indicators', {})
        atr_value = daily_indicators.get('atr', 0)
        
        combined['indicators'] = {
            'rsi': daily.get('rsi', 50),
            'adx': daily.get('adx', 0),  # REAL ADX from technical indicators
            'macd': daily.get('macd', 0),  # REAL MACD from technical indicators
            'macd_histogram': daily.get('macd_histogram', 0),
            'atr': atr_value,  # ATR for dynamic stop loss calculation
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

    def _classify_signal_type(self, daily: Dict, intraday: Optional[Dict], market_regime: Optional[str] = None) -> str:
        """
        Classify signal as BREAKOUT, MOMENTUM, or MEAN_REVERSION
        BALANCED approach - not too strict, not too lenient
        
        RESTORED: Back to working configuration that catches real pullbacks
        ADAPTIVE: Adjusts RSI range based on market regime (SIDEWAYS = more lenient)
        """
        rsi = daily.get('rsi', 50)
        price = daily.get('current_price', 0)
        ema_20 = daily.get('ema_20', 0)
        ema_50 = daily.get('ema_50', 0)
        ema_200 = daily.get('ema_200', 0)
        volume_ratio = daily.get('volume_ratio', 1.0)
        macd_histogram = daily.get('macd_histogram', 0)

        # BREAKOUT: Breaking resistance with volume surge (DAILY + 15-min chart)
        # Breakouts are powerful - they combine momentum + fresh demand
        # Check BOTH daily and intraday breakouts (catch more opportunities)
        
        # 1. Daily breakout detection (NEW - catches daily breakouts)
        daily_breakout = self._detect_daily_breakout(daily)
        if daily_breakout and volume_ratio > 1.3:  # Daily breakouts need 1.3x+ volume
            return 'BREAKOUT'
        
        # 2. Intraday breakout detection (existing - 15-min chart)
        if intraday and intraday.get('recent_breakout'):
            if volume_ratio > 1.3:  # Reduced from 1.5 - more catchable
                return 'BREAKOUT'

        # MEAN_REVERSION: Pullback in uptrend (LOOSENED FOR 3+ TRADES)
        # LOOSENED RSI RANGE: RSI 28-54 (widened from 28-52 to catch more stocks)
        # LOOSENED PRICE CHECK: Allow stocks slightly further from 20-MA (catches stocks already bouncing)
        max_rsi_mean_rev = 54 if market_regime == 'SIDEWAYS' else 53
        if 28 <= rsi <= max_rsi_mean_rev:
            # Must be in uptrend (above 50-MA - STRICT)
            if ema_50 > 0 and price > ema_50:
                # LOOSENED: Allow stocks that have already started bouncing (wider price range)
                if market_regime == 'SIDEWAYS':
                    # SIDEWAYS: Loosened - allow up to 4% above 20-MA (catches stocks already bouncing)
                    if ema_20 > 0 and price <= ema_20 * 1.04:  # Up to 4% above 20-MA (loosened from 3%)
                        return 'MEAN_REVERSION'
                    elif ema_20 <= 0:
                        return 'MEAN_REVERSION'
                else:
                    # BULL/BEAR: Loosened - allow up to 3% above 20-MA (loosened from 2.5%)
                    if ema_20 > 0 and price <= ema_20 * 1.03:  # Up to 3% above 20-MA (loosened from 2.5%)
                        return 'MEAN_REVERSION'
                    elif ema_20 <= 0:
                        return 'MEAN_REVERSION'
            # Alternative: Above 200-MA if 50-MA not available
            elif ema_200 > 0 and price > ema_200:
                if market_regime == 'SIDEWAYS':
                    # SIDEWAYS: Loosened
                    if ema_20 > 0 and price <= ema_20 * 1.04:
                        return 'MEAN_REVERSION'
                    elif ema_20 <= 0:
                        return 'MEAN_REVERSION'
                else:
                    # BULL/BEAR: Loosened
                    if ema_20 > 0 and price <= ema_20 * 1.03:
                        return 'MEAN_REVERSION'
                    elif ema_20 <= 0:
                        return 'MEAN_REVERSION'

        # MOMENTUM: RSI 60-70, strong trend, above EMAs (Industry Standard - ORIGINAL)
        if 60 <= rsi <= 70:
            if price > ema_50:  # Above 50-day MA
                return 'MOMENTUM'
        
        # Default: If nothing else matched, classify as momentum
        # (will be filtered by quality scoring)
        return 'MOMENTUM'

    def _check_mean_reversion_quality(self, daily: Dict) -> Dict:
        """
        🎯 MEAN REVERSION STAGE DETECTOR - Catch stocks in the "LATER MID" ZONE

        Theory: Best mean reversion entries are AFTER bounce has started from oversold
        - Too Early = Falling knife, no bottom confirmation → Losses
        - PERFECT = Bounce confirmed (1-3 days), RSI rising from oversold, 2%+ potential → Best R:R
        - Too Late = Already bounced too much, no 2% left → Minimal gains

        BALANCED SCORING: Matches momentum scale (0-145 points, min 35 = 24%)
        Returns quality metrics for filtering
        """
        from config.settings import MEAN_REVERSION_CONFIG

        quality = {
            'is_valid': False,
            'score': 0,
            'reasons': [],
            'bounce_stage': 'UNKNOWN'
        }

        rsi = daily.get('rsi', 50)
        price = daily.get('current_price', 0)
        ema_20 = daily.get('ema_20', 0)
        ema_50 = daily.get('ema_50', 0)
        volume_ratio = daily.get('volume_ratio', 1.0)
        macd_histogram = daily.get('macd_histogram', 0)
        adx = daily.get('adx', 0)
        rs_rating = daily.get('rs_rating', 100)  # RS vs Nifty 50

        # Get indicators for Bollinger and Stochastic
        indicators = daily.get('indicators', {})

        score = 0
        bounce_stage_bonus = 0

        # 🎯 CRITICAL: BOUNCE STAGE DETECTION (matches momentum's breakout detection)
        # Analyze last 10 days to detect oversold -> bounce timing
        df = daily.get('df')

        if df is not None and len(df) >= 10:
            # Get last 10 days of RSI to detect oversold period
            last_10_days = df.tail(11).iloc[:-1]  # Exclude current day

            # Find when RSI was last oversold (<30)
            oversold_days_ago = None
            for i, (idx, row) in enumerate(last_10_days[::-1].iterrows()):
                row_rsi = self._calculate_rsi(df.loc[:idx, 'Close'], 14)
                if row_rsi < 30:
                    oversold_days_ago = i + 1
                    break

            # Check if RSI is now rising (bounce confirmation)
            current_rsi = rsi
            yesterday_rsi = self._calculate_rsi(df['Close'].iloc[:-1], 14) if len(df) >= 15 else current_rsi
            rsi_rising = current_rsi > yesterday_rsi

            # Check if price is bouncing off support (20-MA or Bollinger lower band)
            bb_position = indicators.get('bb_position', 0.5)
            near_support = bb_position <= 0.30 or (ema_20 > 0 and price <= ema_20 * 1.02)

            # Check MACD momentum building
            macd_turning_positive = macd_histogram > -0.5  # Close to turning positive

            # 🎯 STAGE CLASSIFICATION (like momentum's breakout stages)
            if oversold_days_ago is not None:
                # Bounce has started from oversold
                if oversold_days_ago == 1:
                    # Just bounced yesterday (Day 1 of bounce)
                    if 30 <= current_rsi <= 42 and rsi_rising and near_support:
                        quality['bounce_stage'] = 'PERFECT_DAY1'
                        bounce_stage_bonus = 35  # Strong confirmation
                        quality['reasons'].append(f'🎯 PERFECT DAY1: Just bounced from oversold, RSI rising ({current_rsi:.1f})')
                    else:
                        quality['bounce_stage'] = 'GOOD_DAY1'
                        bounce_stage_bonus = 25
                        quality['reasons'].append(f'Good bounce start (Day 1, RSI {current_rsi:.1f})')

                elif 2 <= oversold_days_ago <= 3:
                    # THE SWEET SPOT - 2-3 days into bounce
                    if 30 <= current_rsi <= 50 and rsi_rising and macd_turning_positive:
                        quality['bounce_stage'] = 'PERFECT_DAY2-3'
                        bounce_stage_bonus = 40  # MAXIMUM BONUS (like momentum)
                        quality['reasons'].append(f'🎯 PERFECT DAY2-3: Bounce confirmed, momentum building (RSI {current_rsi:.1f})')
                    else:
                        quality['bounce_stage'] = 'GOOD_DAY2-3'
                        bounce_stage_bonus = 25
                        quality['reasons'].append(f'Good bounce window (Day {oversold_days_ago}, RSI {current_rsi:.1f})')

                elif 4 <= oversold_days_ago <= 5:
                    # Getting late but still has potential
                    if current_rsi <= 50 and rsi_rising:
                        quality['bounce_stage'] = 'LATE_BUT_OK'
                        bounce_stage_bonus = 15
                        quality['reasons'].append(f'Late bounce (Day {oversold_days_ago}), still potential (RSI {current_rsi:.1f})')
                    else:
                        quality['bounce_stage'] = 'LATE'
                        bounce_stage_bonus = 5
                        quality['reasons'].append(f'Late bounce (Day {oversold_days_ago}, RSI {current_rsi:.1f})')

                else:  # 6+ days
                    # Too late - bounce exhausted
                    quality['bounce_stage'] = 'EXHAUSTED'
                    bounce_stage_bonus = -10  # Penalty
                    quality['reasons'].append(f'⚠️ Bounce exhausted (Day {oversold_days_ago}, RSI {current_rsi:.1f})')

            else:
                # No recent oversold - check if currently falling (FALLING KNIFE) or already bouncing
                if current_rsi < 30 and not rsi_rising:
                    quality['bounce_stage'] = 'FALLING_KNIFE'
                    bounce_stage_bonus = -20  # Heavy penalty - AVOID FALLING KNIFE
                    quality['reasons'].append(f'⚠️ FALLING KNIFE: Still falling, no bounce (RSI {current_rsi:.1f})')
                elif 30 <= current_rsi <= 50 and rsi_rising:
                    # Already bouncing/going up - GOOD! (widened from 42 to 50)
                    quality['bounce_stage'] = 'EARLY_BOUNCE'
                    bounce_stage_bonus = 20
                    quality['reasons'].append(f'✅ Already bouncing up (RSI {current_rsi:.1f}, rising)')
                elif 30 <= current_rsi <= 50:
                    # In bounce zone but RSI not clearly rising - check MACD for confirmation
                    if macd_turning_positive or macd_histogram > -1.0:
                        quality['bounce_stage'] = 'EARLY_BOUNCE'
                        bounce_stage_bonus = 15  # Lower bonus but still acceptable
                        quality['reasons'].append(f'Bounce zone, MACD turning (RSI {current_rsi:.1f})')
                    else:
                        quality['bounce_stage'] = 'NO_RECENT_OVERSOLD'
                        bounce_stage_bonus = 0
                        quality['reasons'].append('In bounce zone but no clear reversal confirmation')
                else:
                    quality['bounce_stage'] = 'NO_RECENT_OVERSOLD'
                    bounce_stage_bonus = 0
                    quality['reasons'].append('No recent oversold condition')

        score += bounce_stage_bonus

        # =========================================================================
        # BALANCED SCORING COMPONENTS (Rebalanced to match momentum scale)
        # =========================================================================

        # 1. RSI in mean reversion zone (28-50 = OPTIMIZED for 2% bounces) - MAX 30 pts (INCREASED from 25)
        if 28 <= rsi <= 35:
            score += 30  # Deep oversold = best 2% bounce potential (INCREASED)
            quality['reasons'].append(f'RSI deeply oversold ({rsi:.1f}) - prime for 2% bounce')
        elif 35 < rsi <= 42:
            score += 24  # Good oversold level (INCREASED from 20)
            quality['reasons'].append(f'RSI oversold ({rsi:.1f}) - good for 2% bounce')
        elif 42 < rsi <= 50:
            score += 18  # Moderate pullback (INCREASED from 15)
            quality['reasons'].append(f'RSI in pullback zone ({rsi:.1f})')

        # 2. Still in uptrend (MUST be above 50-MA - STRICT) - MAX 25 pts (INCREASED from 20, matches momentum)
        if ema_50 > 0 and price > ema_50:
            score += 25
            quality['reasons'].append('Above 50-day MA (uptrend intact)')

        # 3. ADX check (pullback = weaker trend temporarily) - MAX 28 pts (INCREASED from 25)
        # Mean reversion typically has ADX 15-25 (pullback = weaker trend)
        if adx >= 15:
            if adx >= 25:
                score += 22  # Higher ADX = stronger trend = safer mean reversion (INCREASED from 20)
                quality['reasons'].append(f'ADX {adx:.1f} (strong uptrend with pullback)')
            elif adx >= 18:
                score += 28  # Sweet spot for mean reversion (moderate trend) (INCREASED from 25)
                quality['reasons'].append(f'ADX {adx:.1f} (ideal mean reversion setup)')
            else:  # ADX 15-18
                score += 18  # Lower ADX but acceptable (INCREASED from 15)
                quality['reasons'].append(f'ADX {adx:.1f} (moderate pullback)')
        else:
            score += 6  # Very weak trend (INCREASED from 5)
            quality['reasons'].append(f'ADX {adx:.1f} (weak trend)')

        # 4. 2% PROFIT POTENTIAL CHECK (CRITICAL for user requirement) - MAX 18 pts (INCREASED from 15)
        # Calculate distance to resistance (20-MA or recent high)
        # For stocks already bouncing (RSI rising), use higher target (they can go higher)
        # Check if RSI is rising (use variable from bounce stage detection if available)
        is_bouncing_up = False
        if df is not None and len(df) >= 15:
            try:
                current_rsi_check = rsi
                yesterday_rsi_check = self._calculate_rsi(df['Close'].iloc[:-1], 14)
                is_bouncing_up = current_rsi_check > yesterday_rsi_check and current_rsi_check >= 30
            except:
                pass
        
        if is_bouncing_up:
            # Already bouncing - can target 50-MA or higher
            resistance_target = max(ema_20, ema_50) if ema_50 > price else (ema_20 if ema_20 > price else price * 1.03)
        else:
            resistance_target = ema_20 if ema_20 > price else price * 1.02
        profit_potential = ((resistance_target - price) / price) * 100

        if profit_potential >= 2.5:
            score += 18  # Excellent 2%+ potential (INCREASED from 15)
            quality['reasons'].append(f'Profit potential {profit_potential:.1f}% (excellent for 2% target)')
        elif profit_potential >= 2.0:
            score += 14  # Good 2% potential (INCREASED from 12)
            quality['reasons'].append(f'Profit potential {profit_potential:.1f}% (meets 2% target)')
        elif profit_potential >= 1.5:
            score += 9  # Moderate potential (INCREASED from 8)
            quality['reasons'].append(f'Profit potential {profit_potential:.1f}% (below 2% target)')
        elif profit_potential >= 1.0:
            score += 5  # Low but acceptable for stocks already bouncing (NEW)
            quality['reasons'].append(f'Profit potential {profit_potential:.1f}% (low but acceptable for bounce)')
        else:
            score += 0  # Not enough potential
            quality['reasons'].append(f'⚠️ Profit potential only {profit_potential:.1f}% (insufficient)')

        # 5. Volume confirmation - MAX 25 pts (INCREASED from 20, matches momentum)
        if volume_ratio >= 1.5:
            score += 25  # Very strong (INCREASED from 20)
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (very strong)')
        elif volume_ratio >= 1.3:
            score += 19  # Strong (INCREASED from 15)
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (strong)')
        elif volume_ratio >= 1.0:
            score += 12  # Normal (INCREASED from 10)
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (normal)')
        else:
            score += 6  # Low but acceptable (INCREASED from 5)
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (low but acceptable)')

        # 6. MACD/Bollinger/Stochastic - Combined reversal confirmation - MAX 18 pts (INCREASED from 15)
        reversal_points = 0

        # MACD reversal
        if macd_histogram > 0:
            reversal_points += 6  # INCREASED from 5
            quality['reasons'].append('MACD bullish (reversal confirmed)')
        elif macd_histogram > -1.0:
            reversal_points += 4  # INCREASED from 3
            quality['reasons'].append('MACD near reversal')

        # Bollinger Bands
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position <= 0.15:  # At/below lower band
            reversal_points += 6  # INCREASED from 5
            quality['reasons'].append('At Bollinger lower band')
        elif bb_position <= 0.30:
            reversal_points += 4  # INCREASED from 3
            quality['reasons'].append('Near Bollinger lower band')

        # Stochastic
        stoch_k = indicators.get('stoch_k', 50)
        stoch_d = indicators.get('stoch_d', 50)
        if stoch_k < 20 and stoch_k > stoch_d:
            reversal_points += 6  # INCREASED from 5
            quality['reasons'].append(f'Stochastic oversold + cross ({stoch_k:.1f})')
        elif stoch_k < 30:
            reversal_points += 4  # INCREASED from 3
            quality['reasons'].append(f'Stochastic oversold ({stoch_k:.1f})')

        score += min(reversal_points, 18)  # Cap at 18 points (INCREASED from 15)

        # 7. Relative Strength - MAX 25 pts (INCREASED from 20, matches momentum)
        if rs_rating >= 120:
            score += 25  # Very strong outperformer (INCREASED from 20)
            quality['reasons'].append(f'RS {rs_rating:.0f} (very strong outperformer)')
        elif rs_rating >= 110:
            score += 19  # Strong outperformer (INCREASED from 15)
            quality['reasons'].append(f'RS {rs_rating:.0f} (strong outperformer)')
        elif rs_rating >= 100:
            score += 12  # Outperforming (INCREASED from 10)
            quality['reasons'].append(f'RS {rs_rating:.0f} (outperforming)')
        elif rs_rating >= 95:
            score += 6  # Matching market (INCREASED from 5)
            quality['reasons'].append(f'RS {rs_rating:.0f} (matching market)')

        quality['score'] = score

        # =========================================================================
        # BALANCED VALIDATION THRESHOLDS (Middle ground - not too strict, not too loose)
        # =========================================================================
        # NEW BASE MAX: 169 points (up from 140)
        # With stage bonus: up to 209 points (vs 180 before)

        # FURTHER LOOSENED thresholds to catch 3+ MR signals per scan
        # Still avoids falling knives (they get -20 penalty, so won't pass)
        if quality['bounce_stage'] in ['PERFECT_DAY1', 'PERFECT_DAY2-3', 'EARLY_BOUNCE']:
            quality['is_valid'] = score >= 35  # 17% of max 209 (further loosened from 38 to catch more)
        elif quality['bounce_stage'] == 'FALLING_KNIFE':
            # RELAXED: Allow high-quality falling knives (score must be VERY high to overcome risk)
            quality['is_valid'] = score >= 80  # Need 38% of max 209 to pass (vs never before)
        else:
            quality['is_valid'] = score >= 38  # 22% of max 169 (further loosened from 42 to catch more)

        return quality

    def _check_momentum_quality(self, daily: Dict) -> Dict:
        """
        🎯 SAFE MOMENTUM STRATEGY - Low Risk, Steady 2% Profits

        NEW USER PREFERENCE: Stocks ALREADY in confirmed momentum
        - NOT early breakout guessing (risky)
        - YES steady uptrend continuation (safe 2% gains)
        - High win rate, low stress, reliable profits

        Theory: Enter stocks with PROVEN momentum, not speculative breakouts
        - STEADY_MOMENTUM = Already trending, confirmed, ready for 2% (PREFERRED)
        - LATE_BUT_OK = Still has fuel, safe entry
        - NO_BREAKOUT = Smooth uptrend without volatility (BEST for 2%)

        Returns quality metrics for filtering
        """
        from config.settings import MOMENTUM_CONFIG
        import pandas as pd

        quality = {
            'is_valid': False,
            'score': 0,
            'reasons': [],
            'momentum_stage': 'UNKNOWN'  # TOO_EARLY, PERFECT, LATE, EXHAUSTED
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

        # =========================================================================
        # CRITICAL: MOMENTUM STAGE DETECTION (The "Before Mid" Sweet Spot)
        # =========================================================================

        # Get historical data to detect breakout timing
        df = daily.get('df')  # Full dataframe with price history
        momentum_stage_bonus = 0

        if df is not None and len(df) >= 20:
            try:
                # Calculate 20-day high/low for breakout detection
                recent_20d_high = df['High'].tail(21).iloc[:-1].max()  # Exclude today
                recent_20d_low = df['Low'].tail(21).iloc[:-1].min()

                # Check if price recently broke above 20-day high (1-5 days ago)
                last_5_days = df.tail(6).iloc[:-1]  # Last 5 days excluding today
                breakout_days_ago = None

                for i, (idx, row) in enumerate(last_5_days[::-1].iterrows()):
                    if row['Close'] > recent_20d_high * 0.98:  # Within 2% of breakout
                        breakout_days_ago = i + 1
                        break

                # Calculate RSI momentum (rising or falling)
                rsi_series = df['RSI'].tail(5) if 'RSI' in df.columns else None
                rsi_rising = rsi_series.iloc[-1] > rsi_series.iloc[-3] if rsi_series is not None and len(rsi_series) >= 3 else False

                # Determine momentum stage (ADJUSTED FOR SAFE 2% STRATEGY)
                if breakout_days_ago is not None:
                    if breakout_days_ago == 1:
                        # DAY 1: Just broke out today/yesterday - RISKY!
                        if 55 <= rsi <= 68 and adx >= 20:
                            quality['momentum_stage'] = 'PERFECT_DAY1'
                            momentum_stage_bonus = 15  # REDUCED from 35 - Too risky for user preference
                            quality['reasons'].append(f'⚠️ RISKY: Fresh breakout (Day {breakout_days_ago}), not confirmed yet')
                        else:
                            quality['momentum_stage'] = 'TOO_EARLY'
                            momentum_stage_bonus = 0  # REDUCED from 5
                            quality['reasons'].append(f'❌ Too early: Breakout Day {breakout_days_ago} but weak confirmation')

                    elif 2 <= breakout_days_ago <= 3:
                        # DAY 2-3: Still somewhat risky (breakout could fail)
                        if 55 <= rsi <= 70 and adx >= 20 and rsi_rising:
                            quality['momentum_stage'] = 'PERFECT_DAY2-3'
                            momentum_stage_bonus = 25  # REDUCED from 40 - Still early/risky
                            quality['reasons'].append(f'⚠️ MODERATE: Breakout Day {breakout_days_ago}, trend confirming')
                        elif 55 <= rsi <= 72:
                            quality['momentum_stage'] = 'GOOD_DAY2-3'
                            momentum_stage_bonus = 20  # REDUCED from 25
                            quality['reasons'].append(f'Breakout Day {breakout_days_ago}, RSI {rsi:.1f}')
                        else:
                            quality['momentum_stage'] = 'WEAKENING'
                            momentum_stage_bonus = 5  # REDUCED from 10
                            quality['reasons'].append(f'Breakout Day {breakout_days_ago} but momentum weakening')

                    elif 4 <= breakout_days_ago <= 7:
                        # DAY 4-7: SAFER - Breakout proven, still has room
                        if rsi < 70 and rsi_rising and adx >= 25:
                            quality['momentum_stage'] = 'LATE_BUT_OK'
                            momentum_stage_bonus = 30  # INCREASED from 15 - This is safer!
                            quality['reasons'].append(f'✅ SAFE: Proven momentum (Day {breakout_days_ago}), stable uptrend')
                        else:
                            quality['momentum_stage'] = 'LATE'
                            momentum_stage_bonus = 20  # INCREASED from 5 - Still acceptable
                            quality['reasons'].append(f'✅ Established trend (Day {breakout_days_ago}), lower risk')

                    else:  # 8+ days
                        # EXHAUSTED - Too late, move already happened
                        quality['momentum_stage'] = 'EXHAUSTED'
                        momentum_stage_bonus = -10  # PENALTY
                        quality['reasons'].append(f'❌ Too late: Breakout {breakout_days_ago} days ago, move likely exhausted')

                else:
                    # No recent breakout detected - PREFERRED for safe 2% plays!
                    if rsi >= 55 and adx >= 20:
                        quality['momentum_stage'] = 'STEADY_MOMENTUM'
                        momentum_stage_bonus = 35  # INCREASED from 10 - This is what user wants!
                        quality['reasons'].append('✅ SAFE: Steady momentum (proven uptrend, low risk 2% play)')
                    else:
                        quality['momentum_stage'] = 'NO_BREAKOUT'
                        momentum_stage_bonus = 25  # INCREASED from 0 - Still safe if other criteria met
                        quality['reasons'].append('✅ SAFE: No breakout volatility (smooth uptrend for 2%)')

            except Exception as e:
                # Fallback if stage detection fails
                quality['momentum_stage'] = 'DETECTION_FAILED'
                momentum_stage_bonus = 0

        # =========================================================================
        # STANDARD MOMENTUM SCORING (Enhanced with stage bonus)
        # =========================================================================

        # 1. RSI CHECK - Must have room for 2% move (NOT exhausted!)
        # CRITICAL: Avoid overbought stocks that can't move higher
        if 55 <= rsi <= 65:
            score += 30  # PERFECT - Strong but room to run
            quality['reasons'].append(f'✅ RSI {rsi:.1f} (strong + 2% potential)')
        elif 50 <= rsi < 55:
            score += 25  # Building momentum, plenty of room
            quality['reasons'].append(f'✅ RSI {rsi:.1f} (building, lots of fuel)')
        elif 65 < rsi <= 68:
            score += 20  # Still good but getting warm
            quality['reasons'].append(f'RSI {rsi:.1f} (good, some fuel left)')
        elif 68 < rsi <= 70:
            score += 10  # Elevated - limited upside
            quality['reasons'].append(f'⚠️ RSI {rsi:.1f} (elevated, limited fuel)')
        elif rsi > 70:
            score += 0  # EXHAUSTED - avoid!
            quality['reasons'].append(f'❌ RSI {rsi:.1f} (exhausted, no fuel for 2%)')
        else:
            score += 5  # Too weak for momentum
            quality['reasons'].append(f'⚠️ RSI {rsi:.1f} (too weak)')

        # 2. Strong trend (above 50 MA) - MANDATORY
        if ema_50 > 0 and price > ema_50:
            distance_from_50ma = ((price - ema_50) / ema_50) * 100
            if distance_from_50ma >= 2:
                score += 25  # Good cushion above 50-MA
                quality['reasons'].append(f'Strong uptrend ({distance_from_50ma:.1f}% above 50-MA)')
            else:
                score += 15  # Just above 50-MA
                quality['reasons'].append('Above 50-MA (uptrend)')
        else:
            score -= 20  # PENALTY - Not in uptrend
            quality['reasons'].append('❌ Below 50-MA (no uptrend)')

        # 3. ADX - Trend strength (CRITICAL for momentum)
        if adx >= 25:  # Strong trending market
            if adx >= 35:
                score += 35  # Very strong trend
                quality['reasons'].append(f'ADX {adx:.1f} (very strong trend)')
            else:
                score += 28
                quality['reasons'].append(f'ADX {adx:.1f} (strong trend)')
        elif adx >= 20:  # Moderate trend
            score += 20
            quality['reasons'].append(f'ADX {adx:.1f} (moderate trend)')
        elif adx >= 15:  # Weak trend
            score += 10
            quality['reasons'].append(f'ADX {adx:.1f} (weak trend)')
        else:
            score += 0  # No trend - avoid
            quality['reasons'].append(f'⚠️ ADX {adx:.1f} (no trend)')

        # 4. FUEL CHECK - Price vs 20-MA (avoid exhausted moves!)
        # CRITICAL: Stock must have room to run 2%+ from current price
        if ema_20 > 0:
            distance_from_ma20 = ((price - ema_20) / ema_20) * 100
            if 0 <= distance_from_ma20 <= 3:  # IDEAL - Confirmed but fresh
                score += 25  # INCREASED - This is perfect for 2% plays
                quality['reasons'].append(f'✅ Fresh momentum ({distance_from_ma20:+.1f}% from 20-MA, fuel left)')
            elif 3 < distance_from_ma20 <= 5:  # Good - still has room
                score += 20
                quality['reasons'].append(f'✅ Good position ({distance_from_ma20:+.1f}% from 20-MA, some fuel)')
            elif 5 < distance_from_ma20 <= 7:  # Stretched but acceptable
                score += 10
                quality['reasons'].append(f'⚠️ Extended ({distance_from_ma20:+.1f}% from 20-MA, limited fuel)')
            elif distance_from_ma20 > 7:  # TOO EXTENDED - EXHAUSTED!
                score -= 15  # INCREASED PENALTY
                quality['reasons'].append(f'❌ Exhausted ({distance_from_ma20:+.1f}% from 20-MA, no 2% left)')
            else:  # Below 20-MA - pullback
                score += 15  # Good entry on pullback
                quality['reasons'].append(f'✅ Pullback ({distance_from_ma20:+.1f}% from 20-MA, fresh fuel)')

        # 5. Volume confirmation (CRITICAL - institutions buying)
        if volume_ratio >= 1.8:
            score += 25  # Massive volume = institutional interest
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (institutional buying)')
        elif volume_ratio >= 1.5:
            score += 20
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (very strong)')
        elif volume_ratio >= 1.2:
            score += 12
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (strong)')
        elif volume_ratio >= 1.0:
            score += 5
            quality['reasons'].append(f'Volume {volume_ratio:.1f}x (average)')
        else:
            score += 0  # Low volume = no conviction
            quality['reasons'].append(f'⚠️ Volume {volume_ratio:.1f}x (weak)')

        # 6. MACD confirmation
        if macd_histogram > 0:
            score += 12
            quality['reasons'].append('MACD bullish')
        else:
            score += 0
            quality['reasons'].append('MACD bearish/neutral')

        # 7. Relative Strength (Outperformance vs market)
        if rs_rating >= 120:
            score += 25  # Very strong outperformer
            quality['reasons'].append(f'RS {rs_rating:.0f} (market leader)')
        elif rs_rating >= 110:
            score += 18
            quality['reasons'].append(f'RS {rs_rating:.0f} (strong outperformer)')
        elif rs_rating >= 100:
            score += 10
            quality['reasons'].append(f'RS {rs_rating:.0f} (outperforming)')
        elif rs_rating >= 95:
            score += 5
            quality['reasons'].append(f'RS {rs_rating:.0f} (matching market)')
        else:
            score += 0
            quality['reasons'].append(f'⚠️ RS {rs_rating:.0f} (underperforming)')

        # =========================================================================
        # ADD MOMENTUM STAGE BONUS (The secret sauce!)
        # =========================================================================
        score += momentum_stage_bonus

        quality['score'] = score

        # =========================================================================
        # CRITICAL FILTERS - Avoid exhausted stocks!
        # =========================================================================

        # MANDATORY: RSI must be < 70 (room for 2% move)
        if rsi > 70:
            quality['is_valid'] = False
            quality['reasons'].append('❌ REJECTED: RSI >70, stock exhausted')
            return quality

        # MANDATORY: Price < 7% above 20-MA (must have fuel left)
        if ema_20 > 0:
            distance_from_ma20 = ((price - ema_20) / ema_20) * 100
            if distance_from_ma20 > 7:
                quality['is_valid'] = False
                quality['reasons'].append(f'❌ REJECTED: {distance_from_ma20:.1f}% above 20-MA, exhausted')
                return quality

        # =========================================================================
        # VALIDATION THRESHOLDS (Adjusted for safe 2% strategy)
        # =========================================================================
        # Prioritize SAFE entries (steady momentum, proven trends)
        # Penalize RISKY entries (early breakouts, unconfirmed)

        if quality['momentum_stage'] in ['STEADY_MOMENTUM', 'NO_BREAKOUT', 'LATE_BUT_OK', 'LATE']:
            quality['is_valid'] = score >= 50  # RELAXED for safe entries (user preference)
        elif quality['momentum_stage'] in ['PERFECT_DAY2-3', 'GOOD_DAY2-3']:
            quality['is_valid'] = score >= 60  # Moderate threshold for early entries
        else:
            quality['is_valid'] = score >= 70  # STRICT for risky early/uncertain entries

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
        quality['is_valid'] = score >= 50  # Relaxed for swing catching: 50+ (was 60)

        return quality

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate RSI for a price series

        Args:
            prices: Series of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Not enough data, return neutral

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


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
