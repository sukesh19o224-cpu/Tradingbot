"""
🎯 HYBRID SCANNER - Detects Both Swing and Positional Opportunities
Scans all stocks and automatically categorizes as swing, positional, or both
"""

import concurrent.futures
from typing import Dict, List, Tuple
import time
from datetime import datetime

from src.data.data_fetcher import DataFetcher
from src.strategies.signal_generator import SignalGenerator
from src.strategies.hybrid_detector import HybridDetector
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from config.settings import *


class HybridScanner:
    """
    Scans stocks and detects BOTH swing and positional opportunities

    For each stock:
    - Checks if it's a swing trading opportunity
    - Checks if it's a positional trading opportunity
    - Can be both, one, or neither
    """

    def __init__(self, max_workers: int = 10):
        self.data_fetcher = DataFetcher()
        self.signal_generator = SignalGenerator()
        self.hybrid_detector = HybridDetector()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.max_workers = max_workers

    def scan_all_stocks(self, symbols: List[str]) -> Dict:
        """
        Scan all stocks and detect both swing and positional opportunities

        Args:
            symbols: List of stock symbols

        Returns:
            Dict with:
                - swing_signals: List of swing trading signals
                - positional_signals: List of positional trading signals
                - stats: Scanning statistics
        """
        print(f"\n{'='*70}")
        print(f"🎯 HYBRID SCANNER - Swing + Positional Detection")
        print(f"{'='*70}")
        print(f"📊 Stocks to scan: {len(symbols)}")
        print(f"🔧 Parallel threads: {self.max_workers}")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")

        start_time = time.time()

        # Step 1: Fetch data in parallel (daily + 15-minute)
        print("📡 Step 1/3: Fetching market data (Daily + 15-min)...")
        stock_data_daily, stock_data_15m = self._fetch_data_parallel(symbols)

        fetch_time = time.time() - start_time
        print(f"✅ Data fetched: {len(stock_data_daily)}/{len(symbols)} stocks in {fetch_time:.1f}s\n")

        # Step 2: Generate base signals
        print("⚡ Step 2/3: Generating base signals...")
        signal_start = time.time()

        base_signals = self.signal_generator.scan_multiple_stocks(
            list(stock_data_daily.keys()),
            stock_data_daily
        )

        signal_time = time.time() - signal_start
        print(f"✅ Base signals: {len(base_signals)} stocks qualified\n")

        # Step 3: Detect swing and positional opportunities
        print("🎯 Step 3/3: Detecting swing & positional setups...")
        detect_start = time.time()

        swing_signals = []
        positional_signals = []
        both_count = 0

        for base_signal in base_signals:
            symbol = base_signal['symbol']

            # Get data for this stock
            df_daily = stock_data_daily.get(symbol)
            df_15m = stock_data_15m.get(symbol)

            if df_daily is None:
                continue

            # Detect opportunities
            swing_sig, pos_sig = self.hybrid_detector.detect_opportunities(
                symbol, df_daily, df_15m, base_signal
            )

            if swing_sig:
                swing_signals.append(swing_sig)

            if pos_sig:
                positional_signals.append(pos_sig)

            if swing_sig and pos_sig:
                both_count += 1

        detect_time = time.time() - detect_start
        total_time = time.time() - start_time

        # Sort by score
        swing_signals.sort(key=lambda x: x['score'], reverse=True)
        positional_signals.sort(key=lambda x: x['score'], reverse=True)

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ HYBRID SCAN COMPLETE")
        print(f"{'='*70}")
        print(f"⏱️  Total Time: {total_time:.1f}s")
        print(f"   └─ Data Fetch: {fetch_time:.1f}s")
        print(f"   └─ Base Signals: {signal_time:.1f}s")
        print(f"   └─ Hybrid Detection: {detect_time:.1f}s")
        print(f"📊 Success Rate: {len(stock_data_daily)}/{len(symbols)} ({len(stock_data_daily)/len(symbols)*100:.1f}%)")
        print(f"\n🎯 SIGNALS DETECTED:")
        print(f"   🔥 Swing Signals: {len(swing_signals)}")
        print(f"   📈 Positional Signals: {len(positional_signals)}")
        print(f"   ⭐ Both (Swing + Positional): {both_count}")
        print(f"   📊 Total Opportunities: {len(swing_signals) + len(positional_signals)}")
        print(f"⚡ Speed: {len(symbols)/total_time:.1f} stocks/second")
        print(f"{'='*70}\n")

        # Show top signals
        if swing_signals:
            print(f"🔥 TOP 3 SWING SIGNALS:")
            for i, sig in enumerate(swing_signals[:3], 1):
                print(f"   {i}. {sig['symbol']} - Score: {sig['score']:.1f}/10")
                print(f"      Entry: ₹{sig['entry_price']:.2f} → Target: ₹{sig['target2']:.2f} (+{((sig['target2']/sig['entry_price']-1)*100):.1f}%)")
                print(f"      Holding: {sig['expected_holding']}")

        if positional_signals:
            print(f"\n📈 TOP 3 POSITIONAL SIGNALS:")
            for i, sig in enumerate(positional_signals[:3], 1):
                print(f"   {i}. {sig['symbol']} - Score: {sig['score']:.1f}/10")
                print(f"      Entry: ₹{sig['entry_price']:.2f} → Target: ₹{sig['target2']:.2f} (+{((sig['target2']/sig['entry_price']-1)*100):.1f}%)")
                print(f"      Holding: {sig['expected_holding']}")

        return {
            'swing_signals': swing_signals,
            'positional_signals': positional_signals,
            'stats': {
                'total_stocks': len(symbols),
                'successful_fetches': len(stock_data_daily),
                'swing_count': len(swing_signals),
                'positional_count': len(positional_signals),
                'both_count': both_count,
                'total_opportunities': len(swing_signals) + len(positional_signals),
                'total_time': total_time,
                'fetch_time': fetch_time,
                'signal_time': signal_time,
                'detect_time': detect_time
            }
        }

    def _fetch_data_parallel(self, symbols: List[str]) -> Tuple[Dict, Dict]:
        """
        Fetch both daily and 15-minute data in parallel

        Returns:
            (daily_data, intraday_data) dictionaries
        """
        stock_data_daily = {}
        stock_data_15m = {}
        failed = []

        def fetch_single(symbol):
            """Fetch both daily and 15-min data for a single stock"""
            try:
                df_daily = self.data_fetcher.get_stock_data(symbol, period='6mo', interval='1d')
                df_15m = self.data_fetcher.get_stock_data(symbol, period='5d', interval='15m')
                return (symbol, df_daily, df_15m)
            except Exception as e:
                return (symbol, None, None)

        # Use ThreadPoolExecutor for parallel fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(fetch_single, symbol): symbol
                for symbol in symbols
            }

            # Progress tracking
            completed = 0
            total = len(symbols)

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1

                try:
                    symbol, df_daily, df_15m = future.result()

                    if df_daily is not None and not df_daily.empty:
                        stock_data_daily[symbol] = df_daily
                        if df_15m is not None and not df_15m.empty:
                            stock_data_15m[symbol] = df_15m
                        status = "✅"
                    else:
                        failed.append(symbol)
                        status = "❌"

                    # Progress indicator (every 10%)
                    if completed % max(1, total // 10) == 0:
                        progress = (completed / total) * 100
                        print(f"   Progress: {completed}/{total} ({progress:.0f}%) - Latest: {symbol} {status}")

                except Exception as e:
                    failed.append(symbol)
                    print(f"   ⚠️ Error fetching {symbol}: {str(e)[:50]}")

        if failed:
            print(f"\n⚠️ Failed to fetch: {len(failed)} stocks")
            if len(failed) <= 10:
                print(f"   {', '.join(failed)}")

        return stock_data_daily, stock_data_15m
