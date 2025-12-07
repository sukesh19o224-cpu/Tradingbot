#!/usr/bin/env python3
"""
🔬 SIGNAL QUALITY OPTIMIZER
Tests different filter settings to find optimal balance between quality and quantity

Workflow:
1. Runs mini_test.py with 500 stocks
2. Tests different MIN_SIGNAL_SCORE thresholds
3. Analyzes signal quality metrics
4. Recommends best settings

IMPORTANT: Does NOT modify any files permanently!
"""

import sys
import time
from datetime import datetime
from typing import Dict, List
from tabulate import tabulate
import importlib

# Import config
from config import settings

# Import mini test
from mini_test import MiniTest


class SignalQualityOptimizer:
    """Optimize signal quality by testing different filter thresholds"""

    def __init__(self):
        print("\n" + "="*80)
        print("🔬 SIGNAL QUALITY OPTIMIZER")
        print("="*80)
        print("📊 Testing with: 500 NSE stocks (market cap ranked)")
        print("🎯 Objective: Find best MIN_SIGNAL_SCORE for quality + quantity balance")
        print("📱 Discord Alerts: DISABLED during optimization")
        print("💾 File Modifications: NONE (read-only)")
        print("="*80 + "\n")

        # Store original settings
        self.original_min_score = settings.MIN_SIGNAL_SCORE

        # Test thresholds
        self.test_thresholds = [6.0, 6.5, 6.8, 7.0, 7.2, 7.5, 8.0, 8.5]

        print(f"✅ Optimizer initialized")
        print(f"📊 Current MIN_SIGNAL_SCORE: {self.original_min_score}")
        print(f"🧪 Will test thresholds: {', '.join(map(str, self.test_thresholds))}")
        print(f"⏱️  Estimated time: ~{len(self.test_thresholds) * 3} minutes")
        print("\n")

    def analyze_signals(self, result: Dict) -> Dict:
        """Analyze signal quality metrics"""
        swing_signals = result.get('swing_signals', [])
        positional_signals = result.get('positional_signals', [])
        all_signals = swing_signals + positional_signals

        if not all_signals:
            return {
                'total_signals': 0,
                'swing_count': 0,
                'positional_count': 0,
                'avg_score': 0,
                'min_score': 0,
                'max_score': 0,
                'signal_types': {},
                'unique_stocks': 0,
                'quality_rating': '❌ No signals'
            }

        # Calculate metrics
        scores = [sig.get('score', 0) for sig in all_signals]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        # Count signal types
        signal_types = {}
        for sig in all_signals:
            sig_type = sig.get('signal_type', 'UNKNOWN')
            signal_types[sig_type] = signal_types.get(sig_type, 0) + 1

        # Count unique stocks
        unique_stocks = len(set(sig['symbol'] for sig in all_signals))

        # Quality rating based on avg score and diversity
        if avg_score >= 8.0:
            quality_rating = '🌟 EXCELLENT'
        elif avg_score >= 7.5:
            quality_rating = '✅ VERY GOOD'
        elif avg_score >= 7.0:
            quality_rating = '✅ GOOD'
        elif avg_score >= 6.5:
            quality_rating = '⚠️ OK'
        else:
            quality_rating = '❌ Low quality'

        return {
            'total_signals': len(all_signals),
            'swing_count': len(swing_signals),
            'positional_count': len(positional_signals),
            'avg_score': avg_score,
            'min_score': min_score,
            'max_score': max_score,
            'signal_types': signal_types,
            'unique_stocks': unique_stocks,
            'quality_rating': quality_rating
        }

    def filter_signals_by_threshold(self, all_signals: Dict, threshold: float) -> Dict:
        """Filter signals by score threshold"""
        swing_signals = all_signals.get('swing_signals', [])
        positional_signals = all_signals.get('positional_signals', [])

        # Filter by score
        filtered_swing = [s for s in swing_signals if s.get('score', 0) >= threshold]
        filtered_positional = [s for s in positional_signals if s.get('score', 0) >= threshold]

        return {
            'swing_signals': filtered_swing,
            'positional_signals': filtered_positional
        }

    def optimize(self) -> List[Dict]:
        """Run optimization across all thresholds"""
        print(f"\n{'='*80}")
        print(f"🚀 STARTING OPTIMIZATION @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        start_time = time.time()

        # Step 1: Temporarily set MIN_SIGNAL_SCORE to lowest threshold (6.0)
        # This ensures we capture ALL possible signals
        print(f"📊 Step 1: Scanning 500 stocks with MIN_SIGNAL_SCORE = 6.0")
        print(f"   (This captures all signals, then we'll filter by different thresholds)\n")

        original_score = settings.MIN_SIGNAL_SCORE
        settings.MIN_SIGNAL_SCORE = 6.0

        # Run mini test once with lowest threshold
        tester = MiniTest(stock_count=500, enable_discord=False)
        all_signals = tester.run()

        # Restore original setting
        settings.MIN_SIGNAL_SCORE = original_score

        scan_time = time.time() - start_time

        print(f"\n✅ Scan complete in {scan_time/60:.1f} minutes")
        print(f"📊 Collected {len(all_signals.get('swing_signals', [])) + len(all_signals.get('positional_signals', []))} signals\n")

        # Step 2: Filter signals by different thresholds
        print(f"📊 Step 2: Analyzing signals at different thresholds...")
        print(f"{'='*80}\n")

        results = []
        for threshold in self.test_thresholds:
            print(f"   🧪 Testing MIN_SIGNAL_SCORE = {threshold}...", end=" ")

            # Filter signals by this threshold
            filtered = self.filter_signals_by_threshold(all_signals, threshold)

            # Analyze filtered results
            analysis = self.analyze_signals(filtered)
            analysis['threshold'] = threshold

            results.append(analysis)
            print(f"✅ {analysis['total_signals']} signals")

        total_time = time.time() - start_time

        print(f"\n{'='*80}")
        print(f"✅ OPTIMIZATION COMPLETE")
        print(f"{'='*80}")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"🧪 Thresholds tested: {len(results)}")
        print(f"📊 Original MIN_SIGNAL_SCORE: {self.original_min_score}")
        print(f"{'='*80}\n")

        return results

    def display_results(self, results: List[Dict]):
        """Display optimization results in a nice table"""
        print(f"\n{'='*80}")
        print(f"📊 OPTIMIZATION RESULTS")
        print(f"{'='*80}\n")

        # Prepare table data
        table_data = []
        for r in results:
            # Signal type breakdown
            types_str = ', '.join([f"{k}: {v}" for k, v in r['signal_types'].items()])
            if not types_str:
                types_str = '-'

            table_data.append([
                f"{r['threshold']:.1f}",
                r['total_signals'],
                f"{r['avg_score']:.2f}",
                f"{r['min_score']:.1f}-{r['max_score']:.1f}",
                r['unique_stocks'],
                f"{r['swing_count']}",
                f"{r['positional_count']}",
                r['quality_rating']
            ])

        headers = [
            'Threshold',
            'Total',
            'Avg Score',
            'Range',
            'Stocks',
            'Swing',
            'Positional',
            'Quality'
        ]

        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()

        # Detailed signal type breakdown
        print(f"\n{'='*80}")
        print(f"📈 SIGNAL TYPE BREAKDOWN BY THRESHOLD")
        print(f"{'='*80}\n")

        for r in results:
            if r['total_signals'] > 0:
                print(f"MIN_SIGNAL_SCORE = {r['threshold']:.1f}:")
                for sig_type, count in r['signal_types'].items():
                    pct = (count / r['total_signals'] * 100)
                    print(f"   • {sig_type}: {count} ({pct:.1f}%)")
                print()

    def recommend_best(self, results: List[Dict]) -> Dict:
        """Recommend best threshold based on quality and quantity"""
        print(f"\n{'='*80}")
        print(f"💡 RECOMMENDATIONS")
        print(f"{'='*80}\n")

        # Filter out results with 0 signals
        valid_results = [r for r in results if r['total_signals'] > 0]

        if not valid_results:
            print("❌ No valid results found (all thresholds returned 0 signals)")
            print("   Try lowering the minimum thresholds or check market conditions")
            return None

        # Find best balance: good quality (avg_score >= 7.0) + good quantity (>= 10 signals)
        excellent_results = [r for r in valid_results if r['avg_score'] >= 7.5 and r['total_signals'] >= 10]
        good_results = [r for r in valid_results if r['avg_score'] >= 7.0 and r['total_signals'] >= 5]

        if excellent_results:
            # Pick the one with most signals from excellent group
            best = max(excellent_results, key=lambda x: x['total_signals'])
            reason = "🌟 Excellent quality (7.5+ avg score) + good quantity"
        elif good_results:
            # Pick the one with most signals from good group
            best = max(good_results, key=lambda x: x['total_signals'])
            reason = "✅ Good quality (7.0+ avg score) + reasonable quantity"
        else:
            # Pick the one with highest total signals
            best = max(valid_results, key=lambda x: x['total_signals'])
            reason = "⚠️ Best quantity available (consider market conditions)"

        print(f"🎯 RECOMMENDED MIN_SIGNAL_SCORE: {best['threshold']}")
        print(f"   Reason: {reason}")
        print(f"\n📊 Performance at this threshold:")
        print(f"   • Total Signals: {best['total_signals']}")
        print(f"   • Swing: {best['swing_count']}, Positional: {best['positional_count']}")
        print(f"   • Average Score: {best['avg_score']:.2f}")
        print(f"   • Score Range: {best['min_score']:.1f} - {best['max_score']:.1f}")
        print(f"   • Unique Stocks: {best['unique_stocks']}")
        print(f"   • Quality Rating: {best['quality_rating']}")

        # Signal type breakdown
        if best['signal_types']:
            print(f"\n   📈 Signal Types:")
            for sig_type, count in best['signal_types'].items():
                pct = (count / best['total_signals'] * 100)
                print(f"      • {sig_type}: {count} ({pct:.1f}%)")

        # Current vs recommended
        print(f"\n🔄 CHANGE NEEDED:")
        if abs(best['threshold'] - self.original_min_score) < 0.1:
            print(f"   ✅ Current setting ({self.original_min_score}) is already optimal!")
        else:
            change_pct = ((best['threshold'] - self.original_min_score) / self.original_min_score * 100)
            if best['threshold'] > self.original_min_score:
                print(f"   📈 INCREASE from {self.original_min_score} to {best['threshold']} ({change_pct:+.1f}%)")
                print(f"      → This will REDUCE quantity but IMPROVE quality")
            else:
                print(f"   📉 DECREASE from {self.original_min_score} to {best['threshold']} ({change_pct:+.1f}%)")
                print(f"      → This will INCREASE quantity but may reduce quality")

        print(f"\n💾 TO APPLY: Edit config/settings.py")
        print(f"   MIN_SIGNAL_SCORE = {best['threshold']}")
        print()

        return best


def main():
    """Main optimization function"""

    optimizer = SignalQualityOptimizer()

    print("⏳ Starting optimization... This will take a few minutes.\n")
    print("💡 TIP: Run this after market hours when market is closed")
    print("   for consistent results across all tests.\n")

    input("Press ENTER to start optimization... ")

    # Run optimization
    results = optimizer.optimize()

    # Display results
    optimizer.display_results(results)

    # Get recommendation
    best = optimizer.recommend_best(results)

    print(f"\n{'='*80}")
    print(f"✅ OPTIMIZATION SESSION COMPLETE")
    print(f"{'='*80}\n")

    print("📌 NEXT STEPS:")
    print("   1. Review the results and recommendation above")
    print("   2. Edit config/settings.py to apply the recommended MIN_SIGNAL_SCORE")
    print("   3. Run mini test to verify: python mini_test.py")
    print("   4. Run full system: python main_eod_system.py --mode once")
    print("\n")


if __name__ == "__main__":
    main()
