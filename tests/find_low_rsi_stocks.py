#!/usr/bin/env python3
"""Find stocks with RSI < 55 to see if they classify as mean reversion"""

import sys
sys.path.insert(0, '/media/sukesh-k/Storage/new Tr/TraDc')

from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from config.nse_top_500_live import NSE_TOP_500

print("=" * 80)
print("🔍 FINDING STOCKS WITH RSI < 55")
print("=" * 80)
print()

fetcher = EnhancedDataFetcher()
analyzer = MultiTimeframeAnalyzer()

print("Scanning first 100 stocks...")
print()

low_rsi_stocks = []

for i, symbol in enumerate(NSE_TOP_500[:100], 1):
    try:
        data_result = fetcher.get_stock_data_dual(symbol)
        if not data_result or 'daily' not in data_result:
            continue
        
        daily_df = data_result['daily']
        intraday_df = data_result.get('intraday')
        
        result = analyzer.analyze_stock(symbol, daily_df, intraday_df)
        if not result:
            continue
        
        indicators = result.get('indicators', {})
        rsi = indicators.get('rsi', 0)
        
        if rsi < 55:
            signal_type = result.get('signal_type', 'UNKNOWN')
            signal_score = result.get('signal_score', 0)
            mean_rev_quality = result.get('mean_reversion_quality', {})
            mean_rev_score = mean_rev_quality.get('score', 0)
            adx = indicators.get('adx', 0)
            
            low_rsi_stocks.append({
                'symbol': symbol,
                'rsi': rsi,
                'adx': adx,
                'signal_type': signal_type,
                'signal_score': signal_score,
                'mean_rev_score': mean_rev_score
            })
            
            emoji = "✅" if signal_type == "MEAN_REVERSION" else "❌"
            print(f"{emoji} [{i:3d}] {symbol:20s} | RSI:{rsi:5.1f} ADX:{adx:5.1f} | {signal_type:20s} | Quality:{mean_rev_score:3.0f}/100")
    
    except Exception as e:
        pass

print()
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print()

if low_rsi_stocks:
    mean_rev_count = sum(1 for s in low_rsi_stocks if s['signal_type'] == 'MEAN_REVERSION')
    momentum_count = sum(1 for s in low_rsi_stocks if s['signal_type'] == 'MOMENTUM')
    
    print(f"Total stocks with RSI < 55: {len(low_rsi_stocks)}")
    print(f"  ✅ Classified as MEAN_REVERSION: {mean_rev_count}")
    print(f"  ❌ Classified as MOMENTUM: {momentum_count}")
    print()
    
    if mean_rev_count > 0:
        print("✅ MEAN REVERSION DETECTION IS WORKING!")
        print("   The system correctly identifies pullbacks in uptrends")
    else:
        print("❌ MEAN REVERSION DETECTION IS BROKEN!")
        print("   All stocks with RSI < 55 are being classified as MOMENTUM")
        print()
        print("🔍 Checking why first stock failed:")
        first = low_rsi_stocks[0]
        print(f"   Symbol: {first['symbol']}")
        print(f"   RSI: {first['rsi']:.1f} (< 55, should qualify)")
        print(f"   ADX: {first['adx']:.1f}")
        print(f"   Classified as: {first['signal_type']}")
        print()
        print("   Possible reasons:")
        print("   - Stock not in uptrend (below all MAs)")
        print("   - MACD too negative (< -1.5)")
        print("   - ADX too low (blocking in scanner)")
else:
    print("⚠️ NO STOCKS WITH RSI < 55 FOUND in first 100")
    print()
    print("This means:")
    print("  • Market is in strong MOMENTUM phase (all RSI > 55)")
    print("  • No pullbacks happening right now")
    print("  • Mean reversion signals will appear during market corrections")
    print()
    print("💡 This is NORMAL - mean reversion opportunities come and go with market cycles")

print()
print("=" * 80)
