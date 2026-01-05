#!/usr/bin/env python3
"""
Complete test to find why mean reversion signals are not appearing
"""

import sys
sys.path.insert(0, '/media/sukesh-k/Storage/new Tr/TraDc')

from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.data.sequential_scanner import SequentialScanner
from config.nse_top_500_live import NSE_TOP_500

print("=" * 80)
print("🔍 COMPREHENSIVE MEAN REVERSION DETECTION TEST")
print("=" * 80)
print()

# Initialize analyzer
analyzer = MultiTimeframeAnalyzer()

# Test with a subset of stocks
test_stocks = NSE_TOP_500[:50]  # First 50 stocks

print(f"📊 Testing {len(test_stocks)} stocks...")
print()

mean_rev_found = []
momentum_found = []
failed_checks = {}

for i, symbol in enumerate(test_stocks, 1):
    try:
        # Fetch data
        from src.data.enhanced_data_fetcher import EnhancedDataFetcher
        fetcher = EnhancedDataFetcher()
        
        daily_df = fetcher.get_daily_data(symbol, days=90)
        if daily_df is None or len(daily_df) < 50:
            continue
            
        # Analyze
        result = analyzer.analyze_stock(symbol, daily_df, None)
        if not result:
            continue
            
        signal_type = result.get('signal_type', 'UNKNOWN')
        indicators = result.get('indicators', {})
        rsi = indicators.get('rsi', 0)
        adx = indicators.get('adx', 0)
        signal_score = result.get('signal_score', 0)
        uptrend = result.get('uptrend', False)
        
        mean_rev_quality = result.get('mean_reversion_quality', {})
        mean_rev_score = mean_rev_quality.get('score', 0)
        mean_rev_valid = mean_rev_quality.get('is_valid', False)
        
        # Track by signal type
        if signal_type == 'MEAN_REVERSION':
            mean_rev_found.append({
                'symbol': symbol,
                'rsi': rsi,
                'adx': adx,
                'signal_score': signal_score,
                'quality_score': mean_rev_score,
                'valid': mean_rev_valid,
                'uptrend': uptrend
            })
            print(f"✅ [{i:2d}] {symbol:20s} | MEAN_REVERSION | RSI:{rsi:.1f} ADX:{adx:.1f} Quality:{mean_rev_score}/100 Valid:{mean_rev_valid}")
        elif signal_type == 'MOMENTUM':
            momentum_found.append(symbol)
            if i <= 10:  # Show first 10
                print(f"   [{i:2d}] {symbol:20s} | MOMENTUM | RSI:{rsi:.1f} ADX:{adx:.1f}")
        
        # Check why mean reversion might fail
        if rsi < 55 and signal_type != 'MEAN_REVERSION':
            reason = []
            if adx < 18:
                reason.append(f"ADX too low ({adx:.1f} < 18)")
            if not uptrend:
                reason.append("Not in uptrend")
            if signal_score < 6.8:
                reason.append(f"Signal score low ({signal_score:.1f} < 6.8)")
            
            if reason:
                failed_checks[symbol] = {
                    'rsi': rsi,
                    'adx': adx,
                    'signal_score': signal_score,
                    'uptrend': uptrend,
                    'reasons': reason,
                    'classified_as': signal_type
                }
                
    except Exception as e:
        pass

print()
print("=" * 80)
print("📊 RESULTS SUMMARY")
print("=" * 80)
print()

print(f"✅ Mean Reversion Signals Found: {len(mean_rev_found)}")
print(f"📈 Momentum Signals Found: {len(momentum_found)}")
print(f"❌ Potential Mean Rev Failed Checks: {len(failed_checks)}")
print()

if mean_rev_found:
    print("🎯 MEAN REVERSION SIGNALS DETECTED:")
    print("-" * 80)
    for stock in mean_rev_found:
        print(f"  {stock['symbol']:20s} | RSI:{stock['rsi']:5.1f} ADX:{stock['adx']:5.1f} "
              f"Quality:{stock['quality_score']:3.0f}/100 {'✅' if stock['valid'] else '❌'} "
              f"Score:{stock['signal_score']:.1f}")
    print()
else:
    print("❌ NO MEAN REVERSION SIGNALS FOUND!")
    print()
    print("🔍 Analyzing why stocks with RSI < 55 were rejected:")
    print("-" * 80)
    
    if failed_checks:
        for symbol, data in list(failed_checks.items())[:10]:  # Show first 10
            print(f"\n  {symbol} (RSI:{data['rsi']:.1f}, Classified as {data['classified_as']}):")
            for reason in data['reasons']:
                print(f"    ❌ {reason}")
    else:
        print("  All stocks have RSI > 55 (strong momentum market)")

print()
print("=" * 80)
print("🔍 DIAGNOSIS")
print("=" * 80)
print()

if len(mean_rev_found) > 0:
    print("✅ MEAN REVERSION DETECTION IS WORKING!")
    print(f"   Found {len(mean_rev_found)} mean reversion signals in {len(test_stocks)} stocks")
    print()
elif len(failed_checks) > 0:
    # Analyze common failure reasons
    adx_fails = sum(1 for d in failed_checks.values() if any('ADX' in r for r in d['reasons']))
    uptrend_fails = sum(1 for d in failed_checks.values() if any('uptrend' in r for r in d['reasons']))
    score_fails = sum(1 for d in failed_checks.values() if any('score' in r for r in d['reasons']))
    
    print("⚠️ MEAN REVERSION STOCKS EXIST BUT FAILING FILTERS:")
    if adx_fails > 0:
        print(f"   ❌ ADX too low: {adx_fails} stocks (need ADX ≥ 18)")
    if uptrend_fails > 0:
        print(f"   ❌ Not in uptrend: {uptrend_fails} stocks")
    if score_fails > 0:
        print(f"   ❌ Low signal score: {score_fails} stocks (need ≥ 6.8)")
    print()
    print("💡 RECOMMENDATION:")
    if adx_fails > score_fails and adx_fails > uptrend_fails:
        print("   Lower ADX requirement further (maybe 15 for positional)")
    elif score_fails > adx_fails:
        print("   Lower signal_score requirement (maybe 6.5)")
    elif uptrend_fails > 0:
        print("   Check uptrend detection logic")
else:
    print("ℹ️ MARKET CONDITION:")
    print("   No stocks with RSI < 55 meeting basic criteria")
    print("   Market in strong momentum phase (all RSI > 55)")
    print("   Mean reversion signals will appear during pullbacks")

print()
print("=" * 80)
