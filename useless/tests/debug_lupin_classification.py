#!/usr/bin/env python3
"""Debug why LUPIN is showing as MOMENTUM instead of MEAN_REVERSION"""

import sys
sys.path.insert(0, '/media/sukesh-k/Storage/new Tr/TraDc')

from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.data.enhanced_data_fetcher import EnhancedDataFetcher

print("=" * 80)
print("🔍 DEBUGGING LUPIN.NS CLASSIFICATION")
print("=" * 80)
print()

# Fetch real data for LUPIN
fetcher = EnhancedDataFetcher()
symbol = "LUPIN.NS"

data_result = fetcher.get_stock_data_dual(symbol)
if not data_result or 'daily' not in data_result:
    print(f"❌ Could not fetch data for {symbol}")
    sys.exit(1)

daily_df = data_result['daily']
intraday_df = data_result.get('intraday')

# Analyze
analyzer = MultiTimeframeAnalyzer()
result = analyzer.analyze_stock(symbol, daily_df, intraday_df)

if not result:
    print(f"❌ No signal for {symbol}")
    sys.exit(1)

print(f"Stock: {symbol}")
print()

indicators = result.get('indicators', {})
rsi = indicators.get('rsi', 0)
adx = indicators.get('adx', 0)
current_price = indicators.get('price', 0)
ema_20 = indicators.get('ema_20', 0)
ema_50 = indicators.get('ema_50', 0)
ema_200 = indicators.get('ema_200', 0)
macd_histogram = indicators.get('macd_histogram', 0)
volume_ratio = indicators.get('volume_ratio', 1.0)

print("📊 TECHNICAL INDICATORS:")
print(f"   RSI: {rsi:.1f}")
print(f"   ADX: {adx:.1f}")
print(f"   Current Price: ₹{current_price:.2f}")
print(f"   20-MA: ₹{ema_20:.2f}")
print(f"   50-MA: ₹{ema_50:.2f}")
print(f"   200-MA: ₹{ema_200:.2f}")
print(f"   MACD Hist: {macd_histogram:.3f}")
print(f"   Volume Ratio: {volume_ratio:.2f}x")
print()

print("🔍 CLASSIFICATION LOGIC CHECK:")
print()

# Test mean reversion logic
if rsi < 55:
    print(f"✅ Step 1: RSI < 55? {rsi:.1f} < 55 = TRUE")
    
    in_uptrend = False
    reason = None
    
    # Option 1
    if ema_50 > 0 and current_price > ema_50:
        in_uptrend = True
        reason = f"Price ({current_price:.2f}) > 50-MA ({ema_50:.2f})"
    elif ema_20 > 0 and ema_50 > 0:
        if current_price < ema_20 and current_price > ema_50:
            in_uptrend = True
            reason = f"Price between 20-MA ({ema_20:.2f}) and 50-MA ({ema_50:.2f})"
    elif ema_200 > 0 and current_price > ema_200 * 0.95:
        in_uptrend = True
        reason = f"Price ({current_price:.2f}) near 200-MA ({ema_200:.2f})"
    elif ema_50 > 0 and current_price > ema_50 * 0.90:
        in_uptrend = True
        reason = f"Price ({current_price:.2f}) within 10% of 50-MA ({ema_50:.2f})"
    elif ema_200 > 0 and current_price > ema_200:
        in_uptrend = True
        reason = f"Price ({current_price:.2f}) > 200-MA ({ema_200:.2f})"
    
    if in_uptrend:
        print(f"✅ Step 2: In uptrend? TRUE - {reason}")
    else:
        print(f"❌ Step 2: In uptrend? FALSE")
    
    macd_ok = macd_histogram > -1.5
    print(f"{'✅' if macd_ok else '❌'} Step 3: MACD > -1.5? {macd_histogram:.3f} > -1.5 = {macd_ok}")
    
    if in_uptrend and macd_ok:
        print()
        print("🎯 Should classify as: MEAN_REVERSION")
    else:
        print()
        print("❌ Failed uptrend/MACD check, will default to MOMENTUM")
else:
    print(f"❌ Step 1: RSI < 55? {rsi:.1f} < 55 = FALSE")
    if rsi > 60:
        print(f"✅ RSI > 60? {rsi:.1f} > 60 = TRUE")
        print("🎯 Will classify as: MOMENTUM")
    else:
        print(f"   RSI in neutral zone (55-65)")

print()
print("=" * 80)
print("ACTUAL CLASSIFICATION FROM ANALYZER:")
print("=" * 80)
signal_type = result.get('signal_type', 'UNKNOWN')
signal_score = result.get('signal_score', 0)
mean_rev_quality = result.get('mean_reversion_quality', {})
mean_rev_score = mean_rev_quality.get('score', 0)

print(f"   Signal Type: {signal_type}")
print(f"   Signal Score: {signal_score:.1f}/10")
print(f"   Mean Rev Quality: {mean_rev_score}/100")
print()

if signal_type == 'MEAN_REVERSION':
    print("✅ CORRECTLY classified as MEAN_REVERSION")
else:
    print(f"❌ INCORRECTLY classified as {signal_type}")
    print()
    print("🔍 POSSIBLE CAUSES:")
    print("   1. Classification logic has a bug")
    print("   2. Stock doesn't meet mean reversion criteria")
    print("   3. Default return catching edge cases")

print()
print("=" * 80)
