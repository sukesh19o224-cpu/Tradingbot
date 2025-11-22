"""
🧪 QUICK SYSTEM TEST
Tests the enhanced data fetcher + sequential scanner with 10 stocks
"""

import sys
from src.data.sequential_scanner import SequentialScanner

def main():
    print("="*70)
    print("🧪 QUICK SYSTEM TEST - 10 Stocks")
    print("="*70)

    # Create scanner
    scanner = SequentialScanner(api_delay=0.5)  # 0.5s for testing

    # Test with 10 large-cap stocks
    test_stocks = [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS',
        'INFY.NS',
        'ICICIBANK.NS',
        'SBIN.NS',
        'BHARTIARTL.NS',
        'ITC.NS',
        'LT.NS',
        'WIPRO.NS'
    ]

    print(f"\n📊 Testing with {len(test_stocks)} stocks")
    print(f"⏱️ Estimated time: {len(test_stocks) * 0.5 / 60:.1f} minutes")
    print()

    # Run scan
    result = scanner.scan_all_stocks(test_stocks)

    # Show results
    print("\n" + "="*70)
    print("📊 RESULTS:")
    print("="*70)
    print(f"✅ Data Success: {result['stats']['data_success']}/{result['stats']['total']}")
    print(f"🔥 Swing Signals: {result['stats']['swing_found']}")
    print(f"📈 Positional Signals: {result['stats']['positional_found']}")

    if result['swing_signals']:
        print("\n🔥 Swing Signals Found:")
        for sig in result['swing_signals']:
            print(f"   {sig['symbol']:15s} - Score: {sig['score']:.1f}, RSI: {sig['indicators']['rsi']:.1f}")

    if result['positional_signals']:
        print("\n📈 Positional Signals Found:")
        for sig in result['positional_signals']:
            print(f"   {sig['symbol']:15s} - Score: {sig['score']:.1f}, ADX: {sig['indicators']['adx']:.1f}")

    # Show qualified stocks
    if result['stats']['qualified_stocks']:
        print(f"\n⚡ Total Qualified: {len(result['stats']['qualified_stocks'])} stocks")

    print("\n" + "="*70)
    print("✅ TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
