"""
NSE Bhavcopy and Delivery Data Fetcher

Fetches delivery percentage data from NSE which is CRITICAL for Indian markets:
- Delivery >45% = Real institutional buying
- Delivery <35% = Intraday speculation (fake move)

This is the single most important quality metric for momentum trades.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import zipfile
import io
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class NSEDeliveryDataFetcher:
    """
    Fetch delivery percentage data from NSE Bhavcopy reports
    """

    def __init__(self, cache_dir: str = "data/cache/delivery"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # NSE URLs
        self.bhavcopy_url = "https://www.nseindia.com/api/reports?archives=%5B%7B%22name%22%3A%22CM%20-%20Bhavcopy(csv)%22%2C%22type%22%3A%22archives%22%2C%22category%22%3A%22capital-market%22%2C%22section%22%3A%22equities%22%7D%5D&date={date}&type=equities&mode=single"
        self.delivery_url = "https://www.nseindia.com/api/reports?archives=%5B%7B%22name%22%3A%22CM%20-%20Delivery%20position(csv)%22%2C%22type%22%3A%22archives%22%2C%22category%22%3A%22capital-market%22%2C%22section%22%3A%22equities%22%7D%5D&date={date}&type=equities&mode=single"

        # Headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_delivery_data(self, symbol: str, days: int = 5) -> Optional[pd.DataFrame]:
        """
        Get delivery percentage data for a symbol

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            days: Number of trading days to fetch

        Returns:
            DataFrame with columns: [Date, Symbol, Delivered_Qty, Traded_Qty, Delivery_Pct]
        """
        try:
            # Clean symbol (remove .NS if present)
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '')

            delivery_records = []
            current_date = datetime.now()

            # Fetch last N trading days
            attempts = 0
            max_attempts = days * 2  # Account for weekends/holidays

            while len(delivery_records) < days and attempts < max_attempts:
                date_str = current_date.strftime('%d-%b-%Y')

                # Try to get from cache first
                cached_data = self._get_from_cache(current_date)

                if cached_data is not None:
                    # Filter for this symbol
                    symbol_data = cached_data[cached_data['SYMBOL'] == clean_symbol]
                    if not symbol_data.empty:
                        delivery_records.append(symbol_data.iloc[0])
                else:
                    # Fetch from NSE
                    day_data = self._fetch_delivery_for_date(current_date)
                    if day_data is not None:
                        # Cache it
                        self._save_to_cache(current_date, day_data)

                        # Filter for this symbol
                        symbol_data = day_data[day_data['SYMBOL'] == clean_symbol]
                        if not symbol_data.empty:
                            delivery_records.append(symbol_data.iloc[0])

                current_date -= timedelta(days=1)
                attempts += 1

            if not delivery_records:
                logger.warning(f"No delivery data found for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(delivery_records)

            # FIXED: Flexible column mapping (NSE uses different names in different formats)
            # Try multiple column name variations
            date_col = next((c for c in df.columns if c in ['DATE', 'Date', 'TRD_DATE']), 'DATE')
            symbol_col = next((c for c in df.columns if c in ['SYMBOL', 'Symbol', 'SYM']), 'SYMBOL')
            qty_col = next((c for c in df.columns if c in ['QTY_FOR_TRDNG', 'QTY_TRD', 'QUANTITY']), None)
            deliv_col = next((c for c in df.columns if c in ['DELIV_QTY', 'DELIV_QUANTITY', 'DEL_QTY']), None)

            if not qty_col or not deliv_col:
                logger.warning(f"Missing required columns. Available: {df.columns.tolist()}")
                return None

            # Calculate delivery percentage
            df['Date'] = pd.to_datetime(df[date_col], format='%d-%b-%Y', errors='coerce')
            df['Symbol'] = df[symbol_col]
            df['Delivered_Qty'] = pd.to_numeric(df[qty_col], errors='coerce')
            df['Traded_Qty'] = pd.to_numeric(df[deliv_col], errors='coerce')
            df['Delivery_Pct'] = (df['Traded_Qty'] / df['Delivered_Qty'] * 100).round(2)

            # Select and sort
            result = df[['Date', 'Symbol', 'Delivered_Qty', 'Traded_Qty', 'Delivery_Pct']]
            result = result.sort_values('Date', ascending=False).reset_index(drop=True)

            return result

        except Exception as e:
            logger.error(f"Error fetching delivery data for {symbol}: {e}")
            return None

    def _fetch_delivery_for_date(self, date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch delivery data from NSE for a specific date

        FIXED: Updated for NSE's new API requirements (Dec 2025)
        - Uses direct Bhavcopy download URL
        - Adds proper session handling
        - Implements retry logic

        Returns:
            DataFrame with all stocks delivery data for that date
        """
        try:
            # Skip weekends
            if date.weekday() >= 5:
                return None

            date_str = date.strftime('%d-%b-%Y')

            # FIXED: Use direct download URLs (NSE changed API structure)
            # Format: https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O
            # But for delivery, we use the archives API with proper date format

            # Alternative: Try direct Bhavcopy CSV download
            date_url_format = date.strftime('%d%m%Y')  # DDMMYYYY format

            # Try multiple URL patterns (NSE keeps changing)
            urls_to_try = [
                # Pattern 1: New API format
                f"https://www.nseindia.com/api/reports?archives=%5B%7B%22name%22%3A%22CM%20-%20Delivery%20position(csv)%22%2C%22type%22%3A%22archives%22%2C%22category%22%3A%22capital-market%22%2C%22section%22%3A%22equities%22%7D%5D&date={date_str}&type=equities&mode=single",
                # Pattern 2: Direct CSV download
                f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{date_url_format}.csv"
            ]

            for url_idx, url in enumerate(urls_to_try):
                try:
                    # Clear session cookies for fresh attempt
                    if url_idx > 0:
                        self.session = requests.Session()
                        self.session.headers.update(self.headers)

                    # Visit homepage first to get fresh cookies (important!)
                    self.session.get('https://www.nseindia.com', timeout=10)

                    # Small delay for cookie setting
                    import time
                    time.sleep(0.5)

                    # Fetch delivery data
                    response = self.session.get(url, timeout=15, allow_redirects=True)

                    if response.status_code == 200:
                        csv_data = response.text

                        # Check if we got valid CSV data
                        if csv_data and len(csv_data) > 100 and ('SYMBOL' in csv_data or 'Symbol' in csv_data):
                            try:
                                # Read CSV
                                df = pd.read_csv(io.StringIO(csv_data))

                                # Validate it has required columns
                                if len(df) > 0 and any(col in df.columns for col in ['SYMBOL', 'Symbol']):
                                    # Add date column
                                    df['DATE'] = date_str
                                    logger.debug(f"Successfully fetched delivery data for {date_str} using URL pattern {url_idx + 1}")
                                    return df

                            except pd.errors.ParserError:
                                logger.debug(f"CSV parse error for URL pattern {url_idx + 1}")
                                continue

                except requests.RequestException as e:
                    logger.debug(f"Request failed for URL pattern {url_idx + 1}: {e}")
                    continue

            # All URLs failed
            logger.debug(f"All delivery data fetch attempts failed for {date.strftime('%Y-%m-%d')}")
            return None

        except Exception as e:
            logger.debug(f"Could not fetch delivery data for {date.strftime('%Y-%m-%d')}: {e}")
            return None

    def _get_from_cache(self, date: datetime) -> Optional[pd.DataFrame]:
        """Get delivery data from cache"""
        try:
            cache_file = os.path.join(
                self.cache_dir,
                f"delivery_{date.strftime('%Y%m%d')}.pkl"
            )

            if os.path.exists(cache_file):
                # Check if cache is less than 1 day old
                file_age = datetime.now() - datetime.fromtimestamp(
                    os.path.getmtime(cache_file)
                )

                if file_age.days < 1:
                    return pd.read_pickle(cache_file)

            return None

        except Exception as e:
            logger.debug(f"Cache read error: {e}")
            return None

    def _save_to_cache(self, date: datetime, data: pd.DataFrame):
        """Save delivery data to cache"""
        try:
            cache_file = os.path.join(
                self.cache_dir,
                f"delivery_{date.strftime('%Y%m%d')}.pkl"
            )

            data.to_pickle(cache_file)

        except Exception as e:
            logger.debug(f"Cache write error: {e}")

    def get_avg_delivery_pct(self, symbol: str, days: int = 5) -> Optional[float]:
        """
        Get average delivery percentage for last N days

        Args:
            symbol: Stock symbol
            days: Number of days (default: 5)

        Returns:
            Average delivery % or None
        """
        try:
            delivery_data = self.get_delivery_data(symbol, days)

            if delivery_data is not None and len(delivery_data) > 0:
                return delivery_data['Delivery_Pct'].mean()

            return None

        except Exception as e:
            logger.error(f"Error calculating avg delivery %: {e}")
            return None

    def add_delivery_to_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Add delivery percentage column to existing price DataFrame

        Args:
            df: DataFrame with Date and OHLCV data
            symbol: Stock symbol

        Returns:
            DataFrame with added 'delivery_pct' column
        """
        try:
            # Get delivery data
            delivery_data = self.get_delivery_data(symbol, days=len(df))

            if delivery_data is None:
                # Add empty column if no data
                df['delivery_pct'] = None
                return df

            # Merge on date
            df_copy = df.copy()
            df_copy['Date'] = pd.to_datetime(df_copy.index)

            merged = df_copy.merge(
                delivery_data[['Date', 'Delivery_Pct']],
                on='Date',
                how='left'
            )

            merged['delivery_pct'] = merged['Delivery_Pct']
            merged = merged.drop('Delivery_Pct', axis=1)
            merged = merged.set_index('Date')

            return merged

        except Exception as e:
            logger.error(f"Error adding delivery data: {e}")
            df['delivery_pct'] = None
            return df


# Singleton instance
_delivery_fetcher = None


def get_delivery_fetcher() -> NSEDeliveryDataFetcher:
    """Get singleton delivery data fetcher"""
    global _delivery_fetcher

    if _delivery_fetcher is None:
        _delivery_fetcher = NSEDeliveryDataFetcher()

    return _delivery_fetcher
