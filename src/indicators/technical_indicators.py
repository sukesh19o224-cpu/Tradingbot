"""
📊 TECHNICAL INDICATORS - Core Trading Indicators
RSI, MACD, EMA, Bollinger Bands, ADX, Volume Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf

from config.settings import *


class TechnicalIndicators:
    """
    Calculate all technical indicators for stock analysis

    Features:
    - Moving Averages (EMA, SMA)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - ADX (Average Directional Index)
    - Volume Analysis
    - Momentum Indicators
    """

    def __init__(self):
        self.indicators = {}

    def calculate_all(self, df: pd.DataFrame) -> Dict:
        """
        Calculate all technical indicators for a stock

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dict with all indicator values and signals
        """
        if df is None or len(df) < 50:
            return None

        try:
            # Make a copy to avoid modifying original
            df = df.copy()

            # Normalize column names (yfinance returns lowercase when market closed!)
            # Convert: 'open' -> 'Open', 'close' -> 'Close', etc.
            df.columns = df.columns.str.capitalize()

            # Calculate all indicators
            df = self._calculate_emas(df)
            df = self._calculate_rsi(df)
            df = self._calculate_macd(df)
            df = self._calculate_bollinger_bands(df)
            df = self._calculate_stochastic(df)  # Add Stochastic for mean reversion
            df = self._calculate_adx(df)
            df = self._calculate_volume_indicators(df)
            df = self._calculate_momentum(df)
            df = self._calculate_relative_strength(df)  # RS vs Nifty 50

            # Get latest values
            latest = df.iloc[-1]

            # Generate signals
            signals = self._generate_signals(df)

            return {
                'price': latest['Close'],
                'ema_8': latest.get('EMA_8', 0),
                'ema_20': latest.get('EMA_20', 0),  # Add EMA_20 for mean reversion
                'ema_21': latest.get('EMA_21', 0),
                'ema_50': latest.get('EMA_50', 0),
                'ema_200': latest.get('EMA_200', 0),
                'rsi': latest.get('RSI', 50),
                'macd': latest.get('MACD', 0),
                'macd_signal': latest.get('MACD_Signal', 0),
                'macd_histogram': latest.get('MACD_Hist', 0),
                'bb_upper': latest.get('BB_Upper', 0),
                'bb_middle': latest.get('BB_Middle', 0),
                'bb_lower': latest.get('BB_Lower', 0),
                'bb_position': latest.get('BB_Position', 0.5),
                'stoch_k': latest.get('Stoch_K', 50),  # Stochastic %K
                'stoch_d': latest.get('Stoch_D', 50),  # Stochastic %D
                'adx': latest.get('ADX', 0),
                'plus_di': latest.get('+DI', 0),
                'minus_di': latest.get('-DI', 0),
                'atr': latest.get('ATR', 0),  # Include ATR for stop loss calculation
                'volume_ratio': latest.get('Volume_Ratio', 1.0),
                'momentum_1d': latest.get('Momentum_1D', 0),  # Add 1-day momentum
                'momentum_5d': latest.get('Momentum_5D', 0),
                'momentum_20d': latest.get('Momentum_20D', 0),
                'signals': signals,
                'df': df  # Return dataframe for further analysis
            }

        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return None

    def _calculate_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Exponential Moving Averages"""
        for period in EMA_PERIODS:
            df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
        return df

    def _calculate_rsi(self, df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.DataFrame:
        """Calculate RSI (Relative Strength Index)"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = df['Close'].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=MACD_SLOW, adjust=False).mean()

        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        return df

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df['BB_Middle'] = df['Close'].rolling(window=BB_PERIOD).mean()
        bb_std = df['Close'].rolling(window=BB_PERIOD).std()

        df['BB_Upper'] = df['BB_Middle'] + (bb_std * BB_STD)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * BB_STD)

        # Calculate position within bands (0 = lower, 0.5 = middle, 1 = upper)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        df['BB_Position'] = df['BB_Position'].clip(0, 1)

        return df

    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator (%K and %D)
        OPTIMIZED FOR MEAN REVERSION: Detects oversold conditions and reversals

        %K = Fast line (current position in high-low range)
        %D = Slow line (moving average of %K)

        Signals:
        - %K < 20 = Oversold (potential bounce)
        - %K > 80 = Overbought
        - %K crosses above %D = Bullish reversal
        """
        # Get high/low for the period
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()

        # Calculate %K (fast stochastic)
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))

        # Calculate %D (slow stochastic - moving average of %K)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()

        # Fill NaN with neutral value
        df['Stoch_K'] = df['Stoch_K'].fillna(50)
        df['Stoch_D'] = df['Stoch_D'].fillna(50)

        return df

    def _calculate_adx(self, df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.DataFrame:
        """Calculate ADX (Average Directional Index) and ATR"""
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

        # ATR (Average True Range) - Store for stop loss calculation
        atr = tr.rolling(window=period).mean()
        df['ATR'] = atr

        # +DI and -DI
        df['+DI'] = 100 * (plus_dm.rolling(window=period).mean() / atr)
        df['-DI'] = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # DX and ADX
        dx = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
        df['ADX'] = dx.rolling(window=period).mean()

        return df

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based indicators"""
        df['Volume_MA'] = df['Volume'].rolling(window=VOLUME_MA_PERIOD).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

        # On-Balance Volume (OBV)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        return df

    def _calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators"""
        df['Momentum_5D'] = ((df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5) * 100)
        df['Momentum_20D'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20) * 100)
        return df

    def _calculate_relative_strength(self, df: pd.DataFrame, benchmark_symbol: str = '^NSEI') -> pd.DataFrame:
        """
        Calculate Relative Strength (RS) vs benchmark (Nifty 50)
        RS = (Stock % change / Index % change) * 100
        RS > 100 = Outperforming, RS < 100 = Underperforming
        """
        try:
            # Get benchmark data for same period
            benchmark = yf.Ticker(benchmark_symbol)
            bench_df = benchmark.history(start=df.index[0], end=df.index[-1])
            
            if not bench_df.empty and len(bench_df) >= 20:
                # Calculate 20-day returns for stock
                stock_return = df['Close'].pct_change(periods=20)
                
                # Calculate 20-day returns for benchmark
                bench_return = bench_df['Close'].reindex(df.index, method='ffill').pct_change(periods=20)
                
                # RS Rating (100 = matching index)
                df['RS_Rating'] = ((1 + stock_return) / (1 + bench_return) - 1) * 100 + 100
                df['RS_Rating'] = df['RS_Rating'].fillna(100)  # Neutral if no data
            else:
                df['RS_Rating'] = 100  # Neutral if benchmark data unavailable
        except Exception:
            df['RS_Rating'] = 100  # Neutral on error
        
        return df

    def _generate_signals(self, df: pd.DataFrame) -> Dict:
        """
        Generate trading signals based on technical indicators

        Returns:
            Dict with individual indicator signals and overall technical score
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = {}
        score = 0
        max_score = 0

        # 1. EMA Trend Signal
        max_score += 1
        if latest['Close'] > latest['EMA_21'] > latest['EMA_50']:
            signals['ema_trend'] = 'BULLISH'
            score += 1
        elif latest['Close'] < latest['EMA_21'] < latest['EMA_50']:
            signals['ema_trend'] = 'BEARISH'
        else:
            signals['ema_trend'] = 'NEUTRAL'
            score += 0.5

        # 2. RSI Signal
        max_score += 1
        if RSI_BULLISH_THRESHOLD < latest['RSI'] < RSI_OVERBOUGHT:
            signals['rsi_signal'] = 'BULLISH'
            score += 1
        elif latest['RSI'] > RSI_OVERBOUGHT:
            signals['rsi_signal'] = 'OVERBOUGHT'
        elif latest['RSI'] < RSI_OVERSOLD:
            signals['rsi_signal'] = 'OVERSOLD'
            score += 0.5
        else:
            signals['rsi_signal'] = 'NEUTRAL'
            score += 0.3

        # 3. MACD Signal
        max_score += 1
        if latest['MACD'] > latest['MACD_Signal'] and latest['MACD_Hist'] > 0:
            signals['macd_signal'] = 'BULLISH'
            score += 1
        elif prev['MACD'] <= prev['MACD_Signal'] and latest['MACD'] > latest['MACD_Signal']:
            signals['macd_signal'] = 'BULLISH_CROSSOVER'
            score += 1.2  # Bonus for crossover
        elif latest['MACD'] < latest['MACD_Signal']:
            signals['macd_signal'] = 'BEARISH'
        else:
            signals['macd_signal'] = 'NEUTRAL'
            score += 0.3

        # 4. Bollinger Bands Signal
        max_score += 1
        if latest['BB_Position'] > 0.8:
            signals['bb_signal'] = 'NEAR_UPPER'
        elif latest['BB_Position'] < 0.3 and prev['BB_Position'] < latest['BB_Position']:
            signals['bb_signal'] = 'BOUNCE_FROM_LOWER'
            score += 1
        else:
            signals['bb_signal'] = 'NEUTRAL'
            score += 0.5

        # 5. ADX Trend Strength
        max_score += 1
        if latest['ADX'] > ADX_STRONG_TREND:
            if latest['+DI'] > latest['-DI']:
                signals['adx_signal'] = 'STRONG_UPTREND'
                score += 1
            else:
                signals['adx_signal'] = 'STRONG_DOWNTREND'
        else:
            signals['adx_signal'] = 'WEAK_TREND'
            score += 0.3

        # 6. Volume Signal
        max_score += 1
        if latest['Volume_Ratio'] > VOLUME_SURGE_MULTIPLIER:
            signals['volume_signal'] = 'HIGH_VOLUME'
            score += 1
        else:
            signals['volume_signal'] = 'NORMAL_VOLUME'
            score += 0.5

        # 7. Momentum Signal
        max_score += 1
        if latest['Momentum_5D'] > 3 and latest['Momentum_20D'] > 5:
            signals['momentum_signal'] = 'STRONG_MOMENTUM'
            score += 1
        elif latest['Momentum_5D'] > 0:
            signals['momentum_signal'] = 'POSITIVE_MOMENTUM'
            score += 0.7
        else:
            signals['momentum_signal'] = 'NEGATIVE_MOMENTUM'

        # Calculate technical score (0-10 scale)
        technical_score = (score / max_score) * 10 if max_score > 0 else 0

        signals['technical_score'] = round(technical_score, 2)
        signals['raw_score'] = score
        signals['max_score'] = max_score

        return signals


def test_indicators():
    """Test the technical indicators module"""
    print("🧪 Testing Technical Indicators...")

    # Fetch sample data
    ticker = yf.Ticker('RELIANCE.NS')
    df = ticker.history(period='6mo')

    if df.empty:
        print("❌ Failed to fetch data")
        return

    # Calculate indicators
    ti = TechnicalIndicators()
    result = ti.calculate_all(df)

    if result:
        print(f"\n✅ Indicators calculated successfully!")
        print(f"📊 Price: ₹{result['price']:.2f}")
        print(f"📈 RSI: {result['rsi']:.2f}")
        print(f"📊 MACD: {result['macd']:.4f}")
        print(f"📉 ADX: {result['adx']:.2f}")
        print(f"🎯 Technical Score: {result['signals']['technical_score']}/10")
        print(f"\n📋 Signals:")
        for key, value in result['signals'].items():
            if key not in ['technical_score', 'raw_score', 'max_score']:
                print(f"   {key}: {value}")
    else:
        print("❌ Failed to calculate indicators")


if __name__ == "__main__":
    test_indicators()
