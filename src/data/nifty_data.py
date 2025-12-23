"""
Nifty 50 Data Fetcher

For relative strength calculations (stock vs market)
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NiftyDataFetcher:
    """
    Fetch and cache Nifty 50 data for relative strength calculations
    """

    def __init__(self):
        self.nifty_symbol = "^NSEI"  # Nifty 50 index
        self.cache = {}
        self.cache_timestamp = None

    def get_nifty_data(self, days: int = 60) -> Optional[pd.DataFrame]:
        """
        Get Nifty 50 historical data

        Args:
            days: Number of days of history

        Returns:
            DataFrame with Nifty OHLCV data
        """
        try:
            # Check cache (refresh every hour)
            if (self.cache_timestamp and
                (datetime.now() - self.cache_timestamp).seconds < 3600 and
                'data' in self.cache):
                return self.cache['data']

            # Fetch from yfinance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)  # Extra buffer

            nifty = yf.Ticker(self.nifty_symbol)
            df = nifty.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning("No Nifty data fetched")
                return None

            # Cache it
            self.cache['data'] = df
            self.cache_timestamp = datetime.now()

            return df

        except Exception as e:
            logger.error(f"Error fetching Nifty data: {e}")
            return None

    def get_nifty_return(self, days: int = 20) -> Optional[float]:
        """
        Get Nifty return over last N days

        Args:
            days: Number of days

        Returns:
            Return percentage or None
        """
        try:
            nifty_data = self.get_nifty_data(days + 10)

            if nifty_data is None or len(nifty_data) < days:
                return None

            start_price = nifty_data['Close'].iloc[-days]
            end_price = nifty_data['Close'].iloc[-1]

            return ((end_price - start_price) / start_price) * 100

        except Exception as e:
            logger.error(f"Error calculating Nifty return: {e}")
            return None


# Singleton instance
_nifty_fetcher = None


def get_nifty_fetcher() -> NiftyDataFetcher:
    """Get singleton Nifty data fetcher"""
    global _nifty_fetcher

    if _nifty_fetcher is None:
        _nifty_fetcher = NiftyDataFetcher()

    return _nifty_fetcher
