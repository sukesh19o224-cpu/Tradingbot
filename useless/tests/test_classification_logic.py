#!/usr/bin/env python3
"""Test signal classification logic"""

import sys
sys.path.insert(0, '/media/sukesh-k/Storage/new Tr/TraDc')

# Simulate a mean reversion scenario
test_data = {
    'rsi': 42,  # Low RSI (pullback)
    'current_price': 100,
    'ema_20': 105,  # Price below 20-MA
    'ema_50': 95,   # Price above 50-MA
    'ema_200': 90,  # Price above 200-MA
    'volume_ratio': 1.3,
    'macd_histogram': -0.5  # Slightly negative MACD
}

print("=" * 60)
print("TESTING SIGNAL CLASSIFICATION LOGIC")
print("=" * 60)
print()
print("Test Stock Data (Should be MEAN_REVERSION):")
print(f"  RSI: {test_data['rsi']} (pullback)")
print(f"  Price: {test_data['current_price']}")
print(f"  20-MA: {test_data['ema_20']} (price below)")
print(f"  50-MA: {test_data['ema_50']} (price ABOVE)")
print(f"  200-MA: {test_data['ema_200']} (price above)")
print(f"  MACD: {test_data['macd_histogram']}")
print()

# Test classification
rsi = test_data['rsi']
price = test_data['current_price']
ema_20 = test_data['ema_20']
ema_50 = test_data['ema_50']
ema_200 = test_data['ema_200']
macd_histogram = test_data['macd_histogram']

print("Classification Steps:")
print(f"  RSI < 55? {rsi < 55} ✓")

in_uptrend = False

# Option 1
if ema_50 > 0 and price > ema_50:
    in_uptrend = True
    print(f"  Price > 50-MA? {price} > {ema_50} = TRUE ✓")
else:
    print(f"  Price > 50-MA? {price} > {ema_50} = FALSE")

print(f"  In uptrend? {in_uptrend}")
print(f"  MACD > -1.5? {macd_histogram} > -1.5 = {macd_histogram > -1.5}")

if rsi < 55 and in_uptrend and macd_histogram > -1.5:
    result = "MEAN_REVERSION"
else:
    result = "MOMENTUM (default)"

print()
print(f"🎯 Classification Result: {result}")

if result == "MEAN_REVERSION":
    print("   ✅ CORRECT - This should be mean reversion")
else:
    print("   ❌ WRONG - This should be mean reversion but got momentum!")
    print()
    print("   🔍 ISSUE: Falling through to default 'MOMENTUM' return")

print()
print("=" * 60)
