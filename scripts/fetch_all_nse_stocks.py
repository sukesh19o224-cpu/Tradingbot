"""
📥 Fetch Complete NSE Stock List from Yahoo Finance
Downloads and validates all NSE stocks trading on Yahoo Finance
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_nse_stock_list_from_yfinance():
    """
    Get comprehensive NSE stock list from Yahoo Finance

    Yahoo Finance uses .NS suffix for NSE stocks
    We'll scan through known NSE stock symbols
    """
    print("📥 Fetching NSE stock list from Yahoo Finance...")
    print("⏰ This may take 5-10 minutes...\n")

    # Get list from NSE India website (public data)
    # NSE provides equity list in CSV format
    nse_equity_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

    try:
        print("Step 1: Downloading NSE equity list from NSE India...")
        df = pd.read_csv(nse_equity_url)
        print(f"✅ Downloaded {len(df)} stocks from NSE\n")

        # Extract symbols and add .NS suffix for Yahoo Finance
        symbols = []
        for _, row in df.iterrows():
            symbol = str(row['SYMBOL']).strip()
            if symbol and symbol != 'SYMBOL':  # Skip header row if any
                symbols.append(f"{symbol}.NS")

        print(f"📊 Total symbols extracted: {len(symbols)}\n")

        # Step 2: Validate stocks with Yahoo Finance (check if they have data)
        print("Step 2: Validating stocks with Yahoo Finance...")
        print("(Testing if each stock has tradeable data)\n")

        valid_stocks = validate_stocks_parallel(symbols, max_workers=50)

        print(f"\n✅ VALIDATION COMPLETE!")
        print(f"   Total symbols: {len(symbols)}")
        print(f"   Valid stocks: {len(valid_stocks)}")
        print(f"   Invalid/Delisted: {len(symbols) - len(valid_stocks)}")

        return valid_stocks

    except Exception as e:
        print(f"❌ Error downloading from NSE: {e}")
        print("\n⚠️ Falling back to manual list of common NSE stocks...")
        return get_fallback_nse_list()

def validate_stocks_parallel(symbols, max_workers=50):
    """Validate stocks in parallel for speed"""
    valid_stocks = []
    total = len(symbols)
    completed = 0

    print(f"Testing {total} stocks with {max_workers} parallel threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {executor.submit(validate_stock, symbol): symbol for symbol in symbols}

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            completed += 1

            try:
                is_valid = future.result()
                if is_valid:
                    valid_stocks.append(symbol)

                # Progress indicator
                if completed % 100 == 0:
                    print(f"   Progress: {completed}/{total} ({len(valid_stocks)} valid so far)")

            except Exception as e:
                pass  # Skip invalid stocks

    return valid_stocks

def validate_stock(symbol):
    """Check if stock has valid data on Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        # Try to get last 5 days of data
        hist = ticker.history(period='5d')

        # Valid if has data in last 5 days
        if len(hist) > 0:
            return True
        return False

    except:
        return False

def get_fallback_nse_list():
    """
    Fallback list if NSE website is down
    Returns ~500 most liquid NSE stocks
    """
    print("Using fallback list of most liquid NSE stocks...\n")

    # NIFTY indices provide good coverage
    nifty_indices = [
        '^NSEI',      # NIFTY 50
        '^NSEBANK',   # BANK NIFTY
    ]

    # Get NIFTY 50 constituents
    nifty50 = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
        'ICICIBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS',
        'AXISBANK.NS', 'LT.NS', 'BAJFINANCE.NS', 'ASIANPAINT.NS', 'MARUTI.NS',
        'HCLTECH.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS',
        'WIPRO.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BAJAJFINSV.NS',
        'M&M.NS', 'TECHM.NS', 'TATASTEEL.NS', 'ADANIENT.NS', 'ADANIPORTS.NS',
        'COALINDIA.NS', 'JSWSTEEL.NS', 'HINDALCO.NS', 'INDUSINDBK.NS', 'TATAMOTORS.NS',
        'DRREDDY.NS', 'EICHERMOT.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS', 'CIPLA.NS',
        'HEROMOTOCO.NS', 'BPCL.NS', 'BAJAJ-AUTO.NS', 'GRASIM.NS', 'BRITANNIA.NS',
        'TATACONSUM.NS', 'SBILIFE.NS', 'HDFCLIFE.NS', 'UPL.NS', 'LTIM.NS'
    ]

    # This would be expanded with more stocks
    # For now, return the verified list from config
    from config.nse_verified_stocks import ALL_VERIFIED_STOCKS
    return ALL_VERIFIED_STOCKS

def save_stock_list(stocks, filename='data/nse_all_stocks.json'):
    """Save validated stock list to JSON file"""
    data = {
        'last_updated': datetime.now().isoformat(),
        'total_stocks': len(stocks),
        'stocks': sorted(stocks),
        'source': 'NSE India + Yahoo Finance validation',
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n💾 Saved to: {filename}")

def main():
    """Main execution"""
    print("="*70)
    print("📥 NSE STOCK LIST FETCHER")
    print("="*70)
    print()

    # Fetch stocks
    stocks = get_nse_stock_list_from_yfinance()

    if not stocks:
        print("❌ No stocks fetched!")
        return

    # Save to file
    save_stock_list(stocks)

    # Display summary
    print("\n" + "="*70)
    print("✅ STOCK LIST READY!")
    print("="*70)
    print(f"Total valid NSE stocks: {len(stocks)}")
    print(f"\nFirst 10 stocks:")
    for stock in sorted(stocks)[:10]:
        print(f"  • {stock}")
    print(f"\n💡 Stock list saved to: data/nse_all_stocks.json")
    print("\n🎯 Your system will now scan ALL {len(stocks)} NSE stocks!")
    print("="*70)

if __name__ == "__main__":
    main()
