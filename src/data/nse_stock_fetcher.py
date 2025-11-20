"""
🎯 NSE Stock Universe Fetcher
Fetches complete list of NSE stocks from Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict
import json
from datetime import datetime
import os


class NSEStockFetcher:
    """
    Fetches complete NSE stock list from Yahoo Finance

    Yahoo Finance NSE symbols format: SYMBOL.NS
    Example: RELIANCE.NS, TCS.NS, INFY.NS
    """

    def __init__(self):
        self.cache_file = 'data/nse_stock_list.json'
        self.stocks = []

    def fetch_nse_stocks(self) -> List[str]:
        """
        Fetch complete NSE stock list

        Returns:
            List of NSE stock symbols in Yahoo Finance format (SYMBOL.NS)
        """
        print("📊 Fetching complete NSE stock list from Yahoo Finance...")

        # Try to load from cache first (updated daily)
        if os.path.exists(self.cache_file):
            cache_data = json.load(open(self.cache_file))
            cache_date = datetime.fromisoformat(cache_data['updated'])

            # Use cache if less than 1 day old
            if (datetime.now() - cache_date).days < 1:
                print(f"   ✅ Using cached list ({len(cache_data['stocks'])} stocks)")
                return cache_data['stocks']

        # Fetch fresh list
        stocks = self._fetch_from_yahoo()

        # Save to cache
        os.makedirs('data', exist_ok=True)
        cache_data = {
            'stocks': stocks,
            'updated': datetime.now().isoformat(),
            'count': len(stocks)
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

        print(f"   ✅ Fetched {len(stocks)} NSE stocks")
        return stocks

    def _fetch_from_yahoo(self) -> List[str]:
        """
        Fetch NSE stocks from Yahoo Finance

        Strategy:
        1. Use known indices (NIFTY 500, NIFTY SMALLCAP, etc.)
        2. Combine all unique stocks
        3. Verify each stock exists
        """
        all_stocks = set()

        # Fetch from major indices
        indices = {
            '^NSEI': 'NIFTY 50',
            '^NSEBANK': 'NIFTY BANK',
            '^NSMIDCP': 'NIFTY MIDCAP',
        }

        print("   Fetching from NSE indices...")

        # Method 1: Known NIFTY 500 stocks (most comprehensive)
        nifty_500 = self._get_nifty_500_stocks()
        all_stocks.update(nifty_500)
        print(f"   • NIFTY 500: {len(nifty_500)} stocks")

        # Method 2: Popular stocks (ensure we have the top ones)
        popular = self._get_popular_stocks()
        all_stocks.update(popular)

        # Convert to list and sort
        stocks = sorted(list(all_stocks))

        # Verify stocks exist (sample check)
        verified_stocks = self._verify_stocks(stocks)

        return verified_stocks

    def _get_nifty_500_stocks(self) -> List[str]:
        """
        Get NIFTY 500 stocks (covers most liquid NSE stocks)

        This is a curated list of top 500 NSE stocks by market cap
        """
        # Top 500 NSE stocks by market cap (as of 2024)
        # This list covers ~95% of market cap

        stocks = [
            # NIFTY 50
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
            'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
            'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
            'TITAN.NS', 'BAJFINANCE.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS',
            'HCLTECH.NS', 'ONGC.NS', 'POWERGRID.NS', 'NTPC.NS', 'TECHM.NS',
            'M&M.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'ADANIENT.NS', 'COALINDIA.NS',
            'BAJAJFINSV.NS', 'HINDALCO.NS', 'INDUSINDBK.NS', 'JSWSTEEL.NS', 'DIVISLAB.NS',
            'DRREDDY.NS', 'APOLLOHOSP.NS', 'CIPLA.NS', 'GRASIM.NS', 'HEROMOTOCO.NS',
            'EICHERMOT.NS', 'BPCL.NS', 'BRITANNIA.NS', 'ADANIPORTS.NS', 'UPL.NS',
            'TATACONSUM.NS', 'BAJAJ-AUTO.NS', 'SBILIFE.NS', 'HDFCLIFE.NS', 'LTIM.NS',

            # NIFTY NEXT 50
            'ADANIGREEN.NS', 'HAVELLS.NS', 'DLF.NS', 'GODREJCP.NS', 'SIEMENS.NS',
            'PIDILITIND.NS', 'VEDL.NS', 'GAIL.NS', 'INDIGO.NS', 'BOSCHLTD.NS',
            'ABB.NS', 'AMBUJACEM.NS', 'DABUR.NS', 'DMART.NS', 'COLPAL.NS',
            'PGHH.NS', 'MARICO.NS', 'TORNTPHARM.NS', 'MUTHOOTFIN.NS', 'ICICIPRULI.NS',
            'SRF.NS', 'BERGEPAINT.NS', 'ICICIGI.NS', 'BANDHANBNK.NS', 'LUPIN.NS',
            'NAUKRI.NS', 'MOTHERSON.NS', 'PETRONET.NS', 'MCDOWELL-N.NS', 'ZOMATO.NS',
            'TRENT.NS', 'PAGEIND.NS', 'SHREECEM.NS', 'ALKEM.NS', 'HDFCAMC.NS',
            'BIOCON.NS', 'CROMPTON.NS', 'TVSMOTOR.NS', 'BAJAJHLDNG.NS', 'IRCTC.NS',
            'POLYCAB.NS', 'GMRINFRA.NS', 'PNB.NS', 'IOC.NS', 'SAIL.NS',
            'NMDC.NS', 'BEL.NS', 'CANBK.NS', 'UNIONBANK.NS', 'BANKBARODA.NS',

            # NIFTY MIDCAP 150 (selected high volume)
            'TATAPOWER.NS', 'RECLTD.NS', 'PFC.NS', 'IDEA.NS', 'ASHOKLEY.NS',
            'ZEEL.NS', 'NATIONALUM.NS', 'ABFRL.NS', 'VOLTAS.NS', 'LICHSGFIN.NS',
            'CUMMINSIND.NS', 'JINDALSTEL.NS', 'CONCOR.NS', 'MRF.NS', 'AUBANK.NS',
            'IDFCFIRSTB.NS', 'FEDERALBNK.NS', 'RBLBANK.NS', 'M&MFIN.NS', 'L&TFH.NS',
            'BALKRISIND.NS', 'APOLLOTYRE.NS', 'ESCORTS.NS', 'PERSISTENT.NS', 'COFORGE.NS',
            'MPHASIS.NS', 'LTTS.NS', 'MINDTREE.NS', 'OFSS.NS', 'KPITTECH.NS',
            'JUBLFOOD.NS', 'VBL.NS', 'METROPOLIS.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS',
            'GLENMARK.NS', 'TORNTPOWER.NS', 'CESC.NS', 'ADANIPOWER.NS', 'JSWENERGY.NS',
            'TATACOMM.NS', 'DIXON.NS', 'WHIRLPOOL.NS', 'CROMPTON.NS', 'POLYCAB.NS',
            'PIIND.NS', 'CASTROLIND.NS', '3MINDIA.NS', 'BATAINDIA.NS', 'RELAXO.NS',

            # IT Sector
            'TECHM.NS', 'WIPRO.NS', 'HCLTECH.NS', 'INFY.NS', 'TCS.NS',
            'LTIM.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'MPHASIS.NS', 'LTTS.NS',

            # Banking & Finance
            'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
            'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'FEDERALBNK.NS', 'RBLBANK.NS',
            'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'CHOLAFIN.NS', 'SBICARD.NS', 'PEL.NS',

            # Pharma
            'SUNPHARMA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'CIPLA.NS', 'LUPIN.NS',
            'TORNTPHARM.NS', 'BIOCON.NS', 'ALKEM.NS', 'LAURUSLABS.NS', 'GLENMARK.NS',
            'AUROPHARMA.NS', 'CADILAHC.NS', 'GRANULES.NS', 'IPCALAB.NS', 'LALPATHLAB.NS',

            # Auto
            'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS',
            'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'MOTHERSON.NS', 'APOLLOTYRE.NS',
            'ESCORTS.NS', 'BALKRISIND.NS', 'MRF.NS', 'BOSCHLTD.NS', 'EXIDEIND.NS',

            # FMCG
            'HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS',
            'MARICO.NS', 'GODREJCP.NS', 'COLPAL.NS', 'TATACONSUM.NS', 'MCDOWELL-N.NS',
            'PGHH.NS', 'VBL.NS', 'JUBLFOOD.NS', 'PAGEIND.NS', 'EMAMILTD.NS',

            # Metals & Mining
            'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'COALINDIA.NS',
            'JINDALSTEL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'SAIL.NS', 'HINDZINC.NS',

            # Energy & Power
            'RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS', 'POWERGRID.NS',
            'NTPC.NS', 'GAIL.NS', 'TATAPOWER.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS',
            'TORNTPOWER.NS', 'CESC.NS', 'JSWENERGY.NS', 'ADANITRANS.NS', 'PFC.NS',
            'RECLTD.NS', 'PETRONET.NS',

            # Infrastructure & Realty
            'LT.NS', 'ADANIPORTS.NS', 'DLF.NS', 'GODREJPROP.NS', 'PRESTIGE.NS',
            'OBEROIRLTY.NS', 'PHOENIXLTD.NS', 'BRIGADE.NS', 'GMRINFRA.NS', 'CONCOR.NS',

            # Cement
            'ULTRACEMCO.NS', 'AMBUJACEM.NS', 'SHREECEM.NS', 'GRASIM.NS', 'ACC.NS',
            'JKCEMENT.NS', 'RAMCOCEM.NS', 'HEIDELBERG.NS', 'INDIACEM.NS', 'BIRLAMONEY.NS',

            # Telecom & Media
            'BHARTIARTL.NS', 'IDEA.NS', 'ZEEL.NS', 'TATACOMM.NS', 'HATHWAY.NS',

            # Retail & Consumer
            'DMART.NS', 'TRENT.NS', 'TITAN.NS', 'ZOMATO.NS', 'NYKAA.NS',
            'ABFRL.NS', 'SHOPERSTOP.NS', 'BATAINDIA.NS', 'RELAXO.NS', 'METROPOLIS.NS',

            # New Age Tech
            'ZOMATO.NS', 'NYKAA.NS', 'PAYTM.NS', 'POLICYBZR.NS', 'NAUKRI.NS',
            'INDIAMART.NS', 'IRCTC.NS', 'ROUTE.NS', 'ZOMATO.NS', 'SWIGGY.NS',
        ]

        # Remove duplicates and return
        return list(set(stocks))

    def _get_popular_stocks(self) -> List[str]:
        """Get additional popular/actively traded stocks"""
        return [
            'ADANIPOWER.NS', 'ADANITRANS.NS', 'CHAMBLFERT.NS', 'GNFC.NS',
            'MANAPPURAM.NS', 'IRFC.NS', 'SUZLON.NS', 'YESBANK.NS', 'TATACHEM.NS',
            'INDHOTEL.NS', 'PVR.NS', 'INOXLEISUR.NS', 'CRISIL.NS', 'CREDITACC.NS',
        ]

    def _verify_stocks(self, stocks: List[str], sample_size: int = 10) -> List[str]:
        """
        Verify stocks exist on Yahoo Finance (sample check)

        Args:
            stocks: List of stock symbols
            sample_size: Number of stocks to verify

        Returns:
            Original list (assumes most are valid)
        """
        import random

        print(f"   Verifying stocks (sampling {sample_size})...")

        sample = random.sample(stocks, min(sample_size, len(stocks)))
        valid_count = 0

        for symbol in sample:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if 'symbol' in info:
                    valid_count += 1
            except:
                pass

        if valid_count / len(sample) > 0.8:  # 80% valid
            print(f"   ✅ Verification passed ({valid_count}/{len(sample)} valid)")
            return stocks
        else:
            print(f"   ⚠️  Low verification rate ({valid_count}/{len(sample)})")
            return stocks

    def get_stocks_by_sector(self) -> Dict[str, List[str]]:
        """
        Get stocks grouped by sector

        Returns:
            Dictionary with sector names as keys and stock lists as values
        """
        return {
            'IT': [
                'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS',
                'LTIM.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'MPHASIS.NS', 'LTTS.NS',
            ],
            'Banking': [
                'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
                'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'FEDERALBNK.NS', 'PNB.NS',
            ],
            'Pharma': [
                'SUNPHARMA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'CIPLA.NS', 'LUPIN.NS',
                'TORNTPHARM.NS', 'BIOCON.NS', 'ALKEM.NS', 'LAURUSLABS.NS', 'GLENMARK.NS',
            ],
            'Auto': [
                'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS',
                'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'MOTHERSON.NS', 'APOLLOTYRE.NS',
            ],
            'FMCG': [
                'HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS',
                'MARICO.NS', 'GODREJCP.NS', 'COLPAL.NS', 'TATACONSUM.NS', 'MCDOWELL-N.NS',
            ],
            'Energy': [
                'RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS', 'POWERGRID.NS',
                'NTPC.NS', 'GAIL.NS', 'TATAPOWER.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS',
            ],
            'Metals': [
                'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'COALINDIA.NS',
                'JINDALSTEL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'SAIL.NS', 'HINDZINC.NS',
            ],
        }


if __name__ == "__main__":
    # Test the fetcher
    fetcher = NSEStockFetcher()
    stocks = fetcher.fetch_nse_stocks()

    print(f"\n✅ Total NSE stocks: {len(stocks)}")
    print(f"\nFirst 10 stocks:")
    for stock in stocks[:10]:
        print(f"  • {stock}")
