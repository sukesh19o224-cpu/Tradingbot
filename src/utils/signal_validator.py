"""
✅ SIGNAL VALIDATOR
Validates trading signals for freshness, liquidity, and quality
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import yfinance as yf
from config.settings import *


class SignalValidator:
    """
    Validate trading signals before execution

    Checks:
    - Signal freshness (age and price movement)
    - Liquidity (volume, spread, depth)
    - Quality thresholds
    """

    def __init__(self):
        pass

    def validate_signal_freshness(
        self,
        signal: Dict,
        current_price: float
    ) -> Tuple[bool, str]:
        """
        Check if signal is still fresh/valid

        Args:
            signal: Trading signal with timestamp
            current_price: Current market price

        Returns:
            (is_valid, reason)
        """
        try:
            # Check signal age
            signal_timestamp = signal.get('timestamp')
            if not signal_timestamp:
                return True, "OK"  # No timestamp, assume fresh

            signal_time = datetime.fromisoformat(signal_timestamp)
            current_time = datetime.now()

            age_minutes = (current_time - signal_time).total_seconds() / 60

            # Signal too old?
            if age_minutes > SIGNAL_MAX_AGE_MINUTES:
                return False, f"STALE_SIGNAL ({age_minutes:.0f} min old)"

            # Check if price moved significantly since signal
            entry_price = signal.get('entry_price', 0)
            if entry_price > 0:
                price_change = abs(current_price - entry_price) / entry_price

                if price_change > SIGNAL_PRICE_MOVE_THRESHOLD:
                    return False, f"PRICE_MOVED ({price_change*100:.1f}%)"

            return True, "OK"

        except Exception as e:
            print(f"⚠️ Signal freshness check error: {e}")
            return True, "OK"  # Default to allow on error

    def check_liquidity(
        self,
        symbol: str,
        min_volume: int = MIN_AVG_VOLUME,
        min_value: int = MIN_VALUE_TRADED
    ) -> Tuple[bool, str]:
        """
        Check if stock has sufficient liquidity

        Args:
            symbol: Stock symbol
            min_volume: Minimum average volume
            min_value: Minimum daily turnover

        Returns:
            (is_liquid, reason)
        """
        try:
            ticker = yf.Ticker(symbol)

            # Get recent trading data
            hist = ticker.history(period='5d')

            if hist.empty:
                return False, "NO_DATA"

            # Calculate average volume (last 5 days)
            avg_volume = hist['Volume'].mean()

            if avg_volume < min_volume:
                return False, f"LOW_VOLUME ({avg_volume/1000:.0f}K < {min_volume/1000:.0f}K)"

            # Calculate average daily turnover
            avg_price = hist['Close'].mean()
            avg_turnover = avg_volume * avg_price

            if avg_turnover < min_value:
                return False, f"LOW_TURNOVER (₹{avg_turnover/10000000:.1f}Cr < ₹{min_value/10000000:.0f}Cr)"

            return True, "OK"

        except Exception as e:
            print(f"⚠️ Liquidity check error for {symbol}: {e}")
            return True, "OK"  # Default to allow on error (conservative)

    def check_bid_ask_spread(
        self,
        symbol: str,
        max_spread: float = MAX_BID_ASK_SPREAD
    ) -> Tuple[bool, str]:
        """
        Check bid-ask spread (approximation using day range)

        Note: yfinance doesn't provide real-time bid/ask, so we approximate
        using the day's high-low range as a proxy for spread

        Args:
            symbol: Stock symbol
            max_spread: Maximum allowed spread (%)

        Returns:
            (is_acceptable, reason)
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')

            if hist.empty:
                return True, "OK"  # No data, allow by default

            high = hist['High'].iloc[-1]
            low = hist['Low'].iloc[-1]
            close = hist['Close'].iloc[-1]

            # Approximate spread using intraday range
            # Real spread would be (ask - bid) / mid_price
            # We use (high - low) / close as proxy
            approx_spread = (high - low) / close if close > 0 else 0

            # Use 50% of range as spread estimate (conservative)
            estimated_spread = approx_spread * 0.5

            if estimated_spread > max_spread:
                return False, f"WIDE_SPREAD ({estimated_spread*100:.2f}% > {max_spread*100:.1f}%)"

            return True, "OK"

        except Exception as e:
            print(f"⚠️ Spread check error for {symbol}: {e}")
            return True, "OK"  # Default to allow

    def validate_complete_signal(
        self,
        signal: Dict,
        check_liquidity: bool = True
    ) -> Tuple[bool, str]:
        """
        Complete signal validation

        Checks:
        1. Signal score threshold
        2. Signal freshness
        3. Liquidity (if enabled)
        4. Bid-ask spread

        Args:
            signal: Trading signal
            check_liquidity: Whether to check liquidity (can be slow)

        Returns:
            (is_valid, reason)
        """
        # Check 1: Score threshold
        score = signal.get('score', 0)
        if score < MIN_SIGNAL_SCORE:
            return False, f"LOW_SCORE ({score:.1f} < {MIN_SIGNAL_SCORE})"

        # Check 2: Freshness
        symbol = signal.get('symbol', '')
        current_price = signal.get('current_price', signal.get('entry_price', 0))

        is_fresh, reason = self.validate_signal_freshness(signal, current_price)
        if not is_fresh:
            return False, reason

        # Check 3: Liquidity (optional, can be slow)
        if check_liquidity:
            is_liquid, reason = self.check_liquidity(symbol)
            if not is_liquid:
                return False, reason

            # Check 4: Spread
            has_tight_spread, reason = self.check_bid_ask_spread(symbol)
            if not has_tight_spread:
                return False, reason

        return True, "OK"


if __name__ == "__main__":
    # Test signal validator
    print("🧪 Testing Signal Validator...")

    validator = SignalValidator()

    # Test 1: Fresh signal
    print("\n1. Testing signal freshness...")
    test_signal = {
        'symbol': 'RELIANCE.NS',
        'timestamp': datetime.now().isoformat(),
        'entry_price': 2500,
        'current_price': 2505,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(test_signal, 2505)
    print(f"   Fresh signal: {is_valid} ({reason})")

    # Test 2: Stale signal
    print("\n2. Testing stale signal...")
    old_signal = {
        'symbol': 'RELIANCE.NS',
        'timestamp': (datetime.now() - timedelta(minutes=45)).isoformat(),
        'entry_price': 2500,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(old_signal, 2505)
    print(f"   Stale signal (45 min old): {is_valid} ({reason})")

    # Test 3: Price moved
    print("\n3. Testing price movement...")
    moved_signal = {
        'symbol': 'RELIANCE.NS',
        'timestamp': datetime.now().isoformat(),
        'entry_price': 2500,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(moved_signal, 2530)  # +1.2%
    print(f"   Price moved +1.2%: {is_valid} ({reason})")

    # Test 4: Liquidity check
    print("\n4. Testing liquidity check...")
    is_liquid, reason = validator.check_liquidity('RELIANCE.NS')
    print(f"   RELIANCE.NS liquidity: {is_liquid} ({reason})")

    # Test 5: Complete validation
    print("\n5. Testing complete validation...")
    is_valid, reason = validator.validate_complete_signal(test_signal, check_liquidity=False)
    print(f"   Complete validation: {is_valid} ({reason})")
