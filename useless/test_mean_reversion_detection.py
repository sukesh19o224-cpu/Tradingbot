"""
Test Mean Reversion Signal Detection
Check why mean reversion signals are not being generated
"""

from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.data.data_fetcher import DataFetcher
import pandas as pd

def test_mr_detection():
    """Test mean reversion detection on stocks that should qualify"""

    analyzer = MultiTimeframeAnalyzer()
    fetcher = DataFetcher()

    # Test stocks that might have mean reversion setups
    test_symbols = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS',
        'KOTAKBANK.NS',
        'WIPRO.NS',
        'SBIN.NS'
    ]

    print("=" * 80)
    print("🧪 TESTING MEAN REVERSION SIGNAL DETECTION")
    print("=" * 80)
    print("\nChecking if any stocks currently qualify for mean reversion...")
    print("Expected: RSI 28-50, Price > 50-MA, Price <= 20-MA * 1.02\n")

    market_regime = 'SIDEWAYS'  # Most lenient for mean reversion

    mr_count = 0
    momentum_count = 0
    breakout_count = 0

    for symbol in test_symbols:
        print(f"\n📊 Analyzing {symbol}...")

        # Fetch data
        df = fetcher.get_stock_data(symbol, period='6mo', interval='1d')

        if df is None or len(df) < 100:
            print(f"   ❌ Insufficient data")
            continue

        # Analyze
        result = analyzer.analyze_stock(symbol, df, market_regime=market_regime)

        if result:
            signal_type = result.get('signal_type', 'UNKNOWN')
            score = result.get('signal_score', 0)

            # Get raw indicators
            rsi = result.get('rsi', 0)
            price = result.get('current_price', 0)
            ema_20 = result.get('ema_20', 0)
            ema_50 = result.get('ema_50', 0)
            adx = result.get('adx', 0)

            print(f"   Signal Type: {signal_type}")
            print(f"   Score: {score:.2f}/10")
            print(f"   RSI: {rsi:.1f}")
            print(f"   Price: ₹{price:.2f}")
            print(f"   EMA-20: ₹{ema_20:.2f}")
            print(f"   EMA-50: ₹{ema_50:.2f}")
            print(f"   ADX: {adx:.1f}")

            # Check mean reversion conditions
            if signal_type == 'MEAN_REVERSION':
                mr_count += 1
                mr_quality = result.get('mean_reversion_quality', {})
                mr_score = mr_quality.get('score', 0)
                print(f"   ✅ MEAN REVERSION DETECTED!")
                print(f"      Quality Score: {mr_score}/100")
            elif signal_type == 'MOMENTUM':
                momentum_count += 1
                # Check why it's momentum instead of mean reversion
                if 28 <= rsi <= 50:
                    print(f"   ⚠️ RSI in MR range but classified as MOMENTUM")
                    if ema_50 > 0:
                        if price > ema_50:
                            print(f"      Above 50-MA ✓")
                            if ema_20 > 0:
                                if price <= ema_20 * 1.02:
                                    print(f"      Price <= 20-MA * 1.02 ✓")
                                    print(f"      🔥 SHOULD BE MEAN REVERSION but classified as MOMENTUM!")
                                else:
                                    print(f"      Price > 20-MA * 1.02 (₹{price:.2f} > ₹{ema_20 * 1.02:.2f})")
                            else:
                                print(f"      No 20-MA data")
                        else:
                            print(f"      Below 50-MA (₹{price:.2f} < ₹{ema_50:.2f})")
                    else:
                        print(f"      No 50-MA data")
            elif signal_type == 'BREAKOUT':
                breakout_count += 1
        else:
            print(f"   ❌ Analysis failed")

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Mean Reversion: {mr_count}")
    print(f"Momentum: {momentum_count}")
    print(f"Breakout: {breakout_count}")
    print()

    if mr_count == 0:
        print("⚠️ NO MEAN REVERSION SIGNALS DETECTED!")
        print("Possible reasons:")
        print("1. Current market conditions don't have stocks in pullback (RSI 28-50)")
        print("2. Stocks in pullback are below 50-MA (not in uptrend)")
        print("3. Classification logic has a bug")
        print("\nRecommendation: Check live market data or expand test universe")


if __name__ == "__main__":
    test_mr_detection()
