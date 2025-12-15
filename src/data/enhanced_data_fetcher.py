"""
🚀 ENHANCED DATA FETCHER - Perfect Data for Analysis
Fetches BOTH daily (75 days) AND 15-minute (1 day) data for each stock

This is THE KEY to making the system work properly!

Data Strategy:
- Daily: 75 days (~52 trading days) - Optimal for 50-day MA + positional trading
- Intraday: 1 day (15-min candles) - Most reliable with yfinance
"""

import yfinance as yf
import pandas as pd
import time
from typing import Optional, Dict, Tuple
from datetime import datetime
import warnings
import logging

# Suppress warnings
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)


class EnhancedDataFetcher:
    """
    Enhanced Data Fetcher with DUAL data streams

    For each stock, fetches:
    1. 75 days (~52 trading days) of DAILY candles (for trend analysis, moving averages, etc.)
    2. 1 day of 15-MINUTE candles (for current intraday signals)

    Both datasets are properly normalized and ready for analysis.
    Uses most reliable yfinance periods to avoid API errors.
    """

    def __init__(self, api_delay: float = 0.08):
        """
        Initialize enhanced data fetcher

        Args:
            api_delay: Delay in seconds between API calls (0.08s = very fast, monitor rate limits)
        """
        self.api_delay = api_delay
        self.daily_period = '75d'  # 75 days daily data (~52 trading days, enough for 50-MA)
        self.intraday_period = '1d'  # 1 day 15-min data (most reliable)
        self.stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'daily_fetched': 0,
            'intraday_fetched': 0,
            'rate_limits': 0,  # Track rate limit hits
            'retries': 0  # Track retry attempts
        }

    def get_stock_data_dual(self, symbol: str, verbose: bool = True) -> Dict:
        """
        Fetch BOTH daily and 15-minute data for a stock

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            verbose: Show fetch failures (default: True)

        Returns:
            Dict with keys:
                - 'daily': DataFrame with 90 days daily data
                - 'intraday': DataFrame with 1 day 15-min data
                - 'success': True if at least daily data fetched
                - 'symbol': Symbol name
        """
        self.stats['total_attempts'] += 1

        result = {
            'symbol': symbol,
            'daily': None,
            'intraday': None,
            'success': False
        }

        try:
            # STEP 1: Fetch 75 days DAILY data (CRITICAL!)
            daily_df = self._fetch_daily_data(symbol, verbose=verbose)

            if daily_df is not None and not daily_df.empty and len(daily_df) >= 30:
                # Normalize column names (handle market open/closed variations)
                daily_df = self._normalize_columns(daily_df)
                result['daily'] = daily_df
                self.stats['daily_fetched'] += 1
            else:
                # No daily data = skip this stock
                self.stats['failed'] += 1
                if verbose:
                    print(f"   ⚠️ {symbol}: Failed to fetch daily data")
                return result

            # Small delay before intraday request (reduced - same stock, faster)
            time.sleep(self.api_delay * 0.5)  # 50% of delay (same stock = less risk)

            # STEP 2: Fetch today's 15-MINUTE data (for intraday signals)
            intraday_df = self._fetch_intraday_data(symbol, verbose=verbose)

            if intraday_df is not None and not intraday_df.empty:
                # Normalize column names
                intraday_df = self._normalize_columns(intraday_df)
                result['intraday'] = intraday_df
                self.stats['intraday_fetched'] += 1
            elif verbose:
                print(f"   ⚠️ {symbol}: Intraday data unavailable (market closed or no data)")

            # Success if we got at least daily data
            result['success'] = True
            self.stats['successful'] += 1

        except Exception as e:
            self.stats['failed'] += 1
            if verbose:
                error_msg = str(e).lower()
                if 'rate limit' in error_msg or 'too many requests' in error_msg:
                    print(f"   🚨 {symbol}: RATE LIMIT HIT - Too fast! Consider increasing delay")
                else:
                    print(f"   ❌ {symbol}: Fetch error - {str(e)[:50]}")

        return result

    def _fetch_daily_data(self, symbol: str, max_retries: int = 2, verbose: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch 60-90 days of DAILY data (configurable)

        Args:
            symbol: Stock symbol
            max_retries: Number of retry attempts
            verbose: Show retry attempts

        Returns:
            DataFrame with daily OHLCV data
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    if verbose:
                        print(f"   🔄 {symbol}: Retrying daily data fetch (attempt {attempt + 1}/{max_retries})")
                    time.sleep(1.0)  # Wait 1s before retry

                ticker = yf.Ticker(symbol)

                # Fetch daily data (3mo = ~90 days, reliable with yfinance)
                df = ticker.history(period=self.daily_period, interval='1d')

                if not df.empty and len(df) >= 30:  # Need at least 30 days
                    return df

            except Exception as e:
                error_msg = str(e).lower()
                if 'rate limit' in error_msg or 'too many requests' in error_msg or '429' in error_msg or 'forbidden' in error_msg:
                    self.stats['rate_limits'] += 1
                    if verbose and attempt == max_retries - 1:  # Only show on final failure
                        print(f"   🚨 {symbol}: RATE LIMIT on daily fetch - Too fast! (Total rate limits: {self.stats['rate_limits']})")
                if attempt > 0:
                    self.stats['retries'] += 1
                continue

        return None

    def _fetch_intraday_data(self, symbol: str, max_retries: int = 2, verbose: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch today's 15-MINUTE data (1 day only - most reliable)

        Args:
            symbol: Stock symbol
            max_retries: Number of retry attempts
            verbose: Show retry attempts

        Returns:
            DataFrame with 15-min OHLCV data
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    if verbose:
                        print(f"   🔄 {symbol}: Retrying intraday data fetch (attempt {attempt + 1}/{max_retries})")
                    time.sleep(1.0)  # Wait 1s before retry

                ticker = yf.Ticker(symbol)

                # Fetch 1 day of 15-min data (most reliable with yfinance)
                df = ticker.history(period=self.intraday_period, interval='15m')

                if not df.empty:
                    # Return today's intraday data
                    # If market closed, returns last available candles
                    return df

            except Exception as e:
                error_msg = str(e).lower()
                if 'rate limit' in error_msg or 'too many requests' in error_msg or '429' in error_msg or 'forbidden' in error_msg:
                    self.stats['rate_limits'] += 1
                    if verbose and attempt == max_retries - 1:  # Only show on final failure
                        print(f"   🚨 {symbol}: RATE LIMIT on intraday fetch - Too fast! (Total rate limits: {self.stats['rate_limits']})")
                if attempt > 0:
                    self.stats['retries'] += 1
                continue

        return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names (Yahoo Finance inconsistency fix)

        Yahoo Finance returns:
        - Uppercase ('Open', 'High', 'Low', 'Close', 'Volume') when market open
        - Lowercase ('open', 'high', 'low', 'close', 'volume') when market closed

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with normalized column names (Capitalized)
        """
        df = df.copy()

        # Map both cases to proper case
        column_map = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        }

        # Rename columns
        df.rename(columns=column_map, inplace=True)

        # Ensure we have all required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if all(col in df.columns for col in required):
            return df[required]  # Return only OHLCV

        return df

    def get_current_price(self, symbol: str) -> float:
        """
        Get current/latest LIVE price for a stock (ULTRA-ACCURATE)
        
        Uses multiple methods in priority order to get the MOST current price:
        1. fast_info.lastPrice (real-time during market hours - MOST ACCURATE)
        2. fast_info.regularMarketPrice (alternative real-time price)
        3. Intraday data (1m - most recent candle - very current)
        4. Intraday data (5m - fallback)
        5. Daily data (fallback - last close)

        Args:
            symbol: Stock symbol

        Returns:
            Current price or 0 if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Method 1: Try fast_info.lastPrice (REAL-TIME - most accurate during market hours)
            try:
                fast_info = ticker.fast_info
                # Try lastPrice first (most current)
                if hasattr(fast_info, 'lastPrice') and fast_info.lastPrice and fast_info.lastPrice > 0:
                    return float(fast_info.lastPrice)
                # Try regularMarketPrice as alternative
                if hasattr(fast_info, 'regularMarketPrice') and fast_info.regularMarketPrice and fast_info.regularMarketPrice > 0:
                    return float(fast_info.regularMarketPrice)
            except:
                pass
            
            # Method 2: Try intraday data (1-minute - MOST RECENT candle)
            try:
                # 1-minute data is most current (updates every minute)
                intraday_data = ticker.history(period='1d', interval='1m')
                if not intraday_data.empty and len(intraday_data) > 0:
                    latest_price = float(intraday_data['Close'].iloc[-1])
                    if latest_price > 0:
                        return latest_price
            except:
                pass
            
            # Method 3: Fallback to 5-minute data
            try:
                intraday_data = ticker.history(period='1d', interval='5m')
                if not intraday_data.empty and len(intraday_data) > 0:
                    latest_price = float(intraday_data['Close'].iloc[-1])
                    if latest_price > 0:
                        return latest_price
            except:
                pass
            
            # Method 4: Fallback to daily data (last close - when market closed)
            try:
                daily_data = ticker.history(period='1d', interval='1d')
                if not daily_data.empty and len(daily_data) > 0:
                    latest_price = float(daily_data['Close'].iloc[-1])
                    if latest_price > 0:
                        return latest_price
            except:
                pass

            return 0

        except Exception:
            return 0

    def get_stats(self) -> Dict:
        """Get fetching statistics"""
        success_rate = (self.stats['successful'] / self.stats['total_attempts'] * 100
                       if self.stats['total_attempts'] > 0 else 0)

        return {
            'total_attempts': self.stats['total_attempts'],
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'success_rate': success_rate,
            'daily_fetched': self.stats['daily_fetched'],
            'intraday_fetched': self.stats['intraday_fetched']
        }

    def print_stats(self):
        """Print fetching statistics"""
        stats = self.get_stats()
        print(f"\n📊 Data Fetching Statistics:")
        print(f"   Total Attempts: {stats['total_attempts']}")
        print(f"   ✅ Successful: {stats['successful']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   📈 Success Rate: {stats['success_rate']:.1f}%")
        print(f"   📅 Daily Data: {stats['daily_fetched']} stocks")
        print(f"   ⏱️ Intraday Data: {stats['intraday_fetched']} stocks")


def test_enhanced_fetcher():
    """Test the enhanced data fetcher"""
    print("🧪 Testing Enhanced Data Fetcher...")
    print("="*70)

    fetcher = EnhancedDataFetcher(api_delay=0.3)

    # Test with 5 stocks
    test_stocks = [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS',
        'INFY.NS',
        'ICICIBANK.NS'
    ]

    print(f"\n📡 Testing with {len(test_stocks)} stocks...\n")

    for i, symbol in enumerate(test_stocks, 1):
        print(f"{i}. {symbol}...", end=' ', flush=True)

        result = fetcher.get_stock_data_dual(symbol)

        if result['success']:
            daily_len = len(result['daily']) if result['daily'] is not None else 0
            intraday_len = len(result['intraday']) if result['intraday'] is not None else 0

            print(f"✅ Daily: {daily_len} candles, Intraday: {intraday_len} candles")

            if result['daily'] is not None:
                latest_close = result['daily']['Close'].iloc[-1]
                print(f"   Latest Close: ₹{latest_close:.2f}")
        else:
            print("❌ Failed")

    # Print stats
    fetcher.print_stats()

    print("\n" + "="*70)
    print("✅ Test Complete!")


if __name__ == "__main__":
    test_enhanced_fetcher()
