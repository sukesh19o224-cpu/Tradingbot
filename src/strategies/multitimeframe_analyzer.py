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
            math_indicators = {}

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
            'support_level': math_indicators.get('support_level', current_price * 0.95),
            'resistance_level': math_indicators.get('resistance_level', current_price * 1.05),
            'fibonacci_levels': math_indicators.get('fibonacci_levels', {}),
            'volume_trend': indicators['signals']['volume_signal'],
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
        """Detect recent breakout on 15m chart"""
        if len(df) < 20:
            return False

        current_price = float(df['Close'].iloc[-1])
        recent_high = float(df['High'].iloc[-20:-1].max())

        # Breakout if current price > recent high
        return current_price > recent_high * 1.005  # 0.5% above recent high

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

        # Calculate overall quality score
        if intraday:
            # Combined score: 60% daily trend + 40% intraday timing
            combined['overall_quality'] = (
                daily['trend_score'] * 0.6 +
                intraday['entry_quality'] * 0.4
            )
        else:
            combined['overall_quality'] = daily['trend_score']

        # ADD MISSING FIELDS for sequential_scanner compatibility
        combined['uptrend'] = daily['trend'] in ['UPTREND', 'STRONG_UPTREND', 'WEAK_UPTREND']
        combined['signal_score'] = combined['overall_quality']  # Use overall_quality as signal_score
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

        # Add signal type classification
        if intraday and intraday.get('recent_breakout'):
            combined['signal_type'] = 'BREAKOUT'
        elif daily['rsi'] > 60:
            combined['signal_type'] = 'MOMENTUM'
        else:
            combined['signal_type'] = 'MEAN_REVERSION'

        return combined


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
