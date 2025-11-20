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

        # Get top stocks
        top_stocks = valid_signals[:top_n]

        # Display top 10
        print(f"\n🏆 TOP 10 STOCKS FOR TOMORROW:")
        for i, signal in enumerate(top_stocks[:10], 1):
            print(f"   {i}. {signal['symbol']} - Score: {signal['score']:.1f}/10 ({signal['trade_type']})")
            print(f"      Entry: ₹{signal['entry_price']:.2f} | Target: ₹{signal['target2']:.2f} (+{((signal['target2']/signal['entry_price']-1)*100):.1f}%)")

        # Save results
        results = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': len(all_stocks),
            'valid_signals': len(valid_signals),
            'top_stocks': [s['symbol'] for s in top_stocks],
            'top_signals': top_stocks,
            'all_signals': valid_signals[:200],  # Save top 200
            'stats': {
                'excellent': len([s for s in valid_signals if s['score'] >= 8.5]),
                'good': len([s for s in valid_signals if 8.0 <= s['score'] < 8.5]),
                'moderate': len([s for s in valid_signals if 7.0 <= s['score'] < 8.0]),
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

    def get_top_stocks_for_today(self) -> List[str]:
        """
        Get top stocks from yesterday's EOD scan

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

            top_stocks = results.get('top_stocks', [])
            print(f"📊 Loaded {len(top_stocks)} stocks from EOD scan ({scan_date.strftime('%d %b %Y')})")

            return top_stocks

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
