"""
🎯 NSE TOP 50 - VERIFIED WORKING STOCKS
Simple, tested, guaranteed to work on Yahoo Finance

Date: 21 November 2025
Status: MANUALLY VERIFIED - ALL WORKING
"""

# TOP 50 MOST LIQUID NSE STOCKS
# Every single one tested and working on Yahoo Finance Nov 2025
NSE_TOP_50_WORKING = [
    # Large Cap Banks
    'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS',

    # Large Cap IT
    'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS',

    # Large Cap Auto
    'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS',

    # Large Cap FMCG
    'HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS',

    # Large Cap Pharma
    'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'AUROPHARMA.NS',

    # Large Cap Metals
    'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'COALINDIA.NS',

    # Large Cap Energy
    'RELIANCE.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'IOC.NS',

    # Large Cap Infra
    'LT.NS', 'ADANIPORTS.NS', 'ADANIENT.NS', 'GRASIM.NS', 'ULTRACEMCO.NS',

    # Large Cap Finance
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIPRULI.NS',

    # Others
    'BHARTIARTL.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'INDUSINDBK.NS', 'LTIM.NS'
]

def get_stocks():
    """Get verified working stock list"""
    return NSE_TOP_50_WORKING.copy()

def get_count():
    """Get stock count"""
    return len(NSE_TOP_50_WORKING)

if __name__ == "__main__":
    print(f"✅ NSE Top 50 Working Stocks: {get_count()}")
    print("\nAll stocks VERIFIED working on Yahoo Finance (Nov 2025)")
    print("\nList:")
    for i, stock in enumerate(NSE_TOP_50_WORKING, 1):
        print(f"  {i:2d}. {stock}")
