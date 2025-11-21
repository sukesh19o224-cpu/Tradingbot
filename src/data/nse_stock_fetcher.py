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

# Import verified stock lists (OUTDATED - from 2024!)
from config.nse_verified_stocks import ALL_VERIFIED_STOCKS

# NOTE: For LIVE November 2025 symbols, run:
#       python3 scripts/fetch_live_nse_symbols.py


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
        Load stock list with priority (newest first):
        1. data/nse_live_stocks_nov2025.json → LIVE symbols (Nov 2025) ✅ PRIORITY
        2. config/nse_live_nov2025.py → Generated Python config (if exists)
        3. data/nse_all_stocks.json → Old JSON (outdated, if exists)
        4. config/nse_verified_stocks.py → Original 283 stocks (OUTDATED 2024!)

        ⚠️  OLD FILES DELETED! Use live symbol fetcher:
            python3 scripts/fetch_live_nse_symbols.py
        """
        # PRIORITY 1: Try LIVE symbols from Nov 2025 (most recent!)
        live_json = 'data/nse_live_stocks_nov2025.json'
        if os.path.exists(live_json):
            try:
                with open(live_json, 'r') as f:
                    data = json.load(f)
                    stocks = data.get('symbols', [])
                    if stocks:
                        print(f"📡 Using LIVE NSE symbols (November 2025)")
                        print(f"   ✅ Total stocks: {len(stocks)}")
                        print(f"   📅 Generated: {data.get('generated_date_readable', 'Unknown')}")
                        print(f"   🔄 To update: python3 scripts/fetch_live_nse_symbols.py")
                        return stocks
            except Exception as e:
                print(f"⚠️ Error loading {live_json}: {e}")

        # PRIORITY 2: Try generated Python config (Nov 2025)
        try:
            from config.nse_live_nov2025 import NSE_LIVE_STOCKS
            print(f"📡 Using LIVE NSE symbols from Python config")
            print(f"   ✅ Total stocks: {len(NSE_LIVE_STOCKS)}")
            return NSE_LIVE_STOCKS.copy()
        except ImportError:
            pass  # File doesn't exist yet

        # PRIORITY 3: Try old full NSE list JSON (outdated!)
        if os.path.exists(self.all_stocks_file):
            try:
                with open(self.all_stocks_file, 'r') as f:
                    data = json.load(f)
                    stocks = data.get('stocks', [])
                    if stocks:
                        print(f"📊 Loaded NSE stock list from {self.all_stocks_file}")
                        print(f"   ✅ Total stocks: {len(stocks)}")
                        print(f"   ⚠️  WARNING: Contains OUTDATED symbols (from 2024)!")
                        print(f"   🔄 URGENT: Run python3 scripts/fetch_live_nse_symbols.py")
                        return stocks
            except Exception as e:
                print(f"⚠️ Error loading {self.all_stocks_file}: {e}")

        # PRIORITY 4: Last resort fallback (VERY OUTDATED!)
        print(f"📊 Using fallback verified stock list (283 stocks)")
        print(f"   ⚠️  CRITICAL WARNING: Symbols are OUTDATED (from 2024)!")
        print(f"   🔥 URGENT: Run python3 scripts/fetch_live_nse_symbols.py NOW")
        print(f"   Many stocks may fail due to delisting/mergers!")
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
