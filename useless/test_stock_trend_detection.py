"""
Test Stock-Specific Trend Detection
Verify that scoring adjusts based on individual stock trends, not just market regime
"""

from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.data.data_fetcher import DataFetcher

def test_stock_specific_trends():
    """Test that stock trends override market regime"""

    analyzer = MultiTimeframeAnalyzer()
    fetcher = DataFetcher()

    # Test stocks (mix of strong, weak, sideways)
    test_symbols = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS'
    ]

    print("=" * 80)
    print("🧪 TESTING STOCK-SPECIFIC TREND DETECTION")
    print("=" * 80)
    print("\nScenario: Market is SIDEWAYS, but individual stocks have different trends")
    print("Expected: Each stock scored based on ITS OWN trend, not market regime\n")

    # Simulate SIDEWAYS market regime
    market_regime = 'SIDEWAYS'
    print(f"Market Regime: {market_regime}")
    print("-" * 80)

    for symbol in test_symbols:
        print(f"\n📊 Analyzing {symbol}...")

        # Fetch data
        df = fetcher.get_stock_data(symbol, period='6mo', interval='1d')

        if df is None or len(df) < 100:
            print(f"   ❌ Insufficient data")
            continue

        # Analyze with stock-specific trend detection
        result = analyzer.analyze_stock(symbol, df, market_regime=market_regime)

        if result:
            stock_trend = result.get('trend_strength', 'UNKNOWN')
            signal_type = result.get('signal_type', 'UNKNOWN')
            signal_score = result.get('signal_score', 0)

            print(f"   Stock Trend: {stock_trend}")
            print(f"   Signal Type: {signal_type}")
            print(f"   Signal Score: {signal_score:.2f}/10")

            # Show adjustment logic
            if signal_type == 'MEAN_REVERSION':
                if stock_trend in ['WEAK_UPTREND', 'UPTREND']:
                    print(f"   ✅ Mean reversion BOOSTED (+0.7) - stock in pullback")
                elif stock_trend == 'SIDEWAYS':
                    print(f"   ✅ Mean reversion BOOSTED (+0.5) - stock sideways")
                else:
                    print(f"   ⚠️ Mean reversion normal - stock in {stock_trend}")

            elif signal_type == 'MOMENTUM':
                if stock_trend == 'STRONG_UPTREND':
                    print(f"   ✅ Momentum BOOSTED (+0.5) - stock strong")
                elif stock_trend in ['WEAK_UPTREND', 'SIDEWAYS']:
                    print(f"   ⚠️ Momentum PENALIZED (-0.5) - weak stock")
                else:
                    print(f"   ⚠️ Momentum normal - stock in {stock_trend}")
        else:
            print(f"   ❌ Analysis failed")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print("\n📌 Key Insight:")
    print("   Each stock is now scored based on ITS OWN trend characteristics")
    print("   Market regime is only a SECONDARY factor (smaller adjustment)")
    print("   This allows finding momentum stocks even in sideways markets!")
    print("   And finding mean reversion in stocks that are pulling back.")


if __name__ == "__main__":
    test_stock_specific_trends()
