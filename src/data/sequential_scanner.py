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
                print(" ❌ No data")
                stats['data_failed'] += 1
                stats['processed'] += 1
                continue

            stats['data_success'] += 1
            print(" ✅ Data fetched", end='', flush=True)

            # STEP 2: Analyze for signals
            try:
                # Analyze daily data for swing + positional
                signals = self._analyze_stock(symbol, data['daily'], data['intraday'])

                # Check what was found and show quality details
                pos_sig = signals['positional']
                swing_sig = signals['swing']
                
                results = []
                
                # Check swing quality (A+ ONLY: Score ≥8.5, Quality ≥70)
                swing_passed = False
                if swing_sig:
                    swing_signal_type = swing_sig.get('signal_type', 'UNKNOWN')
                    signal_score = swing_sig.get('score', 0)
                    
                    if swing_signal_type == 'MEAN_REVERSION':
                        mean_rev_score = swing_sig.get('mean_reversion_score', 0)
                        is_valid = swing_sig.get('mean_reversion_valid', False)
                        swing_passed = is_valid  # Use quality validation (70+)
                        status = f"Score:{signal_score:.1f}/10 Q:{mean_rev_score}/100"
                        results.append(f"{'✅' if swing_passed else '❌'} SWING ({status})")
                    elif swing_signal_type == 'MOMENTUM':
                        momentum_score = swing_sig.get('momentum_score', 0)
                        is_valid = swing_sig.get('momentum_valid', False)
                        swing_passed = is_valid  # Use quality validation (70+)
                        status = f"Score:{signal_score:.1f}/10 Q:{momentum_score}/100"
                        results.append(f"{'✅' if swing_passed else '❌'} SWING ({status})")
                    elif swing_signal_type == 'BREAKOUT':
                        breakout_score = swing_sig.get('breakout_score', 0)
                        is_valid = swing_sig.get('breakout_valid', False)
                        swing_passed = is_valid  # Use quality validation (60+)
                        status = f"Score:{signal_score:.1f}/10 Q:{breakout_score}/100"
                        results.append(f"{'✅' if swing_passed else '❌'} SWING ({status})")
                else:
                    results.append("❌ Swing")
                
                if pos_sig:
                    signal_type = pos_sig.get('signal_type', 'UNKNOWN')
                    passed_quality = False
                    
                    # Show quality scores for positional
                    if signal_type == 'MEAN_REVERSION':
                        mean_rev_score = pos_sig.get('mean_reversion_score', 0)
                        is_valid = pos_sig.get('mean_reversion_valid', False)
                        signal_score = pos_sig.get('score', 0)
                        reasons = pos_sig.get('mean_reversion_reasons', [])
                        top_reason = reasons[0] if reasons else 'Quality filters'
                        print(f"\n   📊 {signal_type} | Score: {signal_score:.1f}/10 | Quality: {mean_rev_score}/100 {'✅' if is_valid else '❌'}")
                        print(f"      💡 {top_reason}", end='', flush=True)
                        results.append(f"{'✅' if is_valid else '❌'} POSITIONAL")
                        passed_quality = is_valid
                    elif signal_type == 'MOMENTUM':
                        momentum_score = pos_sig.get('momentum_score', 0)
                        is_valid = pos_sig.get('momentum_valid', False)
                        signal_score = pos_sig.get('score', 0)
                        reasons = pos_sig.get('momentum_reasons', [])
                        top_reason = reasons[0] if reasons else 'Quality filters'
                        print(f"\n   📊 {signal_type} | Score: {signal_score:.1f}/10 | Quality: {momentum_score}/100 {'✅' if is_valid else '❌'}")
                        print(f"      💡 {top_reason}", end='', flush=True)
                        results.append(f"{'✅' if is_valid else '❌'} POSITIONAL")
                        passed_quality = is_valid
                    elif signal_type == 'BREAKOUT':
                        breakout_score = pos_sig.get('breakout_score', 0)
                        is_valid = pos_sig.get('breakout_valid', False)
                        signal_score = pos_sig.get('score', 0)
                        reasons = pos_sig.get('breakout_reasons', [])
                        top_reason = reasons[0] if reasons else 'Quality filters'
                        print(f"\n   📊 {signal_type} | Score: {signal_score:.1f}/10 | Quality: {breakout_score}/100 {'✅' if is_valid else '❌'}")
                        print(f"      💡 {top_reason}", end='', flush=True)
                        results.append(f"{'✅' if is_valid else '❌'} POSITIONAL")
                        passed_quality = is_valid
                    else:
                        # Unknown signal type - skip
                        print(f"\n   📊 {signal_type}", end='', flush=True)
                        results.append("❌ POSITIONAL")
                        passed_quality = False
                    
                    # Add to results ONLY if passed quality check
                    if passed_quality:
                        positional_signals.append(pos_sig)
                        stats['positional_found'] += 1
                        stats['qualified_stocks'].append({'symbol': symbol, 'type': 'positional'})
                else:
                    results.append("❌ Positional")
                
                # Add swing if passed quality AND no positional (no duplicates)
                if swing_sig and swing_passed and not (pos_sig and passed_quality):
                    swing_signals.append(swing_sig)
                    stats['swing_found'] += 1
                    stats['qualified_stocks'].append({'symbol': symbol, 'type': 'swing'})

                print(f" | {' '.join(results)}", end='', flush=True)

            except Exception as e:
                print(f" ⚠️ Analysis error: {str(e)[:50]}", end='', flush=True)

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

        # CRITICAL FIX: Sort signals by score (highest first) and take top N
        # This ensures we get BEST quality signals, not first-found signals

        # Sort swing signals by score (descending)
        swing_signals = sorted(swing_signals, key=lambda x: x.get('score', 0), reverse=True)

        # Sort positional signals by score (descending)
        positional_signals = sorted(positional_signals, key=lambda x: x.get('score', 0), reverse=True)

        # Take only top N signals (as per config)
        from config.settings import MAX_SWING_SIGNALS_PER_SCAN, MAX_POSITIONAL_SIGNALS_PER_SCAN

        original_swing_count = len(swing_signals)
        original_positional_count = len(positional_signals)

        swing_signals = swing_signals[:MAX_SWING_SIGNALS_PER_SCAN]
        positional_signals = positional_signals[:MAX_POSITIONAL_SIGNALS_PER_SCAN]

        # Show filtering info
        if original_swing_count > len(swing_signals):
            print(f"\n📊 Filtered swing signals: {original_swing_count} → {len(swing_signals)} (top {len(swing_signals)} by score)")
        if original_positional_count > len(positional_signals):
            print(f"📊 Filtered positional signals: {original_positional_count} → {len(positional_signals)} (top {len(positional_signals)} by score)")

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
        
        STRICT FILTERS - A+ SETUPS ONLY (Paper trading test phase)
        - MOMENTUM ONLY (no mean reversion for swing)
        - ADX ≥28 (very strong trend required)
        - RSI 62-68 (prime momentum zone, not extended)
        - Volume ≥2.5x (explosive moves only)
        - Quality Score ≥70/100 (A+ grade mandatory)
        - Signal Score ≥8.5/10 (exceptional setups only)
        """
        try:
            indicators = mtf_result.get('indicators', {})
            signal_type = mtf_result.get('signal_type', 'MOMENTUM')
            
            # MOMENTUM ONLY - No mean reversion for swing
            if signal_type != 'MOMENTUM':
                return False
            
            # VERY STRONG TREND - ADX ≥28 (explosive momentum required)
            adx = indicators.get('adx', 0)
            if adx < 28:
                return False
            
            # PRIME MOMENTUM ZONE - RSI 62-68 (strong but not overbought)
            rsi = indicators.get('rsi', 0)
            if not (62 <= rsi <= 68):
                return False
            
            # EXPLOSIVE VOLUME - Must be ≥2.5x average (institutional buying)
            volume_ratio = indicators.get('volume_ratio', 0)
            if volume_ratio < 2.5:
                return False
            
            # QUALITY GRADE - Must be ≥70/100 (A+ setup)
            quality_score = mtf_result.get('momentum_score', 0)
            if quality_score < 70:
                return False
            
            # Trend check (must be in strong uptrend)
            if not mtf_result.get('uptrend', False):
                return False

            # SIGNAL STRENGTH - Must be ≥8.5/10 (exceptional only)
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < 8.5:
                return False

            return True

        except Exception:
            return False

    def _is_positional_setup(self, mtf_result: Dict) -> bool:
        """
        Check if stock qualifies for POSITIONAL trade

        IMPROVED: Strategy-aware filtering
        - No hardcoded RSI limits (blocks mean reversion!)
        - Quality scoring validates each signal type
        - ADX: ≥18 for MEAN_REVERSION (lower during pullback), ≥22 for MOMENTUM
        - Score: ≥6.8 (slightly higher quality)
        - Uptrend: Required
        """
        try:
            indicators = mtf_result.get('indicators', {})
            signal_type = mtf_result.get('signal_type', 'MOMENTUM')

            # ADX check - STRATEGY SPECIFIC!
            # Mean reversion: ADX ≥18 (pullback = weaker trend temporarily)
            # Momentum: ADX ≥22 (strong consistent trend)
            adx = indicators.get('adx', 0)
            if signal_type == 'MEAN_REVERSION':
                if adx < 18:  # More lenient for mean reversion
                    return False
            else:
                if adx < 22:  # Strict for momentum
                    return False

            # NO RSI CHECK - Let strategy-specific quality scoring handle it!
            # Mean reversion needs RSI 30-55 (would be rejected by hardcoded limits)
            # Momentum needs RSI 50-68 (validated by quality scoring)

            # Trend check (must be in uptrend)
            if not mtf_result.get('uptrend', False):
                return False

            # Signal strength - balanced (6.5+)
            # Same as swing - quality scoring handles filtering
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < 6.5:
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
        from config.settings import (
            SWING_STOP_LOSS, SWING_TARGETS, POSITIONAL_STOP_LOSS, POSITIONAL_TARGETS,
            INITIAL_CAPITAL, MAX_POSITION_SIZE, MAX_RISK_PER_TRADE
        )

        indicators = mtf_result.get('indicators', {})
        entry_price = mtf_result.get('current_price', 0)
        signal_type = mtf_result.get('signal_type', 'MOMENTUM')

        # Calculate stop loss and targets based on strategy type AND signal type
        if strategy_type == 'swing':
            # SWING: Use config values with optional ATR adjustment
            from config.settings import (SWING_STOP_LOSS, USE_ATR_STOP_LOSS, 
                                        ATR_MULTIPLIER_SWING, ATR_MIN_STOP_LOSS, ATR_MAX_STOP_LOSS)
            
            # Calculate base stop loss percentage
            if USE_ATR_STOP_LOSS and indicators.get('atr', 0) > 0:
                # ATR-based stop loss (volatility-adjusted)
                atr = indicators['atr']
                atr_stop_pct = (atr * ATR_MULTIPLIER_SWING) / entry_price
                # Clamp between min and max
                stop_loss_pct = max(ATR_MIN_STOP_LOSS, min(atr_stop_pct, ATR_MAX_STOP_LOSS))
            else:
                # Fixed percentage stop loss (fallback)
                stop_loss_pct = SWING_STOP_LOSS
            
            if signal_type == 'MEAN_REVERSION':
                stop_loss = entry_price * (1 - stop_loss_pct)
                targets = [0.04, 0.07, 0.10]
            elif signal_type == 'BREAKOUT':
                stop_loss = entry_price * (1 - stop_loss_pct)
                targets = [0.05, 0.08, 0.12]
            else:  # MOMENTUM
                stop_loss = entry_price * (1 - stop_loss_pct)
                targets = [0.04, 0.07, 0.10]
            
            target1 = entry_price * (1 + targets[0])
            target2 = entry_price * (1 + targets[1])
            target3 = entry_price * (1 + targets[2])
        else:  # positional
            # POSITIONAL: Use strategy-specific configs with optional ATR adjustment
            from config.settings import (MEAN_REVERSION_CONFIG, MOMENTUM_CONFIG, BREAKOUT_CONFIG,
                                        USE_ATR_STOP_LOSS, ATR_MULTIPLIER_POSITIONAL, 
                                        ATR_MIN_STOP_LOSS, ATR_MAX_STOP_LOSS)
            
            if signal_type == 'MEAN_REVERSION':
                strategy_config = MEAN_REVERSION_CONFIG
            elif signal_type == 'BREAKOUT':
                strategy_config = BREAKOUT_CONFIG
            else:  # MOMENTUM
                strategy_config = MOMENTUM_CONFIG
            
            # Calculate stop loss with optional ATR adjustment
            if USE_ATR_STOP_LOSS and indicators.get('atr', 0) > 0:
                # ATR-based stop loss (volatility-adjusted)
                atr = indicators['atr']
                atr_stop_pct = (atr * ATR_MULTIPLIER_POSITIONAL) / entry_price
                # Clamp between min and max
                stop_loss_pct = max(ATR_MIN_STOP_LOSS, min(atr_stop_pct, ATR_MAX_STOP_LOSS))
                stop_loss = entry_price * (1 - stop_loss_pct)
            else:
                # Fixed percentage stop loss (fallback)
                stop_loss = entry_price * (1 - strategy_config['STOP_LOSS'])
            target1 = entry_price * (1 + strategy_config['TARGETS'][0])
            target2 = entry_price * (1 + strategy_config['TARGETS'][1])
            target3 = entry_price * (1 + strategy_config['TARGETS'][2])

        # Calculate risk/reward ratio
        risk_amount = entry_price - stop_loss
        reward_amount = target1 - entry_price
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

        # Calculate position sizing (SAME AS PAPER TRADER)
        score = mtf_result.get('signal_score', 0)

        # Use swing or positional capital allocation
        if strategy_type == 'swing':
            allocated_capital = INITIAL_CAPITAL * 0.30  # 30% for swing
        else:
            allocated_capital = INITIAL_CAPITAL * 0.70  # 70% for positional

        # Base position size (25% max per position)
        max_position = allocated_capital * MAX_POSITION_SIZE

        # Risk-based sizing (2% max risk per trade)
        risk_per_share = entry_price - stop_loss
        max_risk_amount = allocated_capital * MAX_RISK_PER_TRADE
        max_shares_by_risk = max_risk_amount / risk_per_share if risk_per_share > 0 else 0

        # Base position size
        base_position_size = min(max_position, max_shares_by_risk * entry_price)

        # Quality-based multiplier (0.5x to 2.0x based on score)
        if score >= 7.0:
            quality_multiplier = 0.5 + (score - 7) * 0.5
            quality_multiplier = min(quality_multiplier, 2.0)
        else:
            quality_multiplier = 0.5

        # Final position size
        position_size = base_position_size * quality_multiplier

        # Calculate number of shares
        shares = int(position_size / entry_price) if entry_price > 0 else 0
        cost = shares * entry_price

        # Determine recommended hold days based on strategy
        if strategy_type == 'swing':
            recommended_hold_days = 5  # 2-5 days for swing
            risk_level = 'MODERATE'
        else:  # positional
            recommended_hold_days = 30  # 10-45 days for positional
            risk_level = 'LOW'

        signal = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_type,
            'signal_type': mtf_result.get('signal_type', 'MOMENTUM'),
            'score': mtf_result.get('signal_score', 0),
            'trade_type': f"{'🔥 SWING' if strategy_type == 'swing' else '📈 POSITIONAL'} TRADE",

            # Detailed scoring breakdown (NEW!)
            'technical_score': mtf_result.get('technical_score', 5.0),  # Technical indicators score
            'trend_only_score': mtf_result.get('trend_only_score', 5.0),  # EMA trend only
            
            # Quality metrics for filtering (CRITICAL!)
            'mean_reversion_score': mtf_result.get('mean_reversion_quality', {}).get('score', 0),
            'mean_reversion_valid': mtf_result.get('mean_reversion_quality', {}).get('is_valid', False),
            'mean_reversion_reasons': mtf_result.get('mean_reversion_quality', {}).get('reasons', []),
            'momentum_score': mtf_result.get('momentum_quality', {}).get('score', 0),
            'momentum_valid': mtf_result.get('momentum_quality', {}).get('is_valid', False),
            'momentum_reasons': mtf_result.get('momentum_quality', {}).get('reasons', []),
            'breakout_score': mtf_result.get('breakout_quality', {}).get('score', 0),
            'breakout_valid': mtf_result.get('breakout_quality', {}).get('is_valid', False),
            'breakout_reasons': mtf_result.get('breakout_quality', {}).get('reasons', []),

            # Price levels
            'current_price': round(entry_price, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2),
            'target3': round(target3, 2),

            # Position sizing (NEW - for Discord alerts!)
            'shares': shares,
            'position_size': round(cost, 2),
            'allocated_capital': round(allocated_capital, 2),

            # Risk management (FLAT fields for Discord)
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'recommended_hold_days': recommended_hold_days,
            'risk_level': risk_level,

            # Technical indicators (FLAT fields for Discord)
            'rsi': round(indicators.get('rsi', 50), 1),
            'adx': round(indicators.get('adx', 25), 1),
            'macd': indicators.get('macd', 0),
            'volume_ratio': round(indicators.get('volume_ratio', 1.0), 2),
            
            # Moving averages for Discord Price Position section
            'ema_20': round(indicators.get('ema_21', 0), 2),  # Using EMA_21 as 20-MA
            'ema_50': round(indicators.get('ema_50', 0), 2),

            # Trend analysis (REAL values from technical analysis)
            'ema_trend': mtf_result.get('ema_trend', 'NEUTRAL'),
            'macd_signal': mtf_result.get('macd_signal', 'NEUTRAL'),
            'uptrend': mtf_result.get('uptrend', False),
            'trend_strength': mtf_result.get('trend_strength', 'SIDEWAYS'),

            # Mathematical indicators (REAL calculated values per stock!)
            'fibonacci_signal': mtf_result.get('fibonacci_signal', 'NO_SIGNAL'),
            'elliott_wave': mtf_result.get('elliott_wave_pattern', 'UNKNOWN'),  # Fixed field name
            'elliott_wave_count': mtf_result.get('elliott_wave_count', 0),  # Added wave count
            'mathematical_score': round(mtf_result.get('mathematical_score', 5.0), 1),  # REAL math score

            # ML predictions (if available)
            'predicted_return': mtf_result.get('predicted_return', 0),
            'ml_confidence': mtf_result.get('ml_confidence', 0),

            # Legacy nested structure (for backward compatibility)
            'indicators': {
                'rsi': indicators.get('rsi', 50),
                'adx': indicators.get('adx', 25),
                'macd': indicators.get('macd', 0),
                'volume_ratio': indicators.get('volume_ratio', 1.0)
            }
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
