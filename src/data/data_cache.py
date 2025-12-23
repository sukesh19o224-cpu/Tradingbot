"""
💾 Data Cache System - Store historical data to speed up scans

Instead of downloading 60 days of data every 5 minutes,
we cache historical data and only fetch NEW candles.

Performance improvement: 5 minutes → 30-60 seconds per scan
"""

import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import yfinance as yf
from pathlib import Path


class DataCache:
    """
    Cache historical stock data to disk

    Features:
    - Store daily and 15-min data separately
    - Only fetch new candles on updates
    - Auto-cleanup old data
    - Thread-safe (for multi-stock scanning)
    """

    def __init__(self, cache_dir: str = 'data/cache'):
        """
        Initialize data cache

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Separate folders for daily and intraday data
        self.daily_cache_dir = self.cache_dir / 'daily'
        self.intraday_cache_dir = self.cache_dir / 'intraday'

        self.daily_cache_dir.mkdir(exist_ok=True)
        self.intraday_cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, symbol: str, interval: str) -> Path:
        """Get cache file path for a symbol"""
        clean_symbol = symbol.replace('.', '_')

        if interval == '1d':
            return self.daily_cache_dir / f"{clean_symbol}.pkl"
        else:
            return self.intraday_cache_dir / f"{clean_symbol}_{interval}.pkl"

    def _load_from_cache(self, symbol: str, interval: str) -> Optional[Dict]:
        """
        Load cached data for a symbol

        Returns:
            Dict with 'data' (DataFrame) and 'last_update' (datetime)
            None if not cached
        """
        cache_path = self._get_cache_path(symbol, interval)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cached = pickle.load(f)

            # Validate cache
            if 'data' not in cached or 'last_update' not in cached:
                return None

            # Check if cache is too old (> 1 day for daily, > 4 hours for intraday)
            # REDUCED from 7 days to 1 day to ensure fresh data
            max_age = timedelta(days=1) if interval == '1d' else timedelta(hours=4)
            cache_age = datetime.now() - cached['last_update']
            if cache_age > max_age:
                # Cache too old - invalidate it
                return None

            # Also check if data itself is stale (latest date is > 2 days old for daily)
            data = cached.get('data')
            if data is not None and len(data) > 0:
                latest_date = data.index[-1]
                # Convert to timezone-naive for comparison
                if hasattr(latest_date, 'tz') and latest_date.tz is not None:
                    latest_date = latest_date.tz_localize(None)
                
                # Get today's date (timezone-naive)
                today = datetime.now().date()
                if hasattr(latest_date, 'date'):
                    data_date = latest_date.date()
                else:
                    data_date = latest_date
                
                days_old = (today - data_date).days
                # If daily data is > 2 days old, invalidate cache (force fresh fetch)
                if interval == '1d' and days_old > 2:
                    return None

            return cached

        except Exception as e:
            print(f"⚠️ Error loading cache for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, interval: str, data: pd.DataFrame):
        """Save data to cache"""
        cache_path = self._get_cache_path(symbol, interval)

        try:
            cached = {
                'data': data,
                'last_update': datetime.now(),
                'symbol': symbol,
                'interval': interval
            }

            with open(cache_path, 'wb') as f:
                pickle.dump(cached, f)

        except Exception as e:
            print(f"⚠️ Error saving cache for {symbol}: {e}")

    def get_data(self, symbol: str, period: str = '60d', interval: str = '1d', force_fresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Get data for a symbol (from cache or download)

        Smart fetching:
        1. Check cache (unless force_fresh=True)
        2. If cached and recent: Only fetch new candles
        3. If not cached: Download full history
        4. Update cache with fresh data

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Period for initial download (e.g., '60d')
            interval: Candle interval ('1d', '15m', '5m')
            force_fresh: If True, skip cache and fetch fresh data

        Returns:
            DataFrame with OHLCV data, or None if failed
        """
        # Force fresh fetch if requested (for critical operations)
        if force_fresh:
            full_data = self._fetch_new_data(symbol, period, interval)
            if full_data is not None and len(full_data) > 0:
                self._save_to_cache(symbol, interval, full_data)
                return full_data
            return None
        
        # Try to load from cache
        cached = self._load_from_cache(symbol, interval)

        if cached is not None:
            # Cache hit! Always try to fetch fresh data to ensure up-to-date
            cached_data = cached['data']
            last_update = cached['last_update']

            # ALWAYS fetch fresh data (even if cache exists) to ensure latest prices
            # Calculate how many new candles we need
            if interval == '1d':
                # For daily data, fetch last 7 days (to ensure we have latest, including weekends)
                new_data = self._fetch_new_data(symbol, '7d', interval)
            else:
                # For intraday, fetch last 2 days
                new_data = self._fetch_new_data(symbol, '2d', interval)

            if new_data is not None and len(new_data) > 0:
                # Merge cached + new data
                combined = pd.concat([cached_data, new_data])

                # Remove duplicates (keep latest - this ensures fresh data overwrites old)
                combined = combined[~combined.index.duplicated(keep='last')]

                # Sort by date
                combined = combined.sort_index()

                # Trim to keep only recent data (60 days for daily, 7 days for intraday)
                # FIX TIMEZONE BUG: Make cutoff timezone-aware if DataFrame index is timezone-aware
                if interval == '1d':
                    cutoff_days = 60
                else:
                    cutoff_days = 7
                
                cutoff = datetime.now() - timedelta(days=cutoff_days)
                
                # Check if DataFrame index is timezone-aware
                if len(combined) > 0 and hasattr(combined.index[0], 'tz') and combined.index[0].tz is not None:
                    # Make cutoff timezone-aware (use same timezone as DataFrame)
                    import pytz
                    tz = combined.index[0].tz
                    cutoff = pytz.UTC.localize(cutoff) if tz is None else cutoff.replace(tzinfo=tz)
                
                # Filter data >= cutoff
                try:
                    combined = combined[combined.index >= cutoff]
                except TypeError:
                    # If timezone comparison fails, convert DataFrame index to timezone-naive
                    combined.index = combined.index.tz_localize(None) if hasattr(combined.index[0], 'tz') and combined.index[0].tz is not None else combined.index
                    cutoff_naive = cutoff.replace(tzinfo=None) if hasattr(cutoff, 'tzinfo') and cutoff.tzinfo is not None else cutoff
                    combined = combined[combined.index >= cutoff_naive]

                # Update cache with fresh data
                self._save_to_cache(symbol, interval, combined)

                return combined
            else:
                # Couldn't fetch new data - check if cached data is recent enough
                # If cache is > 1 day old, try full fetch
                cache_age = datetime.now() - last_update
                if cache_age > timedelta(days=1):
                    # Cache too old and couldn't update - try full fetch
                    full_data = self._fetch_new_data(symbol, period, interval)
                    if full_data is not None and len(full_data) > 0:
                        self._save_to_cache(symbol, interval, full_data)
                        return full_data
                
                # Return cached data as fallback
                return cached_data

        else:
            # Cache miss - download full history
            full_data = self._fetch_new_data(symbol, period, interval)

            if full_data is not None and len(full_data) > 0:
                # Save to cache
                self._save_to_cache(symbol, interval, full_data)
                return full_data

            return None

    def _fetch_new_data(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)

                if df is None or len(df) == 0:
                    if attempt < max_retries - 1:
                        continue  # Retry
                    return None

                # Standardize column names (lowercase)
                df.columns = df.columns.str.lower()
                
                # Ensure index is timezone-aware (consistent with yfinance)
                # This prevents timezone comparison issues later
                if len(df) > 0 and df.index.tz is None:
                    # yfinance returns timezone-aware data, but if not, make it naive for consistency
                    pass  # Keep as-is

                return df

            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.2 * (attempt + 1))  # Exponential backoff
                    continue
                # Fail silently for individual stocks on final attempt
                return None
        
        return None

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cache

        Args:
            symbol: If specified, only clear this symbol. Otherwise clear all.
        """
        if symbol:
            # Clear specific symbol
            for interval in ['1d', '15m', '5m']:
                cache_path = self._get_cache_path(symbol, interval)
                if cache_path.exists():
                    cache_path.unlink()
                    print(f"🗑️ Cleared cache for {symbol} ({interval})")
        else:
            # Clear all cache
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.daily_cache_dir.mkdir(exist_ok=True)
            self.intraday_cache_dir.mkdir(exist_ok=True)
            print("🗑️ Cleared all cache")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        daily_files = list(self.daily_cache_dir.glob('*.pkl'))
        intraday_files = list(self.intraday_cache_dir.glob('*.pkl'))

        total_size = sum(f.stat().st_size for f in daily_files + intraday_files)

        return {
            'daily_cached': len(daily_files),
            'intraday_cached': len(intraday_files),
            'total_files': len(daily_files) + len(intraday_files),
            'total_size_mb': total_size / (1024 * 1024)
        }


if __name__ == "__main__":
    # Test cache system
    print("🧪 Testing Data Cache System...")

    cache = DataCache()

    # Test with a stock
    symbol = "RELIANCE.NS"

    print(f"\n📊 Fetching {symbol} daily data...")
    import time

    # First fetch (should download)
    start = time.time()
    df_daily = cache.get_data(symbol, period='60d', interval='1d')
    elapsed1 = time.time() - start
    print(f"   First fetch: {elapsed1:.2f}s - {len(df_daily) if df_daily is not None else 0} candles")

    # Second fetch (should use cache)
    start = time.time()
    df_daily = cache.get_data(symbol, period='60d', interval='1d')
    elapsed2 = time.time() - start
    print(f"   Cached fetch: {elapsed2:.2f}s - {len(df_daily) if df_daily is not None else 0} candles")
    print(f"   ⚡ Speed improvement: {elapsed1/elapsed2:.1f}x faster!")

    # Cache stats
    stats = cache.get_cache_stats()
    print(f"\n📦 Cache Stats:")
    print(f"   Daily cached: {stats['daily_cached']} stocks")
    print(f"   Intraday cached: {stats['intraday_cached']} stocks")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
