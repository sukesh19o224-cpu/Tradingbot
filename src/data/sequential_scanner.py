"""
🎯 SEQUENTIAL SCANNER - Safe, One-by-One Scanning
Scans 500 stocks sequentially with proper delays (NO threads, NO API ban!)

Perfect for intraday scanning every 10 minutes.
"""

import time
from datetime import datetime
from typing import List, Dict
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.strategies.signal_generator import SignalGenerator
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from config.settings import *


class SequentialScanner:
    """
    Sequential stock scanner - ONE BY ONE

    Features:
    - NO threading (100% safe)
    - Proper delays between stocks
    - Dual data fetching (daily + intraday)
    - Full signal analysis
    - Progress tracking
    """

    def __init__(self, api_delay: float = 0.3):
        """
        Initialize sequential scanner

        Args:
            api_delay: Delay between each stock (0.3s = safe for Yahoo Finance)
        """
        self.data_fetcher = EnhancedDataFetcher(api_delay=api_delay)
        self.signal_generator = SignalGenerator()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.api_delay = api_delay

        print(f"🐌 Sequential Scanner initialized (NO threads, 100% safe)")
        print(f"⏱️ API delay: {api_delay}s between stocks")

    def scan_all_stocks(self, stocks: List[str]) -> Dict:
        """
        Scan ALL stocks sequentially (one by one)

        Args:
            stocks: List of stock symbols to scan

        Returns:
            Dict with:
                - 'swing_signals': List of swing signals
                - 'positional_signals': List of positional signals
                - 'stats': Scanning statistics
        """
        print(f"\n🎯 Starting Sequential Scan - {len(stocks)} stocks")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏱️ Estimated time: {len(stocks) * self.api_delay / 60:.1f} minutes")
        print("="*70)

        start_time = time.time()

        swing_signals = []
        positional_signals = []

        stats = {
            'total': len(stocks),
            'processed': 0,
            'data_success': 0,
            'data_failed': 0,
            'swing_found': 0,
            'positional_found': 0,
            'qualified_stocks': []
        }

        # Scan each stock ONE BY ONE
        for i, symbol in enumerate(stocks, 1):
            # Progress update
            progress_pct = (i / len(stocks)) * 100
            print(f"\n[{i}/{len(stocks)}] ({progress_pct:.1f}%) {symbol}", end='', flush=True)

            # STEP 1: Fetch dual data (daily + intraday)
            data = self.data_fetcher.get_stock_data_dual(symbol)

            if not data['success'] or data['daily'] is None:
                print(" ❌ No data", end='', flush=True)
                stats['data_failed'] += 1
                stats['processed'] += 1
                continue

            stats['data_success'] += 1
            print(" ✅", end='', flush=True)

            # STEP 2: Analyze for signals
            try:
                # Analyze daily data for swing + positional
                signals = self._analyze_stock(symbol, data['daily'], data['intraday'])

                if signals['swing']:
                    swing_signals.append(signals['swing'])
                    stats['swing_found'] += 1
                    stats['qualified_stocks'].append({'symbol': symbol, 'type': 'swing'})
                    print(" 🔥 SWING", end='', flush=True)

                if signals['positional']:
                    positional_signals.append(signals['positional'])
                    stats['positional_found'] += 1
                    stats['qualified_stocks'].append({'symbol': symbol, 'type': 'positional'})
                    print(" 📈 POSITIONAL", end='', flush=True)

            except Exception as e:
                print(f" ⚠️ Analysis error", end='', flush=True)

            stats['processed'] += 1

            # Brief pause before next stock
            if i < len(stocks):  # Don't delay after last stock
                time.sleep(self.api_delay)

        # Scan complete
        elapsed = time.time() - start_time

        print("\n" + "="*70)
        print(f"✅ Sequential Scan Complete!")
        print(f"⏱️ Time: {elapsed/60:.1f} minutes ({elapsed:.1f}s)")
        print(f"📊 Processed: {stats['processed']}/{stats['total']} stocks")

        # Avoid division by zero
        success_rate = (stats['data_success']/stats['total']*100) if stats['total'] > 0 else 0
        print(f"✅ Data Success: {stats['data_success']} ({success_rate:.1f}%)")
        print(f"❌ Data Failed: {stats['data_failed']}")
        print(f"🔥 Swing Signals: {stats['swing_found']}")
        print(f"📈 Positional Signals: {stats['positional_found']}")
        print(f"⚡ Total Qualified: {len(stats['qualified_stocks'])} stocks")

        return {
            'swing_signals': swing_signals,
            'positional_signals': positional_signals,
            'stats': stats
        }

    def _analyze_stock(self, symbol: str, daily_df, intraday_df) -> Dict:
        """
        Analyze a stock for signals

        Args:
            symbol: Stock symbol
            daily_df: Daily OHLCV data (3 months)
            intraday_df: Intraday 15-min data (today)

        Returns:
            Dict with 'swing' and 'positional' signals (or None)
        """
        result = {
            'swing': None,
            'positional': None
        }

        try:
            # Use multi-timeframe analysis (daily + intraday)
            mtf_result = self.mtf_analyzer.analyze_stock(
                symbol=symbol,
                daily_df=daily_df,
                intraday_df=intraday_df
            )

            if not mtf_result:
                return result

            # Check if qualifies for swing
            if self._is_swing_setup(mtf_result):
                result['swing'] = self._create_signal(symbol, mtf_result, 'swing')

            # Check if qualifies for positional
            if self._is_positional_setup(mtf_result):
                result['positional'] = self._create_signal(symbol, mtf_result, 'positional')

        except Exception as e:
            pass  # Silent fail

        return result

    def _is_swing_setup(self, mtf_result: Dict) -> bool:
        """
        Check if stock qualifies for SWING trade

        Swing criteria:
        - Strong momentum (RSI > 55)
        - Recent breakout or pullback bounce
        - Good volume
        - Clear intraday confirmation
        """
        try:
            indicators = mtf_result.get('indicators', {})

            # RSI check
            rsi = indicators.get('rsi', 0)
            if rsi < 55 or rsi > 75:
                return False

            # Trend check (must be in uptrend)
            if not mtf_result.get('uptrend', False):
                return False

            # Signal strength
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < MIN_SIGNAL_SCORE:
                return False

            return True

        except Exception:
            return False

    def _is_positional_setup(self, mtf_result: Dict) -> bool:
        """
        Check if stock qualifies for POSITIONAL trade

        Positional criteria:
        - Strong trend (ADX > 25)
        - Pullback to key support (20 EMA / 50 EMA)
        - Volume confirmation
        - Multi-week setup
        """
        try:
            indicators = mtf_result.get('indicators', {})

            # ADX check (strong trend)
            adx = indicators.get('adx', 0)
            if adx < 25:
                return False

            # RSI check (not overbought)
            rsi = indicators.get('rsi', 0)
            if rsi > 70:
                return False

            # Trend check
            if not mtf_result.get('uptrend', False):
                return False

            # Signal strength
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < MIN_SIGNAL_SCORE:
                return False

            return True

        except Exception:
            return False

    def _create_signal(self, symbol: str, mtf_result: Dict, strategy_type: str) -> Dict:
        """
        Create a trading signal

        Args:
            symbol: Stock symbol
            mtf_result: Multi-timeframe analysis result
            strategy_type: 'swing' or 'positional'

        Returns:
            Signal dict with all details
        """
        indicators = mtf_result.get('indicators', {})

        signal = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_type,
            'signal_type': mtf_result.get('signal_type', 'MOMENTUM'),
            'score': mtf_result.get('signal_score', 0),
            'entry_price': mtf_result.get('current_price', 0),
            'indicators': {
                'rsi': indicators.get('rsi', 0),
                'adx': indicators.get('adx', 0),
                'macd': indicators.get('macd', 0),
                'volume_ratio': indicators.get('volume_ratio', 0)
            },
            'uptrend': mtf_result.get('uptrend', False),
            'trend_strength': mtf_result.get('trend_strength', 'UNKNOWN')
        }

        return signal


