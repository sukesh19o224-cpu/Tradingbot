"""
🌙 End-of-Day Scanner
Scans all NSE stocks after market close and ranks them for next day
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data.data_fetcher import DataFetcher
from src.data.nse_stock_fetcher import NSEStockFetcher
from src.strategies.signal_generator import SignalGenerator


class EODScanner:
    """
    End-of-Day Scanner

    Workflow:
    1. After market close (3:30 PM IST), scan ALL NSE stocks
    2. Generate signals for all stocks
    3. Rank stocks by signal score
    4. Save top N stocks for next day's live scanning
    """

    def __init__(self, max_workers: int = 20):
        self.data_fetcher = DataFetcher()
        self.stock_fetcher = NSEStockFetcher()
        self.signal_generator = SignalGenerator()
        self.max_workers = max_workers

        self.eod_results_file = 'data/eod_scan_results.json'

    def run_eod_scan(self, top_n: int = 100) -> Dict:
        """
        Run end-of-day scan on all NSE stocks

        Args:
            top_n: Number of top stocks to save for next day

        Returns:
            Dictionary with scan results and top stocks
        """
        print("\n" + "="*70)
        print("🌙 END-OF-DAY SCANNER - Full NSE Scan")
        print(f"⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
        print("="*70)

        # Get complete NSE stock list
        all_stocks = self.stock_fetcher.fetch_nse_stocks()
        print(f"\n📊 Total stocks to scan: {len(all_stocks)}")

        # Scan all stocks in parallel
        print(f"🔍 Scanning with {self.max_workers} parallel threads...")
        signals = self._scan_all_stocks_parallel(all_stocks)

        # Filter and rank
        valid_signals = [s for s in signals if s is not None and s.get('score', 0) >= 5.0]
        valid_signals.sort(key=lambda x: x['score'], reverse=True)

        print(f"\n✅ Scan complete!")
        print(f"   • Scanned: {len(all_stocks)} stocks")
        print(f"   • Valid signals: {len(valid_signals)} stocks")
        print(f"   • Top {top_n} selected for tomorrow")

        # Get tiered rankings (Top 50, 100, 250, 500)
        tier1_top50 = valid_signals[:50]   # Best of the best - Swing trading
        tier2_top100 = valid_signals[:100]  # Swing + Positional
        tier3_top250 = valid_signals[:250]  # Positional trading
        tier4_top500 = valid_signals[:500]  # All viable trades

        # Display tiered rankings
        print(f"\n🏆 TIERED RANKINGS FOR TOMORROW:")
        print(f"\n   📊 TIER 1 - TOP 50 (Swing Trading - Aggressive)")
        print(f"      • Count: {len(tier1_top50)}")
        print(f"      • Avg Score: {sum(s['score'] for s in tier1_top50[:50])/len(tier1_top50[:50]):.1f}/10" if tier1_top50 else "      • No stocks")
        print(f"      • Strategy: Short-term momentum + quick profits")

        print(f"\n   📈 TIER 2 - TOP 100 (Swing + Positional)")
        print(f"      • Count: {len(tier2_top100)}")
        print(f"      • Avg Score: {sum(s['score'] for s in tier2_top100[:100])/len(tier2_top100[:100]):.1f}/10" if tier2_top100 else "      • No stocks")
        print(f"      • Strategy: Mixed approach")

        print(f"\n   📉 TIER 3 - TOP 250 (Positional Trading)")
        print(f"      • Count: {len(tier3_top250)}")
        print(f"      • Avg Score: {sum(s['score'] for s in tier3_top250[:250])/len(tier3_top250[:250]):.1f}/10" if tier3_top250 else "      • No stocks")
        print(f"      • Strategy: Medium-term trend following")

        print(f"\n   🔍 TIER 4 - TOP 500 (All Viable)")
        print(f"      • Count: {len(tier4_top500)}")
        print(f"      • Avg Score: {sum(s['score'] for s in tier4_top500[:500])/len(tier4_top500[:500]):.1f}/10" if tier4_top500 else "      • No stocks")
        print(f"      • Strategy: Conservative long-term")

        # Display top 10 from Tier 1 (best trades)
        print(f"\n🌟 TOP 10 STOCKS FROM TIER 1 (BEST SWING TRADES):")
        for i, signal in enumerate(tier1_top50[:10], 1):
            print(f"   {i}. {signal['symbol']} - Score: {signal['score']:.1f}/10 ({signal['trade_type']})")
            print(f"      Entry: ₹{signal['entry_price']:.2f} | Target: ₹{signal['target2']:.2f} (+{((signal['target2']/signal['entry_price']-1)*100):.1f}%)")

        # Save results with tiered structure
        results = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': len(all_stocks),
            'valid_signals': len(valid_signals),

            # Tiered rankings
            'tiers': {
                'tier1_top50': {
                    'symbols': [s['symbol'] for s in tier1_top50],
                    'signals': tier1_top50,
                    'count': len(tier1_top50),
                    'strategy': 'swing_trading',
                    'description': 'Best quality - aggressive swing trades',
                },
                'tier2_top100': {
                    'symbols': [s['symbol'] for s in tier2_top100],
                    'signals': tier2_top100,
                    'count': len(tier2_top100),
                    'strategy': 'swing_and_positional',
                    'description': 'Good quality - mixed approach',
                },
                'tier3_top250': {
                    'symbols': [s['symbol'] for s in tier3_top250],
                    'signals': tier3_top250,
                    'count': len(tier3_top250),
                    'strategy': 'positional_trading',
                    'description': 'Medium quality - positional trades',
                },
                'tier4_top500': {
                    'symbols': [s['symbol'] for s in tier4_top500],
                    'signals': tier4_top500,
                    'count': len(tier4_top500),
                    'strategy': 'conservative_longterm',
                    'description': 'All viable - conservative approach',
                },
            },

            # Legacy format (for backward compatibility)
            'top_stocks': [s['symbol'] for s in tier1_top50],  # Default to Tier 1
            'top_signals': tier1_top50,
            'all_signals': valid_signals[:200],  # Save top 200

            # Stats
            'stats': {
                'excellent': len([s for s in valid_signals if s['score'] >= 8.5]),
                'good': len([s for s in valid_signals if 8.0 <= s['score'] < 8.5]),
                'moderate': len([s for s in valid_signals if 7.0 <= s['score'] < 8.0]),
                'tier1_count': len(tier1_top50),
                'tier2_count': len(tier2_top100),
                'tier3_count': len(tier3_top250),
                'tier4_count': len(tier4_top500),
            }
        }

        # Save to file
        os.makedirs('data', exist_ok=True)
        with open(self.eod_results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to: {self.eod_results_file}")
        print(f"\n📈 Signal Distribution:")
        print(f"   • Excellent (≥8.5): {results['stats']['excellent']} stocks")
        print(f"   • Good (≥8.0): {results['stats']['good']} stocks")
        print(f"   • Moderate (≥7.0): {results['stats']['moderate']} stocks")

        return results

    def _scan_all_stocks_parallel(self, symbols: List[str]) -> List[Dict]:
        """
        Scan all stocks in parallel using ThreadPoolExecutor

        Args:
            symbols: List of stock symbols

        Returns:
            List of signal dictionaries
        """
        signals = []
        completed = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self._scan_single_stock, symbol): symbol
                for symbol in symbols
            }

            # Process as completed
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1

                # Progress update every 50 stocks
                if completed % 50 == 0:
                    print(f"   Progress: {completed}/{len(symbols)} ({completed/len(symbols)*100:.0f}%)")

                try:
                    signal = future.result()
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    errors += 1

        if errors > 0:
            print(f"   ⚠️  {errors} stocks failed to scan (network issues/delisted)")

        return signals

    def _scan_single_stock(self, symbol: str) -> Dict:
        """
        Scan a single stock

        Args:
            symbol: Stock symbol

        Returns:
            Signal dictionary or None
        """
        try:
            # Fetch data (daily timeframe for EOD scan)
            df = self.data_fetcher.get_stock_data(symbol, period='6mo', interval='1d')

            if df is None or len(df) < 100:
                return None

            # Generate signal
            signal = self.signal_generator.generate_signal(symbol, df)

            return signal

        except Exception as e:
            return None

    def get_top_stocks_for_today(self, tier: str = 'tier1') -> List[str]:
        """
        Get top stocks from yesterday's EOD scan by tier

        Args:
            tier: Which tier to load ('tier1', 'tier2', 'tier3', 'tier4', or 'all')

        Returns:
            List of stock symbols to scan today
        """
        if not os.path.exists(self.eod_results_file):
            print("⚠️  No EOD scan results found. Using default watchlist.")
            return []

        try:
            with open(self.eod_results_file) as f:
                results = json.load(f)

            scan_date = datetime.fromisoformat(results['scan_date'])
            age_days = (datetime.now() - scan_date).days

            if age_days > 1:
                print(f"⚠️  EOD scan is {age_days} days old. Consider running fresh scan.")

            # Load from tiered structure
            if 'tiers' in results:
                if tier == 'all':
                    # Combine all tiers
                    all_stocks = []
                    for tier_key in ['tier1_top50', 'tier2_top100', 'tier3_top250', 'tier4_top500']:
                        all_stocks.extend(results['tiers'].get(tier_key, {}).get('symbols', []))
                    stocks = list(set(all_stocks))  # Remove duplicates
                elif tier == 'tier1':
                    stocks = results['tiers'].get('tier1_top50', {}).get('symbols', [])
                elif tier == 'tier2':
                    stocks = results['tiers'].get('tier2_top100', {}).get('symbols', [])
                elif tier == 'tier3':
                    stocks = results['tiers'].get('tier3_top250', {}).get('symbols', [])
                elif tier == 'tier4':
                    stocks = results['tiers'].get('tier4_top500', {}).get('symbols', [])
                else:
                    stocks = results['tiers'].get('tier1_top50', {}).get('symbols', [])
            else:
                # Legacy format
                stocks = results.get('top_stocks', [])

            tier_name = tier.upper().replace('TIER', 'TIER ')
            print(f"📊 Loaded {len(stocks)} stocks from {tier_name} ({scan_date.strftime('%d %b %Y')})")

            return stocks

        except Exception as e:
            print(f"⚠️  Error loading EOD results: {e}")
            return []

    def get_scan_summary(self) -> Dict:
        """
        Get summary of last EOD scan

        Returns:
            Summary dictionary
        """
        if not os.path.exists(self.eod_results_file):
            return {'status': 'no_scan'}

        with open(self.eod_results_file) as f:
            results = json.load(f)

        scan_date = datetime.fromisoformat(results['scan_date'])

        return {
            'status': 'available',
            'scan_date': scan_date.strftime('%d %b %Y, %I:%M %p'),
            'age_days': (datetime.now() - scan_date).days,
            'total_scanned': results['total_scanned'],
            'valid_signals': results['valid_signals'],
            'top_stocks_count': len(results['top_stocks']),
            'stats': results['stats']
        }


if __name__ == "__main__":
    # Test EOD scanner
    scanner = EODScanner(max_workers=10)

    print("Running EOD scan (this will take 5-10 minutes)...")
    results = scanner.run_eod_scan(top_n=50)

    print("\n" + "="*70)
    print("📊 SCAN SUMMARY")
    print("="*70)
    print(f"Total scanned: {results['total_scanned']}")
    print(f"Valid signals: {results['valid_signals']}")
    print(f"Top stocks selected: {len(results['top_stocks'])}")
