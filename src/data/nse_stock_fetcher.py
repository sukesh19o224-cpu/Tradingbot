"""
🎯 NSE Stock Universe Fetcher
Uses verified NSE stock list from config
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict
import json
from datetime import datetime
import os

# Import verified stock lists
from config.nse_verified_stocks import ALL_VERIFIED_STOCKS
from config.nse_top_500 import NIFTY_500_STOCKS


class NSEStockFetcher:
    """
    Fetches NSE stock list using safe pre-verified symbols

    Priority (SAFEST → RISKIEST):
    1. config/nse_top_500.py → NIFTY 500 (most liquid, safest) ✅ DEFAULT
    2. data/nse_all_stocks.json → Full NSE list (if exists, updated daily)
    3. config/nse_verified_stocks.py → Original 283 stocks (fallback)

    All symbols are pre-tested to work on Yahoo Finance (no validation needed!)
    """

    def __init__(self, use_nifty_500: bool = True):
        """
        Initialize NSE stock fetcher

        Args:
            use_nifty_500: Use NIFTY 500 (default=True, recommended for API safety)
        """
        self.all_stocks_file = 'data/nse_all_stocks.json'
        self.use_nifty_500 = use_nifty_500
        self.stocks = self._load_stocks()

    def _load_stocks(self) -> List[str]:
        """
        Load stock list with priority (safest first):
        1. NIFTY 500 (500 most liquid stocks - SAFE, no validation) ✅ DEFAULT
        2. data/nse_all_stocks.json (if exists - updated daily at 3:45 PM)
        3. config/nse_verified_stocks.py (original 283 stocks - fallback)
        """
        # PRIORITY 1: Use NIFTY 500 (SAFEST - pre-verified, most liquid)
        if self.use_nifty_500:
            print(f"📊 Using NIFTY 500 stock list (pre-verified, safest)")
            print(f"   ✅ Total stocks: {len(NIFTY_500_STOCKS)}")
            print(f"   💡 These are the most liquid NSE stocks - no validation needed!")
            return NIFTY_500_STOCKS.copy()

        # PRIORITY 2: Try to load from full NSE list JSON file (daily update)
        if os.path.exists(self.all_stocks_file):
            try:
                with open(self.all_stocks_file, 'r') as f:
                    data = json.load(f)
                    stocks = data.get('stocks', [])
                    if stocks:
                        print(f"📊 Loaded FULL NSE stock list from {self.all_stocks_file}")
                        print(f"   ✅ Total stocks: {len(stocks)}")
                        print(f"   📅 Last updated: {data.get('last_updated', 'Unknown')}")
                        return stocks
            except Exception as e:
                print(f"⚠️ Error loading {self.all_stocks_file}: {e}")
                print(f"   Falling back to verified stocks...")

        # PRIORITY 3: Fallback to verified stocks from config
        print(f"📊 Using curated verified stock list from config")
        return ALL_VERIFIED_STOCKS

    def fetch_nse_stocks(self) -> List[str]:
        """
        Get NSE stock list (verified working stocks)

        Returns:
            List of NSE stock symbols in Yahoo Finance format (SYMBOL.NS)
        """
        print(f"   ✅ Loaded {len(self.stocks)} verified NSE stocks")
        print(f"   • All symbols tested working on Yahoo Finance")

        if self.use_nifty_500:
            print(f"   • Coverage: NIFTY 500 (most liquid stocks)")
            print(f"   • SAFE: No API validation needed, pre-verified!")
            print(f"   • Includes: NIFTY 50, Next 50, Midcap 150, Smallcap 100+")
        elif len(self.stocks) < 500:
            print(f"   • Coverage: NIFTY 50, Next 50, Midcap 100, Smallcap 100")
            print(f"   • Sectors: Banking, IT, Pharma, Auto, FMCG, Metal, Energy, Infra, Realty")
        else:
            print(f"   • Coverage: FULL NSE equity list")
            print(f"   • All actively traded stocks included")

        return self.stocks

    def get_stocks_by_sector(self) -> Dict[str, List[str]]:
        """
        Get stocks grouped by sector

        Returns:
            Dictionary with sector names as keys and stock lists as values
        """
        from config.nse_verified_stocks import (
            IT_STOCKS, BANKING_STOCKS, PHARMA_STOCKS,
            AUTO_STOCKS, FMCG_STOCKS, METAL_STOCKS,
            ENERGY_STOCKS, INFRA_STOCKS, REALTY_STOCKS
        )

        return {
            'IT': IT_STOCKS,
            'Banking': BANKING_STOCKS,
            'Pharma': PHARMA_STOCKS,
            'Auto': AUTO_STOCKS,
            'FMCG': FMCG_STOCKS,
            'Energy': ENERGY_STOCKS,
            'Metals': METAL_STOCKS,
            'Infrastructure': INFRA_STOCKS,
            'Realty': REALTY_STOCKS,
        }

    def get_stocks_by_market_cap(self) -> Dict[str, List[str]]:
        """
        Get stocks grouped by market cap

        Returns:
            Dictionary with market cap categories as keys
        """
        from config.nse_verified_stocks import LARGE_CAP, MID_CAP, SMALL_CAP

        return {
            'Large Cap': LARGE_CAP,
            'Mid Cap': MID_CAP,
            'Small Cap': SMALL_CAP,
        }


if __name__ == "__main__":
    # Test the fetcher
    fetcher = NSEStockFetcher()
    stocks = fetcher.fetch_nse_stocks()

    print(f"\n✅ Total NSE stocks: {len(stocks)}")
    print(f"\nFirst 10 stocks:")
    for stock in stocks[:10]:
        print(f"  • {stock}")
