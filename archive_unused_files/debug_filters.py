"""
🔍 DEBUG SCRIPT - Check Filter Values
Shows why stocks pass or fail filters
"""

from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer

def debug_stock(symbol):
    """Debug a single stock to see filter values"""
    print(f"\n{'='*70}")
    print(f"🔍 DEBUGGING: {symbol}")
    print(f"{'='*70}\n")

    # Fetch data
    print("📊 Fetching data...")
    fetcher = EnhancedDataFetcher(api_delay=0.3)
    data = fetcher.get_stock_data_dual(symbol)

    if not data['success']:
        print("❌ Failed to fetch data")
        return

    print(f"✅ Data fetched: {len(data['daily'])} daily candles")
    if data['intraday'] is not None:
        print(f"✅ Intraday data: {len(data['intraday'])} 15-min candles")

    # Analyze
    print("\n📈 Analyzing...")
    analyzer = MultiTimeframeAnalyzer()

    try:
        result = analyzer.analyze_stock(symbol, data['daily'], data['intraday'])

        if not result:
            print("❌ Analysis failed (returned None)")
            return
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Show key values
    print(f"\n🎯 KEY VALUES:")
    print(f"{'='*70}")

    indicators = result.get('indicators', {})
    print(f"\n📊 Indicators:")
    print(f"   RSI: {indicators.get('rsi', 0):.2f}")
    print(f"   ADX: {indicators.get('adx', 0):.2f}")
    print(f"   MACD: {indicators.get('macd', 0):.2f}")
    print(f"   Volume Ratio: {indicators.get('volume_ratio', 0):.2f}")

    print(f"\n📈 Analysis:")
    print(f"   Uptrend: {result.get('uptrend', False)}")
    print(f"   Signal Score: {result.get('signal_score', 0):.2f}/10")
    print(f"   Overall Quality: {result.get('overall_quality', 0):.2f}/10")
    print(f"   Trend: {result.get('trend_strength', 'N/A')}")
    print(f"   Signal Type: {result.get('signal_type', 'N/A')}")

    # Check filters
    print(f"\n🎯 FILTER CHECKS:")
    print(f"{'='*70}")

    rsi = indicators.get('rsi', 0)
    adx = indicators.get('adx', 0)
    uptrend = result.get('uptrend', False)
    score = result.get('signal_score', 0)

    # Swing filters
    print(f"\n🔥 SWING FILTERS:")
    print(f"   ✓ RSI 50-80: {rsi:.2f} → {'✅ PASS' if 50 <= rsi <= 80 else '❌ FAIL'}")
    print(f"   ✓ Uptrend: {uptrend} → {'✅ PASS' if uptrend else '❌ FAIL'}")
    print(f"   ✓ Score ≥6.0: {score:.2f} → {'✅ PASS' if score >= 6.0 else '❌ FAIL'}")

    swing_pass = (50 <= rsi <= 80) and uptrend and (score >= 6.0)
    print(f"\n   🎯 SWING RESULT: {'✅ PASS' if swing_pass else '❌ FAIL'}")

    # Positional filters
    print(f"\n📈 POSITIONAL FILTERS:")
    print(f"   ✓ ADX ≥20: {adx:.2f} → {'✅ PASS' if adx >= 20 else '❌ FAIL'}")
    print(f"   ✓ RSI <75: {rsi:.2f} → {'✅ PASS' if rsi < 75 else '❌ FAIL'}")
    print(f"   ✓ Uptrend: {uptrend} → {'✅ PASS' if uptrend else '❌ FAIL'}")
    print(f"   ✓ Score ≥6.0: {score:.2f} → {'✅ PASS' if score >= 6.0 else '❌ FAIL'}")

    positional_pass = (adx >= 20) and (rsi < 75) and uptrend and (score >= 6.0)
    print(f"\n   🎯 POSITIONAL RESULT: {'✅ PASS' if positional_pass else '❌ FAIL'}")

    print(f"\n{'='*70}")

if __name__ == "__main__":
    # Test a few stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']

    for symbol in test_stocks:
        try:
            debug_stock(symbol)
        except Exception as e:
            print(f"\n❌ Error debugging {symbol}: {e}")

        print("\n")
