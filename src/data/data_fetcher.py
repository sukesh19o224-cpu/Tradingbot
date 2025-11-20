"""
📡 DATA FETCHER - NSE Stock Data with Smart Caching
Efficient data retrieval with caching to reduce API calls
"""

import yfinance as yf
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import warnings
warnings.filterwarnings('ignore')

from config.settings import *


class DataFetcher:
    """
    Fetch and cache stock data from Yahoo Finance

    Features:
    - Automatic caching (reduces API calls)
    - Retry logic for failed requests
    - Batch fetching for multiple stocks
    - Cache expiration management
    """

    def __init__(self):
        self.cache_dir = CACHE_FOLDER
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_duration = timedelta(minutes=CACHE_DURATION_MINUTES)

    def get_stock_data(self, symbol: str, period: str = HISTORICAL_DATA_PERIOD,
                      interval: str = '1d', use_cache: bool = CACHE_ENABLED) -> Optional[pd.DataFrame]:
        """
        Fetch stock data with caching

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1mo', '3mo', '6mo', '1y', etc.)
            interval: Data interval ('1d', '15m', '5m', '1h', etc.)
            use_cache: Whether to use cached data

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            # Check cache first
            if use_cache:
                cached_data = self._load_from_cache(symbol, period)
                if cached_data is not None:
                    return cached_data

            # Fetch from Yahoo Finance with retries
            df = self._fetch_with_retry(symbol, period, interval)

            if df is not None and not df.empty:
                # Save to cache
                if use_cache:
                    self._save_to_cache(symbol, period, df)
                return df
            else:
                print(f"⚠️ No data received for {symbol}")
                return None

        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """
        Get current/latest price for a stock

        Args:
            symbol: Stock symbol

        Returns:
            Current price or 0 if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')

            if not data.empty:
                return float(data['Close'].iloc[-1])
            else:
                # Try fast_info as backup
                return float(ticker.fast_info.get('lastPrice', 0))

        except Exception as e:
            print(f"❌ Error getting price for {symbol}: {e}")
            return 0

    def get_multiple_stocks(self, symbols: List[str], period: str = HISTORICAL_DATA_PERIOD) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks

        Args:
            symbols: List of stock symbols
            period: Data period

        Returns:
            Dict mapping symbol to DataFrame
        """
        results = {}

        print(f"📡 Fetching data for {len(symbols)} stocks...")

        for i, symbol in enumerate(symbols, 1):
            print(f"   [{i}/{len(symbols)}] {symbol}...", end=' ')

            df = self.get_stock_data(symbol, period)

            if df is not None and not df.empty:
                results[symbol] = df
                print("✅")
            else:
                print("❌")

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        print(f"✅ Successfully fetched {len(results)}/{len(symbols)} stocks")

        return results

    def _fetch_with_retry(self, symbol: str, period: str, interval: str = '1d', max_retries: int = MAX_API_RETRIES) -> Optional[pd.DataFrame]:
        """Fetch data with automatic retry on failure"""
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)

                if not df.empty:
                    return df

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ Attempt {attempt + 1} failed for {symbol}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All retries failed for {symbol}: {e}")

        return None

    def _load_from_cache(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh"""
        try:
            cache_file = self._get_cache_filename(symbol, period)

            if not os.path.exists(cache_file):
                return None

            # Check if cache is still fresh
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time > self.cache_duration:
                return None  # Cache expired

            # Load cached data
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            print(f"📦 Loaded {symbol} from cache")
            return df

        except Exception as e:
            print(f"⚠️ Cache load error for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, period: str, df: pd.DataFrame):
        """Save data to cache"""
        try:
            cache_file = self._get_cache_filename(symbol, period)
            df.to_csv(cache_file)
        except Exception as e:
            print(f"⚠️ Cache save error for {symbol}: {e}")

    def _get_cache_filename(self, symbol: str, period: str) -> str:
        """Generate cache filename"""
        safe_symbol = symbol.replace('.', '_')
        return os.path.join(self.cache_dir, f"{safe_symbol}_{period}.csv")

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cache for a specific symbol or all cache

        Args:
            symbol: Specific symbol to clear, or None for all
        """
        try:
            if symbol:
                # Clear specific symbol
                for file in os.listdir(self.cache_dir):
                    if file.startswith(symbol.replace('.', '_')):
                        os.remove(os.path.join(self.cache_dir, file))
                print(f"🗑️ Cleared cache for {symbol}")
            else:
                # Clear all cache
                for file in os.listdir(self.cache_dir):
                    os.remove(os.path.join(self.cache_dir, file))
                print("🗑️ Cleared all cache")

        except Exception as e:
            print(f"❌ Cache clear error: {e}")


def test_data_fetcher():
    """Test the data fetcher module"""
    print("🧪 Testing Data Fetcher...")

    fetcher = DataFetcher()

    # Test single stock
    print("\n1. Testing single stock fetch...")
    df = fetcher.get_stock_data('RELIANCE.NS')

    if df is not None:
        print(f"✅ Fetched {len(df)} rows for RELIANCE.NS")
        print(f"📊 Latest price: ₹{df['Close'].iloc[-1]:.2f}")
    else:
        print("❌ Failed to fetch RELIANCE.NS")

    # Test current price
    print("\n2. Testing current price...")
    price = fetcher.get_current_price('TCS.NS')
    print(f"📈 TCS.NS current price: ₹{price:.2f}")

    # Test multiple stocks
    print("\n3. Testing multiple stocks fetch...")
    test_symbols = ['INFY.NS', 'HDFCBANK.NS', 'ITC.NS']
    results = fetcher.get_multiple_stocks(test_symbols)
    print(f"✅ Successfully fetched {len(results)}/{len(test_symbols)} stocks")

    # Test cache
    print("\n4. Testing cache (second fetch should be instant)...")
    start = time.time()
    df2 = fetcher.get_stock_data('RELIANCE.NS')
    elapsed = time.time() - start
    print(f"⚡ Cached fetch took {elapsed:.3f}s")


if __name__ == "__main__":
    test_data_fetcher()
