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
    print("⏰ This may take 10-15 minutes (slower = safer for API)...\n")

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
        print("🛡️ Using 20 threads + retry logic to avoid API rate limits\n")

        valid_stocks = validate_stocks_parallel(symbols, max_workers=20)

        print(f"\n✅ VALIDATION COMPLETE!")
        print(f"   Total symbols: {len(symbols)}")
        print(f"   Valid stocks: {len(valid_stocks)}")
        print(f"   Invalid/Delisted: {len(symbols) - len(valid_stocks)}")

        return valid_stocks

    except Exception as e:
        print(f"❌ Error downloading from NSE: {e}")
        print("\n⚠️ Falling back to manual list of common NSE stocks...")
        return get_fallback_nse_list()

def validate_stocks_parallel(symbols, max_workers=20):
    """
    Validate stocks in parallel with rate limit protection

    Uses reduced thread count (20) and retry logic to avoid API bans
    """
    valid_stocks = []
    total = len(symbols)
    completed = 0

    print(f"Testing {total} stocks with {max_workers} parallel threads...")
    print(f"🛡️ Rate limit protection: 100ms delay + 3 retries per stock\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {executor.submit(validate_stock, symbol): symbol for symbol in symbols}

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            completed += 1

            try:
                is_valid = future.result()
                if is_valid:
                    valid_stocks.append(symbol)

                # Progress indicator (every 50 stocks)
                if completed % 50 == 0:
                    percent = (completed / total) * 100
                    print(f"   Progress: {completed}/{total} ({percent:.1f}%) - {len(valid_stocks)} valid stocks found")

            except Exception as e:
                pass  # Skip invalid stocks

    return valid_stocks

def validate_stock(symbol, max_retries=3):
    """
    Check if stock has valid data on Yahoo Finance

    Includes retry logic to handle API rate limits
    """
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            # Try to get last 5 days of data
            hist = ticker.history(period='5d')

            # Add small delay to avoid rate limiting
            time.sleep(0.1)  # 100ms delay between requests

            # Valid if has data in last 5 days
            if len(hist) > 0:
                return True
            return False

        except Exception as e:
            # If rate limited or network error, retry after delay
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                time.sleep(wait_time)
            else:
                return False  # Failed after all retries

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
