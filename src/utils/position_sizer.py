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
        Calculate EQUAL position size for all trades

        EQUAL SIZING: Each position gets the same capital allocation (16.7% of portfolio)
        This ensures consistent position sizing regardless of stop loss distance.

        For ₹50,000 portfolio with 6 max positions:
        - Each position = ₹50,000 × 16.7% = ₹8,350

        Stop loss is still ATR-adjusted for proper risk management,
        but position SIZE is equal for all trades.

        Args:
            portfolio_value: Total portfolio value
            signal: Trading signal with entry/stop
            df: Historical OHLCV data (not used for equal sizing)
            base_risk: Base risk per trade (not used for equal sizing)

        Returns:
            Position size in rupees (equal for all positions)
        """
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']

            # Validate stop loss
            risk_per_share = entry_price - stop_loss
            if risk_per_share <= 0:
                # Invalid stop loss (above entry price)
                print(f"   ⚠️  Invalid stop loss: Entry={entry_price:.2f}, Stop={stop_loss:.2f}")
                return 0

            # EQUAL SIZING: Use MAX_POSITION_SIZE for all positions
            # MAX_POSITION_SIZE = 16.7% (for 6 positions in ₹50K portfolio)
            position_value = portfolio_value * MAX_POSITION_SIZE

            # That's it! Every position gets the same capital allocation
            # No complex risk calculations - just equal distribution

            return position_value

        except Exception as e:
            print(f"⚠️ Position sizing error: {e}")
            # Fallback to equal sizing
            return portfolio_value * MAX_POSITION_SIZE

    def _fallback_sizing(
        self,
        portfolio_value: float,
        entry: float,
        stop: float,
        base_risk: float
    ) -> float:
        """Fallback to equal sizing"""
        # EQUAL SIZING: Just return MAX_POSITION_SIZE
        return portfolio_value * MAX_POSITION_SIZE

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
        signal_score: float,
        strategy: str = 'positional',
        mqs_score: Optional[float] = None
    ) -> float:
        """
        Adjust position size based on signal quality

        Args:
            position_size: Base position size
            signal_score: Signal score (0-10)
            strategy: 'swing' or 'positional' - uses different thresholds
            mqs_score: Optional MQS score (0-8) for additional quality adjustment

        Returns:
            Quality-adjusted position size
        """
        from config.settings import MIN_SIGNAL_SCORE, MIN_SWING_SIGNAL_SCORE, MQS_CONFIG, USE_MQS_QUALITY_FILTER

        # Different thresholds for swing vs positional
        if strategy == 'swing':
            min_score = MIN_SWING_SIGNAL_SCORE  # 5.5 for swing
            if signal_score < min_score:
                return 0  # Skip below swing threshold
            # For swing: 0.5x at 5.5, 0.75x at 6.0, 1.0x at 6.5, 1.25x at 7.0
            quality_multiplier = 0.5 + (signal_score - 5.5) * 0.5
        else:
            min_score = MIN_SIGNAL_SCORE  # 7.0 for positional
            if signal_score < min_score:
                return 0  # Skip below positional threshold
            # EQUAL POSITION SIZING: All qualifying signals get same position size
            # This ensures consistent ₹8,500 per trade for better capital allocation
            quality_multiplier = 1.0  # Always 100% for positional trades

        quality_multiplier = min(quality_multiplier, 1.0)  # FIXED: Cap at 1x (no oversizing)
        base_adjusted = position_size * quality_multiplier

        # =========================================================================
        # 🎯 MQS QUALITY ADJUSTMENT (if enabled and available)
        # =========================================================================
        if USE_MQS_QUALITY_FILTER and mqs_score is not None and mqs_score > 0:
            use_mqs_sizing = MQS_CONFIG.get('USE_MQS_POSITION_SIZING', True)

            if use_mqs_sizing:
                # MQS-based position sizing multiplier
                # 7-8: 100% (1.0x)
                # 5-6: 75% (0.75x)
                # 3-4: 50% (0.5x)
                # <3: Already filtered out

                if mqs_score >= MQS_CONFIG['MQS_HIGH_CONVICTION']:  # ≥7.0
                    mqs_multiplier = 1.0  # Full position (100%)
                elif mqs_score >= MQS_CONFIG['MQS_GOOD_SETUP']:  # 5.0-6.9
                    mqs_multiplier = 0.75  # Reduced position (75%)
                elif mqs_score >= MQS_CONFIG['MQS_CAUTIOUS']:  # 3.0-4.9
                    mqs_multiplier = 0.5  # Half position (50%)
                else:
                    mqs_multiplier = 0.25  # Minimal position (25%) - should be filtered already

                # Apply MQS adjustment
                final_size = base_adjusted * mqs_multiplier

                # Show adjustment if significant
                if abs(mqs_multiplier - 1.0) > 0.01:
                    print(f"   🎯 MQS Adjustment: Score {mqs_score:.1f}/8 → {mqs_multiplier*100:.0f}% position size")

                return final_size

        return base_adjusted

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
        if base_size <= 0:
            print(f"   ⚠️  Base size is 0 or negative: {base_size:.2f}")

        # Step 2: Drawdown adjustment
        size_after_drawdown = self.adjust_for_drawdown(base_size, current_drawdown)

        # Step 3: Quality adjustment (with strategy-aware threshold)
        signal_score = signal.get('score', 7.0)
        strategy = signal.get('strategy', 'positional')  # Get strategy type
        mqs_score = signal.get('mqs_score')  # Get MQS score if available
        final_size = self.adjust_for_quality(size_after_drawdown, signal_score, strategy, mqs_score)
        if final_size <= 0:
            print(f"   ⚠️  Quality adjustment returned 0 (score={signal_score:.1f}, strategy={strategy})")

        # Step 4: Re-apply MAX_POSITION_SIZE cap (quality adjustment might have increased it)
        max_position = portfolio_value * MAX_POSITION_SIZE
        if final_size > max_position:
            print(f"   📊 Position capped: ₹{final_size:,.0f} → ₹{max_position:,.0f} (20% max)")
            final_size = max_position

        # Step 5: Don't exceed available capital
        final_size = min(final_size, available_capital)
        if final_size <= 0:
            print(f"   ⚠️  Final size is 0 (available_capital={available_capital:,.0f})")

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
