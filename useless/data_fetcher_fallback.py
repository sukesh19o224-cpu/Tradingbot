"""
📡 DATA FETCHER WITH FALLBACK
Multi-source data fetching with automatic fallback for reliability
"""

import yfinance as yf
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
import time
from config.settings import *


class DataFetcherWithFallback:
    """
    Robust data fetcher with multiple source fallbacks

    Fallback chain:
    1. yfinance (primary - free, reliable)
    2. yfinance with longer timeout (retry)
    3. Alternative calculation methods

    Note: NSE-specific libraries (jugaad_data, nsepython) require additional setup
    and may have reliability issues, so we focus on yfinance with smart retries
    """

    def __init__(self, api_delay: float = 0.1):
        """
        Initialize data fetcher

        Args:
            api_delay: Delay between API calls (seconds)
        """
        self.api_delay = api_delay

    def get_stock_data(
        self,
        symbol: str,
        period: str = '6mo',
        interval: str = '1d',
        max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch stock data with automatic fallback and retries

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1mo', '3mo', '6mo', '1y')
            interval: Data interval ('1d', '15m', '5m', '1h')
            max_retries: Maximum retry attempts

        Returns:
            DataFrame with OHLCV data or None if all attempts fail
        """
        # Method 1: Standard yfinance
        df = self._fetch_yfinance(symbol, period, interval)
        if df is not None and not df.empty:
            return df

        # Method 2: yfinance with extended timeout and retries
        df = self._fetch_yfinance_retry(symbol, period, interval, max_retries)
        if df is not None and not df.empty:
            return df

        # Method 3: Try with shorter period (sometimes works)
        if period in ['6mo', '1y', '2y']:
            print(f"   ⚠️ Trying shorter period for {symbol}...")
            df = self._fetch_yfinance(symbol, '3mo', interval)
            if df is not None and not df.empty:
                return df

        # All methods failed
        return None

    def _fetch_yfinance(
        self,
        symbol: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Primary yfinance fetch"""
        try:
            time.sleep(self.api_delay)  # Rate limiting

            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if not df.empty:
                return df

        except Exception as e:
            # Silent failure for clean logs
            pass

        return None

    def _fetch_yfinance_retry(
        self,
        symbol: str,
        period: str,
        interval: str,
        max_retries: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch with exponential backoff retry

        Uses progressively longer timeouts and delays
        """
        for attempt in range(max_retries):
            try:
                # Increasing delay on each retry
                delay = self.api_delay * (2 ** attempt)  # 0.1s, 0.2s, 0.4s, etc.
                time.sleep(delay)

                ticker = yf.Ticker(symbol)

                # Try with increasing timeout
                import requests
                session = requests.Session()
                session.timeout = 10 + (attempt * 5)  # 10s, 15s, 20s

                ticker._session = session

                df = ticker.history(period=period, interval=interval)

                if not df.empty:
                    if attempt > 0:
                        print(f"   ✅ {symbol} fetched on retry #{attempt + 1}")
                    return df

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    pass
                else:
                    # Wait before next retry
                    time.sleep(1 * (2 ** attempt))  # 1s, 2s, 4s

        return None

    def get_current_price(
        self,
        symbol: str
    ) -> float:
        """
        Get current price with fallback

        Args:
            symbol: Stock symbol

        Returns:
            Current price or 0 if failed
        """
        try:
            # Method 1: Regular history
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')

            if not data.empty:
                return float(data['Close'].iloc[-1])

            # Method 2: Fast info
            price = ticker.fast_info.get('lastPrice', 0)
            if price > 0:
                return float(price)

            # Method 3: Previous close
            price = ticker.fast_info.get('previousClose', 0)
            if price > 0:
                print(f"   ⚠️ Using previous close for {symbol}")
                return float(price)

        except Exception as e:
            pass

        return 0

    def verify_data_quality(
        self,
        df: pd.DataFrame,
        min_rows: int = 50
    ) -> bool:
        """
        Verify fetched data quality

        Args:
            df: DataFrame to verify
            min_rows: Minimum required rows

        Returns:
            True if data quality is good
        """
        if df is None or df.empty:
            return False

        # Check minimum rows
        if len(df) < min_rows:
            return False

        # Check for required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            return False

        # Check for NaN values in recent data (last 10 rows)
        recent = df.tail(10)
        if recent[required_cols].isnull().any().any():
            return False

        # Check for zero/negative prices
        if (recent['Close'] <= 0).any():
            return False

        return True


def test_fallback_fetcher():
    """Test the fallback data fetcher"""
    print("🧪 Testing Data Fetcher with Fallback...")

    fetcher = DataFetcherWithFallback(api_delay=0.2)

    # Test 1: Valid stock
    print("\n1. Testing valid stock (RELIANCE.NS)...")
    df = fetcher.get_stock_data('RELIANCE.NS', period='3mo')

    if df is not None:
        is_quality = fetcher.verify_data_quality(df)
        print(f"   ✅ Fetched {len(df)} rows")
        print(f"   Quality check: {'✅ PASS' if is_quality else '❌ FAIL'}")
        print(f"   Latest price: ₹{df['Close'].iloc[-1]:.2f}")
    else:
        print("   ❌ Failed to fetch")

    # Test 2: Invalid stock
    print("\n2. Testing invalid stock...")
    df = fetcher.get_stock_data('INVALID.NS', period='3mo')
    print(f"   Result: {'❌ Correctly failed' if df is None else '⚠️ Unexpected success'}")

    # Test 3: Current price
    print("\n3. Testing current price fetch...")
    price = fetcher.get_current_price('TCS.NS')
    print(f"   TCS.NS current price: ₹{price:.2f}")

    # Test 4: Multiple stocks (stress test)
    print("\n4. Testing multiple stocks...")
    test_symbols = ['INFY.NS', 'HDFCBANK.NS', 'ITC.NS']
    success = 0

    for symbol in test_symbols:
        df = fetcher.get_stock_data(symbol, period='1mo')
        if df is not None and not df.empty:
            success += 1
            print(f"   ✅ {symbol}")
        else:
            print(f"   ❌ {symbol}")

    print(f"\n   Success rate: {success}/{len(test_symbols)} ({success/len(test_symbols)*100:.0f}%)")


if __name__ == "__main__":
    test_fallback_fetcher()
