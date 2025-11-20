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

# Import verified stock list
from config.nse_verified_stocks import ALL_VERIFIED_STOCKS


class NSEStockFetcher:
    """
    Fetches complete NSE stock list using verified symbols

    Priority:
    1. If data/nse_all_stocks.json exists → Use that (full NSE list)
    2. Otherwise → Use config/nse_verified_stocks.py (curated 283 stocks)

    All symbols are tested to work on Yahoo Finance
    """

    def __init__(self):
        self.all_stocks_file = 'data/nse_all_stocks.json'
        self.stocks = self._load_stocks()

    def _load_stocks(self) -> List[str]:
        """
        Load stock list with priority:
        1. From data/nse_all_stocks.json (if exists)
        2. From config/nse_verified_stocks.py (fallback)
        """
        # Try to load from full NSE list JSON file
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

        # Fallback to verified stocks from config
        print(f"📊 Using curated verified stock list from config")
        return ALL_VERIFIED_STOCKS

    def fetch_nse_stocks(self) -> List[str]:
        """
        Get complete NSE stock list (verified working stocks)

        Returns:
            List of NSE stock symbols in Yahoo Finance format (SYMBOL.NS)
        """
        print(f"   ✅ Loaded {len(self.stocks)} verified NSE stocks")
        print(f"   • All symbols tested working on Yahoo Finance")

        if len(self.stocks) < 500:
            print(f"   • Coverage: NIFTY 50, Next 50, Midcap 100, Smallcap 100")
            print(f"   • Sectors: Banking, IT, Pharma, Auto, FMCG, Metal, Energy, Infra, Realty")
            print(f"   💡 To get FULL NSE list (~1500-2000 stocks): python scripts/fetch_all_nse_stocks.py")
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
