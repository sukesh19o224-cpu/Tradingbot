"""
💰 ADVANCED POSITION SIZING
Volatility-based (ATR) and Drawdown-adjusted position sizing
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from config.settings import *


class PositionSizer:
    """
    Calculate position sizes based on volatility and portfolio drawdown

    Features:
    - ATR-based volatility sizing
    - Drawdown-based risk reduction
    - Quality-adjusted sizing
    - Portfolio-aware calculations
    """

    def __init__(self):
        pass

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR) for volatility measurement

        Args:
            df: OHLCV DataFrame
            period: ATR period (default 14)

        Returns:
            Current ATR value
        """
        if df is None or len(df) < period + 1:
            return 0

        try:
            # Normalize column names
            df = df.copy()
            df.columns = df.columns.str.capitalize()

            # Calculate True Range
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift(1))
            low_close = abs(df['Low'] - df['Close'].shift(1))

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

            # Calculate ATR (simple moving average of TR)
            atr = true_range.rolling(window=period).mean()

            return float(atr.iloc[-1])

        except Exception as e:
            print(f"⚠️ ATR calculation error: {e}")
            return 0

    def calculate_volatility_based_size(
        self,
        portfolio_value: float,
        signal: Dict,
        df: pd.DataFrame,
        base_risk: float = MAX_RISK_PER_TRADE
    ) -> float:
        """
        Calculate position size based on ATR volatility

        Uses ATR to normalize risk across stocks with different volatility

        Args:
            portfolio_value: Total portfolio value
            signal: Trading signal with entry/stop
            df: Historical OHLCV data
            base_risk: Base risk per trade (default from settings)

        Returns:
            Position size in rupees
        """
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']

            # Calculate ATR
            atr = self.calculate_atr(df)

            if atr == 0:
                # Fallback to stop-loss based sizing
                return self._fallback_sizing(portfolio_value, entry_price, stop_loss, base_risk)

            # Risk amount (in rupees)
            risk_amount = portfolio_value * base_risk

            # Stop distance in ATR multiples
            # Use 2 ATR as stop distance (common practice)
            stop_distance_atr = atr * 2

            # Shares to buy
            shares = risk_amount / stop_distance_atr

            # Position value
            position_value = shares * entry_price

            # Cap at max position size
            max_position = portfolio_value * MAX_POSITION_SIZE
            position_value = min(position_value, max_position)

            return position_value

        except Exception as e:
            print(f"⚠️ Volatility sizing error: {e}")
            return self._fallback_sizing(portfolio_value, entry_price, stop_loss, base_risk)

    def _fallback_sizing(
        self,
        portfolio_value: float,
        entry: float,
        stop: float,
        base_risk: float
    ) -> float:
        """Fallback to simple stop-loss based sizing"""
        risk_amount = portfolio_value * base_risk
        risk_per_share = entry - stop

        if risk_per_share <= 0:
            return 0

        shares = risk_amount / risk_per_share
        position_value = shares * entry

        max_position = portfolio_value * MAX_POSITION_SIZE
        return min(position_value, max_position)

    def adjust_for_drawdown(
        self,
        position_size: float,
        current_drawdown: float
    ) -> float:
        """
        Reduce position size based on portfolio drawdown

        Args:
            position_size: Calculated position size
            current_drawdown: Current portfolio drawdown (0.0 to 1.0)

        Returns:
            Adjusted position size
        """
        if not DRAWDOWN_RISK_REDUCTION_ENABLED:
            return position_size

        # Calculate reduction multiplier based on drawdown
        if current_drawdown >= DRAWDOWN_THRESHOLD_MAJOR:
            # At 10%+ drawdown: 50% size
            multiplier = 0.5
        elif current_drawdown >= DRAWDOWN_THRESHOLD_MINOR:
            # At 5-10% drawdown: 75% size
            multiplier = 0.75
        else:
            # Below 5% drawdown: Full size
            multiplier = 1.0

        adjusted_size = position_size * multiplier

        if multiplier < 1.0:
            print(f"   📉 Drawdown adjustment: {current_drawdown*100:.1f}% → {multiplier*100:.0f}% size")

        return adjusted_size

    def adjust_for_quality(
        self,
        position_size: float,
        signal_score: float
    ) -> float:
        """
        Adjust position size based on signal quality

        Args:
            position_size: Base position size
            signal_score: Signal score (0-10)

        Returns:
            Quality-adjusted position size
        """
        if signal_score < 7.0:
            return 0  # Skip low quality

        # Linear multiplier: 0.5x at score 7, 1.0x at score 8, 1.5x at score 9, 2.0x at score 10
        quality_multiplier = 0.5 + (signal_score - 7) * 0.5
        quality_multiplier = min(quality_multiplier, 2.0)  # Cap at 2x

        return position_size * quality_multiplier

    def calculate_complete_position_size(
        self,
        portfolio_value: float,
        available_capital: float,
        signal: Dict,
        df: pd.DataFrame,
        current_drawdown: float = 0.0
    ) -> float:
        """
        Calculate complete position size with all adjustments

        Steps:
        1. Calculate base size using ATR volatility
        2. Adjust for portfolio drawdown
        3. Adjust for signal quality
        4. Ensure doesn't exceed available capital

        Args:
            portfolio_value: Total portfolio value
            available_capital: Available cash
            signal: Trading signal
            df: Historical data for ATR calculation
            current_drawdown: Current portfolio drawdown

        Returns:
            Final position size in rupees
        """
        # Step 1: Volatility-based sizing
        base_size = self.calculate_volatility_based_size(
            portfolio_value, signal, df
        )

        # Step 2: Drawdown adjustment
        size_after_drawdown = self.adjust_for_drawdown(base_size, current_drawdown)

        # Step 3: Quality adjustment
        signal_score = signal.get('score', 7.0)
        final_size = self.adjust_for_quality(size_after_drawdown, signal_score)

        # Step 4: Don't exceed available capital
        final_size = min(final_size, available_capital)

        return final_size


if __name__ == "__main__":
    # Test position sizer
    print("🧪 Testing Position Sizer...")

    import yfinance as yf

    sizer = PositionSizer()

    # Get sample data
    df = yf.Ticker("RELIANCE.NS").history(period="3mo")

    if not df.empty:
        atr = sizer.calculate_atr(df)
        print(f"✅ RELIANCE.NS ATR: ₹{atr:.2f}")

        # Test position sizing
        test_signal = {
            'entry_price': 2500,
            'stop_loss': 2450,
            'score': 8.5
        }

        portfolio_value = 100000

        position_size = sizer.calculate_complete_position_size(
            portfolio_value=portfolio_value,
            available_capital=portfolio_value,
            signal=test_signal,
            df=df,
            current_drawdown=0.08  # 8% drawdown
        )

        print(f"✅ Calculated position size: ₹{position_size:,.0f}")
        print(f"   Portfolio: ₹{portfolio_value:,.0f}")
        print(f"   Signal score: {test_signal['score']}")
        print(f"   Drawdown: 8% → Size reduced to 75%")
