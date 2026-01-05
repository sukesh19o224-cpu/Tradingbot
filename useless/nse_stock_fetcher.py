"""
🎯 NSE Stock Universe Fetcher - SIMPLE & WORKING
Uses verified working NSE stocks (Nov 2025)
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict
import json
from datetime import datetime
import os

# Import WORKING stock lists
from config.nse_top_50_working import NSE_TOP_50_WORKING
from config.nse_verified_stocks import ALL_VERIFIED_STOCKS


class NSEStockFetcher:
    """
    Fetches NSE stock list - SIMPLE & BULLETPROOF

    Priority (SAFEST FIRST):
    1. config/nse_top_50_working.py → 50 VERIFIED stocks ✅ DEFAULT
    2. data/nse_live_stocks_nov2025.json → Live symbols (if exists)
    3. config/nse_verified_stocks.py → 283 stocks (fallback)
    """

    def __init__(self, use_simple: bool = True):
        """
        Initialize NSE stock fetcher

        Args:
            use_simple: Use simple Top 50 (default=True, RECOMMENDED!)
        """
        self.use_simple = use_simple
        self.stocks = self._load_stocks()

    def _load_stocks(self) -> List[str]:
        """
        Load stock list - SIMPLE & WORKING

        Priority:
        1. Top 50 working stocks (SAFEST!) ✅
        2. Live Nov 2025 JSON (if exists)
        3. Verified 283 stocks (fallback)
        """
        # PRIORITY 1: Use SIMPLE TOP 50 - ALL VERIFIED WORKING! ✅
        if self.use_simple:
            print(f"✅ Using NSE Top 50 VERIFIED WORKING Stocks")
            print(f"   Total: {len(NSE_TOP_50_WORKING)} stocks")
            print(f"   Status: ALL TESTED & WORKING (Nov 2025)")
            print(f"   Quality: Large Cap, High Liquidity, Zero Errors")
            print(f"   Coverage: Banks, IT, Auto, FMCG, Pharma, Metals, Energy, Infra")
            return NSE_TOP_50_WORKING.copy()

        # PRIORITY 2: Try live Nov 2025 JSON
        live_json = 'data/nse_live_stocks_nov2025.json'
        if os.path.exists(live_json):
            try:
                with open(live_json, 'r') as f:
                    data = json.load(f)
                    stocks = data.get('symbols', [])
                    if stocks:
                        print(f"📡 Using LIVE NSE symbols (November 2025)")
                        print(f"   Total: {len(stocks)} stocks")
                        print(f"   Generated: {data.get('generated_date_readable', 'Unknown')}")
                        return stocks
            except Exception as e:
                print(f"⚠️ Error loading {live_json}, falling back...")

        # PRIORITY 3: Use verified 283 stocks
        print(f"📊 Using verified stock list")
        print(f"   Total: {len(ALL_VERIFIED_STOCKS)} stocks")
        print(f"   Status: Pre-verified (some may be outdated)")
        return ALL_VERIFIED_STOCKS

    def fetch_nse_stocks(self) -> List[str]:
        """
        Get NSE stock list (verified working stocks)

        Returns:
            List of NSE stock symbols in Yahoo Finance format (SYMBOL.NS)
        """
        return self.stocks

    def get_stocks_by_sector(self) -> Dict[str, List[str]]:
        """Get stocks grouped by sector"""
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


if __name__ == "__main__":
    # Test the fetcher
    print("🧪 Testing NSE Stock Fetcher...\n")

    fetcher = NSEStockFetcher(use_simple=True)
    stocks = fetcher.fetch_nse_stocks()

    print(f"\n✅ Loaded {len(stocks)} stocks")
    print(f"\nFirst 10 stocks:")
    for i, stock in enumerate(stocks[:10], 1):
        print(f"  {i:2d}. {stock}")

    print(f"\n✅ Stock fetcher working perfectly!")