def test_sequential_scanner():
    """Test the sequential scanner with a small stock list"""
    print("🧪 Testing Sequential Scanner...")
    print("="*70)

    scanner = SequentialScanner(api_delay=0.5)  # 0.5s delay for testing

    # Test with 10 stocks
    test_stocks = [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS',
        'INFY.NS',
        'ICICIBANK.NS',
        'SBIN.NS',
        'BHARTIARTL.NS',
        'ITC.NS',
        'KOTAKBANK.NS',
        'LT.NS'
    ]

    result = scanner.scan_all_stocks(test_stocks)

    print("\n" + "="*70)
    print("📊 TEST RESULTS:")
    print(f"   Swing Signals: {len(result['swing_signals'])}")
    print(f"   Positional Signals: {len(result['positional_signals'])}")

    if result['swing_signals']:
        print("\n🔥 Swing Signals Found:")
        for sig in result['swing_signals']:
            print(f"   - {sig['symbol']}: Score {sig['score']:.1f}, RSI {sig['indicators']['rsi']:.1f}")

    if result['positional_signals']:
        print("\n📈 Positional Signals Found:")
        for sig in result['positional_signals']:
            print(f"   - {sig['symbol']}: Score {sig['score']:.1f}, ADX {sig['indicators']['adx']:.1f}")


if __name__ == "__main__":
    test_sequential_scanner()
