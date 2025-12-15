"""
📄 PAPER TRADING SYSTEM - Virtual Portfolio with Auto-Execution
Test strategies with fake money before risking real capital
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from config.settings import *
from src.utils.trading_calendar import calculate_trading_days
from src.utils.position_sizer import PositionSizer
from src.data.enhanced_data_fetcher import EnhancedDataFetcher


class PaperTrader:
    """
    Paper trading portfolio that automatically executes signals

    Features:
    - Auto-execute all generated signals
    - Track performance in real-time
    - Compare with manual trading
    - Calculate realistic P&L
    - Position management (targets & stop loss)
    """

    def __init__(self, capital: float = None, data_file: str = None, portfolio_file: str = None):
        """
        Initialize paper trader

        Args:
            capital: Initial capital (if starting fresh)
            data_file: Path to trades history file
            portfolio_file: Path to portfolio state file
        """
        # Use provided files or defaults
        self.trades_file = data_file if data_file else 'data/trades.json'
        self.portfolio_file = portfolio_file if portfolio_file else PAPER_TRADING_FILE
        self.initial_capital = capital if capital else PAPER_TRADING_CAPITAL

        # Initialize position sizer for volatility-based sizing
        self.position_sizer = PositionSizer()

        # Load or initialize portfolio
        if os.path.exists(self.portfolio_file):
            self._load_portfolio()
        else:
            self._initialize_portfolio()

    def _initialize_portfolio(self):
        """Initialize new paper portfolio"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0
        }
        self.start_date = datetime.now().isoformat()
        self._save_portfolio()

        print(f"📄 Paper Trading initialized - Capital: ₹{self.capital:,.0f}")

    def _load_portfolio(self):
        """Load existing portfolio from file"""
        try:
            with open(self.portfolio_file, 'r') as f:
                data = json.load(f)

            self.capital = data.get('capital', self.initial_capital)
            
            # FIX: Ensure positions is always a dict (not list from old format)
            positions_data = data.get('positions', {})
            self.positions = positions_data if isinstance(positions_data, dict) else {}
            
            self.performance = data.get('performance', {})
            self.start_date = data.get('start_date', datetime.now().isoformat())

            # Load initial capital from saved data
            saved_initial = data.get('initial_capital')
            if saved_initial:
                self.initial_capital = saved_initial

            # Load trade history from separate file
            self._load_trades()

            print(f"📄 Paper Portfolio loaded - Capital: ₹{self.capital:,.0f}")

        except Exception as e:
            print(f"❌ Error loading portfolio: {e}")
            self._initialize_portfolio()

    def _load_trades(self):
        """Load trade history from separate file"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    self.trade_history = json.load(f)
            else:
                self.trade_history = []
        except Exception as e:
            print(f"❌ Error loading trades: {e}")
            self.trade_history = []

    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)

            data = {
                'capital': self.capital,
                'positions': self.positions,
                'performance': self.performance,
                'start_date': self.start_date,
                'last_updated': datetime.now().isoformat(),
                'initial_capital': self.initial_capital,
                'mode': 'PAPER_TRADING'
            }

            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving portfolio: {e}")

    def _save_trades(self):
        """Save trade history to separate file"""
        try:
            os.makedirs(os.path.dirname(self.trades_file), exist_ok=True)

            with open(self.trades_file, 'w') as f:
                json.dump(self.trade_history, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving trades: {e}")

    def _calculate_trading_charges(self, trade_value: float, is_sell: bool = False) -> float:
        """
        Calculate trading charges for a trade (Zerodha charges)
        
        Args:
            trade_value: Total value of the trade (shares * price)
            is_sell: True for sell, False for buy
            
        Returns:
            Total charges in rupees
        """
        if trade_value <= 0:
            return 0.0
        
        # Base charges (percentage-based)
        exchange_charge_rate = 0.000035  # 0.0035% exchange transaction charges
        gst_rate = 0.000008  # 18% GST on brokerage+exchange (~0.0008%)
        sebi_rate = 0.000001  # 0.0001% SEBI turnover fees
        ipft_rate = 0.000001  # 0.0001% NSE IPFT
        
        # Buy-side charges
        if not is_sell:
            stamp_duty_rate = 0.00015  # 0.015% stamp duty (buy only)
            buy_charges = trade_value * (exchange_charge_rate + gst_rate + sebi_rate + ipft_rate + stamp_duty_rate)
            return buy_charges
        
        # Sell-side charges (includes STT)
        stt_rate = 0.000125  # 0.0125% STT (sell only)
        sell_charges = trade_value * (stt_rate + exchange_charge_rate + gst_rate + sebi_rate + ipft_rate)
        return sell_charges

    def execute_signal(self, signal: Dict) -> bool:
        """
        Auto-execute a trading signal

        INTRADAY SYSTEM: Entry window restriction (9:30 AM - 2:00 PM) - matches scanning start time

        Args:
            signal: Signal dictionary from SignalGenerator

        Returns:
            bool: True if executed successfully
        """
        if not PAPER_TRADING_AUTO_EXECUTE:
            return False

        try:
            symbol = signal['symbol']
            strategy = signal.get('strategy', 'positional')
            
            # INTRADAY ENTRY WINDOW CHECK (For swing/intraday ONLY, not positional)
            if strategy == 'swing':
                from config.settings import INTRADAY_ENTRY_CUTOFF_TIME
                import pytz
                # Note: datetime is already imported at top of file (line 8)
                
                IST = pytz.timezone('Asia/Kolkata')
                current_time_ist = datetime.now(IST)
                current_hour = current_time_ist.hour
                current_minute = current_time_ist.minute
                current_time_str = f"{current_hour:02d}:{current_minute:02d}"
                
                # Check if market is open (9:30 AM - 3:30 PM) - matches scanning start time
                market_open = current_time_str >= "09:30" and current_time_str < "15:30"
                
                # Check if entry window has passed (after 2:00 PM) - ONLY for swing/intraday
                if market_open and current_time_str >= INTRADAY_ENTRY_CUTOFF_TIME:
                    print(f"⏰ INTRADAY: Entry window closed (after {INTRADAY_ENTRY_CUTOFF_TIME}) - Skipping {symbol} (swing only)")
                    return False

            # Don't buy if already holding
            if symbol in self.positions:
                print(f"📄 Already holding {symbol}, skipping")
                return False

            # CRITICAL FIX: Prevent re-entering stocks that just lost money (blacklist)
            # For swing trades: Don't re-enter a stock that lost >1% in the last 24 hours
            if strategy == 'swing':
                from datetime import timedelta
                recent_cutoff = datetime.now() - timedelta(hours=24)
                
                # Check recent trades for this symbol
                recent_losing_trades = [
                    t for t in self.trade_history
                    if t.get('symbol') == symbol
                    and t.get('exit_date')
                    and datetime.fromisoformat(t.get('exit_date', '')) >= recent_cutoff
                    and t.get('pnl_percent', 0) < -0.01  # Lost more than 1%
                ]
                
                if recent_losing_trades:
                    worst_loss = min(t.get('pnl_percent', 0) for t in recent_losing_trades)
                    print(f"🚫 {symbol} blacklisted - Lost {worst_loss:.2f}% in last 24 hours (swing protection)")
                    return False

            # CRITICAL FIX #1: Enforce MAX_POSITIONS limit
            # BUT: Allow replacement if signal is high quality
            if len(self.positions) >= MAX_POSITIONS:
                # Try to exit weakest position if new signal is high quality
                if self._try_smart_replacement(signal):
                    print(f"📄 Replaced weak position for high-quality signal {symbol}")
                else:
                    print(f"📄 Max positions ({MAX_POSITIONS}) reached, skipping {symbol}")
                    return False

            # Calculate position size (Kelly Criterion based + quality multiplier)
            position_size = self._calculate_position_size(signal)

            # Extra safety for swing (intraday) trades:
            # Don't commit 100% of free capital to product value because we also need
            # a *little* buffer for trading charges. Otherwise, for very large
            # positions capital could go slightly negative by a few rupees.
            strategy_for_sizing = signal.get('strategy', 'positional')
            if strategy_for_sizing == 'swing' and self.capital > 0:
                # Buy‑side charges are ~0.02% of trade value.
                # Limiting notional to capital / 1.0002 guarantees we always have
                # enough to cover charges as well.
                max_notional_with_charges = self.capital / 1.0002
                if position_size > max_notional_with_charges:
                    position_size = max_notional_with_charges

            if position_size <= 0:
                # Try to exit weakest position if new signal is high quality
                if self._try_smart_replacement(signal):
                    print(f"📄 Freed capital by exiting weak position for {symbol}")
                    # Recalculate position size after freeing capital
                    position_size = self._calculate_position_size(signal)
                    if position_size <= 0:
                        print(f"📄 Still insufficient capital for {symbol}")
                        return False
                else:
                    print(f"📄 Insufficient capital for {symbol}")
                    return False

            entry_price = signal.get('entry_price', 0)
            
            # Safety check: entry_price must be valid
            if entry_price <= 0:
                print(f"⚠️ Invalid entry_price ({entry_price}) for {symbol}, cannot execute")
                return False
            
            shares = int(position_size / entry_price)

            if shares <= 0:
                print(f"📄 Cannot afford even 1 share of {symbol}")
                return False

            # CRITICAL FIX: Ensure minimum viable position size (not just 1 share when capital is low)
            # For intraday/swing: Minimum 2 shares or minimum ₹500 position value
            strategy = signal.get('strategy', 'positional')
            if strategy == 'swing':
                min_position_value = 500  # Minimum ₹500 position for intraday
                min_shares = 2  # Minimum 2 shares
                
                if shares < min_shares:
                    # Try to get at least min_shares if capital allows
                    min_cost = min_shares * entry_price
                    if min_cost <= self.capital:
                        shares = min_shares
                        print(f"   💡 Adjusted to minimum {min_shares} shares for viable position")
                    else:
                        print(f"📄 Cannot afford minimum {min_shares} shares of {symbol} (need ₹{min_cost:.2f}, have ₹{self.capital:.2f})")
                        return False
                
                # Ensure minimum position value
                cost = shares * entry_price
                if cost < min_position_value and self.capital >= min_position_value:
                    # Try to increase shares to meet minimum value
                    shares_for_min_value = int(min_position_value / entry_price)
                    if shares_for_min_value > shares and shares_for_min_value * entry_price <= self.capital:
                        shares = shares_for_min_value
                        print(f"   💡 Adjusted to {shares} shares to meet minimum ₹{min_position_value} position value")
            
            cost = shares * entry_price

            # FIX: Update signal with ACTUAL shares and position_size for Discord alerts
            # This ensures Discord shows what was actually bought, not theoretical calculation
            # CRITICAL: Only set these AFTER successful execution to prevent false alerts
            signal['shares'] = shares
            signal['position_size'] = round(cost, 2)
            signal['executed'] = True  # Mark as executed to prevent duplicate alerts

            # Calculate and deduct trading charges (ONLY for swing trades)
            strategy = signal.get('strategy', 'positional')
            buy_charges = 0.0
            if strategy == 'swing':
                buy_charges = self._calculate_trading_charges(cost, is_sell=False)
                # Store charges in position for tracking
                position_charges_key = 'buy_charges'
            else:
                position_charges_key = None

            # Deduct capital (cost + charges for swing)
            self.capital -= (cost + buy_charges)

            # Determine default max holding days based on strategy
            strategy = signal.get('strategy', 'unknown')
            if strategy == 'swing':
                default_max_days = 1  # Swing trades: ONE DAY TRADER (intraday only - same day exits, force exit at 3:25 PM)
            elif strategy == 'positional':
                default_max_days = 15  # Positional trades: 15 trading days (~3 weeks) - FAST PROFIT
            else:
                default_max_days = 15  # Unknown strategy: conservative default

            # Get ATR from signal indicators (for trailing stop calculation)
            indicators = signal.get('indicators', {})
            atr = indicators.get('atr', 0)
            
            # Add position
            position_data = {
                'symbol': symbol,
                'shares': shares,
                'initial_shares': shares,  # Track initial shares for partial exit tracking
                'entry_price': entry_price,
                'entry_date': datetime.now().isoformat(),
                'trade_type': signal['trade_type'],
                'target1': signal['target1'],
                'target2': signal['target2'],
                'target3': signal['target3'],
                'stop_loss': signal['stop_loss'],
                'initial_stop_loss': signal['stop_loss'],  # Store initial stop for trailing calculations
                'atr': atr,  # Store ATR for trailing stop calculations
                'score': signal['score'],
                'cost': cost,
                'max_holding_days': signal.get('max_holding_days', default_max_days),
                'strategy': signal.get('strategy', 'unknown'),
                'signal_type': signal.get('signal_type', 'MOMENTUM'),  # MEAN_REVERSION, MOMENTUM, or BREAKOUT
                # FIX: Track which targets have been hit to prevent duplicate exits
                't1_hit': False,
                't2_hit': False,
                't3_hit': False,
                # Trailing stop flags
                'breakeven_active': False,
                'trailing_active': False
            }
            
            # Store buy charges for swing trades only
            if strategy == 'swing' and buy_charges > 0:
                position_data['buy_charges'] = buy_charges
            
            self.positions[symbol] = position_data

            self._save_portfolio()
            # No need to save trades here - no trade completed yet

            print(f"📄 PAPER BUY: {symbol} x{shares} @ ₹{entry_price:.2f} = ₹{cost:,.0f}")
            print(f"   Remaining Capital: ₹{self.capital:,.0f}")

            return True

        except Exception as e:
            print(f"❌ Error executing signal: {e}")
            return False

    def check_exits(self, current_prices: Dict[str, float]) -> tuple[List[Dict], List[Dict]]:
        """
        Check if any positions should be exited

        CRITICAL FIX #3: Exit priority corrected
        1. Check TARGETS first (lock in profits)
        2. Check STOP LOSS second (cut losses)
        3. Check TIME last (only if not profitable)

        NEW FEATURE: Trailing stops to lock in profits

        Args:
            current_prices: Dict mapping symbol to current price

        Returns:
            Tuple of (exit notifications, trailing stop activations)
        """
        exits = []
        trailing_activations = []

        for symbol, position in list(self.positions.items()):
            current_price = current_prices.get(symbol, 0)

            if current_price == 0:
                continue

            entry_price = position['entry_price']
            shares = position['shares']
            
            # CRITICAL FIX: Check STOP LOSS FIRST (before any other logic)
            # This prevents positions from losing more than the stop loss amount
            # Priority 0: STOP LOSS (MUST CHECK FIRST - before trailing stops or targets)
            if current_price <= position['stop_loss']:
                exit_info = self._exit_position(
                    symbol, current_price, 'STOP_LOSS', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)
                continue  # Position closed - don't process further

            # HYBRID TRAILING STOP (Breakeven + ATR-based) - Lock profits surgically
            profit_pct = (current_price - entry_price) / entry_price
            initial_stop_loss = position.get('initial_stop_loss', position['stop_loss'])
            stop_loss_changed = False
            
            # Strategy-specific trailing stop thresholds
            strategy = position.get('strategy', 'positional')
            if strategy == 'swing':
                # Swing: ULTRA-TIGHT trailing to lock in profits quickly
                breakeven_threshold = 0.005  # Move to breakeven at +0.5% (protect capital quickly)
                trailing_threshold = 0.007  # Activate trailing at +0.7% (tighter than before)
            else:
                # Positional: Standard trailing
                breakeven_threshold = 0.02  # +2% (override for positional)
                trailing_threshold = 0.03  # +3% (override for positional)
            
            # Step 1: Move to breakeven (risk-free trade)
            breakeven_just_activated = False
            if profit_pct >= breakeven_threshold:
                breakeven_stop = entry_price
                if breakeven_stop > position['stop_loss']:
                    # Check if this is the first time breakeven is being activated
                    breakeven_just_activated = not position.get('breakeven_active', False)
                    position['stop_loss'] = breakeven_stop
                    # Store that breakeven is active
                    position['breakeven_active'] = True
                    stop_loss_changed = True
                    
                    # Prepare trailing stop activation info for Discord alert
                    if breakeven_just_activated:
                        trailing_activations.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'entry_price': entry_price,
                            'stop_loss': breakeven_stop,
                            'initial_stop_loss': initial_stop_loss,
                            'profit_pct': profit_pct,
                            'breakeven_active': True,
                            'trailing_active': False,
                            'atr': position.get('atr', 0)
                        })
            
            # Step 2: ATR-based trailing (adaptive to volatility)
            trailing_just_activated = False
            if profit_pct >= trailing_threshold:
                # Try to get ATR from position data (stored during entry) or calculate on-the-fly
                atr = position.get('atr', 0)
                
                if atr > 0 and USE_ATR_STOP_LOSS:
                    # ATR-based trailing: Strategy-specific multiplier
                    if strategy == 'swing':
                        # Swing: ULTRA-TIGHT trailing (0.5x ATR) to protect profits aggressively
                        swing_atr_multiplier = 0.5  # Very tight for quick profit protection
                        trailing_distance = atr * swing_atr_multiplier
                    else:
                        # Positional: Standard trailing
                        trailing_distance = atr * TRAILING_STOP_ATR_MULTIPLIER
                    atr_trailing_stop = current_price - trailing_distance
                    # Ensure trailing stop is at least at breakeven
                    trailing_stop = max(entry_price, atr_trailing_stop)
                else:
                    # Fallback: Strategy-specific fixed trailing if ATR unavailable
                    if strategy == 'swing':
                        # Swing: ULTRA-TIGHT trailing (0.5%) to lock in profits
                        swing_trailing_distance = 0.005  # 0.5% - very tight
                        trailing_stop = max(entry_price, current_price * (1 - swing_trailing_distance))
                    else:
                        # Positional: Standard trailing (wider than swing for proper trend following)
                        # Use 1.5% trailing distance for positional (wider than swing's 0.8%)
                        positional_trailing_distance = 0.015  # 1.5% - appropriate for positional trades
                        trailing_stop = max(entry_price, current_price * (1 - positional_trailing_distance))
                
                # Only raise stop loss, never lower it
                if trailing_stop > position['stop_loss']:
                    # Check if this is the first time trailing is being activated
                    trailing_just_activated = not position.get('trailing_active', False)
                    position['stop_loss'] = trailing_stop
                    position['trailing_active'] = True
                    stop_loss_changed = True
                    
                    # Prepare trailing stop activation info for Discord alert
                    if trailing_just_activated:
                        trailing_activations.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'entry_price': entry_price,
                            'stop_loss': trailing_stop,
                            'initial_stop_loss': initial_stop_loss,
                            'profit_pct': profit_pct,
                            'breakeven_active': position.get('breakeven_active', False),
                            'trailing_active': True,
                            'atr': atr
                        })
            
            # Save portfolio if stop loss was updated (batch save - more efficient)
            if stop_loss_changed:
                self._save_portfolio()

            # CRITICAL FIX #3: Check TARGETS FIRST (not time!)
            # Priority 1: Target 3 (highest profit)
            if current_price >= position['target3'] and not position.get('t3_hit', False):
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_3', full_exit=True
                )
                if exit_info:
                    exits.append(exit_info)
                    # Mark T3 as hit (position deleted on full exit, but good practice)
                    if symbol in self.positions:
                        self.positions[symbol]['t3_hit'] = True
                continue  # Move to next position

            # Priority 2: Target 2 (good profit)
            elif current_price >= position['target2'] and not position.get('t2_hit', False):
                # INTRADAY: More aggressive exit for swing (quick profit-taking)
                strategy = position.get('strategy', 'positional')
                partial_exit_pct = 0.30 if strategy == 'swing' else 0.40  # Swing/Intraday: 30% at T2 (T1 already took 70%), Positional: 40%
                exit_info = self._exit_position(
                    symbol, current_price, 'TARGET_2', partial=partial_exit_pct
                )
                if exit_info:
                    exits.append(exit_info)
                    # Adjust profit lock based on strategy
                    if strategy == 'swing':
                        # Swing: T2 is 1.5% - lock at +1.2% (most of profit secured, ultra-tight)
                        profit_lock_stop_t2 = entry_price * 1.012  # +1.2% profit locked (ultra-tight)
                    else:
                        # Positional: T2 is 7-10% - lock at +6%
                        profit_lock_stop_t2 = entry_price * 1.06  # +6% profit locked
                    
                    if symbol in self.positions and exit_info['exit_type'] == 'PARTIAL':
                        self.positions[symbol]['stop_loss'] = profit_lock_stop_t2
                        self.positions[symbol]['t2_hit'] = True  # Mark T2 as hit
                        self._save_portfolio()  # Save updated stop
                        print(f"   🔒 Stop moved to +{(profit_lock_stop_t2/entry_price - 1)*100:.1f}% (₹{profit_lock_stop_t2:.2f}) after T2 - PROFIT LOCKED!")
                # Don't continue, check other exits too

            # Priority 3: Target 1 (minimum profit)
            elif current_price >= position['target1']:
                # Check if T1 was already hit (price came back to T1 after partial exit)
                t1_already_hit = position.get('t1_hit', False)
                
                if t1_already_hit:
                    # T1 hit again after partial exit - Exit remaining shares FULLY to lock profit
                    # Rationale: Price went down, came back to T1 - better to secure profit than wait for T2
                    print(f"   💡 T1 hit again - Exiting remaining {position['shares']} shares fully to lock profit")
                    exit_info = self._exit_position(
                        symbol, current_price, 'TARGET_1_REVISIT (Full Exit)', full_exit=True
                    )
                    if exit_info:
                        exits.append(exit_info)
                    continue  # Position closed
                else:
                    # T1 hit for first time - Partial exit
                    # INTRADAY: Ultra-aggressive exit for swing (quick profit-taking)
                    strategy = position.get('strategy', 'positional')
                    partial_exit_pct = 0.70 if strategy == 'swing' else 0.30  # Swing/Intraday: 70% at T1 (lock profit quickly), Positional: 30%
                    exit_info = self._exit_position(
                        symbol, current_price, 'TARGET_1', partial=partial_exit_pct
                    )
                    if exit_info:
                        exits.append(exit_info)
                        # Adjust profit lock based on strategy
                        if strategy == 'swing':
                            # Swing: T1 is 1.0% - move to breakeven immediately (risk-free trade)
                            profit_lock_stop = entry_price * 1.002  # +0.2% profit locked (ultra-tight, risk-free)
                        else:
                            # Positional: T1 is 4-5% - lock at +3%
                            profit_lock_stop = entry_price * 1.03  # +3% profit locked
                        
                        if symbol in self.positions and exit_info['exit_type'] == 'PARTIAL':
                            self.positions[symbol]['stop_loss'] = profit_lock_stop
                            self.positions[symbol]['t1_hit'] = True  # Mark T1 as hit
                            self._save_portfolio()  # Save updated stop
                            print(f"   🔒 Stop moved to +{(profit_lock_stop/entry_price - 1)*100:.1f}% (₹{profit_lock_stop:.2f}) after T1 - PROFIT LOCKED!")
                # Don't continue, check other exits too

            # STOP LOSS already checked at the beginning (Priority 0) - removed duplicate check

            # Priority 5: INTRADAY TIME-BASED EXITS (For swing/intraday only - before market close)
            strategy = position.get('strategy', 'positional')
            if strategy == 'swing':
                # INTRADAY SYSTEM: Force close all positions before 3:30 PM
                from config.settings import (
                    INTRADAY_PROFIT_EXIT_TIME, INTRADAY_BREAKEVEN_EXIT_TIME, 
                    INTRADAY_FORCE_EXIT_TIME
                )
                import pytz
                # Note: datetime is already imported at top of file
                
                IST = pytz.timezone('Asia/Kolkata')
                current_time_ist = datetime.now(IST)
                current_hour = current_time_ist.hour
                current_minute = current_time_ist.minute
                current_time_str = f"{current_hour:02d}:{current_minute:02d}"
                
                # 3:00 PM - Exit all profitable positions (lock gains)
                if current_time_str >= INTRADAY_PROFIT_EXIT_TIME and profit_pct > 0:
                    exit_info = self._exit_position(
                        symbol, current_price, f'INTRADAY_PROFIT_EXIT (3:00 PM - Lock Gains)', full_exit=True
                    )
                    if exit_info:
                        exits.append(exit_info)
                    continue
                
                # 3:15 PM - Exit all positions at breakeven (if in small loss, max -0.5%)
                if current_time_str >= INTRADAY_BREAKEVEN_EXIT_TIME and profit_pct < 0.005:
                    # Exit at breakeven or small loss (max -0.5%)
                    if profit_pct >= -0.005:
                        exit_price_breakeven = entry_price  # Exit at breakeven
                    else:
                        exit_price_breakeven = entry_price * 0.995  # Exit at -0.5% max loss
                    
                    exit_info = self._exit_position(
                        symbol, exit_price_breakeven, f'INTRADAY_BREAKEVEN_EXIT (3:15 PM - No Overnight Risk)', full_exit=True
                    )
                    if exit_info:
                        exits.append(exit_info)
                    continue
                
                # 3:25 PM - Force exit ALL remaining positions (no overnight risk)
                if current_time_str >= INTRADAY_FORCE_EXIT_TIME:
                    exit_info = self._exit_position(
                        symbol, current_price, f'INTRADAY_FORCE_EXIT (3:25 PM - Market Close)', full_exit=True
                    )
                    if exit_info:
                        exits.append(exit_info)
                    continue
            
            # Priority 6: TIME-BASED exit (For POSITIONAL ONLY - max holding days)
            # CRITICAL FIX: Swing trades should NOT use max_holding_days check
            # Swing trades are intraday only and exit via time-based exits (3:00 PM, 3:15 PM, 3:25 PM)
            # Only positional trades should use max_holding_days
            strategy = position.get('strategy', 'positional')
            if strategy != 'swing' and 'entry_date' in position and 'max_holding_days' in position:
                try:
                    entry_date = datetime.fromisoformat(position['entry_date'])
                    # CRITICAL FIX: Use TRADING DAYS instead of calendar days
                    trading_days_held = calculate_trading_days(entry_date, datetime.now())
                    max_days = position['max_holding_days']

                    # Only exit on time if:
                    # 1. Max trading days reached AND
                    # 2. Not in profit (strategy-specific threshold)
                    profit_threshold = 0.03  # Positional: 3% (only exit if not making good profit)
                    if trading_days_held >= max_days and profit_pct < profit_threshold:
                        exit_info = self._exit_position(
                            symbol, current_price, f'MAX_HOLDING_PERIOD ({trading_days_held} trading days)', full_exit=True
                        )
                        if exit_info:
                            exits.append(exit_info)
                        continue
                except Exception as e:
                    print(f"⚠️ Error checking holding period for {symbol}: {e}")

        return exits, trailing_activations

    def _exit_position(self, symbol: str, exit_price: float, reason: str,
                      full_exit: bool = False, partial: float = 0) -> Optional[Dict]:
        """Exit position (full or partial)"""
        try:
            if symbol not in self.positions:
                return None

            position = self.positions[symbol]
            entry_price = position['entry_price']

            if partial > 0 and not full_exit:
                # CRITICAL FIX: Calculate partial exit based on ORIGINAL shares, not current shares
                # This ensures consistent exit percentages (e.g., 70% of original, not 70% of remaining)
                initial_shares = position.get('initial_shares', position['shares'])
                
                # Calculate how many shares should be sold based on ORIGINAL position
                total_shares_to_sell = int(initial_shares * partial)
                
                # Calculate how many shares have already been sold (if any)
                shares_already_sold = initial_shares - position['shares']
                
                # Calculate how many shares to sell NOW (remaining portion)
                shares_to_sell = total_shares_to_sell - shares_already_sold
                
                # Ensure we don't sell more than available
                shares_to_sell = min(shares_to_sell, position['shares'])
                
                # If we've already sold the required percentage, don't sell more
                if shares_to_sell <= 0:
                    print(f"   💡 Already exited {partial*100:.0f}% of position ({shares_already_sold}/{initial_shares} shares), skipping")
                    return None
                
                remaining_shares = position['shares'] - shares_to_sell
                
                # CRITICAL FIX: If partial exit would leave very small position (< 3 shares or < ₹500), exit FULL position instead
                # This prevents multiple tiny exits (1-2 shares) that create unnecessary trade records
                min_viable_shares = 3
                min_viable_value = 500  # Minimum ₹500 position value
                
                if shares_to_sell <= 0:
                    # Position too small for partial exit
                    print(f"   💡 Position too small for partial exit ({position['shares']} shares), exiting full position to lock profit")
                    shares_to_sell = position['shares']
                    full_exit = True
                elif remaining_shares < min_viable_shares:
                    # Remaining position would be too small (< 3 shares)
                    print(f"   💡 Partial exit would leave {remaining_shares} shares (too small), exiting full {position['shares']} shares instead")
                    shares_to_sell = position['shares']
                    full_exit = True
                elif remaining_shares * entry_price < min_viable_value:
                    # Remaining position value would be too small (< ₹500)
                    print(f"   💡 Partial exit would leave ₹{remaining_shares * entry_price:.2f} position (too small), exiting full {position['shares']} shares instead")
                    shares_to_sell = position['shares']
                    full_exit = True
                elif shares_to_sell < min_viable_shares and position['shares'] <= min_viable_shares * 2:
                    # If selling < 3 shares and total position is small (≤ 6 shares), exit full position
                    print(f"   💡 Partial exit would sell only {shares_to_sell} shares (too small), exiting full {position['shares']} shares instead")
                    shares_to_sell = position['shares']
                    full_exit = True
            else:
                # Full exit
                shares_to_sell = position['shares']

            proceeds = shares_to_sell * exit_price
            cost = shares_to_sell * entry_price
            
            # Calculate trading charges (ONLY for swing trades)
            strategy = position.get('strategy', 'positional')
            sell_charges = 0.0
            buy_charges_proportional = 0.0
            
            if strategy == 'swing':
                # Calculate sell charges
                sell_charges = self._calculate_trading_charges(proceeds, is_sell=True)
                
                # Get proportional buy charges for shares being sold
                total_buy_charges = position.get('buy_charges', 0.0)
                if total_buy_charges > 0:
                    initial_shares_for_charges = position.get('initial_shares', position.get('shares', shares_to_sell))
                    if initial_shares_for_charges > 0:
                        buy_charges_proportional = total_buy_charges * (shares_to_sell / initial_shares_for_charges)

            # Calculate net P&L (after all charges)
            total_charges = sell_charges + buy_charges_proportional
            net_proceeds = proceeds - sell_charges
            pnl = net_proceeds - (cost + buy_charges_proportional)
            pnl_percent = (exit_price - entry_price) / entry_price * 100  # Gross % for reference

            # Update capital (net proceeds after charges)
            self.capital += net_proceeds

            # CRITICAL FIX: Determine if this is a FULL exit BEFORE updating position
            # Check if we're selling ALL remaining shares (not comparing to initial_shares)
            # This ensures we correctly identify full exits even after partial exits
            is_full_exit = (shares_to_sell >= position['shares'])
            
            # CRITICAL: Save position values BEFORE deletion (for full exits)
            # These are needed for the return dict, especially for Discord alerts
            initial_stop_loss = position.get('initial_stop_loss', position.get('stop_loss', 0))
            final_stop_loss = position.get('stop_loss', 0)
            target1 = position.get('target1', 0)
            target2 = position.get('target2', 0)
            target3 = position.get('target3', 0)
            trade_type = position.get('trade_type', '')
            initial_shares = position.get('initial_shares', position['shares'])  # Save initial shares BEFORE update

            # Update position
            if is_full_exit:
                # Full exit - delete position
                remaining_shares = 0
                del self.positions[symbol]
            else:
                # Partial exit - update shares AND cost
                position['shares'] -= shares_to_sell
                remaining_shares = position['shares']  # Get remaining after update
                # Reduce cost by the cost of shares sold
                position['cost'] = position.get('cost', shares_to_sell * entry_price) - cost

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'shares': shares_to_sell,
                'entry_date': position['entry_date'],
                'exit_date': datetime.now().isoformat(),
                'pnl': pnl,  # Net P&L (after charges)
                'pnl_percent': pnl_percent,  # Gross % (for reference)
                'reason': reason,
                'trade_type': position['trade_type'],
                'signal_type': position.get('signal_type', 'MOMENTUM'),  # Save signal type for analysis
                'strategy': strategy  # Save strategy for filtering
            }
            
            # Add charges info for swing trades only
            if strategy == 'swing' and total_charges > 0:
                trade_record['trading_charges'] = round(total_charges, 2)
                trade_record['buy_charges'] = round(buy_charges_proportional, 2)
                trade_record['sell_charges'] = round(sell_charges, 2)
                trade_record['gross_proceeds'] = proceeds  # For reference
                trade_record['net_proceeds'] = net_proceeds  # After charges

            self.trade_history.append(trade_record)

            # Update performance stats
            # CRITICAL FIX: Only count FULL exits as trades (not partial exits)
            # Partial exits are just profit-taking, not separate trades
            # is_full_exit already determined above
            
            if is_full_exit:
                # Only increment trade counts for full exits
                self.performance['total_trades'] += 1

            if pnl > 0:
                self.performance['winning_trades'] += 1
                if pnl > self.performance.get('best_trade', 0):
                    self.performance['best_trade'] = pnl
            else:
                self.performance['losing_trades'] += 1
                if pnl < self.performance.get('worst_trade', 0):
                    self.performance['worst_trade'] = pnl
            
            # Always update total P&L (includes partial exits)
            self.performance['total_pnl'] += pnl

            self._save_portfolio()
            self._save_trades()  # Save trade history when trade completes

            # CRITICAL FIX: Use is_full_exit (determined BEFORE position update)
            # Don't check position['shares'] here because:
            # - If full exit: position was deleted (KeyError)
            # - If partial exit: position['shares'] was already reduced (wrong comparison)
            exit_type = 'FULL' if is_full_exit else 'PARTIAL'

            print(f"📄 PAPER EXIT ({exit_type}): {symbol} x{shares_to_sell} @ ₹{exit_price:.2f}")
            if strategy == 'swing' and total_charges > 0:
                print(f"   Charges: ₹{total_charges:.2f} (Buy: ₹{buy_charges_proportional:.2f}, Sell: ₹{sell_charges:.2f})")
                print(f"   Net P&L: ₹{pnl:+,.2f} (Gross: ₹{proceeds - cost:+,.2f}, %: {pnl_percent:+.2f}%)")
            else:
                print(f"   P&L: ₹{pnl:+,.0f} ({pnl_percent:+.2f}%)")

            # Calculate percentage of position being sold
            # initial_shares was saved BEFORE position update/deletion
            exit_percentage = (shares_to_sell / initial_shares * 100) if initial_shares > 0 else 0
            
            return {
                'symbol': symbol,
                'exit_type': exit_type,
                'exit_price': exit_price,
                'entry_price': entry_price,  # Add entry price for Discord
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'reason': reason,
                'shares': shares_to_sell,
                'shares_sold': shares_to_sell,  # Explicit field for Discord
                'remaining_shares': remaining_shares,  # For partial exits
                'initial_shares': initial_shares,  # Total shares originally bought
                'exit_percentage': exit_percentage,  # Percentage of position being sold
                'trade_type': trade_type,  # Add trade type (SWING/POSITIONAL)
                'initial_stop_loss': initial_stop_loss,  # For trailing stop display
                'stop_loss': final_stop_loss,  # Final stop loss (may be trailing)
                'target1': target1,  # Add targets for reference
                'target2': target2,
                'target3': target3,
                'is_full_exit': is_full_exit  # Add flag for reference
            }

        except Exception as e:
            print(f"❌ Error exiting position: {e}")
            return None

    def _calculate_position_size(self, signal: Dict) -> float:
        """
        Calculate position size using ADVANCED risk management

        Uses:
        - Portfolio value (not just cash) for fair sizing
        - ATR-based volatility sizing (normalize risk across stocks)
        - Drawdown-based risk reduction (reduce size during drawdowns)
        - Quality multiplier based on signal score
        """
        try:
            # Calculate portfolio value and current drawdown
            portfolio_value = self.capital + sum(p['shares'] * p['entry_price'] for p in self.positions.values())
            current_drawdown = max(0, (self.initial_capital - portfolio_value) / self.initial_capital)

            # Get historical data for ATR calculation
            df = None
            # Try to get from signal first
            if '_technical_details' in signal and 'df' in signal['_technical_details']:
                df = signal['_technical_details']['df']
            
            # If not in signal, fetch it for ATR-based sizing
            if df is None or df.empty:
                try:
                    symbol = signal.get('symbol', '')
                    if symbol:
                        # Fetch historical data for ATR calculation
                        fetcher = EnhancedDataFetcher(api_delay=0.1)
                        data_result = fetcher.get_stock_data_dual(symbol, verbose=False)
                        if data_result and data_result.get('daily') is not None:
                            df = data_result['daily']
                            if df is not None and not df.empty:
                                print(f"   📊 Fetched historical data for ATR-based position sizing")
                except Exception as e:
                    print(f"   ⚠️  Could not fetch data for ATR sizing: {e}")

            # Use advanced position sizer if we have historical data
            if df is not None and not df.empty:
                position_size = self.position_sizer.calculate_complete_position_size(
                    portfolio_value=portfolio_value,
                    available_capital=self.capital,
                    signal=signal,
                    df=df,
                    current_drawdown=current_drawdown
                )
                print(f"   ✅ Using ATR-based position sizing")
            else:
                # Fallback to simple sizing if no data available
                print(f"   ⚠️  Using fallback position sizing (no historical data)")
                position_size = self._simple_position_sizing(signal, portfolio_value, current_drawdown)

            # Don't exceed available capital
            position_size = min(position_size, self.capital)

            return position_size

        except Exception as e:
            print(f"❌ Position sizing error: {e}")
            # Fallback to simple sizing
            return self._simple_position_sizing(signal, portfolio_value, 0)

    def _simple_position_sizing(self, signal: Dict, portfolio_value: float, drawdown: float) -> float:
        """Simple fallback position sizing without ATR"""
        try:
            entry = signal['entry_price']
            stop = signal['stop_loss']
            risk_per_share = entry - stop

            if risk_per_share <= 0:
                return 0

            # Base risk
            base_risk = MAX_RISK_PER_TRADE

            # Adjust for drawdown
            if DRAWDOWN_RISK_REDUCTION_ENABLED:
                if drawdown >= DRAWDOWN_THRESHOLD_MAJOR:
                    base_risk *= 0.5
                elif drawdown >= DRAWDOWN_THRESHOLD_MINOR:
                    base_risk *= 0.75

            # Calculate position size
            max_risk_amount = portfolio_value * base_risk
            max_shares = max_risk_amount / risk_per_share
            base_position_size = min(max_shares * entry, portfolio_value * MAX_POSITION_SIZE)

            # Quality adjustment (strategy-aware)
            score = signal.get('score', 7.0)
            strategy = signal.get('strategy', 'positional')
            
            from config.settings import MIN_SIGNAL_SCORE, MIN_SWING_SIGNAL_SCORE
            min_score = MIN_SWING_SIGNAL_SCORE if strategy == 'swing' else MIN_SIGNAL_SCORE
            
            if score < min_score:
                return 0

            # Different multipliers for swing vs positional
            if strategy == 'swing':
                # Swing: 0.5x at 5.5, 0.75x at 6.0, 1.0x at 6.5, 1.25x at 7.0
                quality_multiplier = 0.5 + (score - 5.5) * 0.5
            else:
                # Positional: 0.5x at 7, 1.0x at 8, 1.5x at 9, 2.0x at 10
                quality_multiplier = 0.5 + (score - 7) * 0.5

            quality_multiplier = min(quality_multiplier, 2.0)
            return base_position_size * quality_multiplier

        except:
            return 0

    def _try_smart_replacement(self, new_signal: Dict) -> bool:
        """
        Smart P&L-based position replacement

        Exit weakest position (by P&L and score) to free capital for high-quality new signal

        Logic:
        1. Only works if new signal score >= QUALITY_REPLACEMENT_THRESHOLD (8.5)
        2. Finds weakest position considering:
           - Current P&L (loss/low profit prioritized for exit)
           - Signal score (low score prioritized for exit)
        3. Only exits if new signal is significantly better (MIN_SCORE_DIFFERENCE)

        Returns:
            True if a position was exited to free capital
        """
        # Import settings
        from config.settings import (AUTO_EXIT_WEAK_FOR_QUALITY, QUALITY_REPLACEMENT_THRESHOLD, 
                                     QUALITY_REPLACEMENT_THRESHOLD_BREAKOUT, MIN_SCORE_DIFFERENCE)

        if not AUTO_EXIT_WEAK_FOR_QUALITY:
            return False

        new_score = new_signal.get('score', 0)
        signal_type = new_signal.get('signal_type', 'UNKNOWN')

        # BREAKOUT gets lower threshold (rare but powerful)
        threshold = QUALITY_REPLACEMENT_THRESHOLD_BREAKOUT if signal_type == 'BREAKOUT' else QUALITY_REPLACEMENT_THRESHOLD

        # Only replace for high-quality signals
        if new_score < threshold:
            return False

        # Need at least one position to replace
        if len(self.positions) == 0:
            return False

        # Find weakest position by combined P&L and score ranking
        # We need current prices to calculate P&L
        from src.data.enhanced_data_fetcher import EnhancedDataFetcher
        fetcher = EnhancedDataFetcher(api_delay=0.2)

        weakest_symbol = None
        weakest_rank = float('inf')  # Lower is worse

        for symbol, position in self.positions.items():
            # Get current price
            current_price = fetcher.get_current_price(symbol)
            if current_price <= 0:
                current_price = position['entry_price']  # Fallback

            # Calculate P&L percentage
            pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100

            # Get position score
            pos_score = position.get('score', 7.0)

            # Calculate weakness rank (lower = weaker = better to exit)
            # Priority: Losing positions first, then low-profit, then low-score
            # Formula: pnl_pct (negative is bad) + score (low is bad) * 10
            # Example: -5% P&L, score 7.0 = -5 + 70 = 65
            # Example: +2% P&L, score 7.5 = 2 + 75 = 77
            # Example: -2% P&L, score 8.0 = -2 + 80 = 78
            # So losing position with low score gets lowest rank
            weakness_rank = pnl_pct + (pos_score * 10)

            if weakness_rank < weakest_rank:
                weakest_rank = weakness_rank
                weakest_symbol = symbol
                weakest_price = current_price
                weakest_score = pos_score

        # Check if new signal is significantly better than weakest position
        if weakest_symbol and (new_score >= weakest_score + MIN_SCORE_DIFFERENCE):
            # Exit the weakest position
            exit_info = self._exit_position(
                weakest_symbol,
                weakest_price,
                f'SMART_REPLACEMENT (Score: {weakest_score:.1f} → {new_score:.1f})',
                full_exit=True
            )

            if exit_info:
                print(f"   💡 Smart replacement: Exited {weakest_symbol} (Score {weakest_score:.1f}, P&L {exit_info['pnl_percent']:+.1f}%) for better signal!")
                return True

        return False

    def get_position_trading_days(self, symbol: str) -> int:
        """
        Get trading days held for a position

        Args:
            symbol: Stock symbol

        Returns:
            Number of trading days held (0 if position not found)
        """
        if symbol not in self.positions:
            return 0

        try:
            entry_date = datetime.fromisoformat(self.positions[symbol]['entry_date'])
            return calculate_trading_days(entry_date, datetime.now())
        except Exception as e:
            print(f"⚠️ Error calculating trading days for {symbol}: {e}")
            return 0

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        total = self.capital

        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position['entry_price'])
            total += position['shares'] * current_price

        return total

    def get_summary(self, current_prices: Dict[str, float] = None) -> Dict:
        """Get portfolio summary"""
        if current_prices is None:
            current_prices = {}

        # Calculate unrealized P&L
        unrealized_pnl = 0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position['entry_price'])
            unrealized_pnl += (current_price - position['entry_price']) * position['shares']

        # Total portfolio value
        portfolio_value = self.get_portfolio_value(current_prices)

        # Calculate metrics
        total_return = ((portfolio_value - self.initial_capital) / self.initial_capital * 100)

        win_rate = 0
        if self.performance['total_trades'] > 0:
            win_rate = (self.performance['winning_trades'] / self.performance['total_trades'] * 100)

        return {
            'capital': self.capital,
            'portfolio_value': portfolio_value,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': self.performance['total_pnl'],
            'total_return_percent': total_return,
            'open_positions': len(self.positions),
            'total_trades': self.performance['total_trades'],
            'winning_trades': self.performance['winning_trades'],
            'losing_trades': self.performance['losing_trades'],
            'win_rate': win_rate,
            'best_trade': self.performance.get('best_trade', 0),
            'worst_trade': self.performance.get('worst_trade', 0)
        }

    def reset(self):
        """Reset paper portfolio"""
        self._initialize_portfolio()
        print("🗑️ Paper portfolio reset")


if __name__ == "__main__":
    # Test paper trader
    print("🧪 Testing Paper Trader...")

    trader = PaperTrader()
    summary = trader.get_summary()

    print(f"\n📄 Paper Portfolio Summary:")
    print(f"   Capital: ₹{summary['capital']:,.0f}")
    print(f"   Portfolio Value: ₹{summary['portfolio_value']:,.0f}")
    print(f"   Total Return: {summary['total_return_percent']:+.2f}%")
    print(f"   Win Rate: {summary['win_rate']:.1f}%")
