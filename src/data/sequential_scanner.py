"""
🎯 SEQUENTIAL SCANNER - Safe, One-by-One Scanning
Scans stocks sequentially with proper delays (NO threads, NO API ban!)

Perfect for intraday scanning every 10 minutes.
Supports any number of stocks (currently configured for Top 1000).
"""

import time
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.strategies.signal_generator import SignalGenerator
from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
from src.strategies.market_regime_detector import MarketRegimeDetector
from src.strategies.sector_rotation_tracker import SectorRotationTracker
from src.strategies.bank_nifty_adjuster import BankNiftyAdjuster
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

    def __init__(self, api_delay: float = 0.08):
        """
        Initialize sequential scanner

        Args:
            api_delay: Delay between each stock (0.08s = very fast, monitor for rate limits)
        """
        self.data_fetcher = EnhancedDataFetcher(api_delay=api_delay)
        self.signal_generator = SignalGenerator()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.api_delay = api_delay
        
        # Market Regime Detection (Professional Feature)
        self.regime_detector = MarketRegimeDetector() if MARKET_REGIME_DETECTION_ENABLED else None
        self.current_regime = None
        self.regime_adjustments = None
        
        # Sector Rotation Tracking (India-Specific)
        self.sector_tracker = SectorRotationTracker() if SECTOR_ROTATION_ENABLED else None
        self.leading_sectors = []
        self.lagging_sectors = []
        
        # Bank Nifty Volatility Adjustment (India-Specific)
        self.bank_adjuster = BankNiftyAdjuster() if BANK_NIFTY_VOLATILITY_ADJUSTMENT else None

        print(f"🚀 Sequential Scanner initialized (NO threads, 100% safe, OPTIMIZED)")
        print(f"⏱️ API delay: {api_delay}s between stocks (optimized for speed)")
        
        # Feature status
        if MARKET_REGIME_DETECTION_ENABLED:
            print(f"📊 Market Regime Detection: ENABLED ✅")
        else:
            print(f"📊 Market Regime Detection: DISABLED")
            
        if SECTOR_ROTATION_ENABLED:
            print(f"🔄 Sector Rotation Tracking: ENABLED ✅")
        else:
            print(f"🔄 Sector Rotation Tracking: DISABLED")
            
        if BANK_NIFTY_VOLATILITY_ADJUSTMENT:
            print(f"🏦 Bank Nifty Adjustment: ENABLED ✅")
        else:
            print(f"🏦 Bank Nifty Adjustment: DISABLED")

    def scan_all_stocks(self, stocks: List[str], monitor_callback=None, monitor_callback_data=None) -> Dict:
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
        print(f"\n{'='*70}")
        print(f"🔍 SEQUENTIAL SCAN STARTED")
        print(f"{'='*70}")
        print(f"📊 Total stocks to scan: {len(stocks)}")
        print(f"⏱️ Estimated time: {len(stocks) * self.api_delay / 60:.1f} minutes")
        
        # MARKET REGIME DETECTION (if enabled)
        if self.regime_detector:
            print(f"\n📊 Detecting market regime...")
            self.current_regime, regime_details = self.regime_detector.detect_regime()
            self.regime_adjustments = self.regime_detector.get_regime_adjustments(self.current_regime)
            
            if SHOW_REGIME_IN_LOGS:
                self.regime_detector.print_regime_summary()
        else:
            print(f"\n📊 Market Regime Detection: DISABLED (normal operation)")
            self.current_regime = 'BULL'  # Default to normal operation
            self.regime_adjustments = {'quality_multiplier': 1.0, 'max_positions_multiplier': 1.0, 'position_size_multiplier': 1.0}
        
        # SECTOR ROTATION ANALYSIS (if enabled)
        if self.sector_tracker:
            print(f"\n🔄 Analyzing sector rotation...")
            sector_results = self.sector_tracker.analyze_sectors(lookback_days=30)
            self.leading_sectors = sector_results['leading_sectors']
            self.lagging_sectors = sector_results['lagging_sectors']
        else:
            print(f"\n🔄 Sector Rotation: DISABLED (normal operation)")
        
        print(f"\n{'='*70}\n")

        swing_signals = []
        positional_signals = []
        scanned_count = 0
        start_time = time.time()

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
            # CRITICAL: Monitor positions periodically during scan (every ~2 minutes)
            # This ensures positions are checked even during long scans (7+ minutes)
            # Calculation: 7 min scan = 420s, ~0.4s per stock = 1000 stocks
            # For 2-min intervals: 120s / 0.4s = ~300 stocks per check
            # Use 50 stocks for more frequent monitoring (~20-25 seconds)
            if monitor_callback and monitor_callback_data is not None:
                if i % 50 == 0:
                    try:
                        monitor_callback(monitor_callback_data)
                    except Exception as e:
                        # Don't let monitoring errors stop the scan
                        print(f"\n⚠️ Position monitoring error during scan: {e}")
            
            # Progress update
            progress_pct = (i / len(stocks)) * 100
            print(f"\n[{i}/{len(stocks)}] ({progress_pct:.1f}%) {symbol}", end='', flush=True)

            # STEP 1: Fetch dual data (daily + intraday)
            data = self.data_fetcher.get_stock_data_dual(symbol, verbose=True)

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
                
                # Check swing quality (MOMENTUM ONLY - optimized for 1-2% quick moves)
                swing_passed = False
                if swing_sig:
                    swing_signal_type = swing_sig.get('signal_type', 'UNKNOWN')
                    signal_score = swing_sig.get('score', 0)
                    
                    # SWING: MOMENTUM ONLY - Reject Mean Reversion and Breakout
                    if swing_signal_type != 'MOMENTUM':
                        swing_passed = False
                        status = f"Only MOMENTUM allowed (got {swing_signal_type})"
                        results.append(f"❌ SWING ({status})")
                    elif swing_signal_type == 'MOMENTUM':
                        momentum_score = swing_sig.get('momentum_score', 0)
                        is_valid = swing_sig.get('momentum_valid', False)
                        swing_passed = is_valid  # Use quality validation (25+)
                        status = f"Score:{signal_score:.1f}/10 Q:{momentum_score}/100"
                        results.append(f"{'✅' if swing_passed else '❌'} SWING MOMENTUM ({status})")
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
        
        # Show rate limit warnings if any (VERBOSE - tells you if too fast)
        fetcher_stats = self.data_fetcher.stats
        if fetcher_stats.get('rate_limits', 0) > 0:
            print(f"🚨 RATE LIMITS HIT: {fetcher_stats['rate_limits']} times - TOO FAST! Consider increasing delay")
        if fetcher_stats.get('retries', 0) > 0:
            print(f"🔄 Retries: {fetcher_stats['retries']} (some fetches needed retry)")
        
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
            # Pass market regime for adaptive mean reversion classification
            mtf_result = self.mtf_analyzer.analyze_stock(
                symbol=symbol,
                daily_df=daily_df,
                intraday_df=intraday_df,
                market_regime=self.current_regime  # Pass current market regime
            )

            if not mtf_result:
                return result

            # Check if qualifies for swing (with verbose logging)
            if self._is_swing_setup(mtf_result, symbol=symbol, verbose=True):
                result['swing'] = self._create_signal(symbol, mtf_result, 'swing', daily_df)

            # Check if qualifies for positional
            if self._is_positional_setup(mtf_result):
                result['positional'] = self._create_signal(symbol, mtf_result, 'positional', daily_df)

        except Exception as e:
            pass  # Silent fail

        return result

    def _is_swing_setup(self, mtf_result: Dict, symbol: str = "", verbose: bool = True) -> bool:
        """
        Check if stock qualifies for SWING trade (1-2% QUICK PROFITS)
        
        MOMENTUM ONLY - Optimized specifically for 1-2% quick moves
        Mean Reversion and Breakout are DISABLED for swing (use positional for those)
        
        KEY PRINCIPLE: Lower ADX, focused RSI ranges, short-term momentum
        - We want stocks that are STARTING to move, not already in strong trend
        - ADX 12-25: Some trend but room for quick move (strong trends already moved)
        - RSI 42-68: Good momentum but not exhausted (perfect for 1-2% moves)
        - Volume spikes: Sudden interest = quick move coming
        - Short-term momentum: Price just started moving (1-3 day window)
        
        MOMENTUM (OPTIMIZED FOR 1-2% QUICK MOVES):
        - ADX 12-25 (lower = catch stocks about to move, not already moved)
        - RSI 42-68 (sweet spot - strong enough but room to grow)
        - Volume ≥0.8x (catch volume spikes starting)
        - Short-term momentum positive (1-3 day price action)
        - Quality Score ≥25/100 (lower threshold for quick moves)
        - MACD bullish or momentum building
        
        All require: Signal Score ≥6.0/10 (lower for 1-2% moves) and Uptrend
        """
        try:
            from config.settings import ADX_MIN_TREND, RSI_SWING_MIN, RSI_SWING_MAX, VOLUME_SWING_MULTIPLIER
            
            indicators = mtf_result.get('indicators', {})
            signal_type = mtf_result.get('signal_type', 'MOMENTUM')
            
            # FORCE MOMENTUM ONLY FOR SWING - But allow conversion if it's a good momentum candidate
            # If signal type is not MOMENTUM, check if we can convert it to momentum
            original_signal_type = signal_type  # Save original for logging
            if signal_type != 'MOMENTUM':
                # Try to convert MEAN_REVERSION or BREAKOUT to MOMENTUM if it meets momentum criteria
                rsi = indicators.get('rsi', 0)
                adx = indicators.get('adx', 0)
                
                # If RSI is in momentum range (40-72) and ADX shows some trend, convert to MOMENTUM
                if 40 <= rsi <= 72 and adx >= 12:
                    signal_type = 'MOMENTUM'  # Force conversion
                    mtf_result['signal_type'] = 'MOMENTUM'  # Update the result
                    if verbose and symbol:
                        print(f"      ℹ️ Converted {original_signal_type} to MOMENTUM for swing (RSI {rsi:.1f}, ADX {adx:.1f})")
                else:
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: Only MOMENTUM allowed (got {original_signal_type}, RSI {rsi:.1f}, ADX {adx:.1f})")
                    return False
            
            # SIGNAL STRENGTH - Must be ≥6.0/10 (optimized for quick moves)
            from config.settings import MIN_SWING_SIGNAL_SCORE
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < MIN_SWING_SIGNAL_SCORE:
                if verbose and symbol:
                    print(f"      ⚠️ Swing rejected: Score {signal_score:.1f} < {MIN_SWING_SIGNAL_SCORE}")
                return False
            
            # Trend check (must be in uptrend)
            if not mtf_result.get('uptrend', False):
                if verbose and symbol:
                    print(f"      ⚠️ Swing rejected: Not in uptrend")
                return False
            
            adx = indicators.get('adx', 0)
            rsi = indicators.get('rsi', 0)
            volume_ratio = indicators.get('volume_ratio', 0)
            macd_signal = indicators.get('signals', {}).get('macd_signal', '')
            momentum_5d = indicators.get('momentum_5d', 0)
            
            # MOMENTUM ONLY - Optimized for 1-2% quick moves
            if signal_type == 'MOMENTUM':
                # MOMENTUM: Optimized for 1-2% quick moves
                # ADX: 12-40 range (REMOVED upper limit - stocks with ADX 26-40 can still make 1-2% moves quickly)
                if adx < 12:  # Too weak, no trend
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: ADX {adx:.1f} < 12 (too weak for momentum)")
                    return False
                # REMOVED: ADX > 25 rejection - allow higher ADX for swing (they can still make 1-2% moves)
                # Many momentum stocks have ADX 26-40 and can still move 1-2% quickly
                # RSI: More lenient range for 1-2% moves (40-72 allows more stocks)
                # RSI 40-42 and 68-72 can still make 1-2% moves quickly
                if not (40 <= rsi <= 72):  # Expanded range for more opportunities
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: RSI {rsi:.1f} not in 40-72 range (need room for 1-2% move)")
                    return False
                # VOLUME - Must be ≥VOLUME_SWING_MULTIPLIER (0.8x - catch volume spikes starting)
                if volume_ratio < VOLUME_SWING_MULTIPLIER:
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: Volume {volume_ratio:.1f}x < {VOLUME_SWING_MULTIPLIER}x")
                    return False
                
                # QUALITY - More lenient for 1-2% quick moves (≥15/100 OR just check basic momentum)
                # Many stocks with quality 15-25 can still make 1-2% moves quickly
                quality_score = mtf_result.get('momentum_score', 0)
                
                # Alternative: If quality is low but RSI/ADX/Volume are good, accept anyway
                # This catches stocks that might make 1-2% even with lower quality scores
                rsi_good = RSI_SWING_MIN <= rsi <= RSI_SWING_MAX
                adx_good = adx >= 12
                volume_good = volume_ratio >= VOLUME_SWING_MULTIPLIER
                
                if quality_score < 15 and not (rsi_good and adx_good and volume_good):
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: Momentum quality {quality_score}/100 < 15 and basic criteria not all met")
                    return False
                # If quality < 15 BUT basic criteria met, allow it (optimistic for 1-2% quick moves)
                
                # ADDITIONAL MOMENTUM OPTIMIZATION: Short-term momentum checks
                # For 1-2% quick moves, we want stocks that just started moving
                momentum_1d = indicators.get('momentum_1d', 0) if indicators.get('momentum_1d') is not None else 0
                
                # Check: Not falling too fast (would miss quick move)
                if momentum_1d < -1.0:  # Falling fast = not a good entry
                    if verbose and symbol:
                        print(f"      ⚠️ Swing rejected: Falling too fast (1d momentum {momentum_1d:.1f}%)")
                    return False
                    
                # Check: Momentum building (MACD bullish OR short-term momentum positive)
                # More lenient - accept if RSI/ADX/Volume are good even without strong momentum indicators
                # This catches stocks that might start moving soon
                if macd_signal not in ['BULLISH', 'BULLISH_CROSSOVER']:
                    if momentum_1d < -0.5 and momentum_5d < 0:  # Only reject if clearly falling
                        if verbose and symbol:
                            print(f"      ⚠️ Swing rejected: Falling momentum (MACD: {macd_signal}, 1d: {momentum_1d:.1f}%, 5d: {momentum_5d:.1f}%)")
                        return False
                    # If not falling fast, allow it (optimistic for quick 1-2% moves)
                
            else:
                # Should never reach here (we already rejected non-MOMENTUM above)
                if verbose and symbol:
                    print(f"      ⚠️ Swing rejected: Only MOMENTUM allowed for swing (got {signal_type})")
                return False
            
            return True
            
        except Exception as e:
            if verbose and symbol:
                print(f"      ⚠️ Swing check error: {e}")
            return False

    def _is_positional_setup(self, mtf_result: Dict) -> bool:
        """
        Check if stock qualifies for POSITIONAL trade

        IMPROVED: Strategy-aware filtering with BREAKOUT optimization
        - Mean reversion: ADX ≥18 (pullback = weaker trend temporarily)
        - Momentum: ADX ≥22 (strong consistent trend)
        - BREAKOUT: ADX ≥20, Volume ≥1.8x, Quality ≥50 (optimized for daily catching)
        - Score: ≥6.5 (balanced quality)
        - Uptrend: Required
        """
        try:
            indicators = mtf_result.get('indicators', {})
            signal_type = mtf_result.get('signal_type', 'MOMENTUM')
            adx = indicators.get('adx', 0)
            rsi = indicators.get('rsi', 0)
            volume_ratio = indicators.get('volume_ratio', 0)

            # BREAKOUT: Optimized for daily catching (industry standard for positional)
            if signal_type == 'BREAKOUT':
                # ADX: ≥18 (reduced from 20 - more catchable, breakouts can work with moderate trend)
                if adx < 18:
                    return False
                # RSI: 40-75 (wider range for positional - catch breakouts at various levels)
                if not (40 <= rsi <= 75):
                    return False
                # VOLUME: ≥1.5x (reduced from 1.8x - more catchable, breakouts need volume but not extreme)
                if volume_ratio < 1.5:
                    return False
                # QUALITY: ≥45/100 (reduced from 50 - more catchable, breakouts are rare but powerful)
                quality_score = mtf_result.get('breakout_score', 0)
                if quality_score < 45:
                    return False
            # MEAN_REVERSION: ADX ≥18 (pullback = weaker trend temporarily)
            elif signal_type == 'MEAN_REVERSION':
                if adx < 18:
                    return False
            # MOMENTUM: ADX ≥22 (strong consistent trend)
            else:
                if adx < 22:
                    return False

            # NO RSI CHECK for non-breakout - Let strategy-specific quality scoring handle it!
            # Mean reversion needs RSI 30-55 (would be rejected by hardcoded limits)
            # Momentum needs RSI 50-68 (validated by quality scoring)

            # Trend check (must be in uptrend)
            if not mtf_result.get('uptrend', False):
                return False

            # Signal strength - must meet MIN_SIGNAL_SCORE (7.0 for positional)
            # CRITICAL FIX: Use MIN_SIGNAL_SCORE instead of hardcoded 6.5
            # This ensures consistency with position sizing and validation checks
            signal_score = mtf_result.get('signal_score', 0)
            if signal_score < MIN_SIGNAL_SCORE:  # 7.0 for positional
                return False

            return True

        except Exception:
            return False

    def _detect_gap_up(self, df: pd.DataFrame, threshold: float = 0.01) -> Tuple[bool, float]:
        """
        Detect gap up opening
        
        Args:
            df: Daily OHLCV DataFrame
            threshold: Minimum percentage for a gap up (e.g., 0.01 for 1%, 0.015 for 1.5%)
            
        Returns:
            (has_gap_up: bool, gap_percent: float)
        """
        try:
            if df is None or len(df) < 2:
                return False, 0.0
            
            today_open = df['Open'].iloc[-1]
            yesterday_close = df['Close'].iloc[-2]
            
            if yesterday_close <= 0:
                return False, 0.0
            
            gap_percent_decimal = ((today_open - yesterday_close) / yesterday_close)  # As decimal
            gap_percent_pct = gap_percent_decimal * 100  # As percentage for return
            
            # Gap up: opening > previous close by at least threshold (threshold is decimal, e.g., 0.015 = 1.5%)
            if gap_percent_decimal >= threshold:
                return True, round(gap_percent_pct, 2)  # Return percentage (e.g., 1.5 for 1.5%)
            else:
                return False, round(gap_percent_pct, 2)  # Return percentage (can be negative for gap down)
        except Exception:
            return False, 0.0
    
    def _is_near_20_day_high(self, df: pd.DataFrame, current_price: float, threshold: float = 0.02) -> bool:
        """
        Check if price is near 20-day high (within threshold%)
        
        Args:
            df: Daily OHLCV DataFrame
            current_price: Current stock price
            threshold: Percentage threshold (default 2% = within 2% of high)
            
        Returns:
            True if price is within threshold% of 20-day high
        """
        try:
            if df is None or len(df) < 20:
                return False
            
            high_20d = df['High'].tail(20).max()
            
            if high_20d <= 0:
                return False
            
            # Check if current price is within threshold% of 20-day high
            price_ratio = current_price / high_20d
            return price_ratio >= (1.0 - threshold)  # Within 2% of high
        except Exception:
            return False
    
    def _calculate_top_gainer_score_boosts(
        self, 
        df: pd.DataFrame, 
        indicators: Dict, 
        strategy_type: str
    ) -> float:
        """
        Calculate score boosts for top gainer characteristics
        
        Args:
            df: Daily OHLCV DataFrame
            indicators: Technical indicators dict
            strategy_type: 'swing' or 'positional'
            
        Returns:
            Total score boost (will be added to base score)
        """
        boost = 0.0
        current_price = indicators.get('current_price', 0)
        
        if current_price <= 0 or df is None or len(df) < 20:
            return 0.0
        
        # 1. Gap up detection (BALANCED - catch meaningful gaps)
        has_gap_up, gap_percent = self._detect_gap_up(df, threshold=0.010)  # 1.0% threshold (BALANCED - catch early momentum)
        if has_gap_up:
            if strategy_type == 'swing':
                # Swing: +0.8 for significant gap up
                boost += 0.8
            else:  # positional
                # Positional: +0.5 for gap up (BALANCED - moderate boost)
                boost += 0.5
        
        # 2. Volume surge boosters (STRICT - strong institutional confirmation required)
        try:
            current_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        except Exception:
            # Fallback to indicators if calculation fails
            volume_ratio = indicators.get('volume_ratio', 1.0)
        if strategy_type == 'swing':
            if volume_ratio >= 2.0:  # Strong volume surge
                boost += 0.8
            elif volume_ratio >= 1.8:  # Good volume surge
                boost += 0.4
        else:  # positional
            if volume_ratio >= 2.5:  # HIGH - 2.5x volume (very strong institutional buying)
                boost += 1.0  # Very strong volume boost
            elif volume_ratio >= 1.7:  # HIGH - 1.7x volume (good institutional confirmation)
                boost += 0.7  # Strong volume boost
        
        # 3. 10-day high breakout (BALANCED - shorter timeframe for 10-day rotation)
        if self._is_near_20_day_high(df, current_price, threshold=0.010):  # BALANCED - 1% threshold (catch early breakouts)
            if strategy_type == 'swing':
                boost += 0.5  # Breaking highs = strong momentum
            else:  # positional
                boost += 0.7  # BALANCED - important for momentum continuation
        
        # 4. ADX strength boost (STRICT - strong trends only for fast moves)
        adx = indicators.get('adx', 0)
        if strategy_type == 'swing':
            if adx >= 25:  # Strong trend
                boost += 0.3
        else:  # positional
            if adx >= 25:  # STRICT - strong trend (fast 2-3% moves)
                boost += 0.6  # Strong trend boost (increased)
            elif adx >= 22:  # STRICT - building momentum (catch early)
                boost += 0.4  # Moderate trend boost
        
        # Cap boost at 2.0 to prevent score inflation (reduced from 3.0)
        return min(boost, 2.0)
    
    def _create_signal(self, symbol: str, mtf_result: Dict, strategy_type: str, daily_df: pd.DataFrame = None) -> Dict:
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
        
        # Safety: Handle None daily_df (create empty DataFrame to prevent errors)
        if daily_df is None:
            daily_df = pd.DataFrame()

        # Safety check: entry_price must be valid
        if entry_price <= 0:
            print(f"⚠️ Invalid entry_price ({entry_price}) for {symbol}, skipping signal creation")
            return None

        # Calculate stop loss and targets based on strategy type AND signal type
        if strategy_type == 'swing':
            # SWING: Use config values with optional ATR adjustment
            from config.settings import (SWING_STOP_LOSS, USE_ATR_STOP_LOSS, 
                                        ATR_MULTIPLIER_SWING, ATR_MIN_STOP_LOSS_SWING, ATR_MAX_STOP_LOSS_SWING)
            
            # Calculate base stop loss percentage
            if USE_ATR_STOP_LOSS and indicators.get('atr', 0) > 0 and entry_price > 0:
                # ATR-based stop loss (volatility-adjusted) - SWING: Tight range
                atr = indicators['atr']
                atr_stop_pct = (atr * ATR_MULTIPLIER_SWING) / entry_price
                # Clamp between swing-specific min and max (tight for quick trades)
                stop_loss_pct = max(ATR_MIN_STOP_LOSS_SWING, min(atr_stop_pct, ATR_MAX_STOP_LOSS_SWING))
            else:
                # Fixed percentage stop loss (fallback)
                stop_loss_pct = SWING_STOP_LOSS
            
            # Use SWING_TARGETS from config (high-frequency: 1%, 2%, 3%)
            from config.settings import SWING_TARGETS
            stop_loss = entry_price * (1 - stop_loss_pct)
            targets = SWING_TARGETS  # Now: [0.01, 0.02, 0.03] for quick profits
            
            target1 = entry_price * (1 + targets[0])
            target2 = entry_price * (1 + targets[1])
            target3 = entry_price * (1 + targets[2])
        else:  # positional
            # POSITIONAL: Use strategy-specific configs with optional ATR adjustment
            from config.settings import (MEAN_REVERSION_CONFIG, MOMENTUM_CONFIG, BREAKOUT_CONFIG,
                                        USE_ATR_STOP_LOSS, ATR_MULTIPLIER_POSITIONAL, 
                                        ATR_MIN_STOP_LOSS_POSITIONAL, ATR_MAX_STOP_LOSS_POSITIONAL)
            
            if signal_type == 'MEAN_REVERSION':
                strategy_config = MEAN_REVERSION_CONFIG
            elif signal_type == 'BREAKOUT':
                strategy_config = BREAKOUT_CONFIG
            else:  # MOMENTUM
                strategy_config = MOMENTUM_CONFIG
            
            # Calculate stop loss with optional ATR adjustment
            if USE_ATR_STOP_LOSS and indicators.get('atr', 0) > 0 and entry_price > 0:
                # ATR-based stop loss (volatility-adjusted) - POSITIONAL: Wider range for proper ATR stops
                atr = indicators['atr']
                atr_stop_pct = (atr * ATR_MULTIPLIER_POSITIONAL) / entry_price
                # Clamp between positional-specific min and max (wider: 2-6% allows proper 2.5x ATR calculation)
                stop_loss_pct = max(ATR_MIN_STOP_LOSS_POSITIONAL, min(atr_stop_pct, ATR_MAX_STOP_LOSS_POSITIONAL))
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
        base_score = mtf_result.get('signal_score', 0)
        
        # 🎯 TOP GAINER SCORE BOOSTERS (Surgically added - maintains quantity, improves quality)
        # Apply boosters if daily_df is available (for gap/high detection)
        score_boost = 0.0
        if daily_df is not None and len(daily_df) >= 2:
            # Create indicators dict with current_price for booster calculation
            booster_indicators = indicators.copy()
            booster_indicators['current_price'] = entry_price
            score_boost = self._calculate_top_gainer_score_boosts(
                daily_df, 
                booster_indicators, 
                strategy_type
            )
        
        # Apply boost (cap at 10.0 max score)
        score = min(10.0, base_score + score_boost)

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
        # STRATEGY-AWARE FIX: Use correct min score for swing vs positional
        if strategy_type == 'swing':
            min_score = MIN_SWING_SIGNAL_SCORE  # 5.5 for swing
        else:  # positional
            min_score = MIN_SIGNAL_SCORE  # 7.0 for positional
        
        if score >= min_score:
            quality_multiplier = 0.5 + (score - min_score) * 0.5
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
            recommended_hold_days = 1  # ONE DAY TRADER - same day exit only (intraday, force exit at 3:25 PM)
            risk_level = 'MODERATE'
        else:  # positional
            recommended_hold_days = 30  # 10-45 days for positional - UNTOUCHED
            risk_level = 'LOW'

        # Get gap info for signal metadata
        has_gap_up, gap_percent = self._detect_gap_up(daily_df) if daily_df is not None and len(daily_df) >= 2 else (False, 0.0)
        near_20d_high = self._is_near_20_day_high(daily_df, entry_price, 0.02) if daily_df is not None and len(daily_df) >= 20 else False

        signal = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_type,
            'signal_type': mtf_result.get('signal_type', 'MOMENTUM'),
            'score': score,  # Use boosted score
            'base_score': base_score,  # Original score before boost
            'score_boost': round(score_boost, 2),  # Amount boosted
            'has_gap_up': has_gap_up,
            'gap_percent': gap_percent,
            'near_20d_high': near_20d_high,
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
                'atr': indicators.get('atr', 0),  # Include ATR for trailing stop calculations
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
