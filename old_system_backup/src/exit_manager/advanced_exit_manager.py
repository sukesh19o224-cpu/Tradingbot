"""
V5.5 ULTRA - Advanced Exit Manager
Handles sophisticated exit strategies to maximize profits and minimize losses
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedExitManager:
    """
    Advanced exit logic for maximizing profits:
    - Trailing stops: Lock profits as price moves up
    - Partial exits: Take profits in stages
    - Profit locks: Move stop to breakeven after threshold
    - Time-based exits: Exit stale positions
    """

    def __init__(self):
        # Trailing stop configuration
        self.TRAILING_STOP_CONFIG = {
            'enabled': True,
            'activation_profit': 0.03,  # Start trailing after 3% profit
            'trail_percentage': 0.02,    # Trail by 2% from peak
        }

        # Partial exit configuration
        self.PARTIAL_EXIT_CONFIG = {
            'enabled': True,
            'exits': [
                {'profit_target': 0.05, 'exit_percentage': 0.30},  # Exit 30% at +5%
                {'profit_target': 0.10, 'exit_percentage': 0.40},  # Exit 40% at +10%
                {'profit_target': 0.15, 'exit_percentage': 0.30},  # Exit 30% at +15%
            ]
        }

        # Profit lock configuration
        self.PROFIT_LOCK_CONFIG = {
            'enabled': True,
            'activation_profit': 0.04,   # Lock after 4% profit
            'lock_percentage': 0.01,     # Lock at +1% (breakeven + 1%)
        }

        # Time-based exit configuration
        self.TIME_EXIT_CONFIG = {
            'enabled': True,
            'max_hold_days': 50,         # Force exit after 50 days
            'stale_days': 15,            # Consider stale after 15 days
            'stale_min_movement': 0.02,  # Exit if < 2% movement in stale period
        }

        # Track position peaks and partial exits
        self.position_peaks = {}      # symbol -> highest_price
        self.partial_exit_tracking = {}  # symbol -> list of executed exit levels

    def check_exit_conditions(self, position: Dict, current_price: float) -> Dict:
        """
        Master function: Check all exit conditions for a position

        Returns:
        {
            'should_exit': bool,
            'exit_type': str (FULL/PARTIAL),
            'exit_percentage': float (0-1),
            'exit_price': float,
            'reason': str,
            'lock_profit': bool
        }
        """
        symbol = position['symbol']
        entry_price = position['entry_price']
        current_pnl_pct = (current_price - entry_price) / entry_price
        days_held = (datetime.now() - datetime.fromisoformat(position['entry_date'])).days

        # Initialize tracking
        if symbol not in self.position_peaks:
            self.position_peaks[symbol] = entry_price
        if symbol not in self.partial_exit_tracking:
            self.partial_exit_tracking[symbol] = []

        # Update peak price
        if current_price > self.position_peaks[symbol]:
            self.position_peaks[symbol] = current_price

        exit_decision = {
            'should_exit': False,
            'exit_type': 'NONE',
            'exit_percentage': 0.0,
            'exit_price': current_price,
            'reason': '',
            'lock_profit': False
        }

        # Check each exit condition (priority order)

        # 1. Partial Exits (highest priority - take profits)
        partial_exit = self._check_partial_exit(symbol, current_pnl_pct)
        if partial_exit['should_exit']:
            return partial_exit

        # 2. Trailing Stop (second priority - protect profits)
        trailing_exit = self._check_trailing_stop(symbol, current_price, entry_price, current_pnl_pct)
        if trailing_exit['should_exit']:
            return trailing_exit

        # 3. Profit Lock (third priority - move to breakeven)
        profit_lock = self._check_profit_lock(position, current_pnl_pct)
        if profit_lock['lock_profit']:
            return profit_lock

        # 4. Time-Based Exit (lowest priority - stale positions)
        time_exit = self._check_time_exit(symbol, days_held, entry_price, current_price)
        if time_exit['should_exit']:
            return time_exit

        return exit_decision

    def _check_partial_exit(self, symbol: str, current_pnl_pct: float) -> Dict:
        """Check if position should take partial profits"""
        if not self.PARTIAL_EXIT_CONFIG['enabled']:
            return {'should_exit': False}

        for exit_level in self.PARTIAL_EXIT_CONFIG['exits']:
            target = exit_level['profit_target']
            exit_pct = exit_level['exit_percentage']

            # Check if we hit this target and haven't exited at this level yet
            if current_pnl_pct >= target and target not in self.partial_exit_tracking[symbol]:
                self.partial_exit_tracking[symbol].append(target)
                logger.info(f"📊 {symbol}: Partial exit triggered at {target*100:.1f}% profit")

                return {
                    'should_exit': True,
                    'exit_type': 'PARTIAL',
                    'exit_percentage': exit_pct,
                    'exit_price': 0,  # Will be filled by caller
                    'reason': f'PARTIAL_EXIT_{int(target*100)}PCT',
                    'lock_profit': False
                }

        return {'should_exit': False}

    def _check_trailing_stop(self, symbol: str, current_price: float,
                            entry_price: float, current_pnl_pct: float) -> Dict:
        """Check trailing stop condition"""
        if not self.TRAILING_STOP_CONFIG['enabled']:
            return {'should_exit': False}

        # Only activate trailing stop after minimum profit
        if current_pnl_pct < self.TRAILING_STOP_CONFIG['activation_profit']:
            return {'should_exit': False}

        peak_price = self.position_peaks[symbol]
        drop_from_peak = (peak_price - current_price) / peak_price

        # Exit if dropped more than trail percentage from peak
        if drop_from_peak >= self.TRAILING_STOP_CONFIG['trail_percentage']:
            logger.info(f"🔻 {symbol}: Trailing stop hit - dropped {drop_from_peak*100:.1f}% from peak ₹{peak_price:.2f}")

            return {
                'should_exit': True,
                'exit_type': 'FULL',
                'exit_percentage': 1.0,
                'exit_price': current_price,
                'reason': f'TRAILING_STOP (Peak: ₹{peak_price:.2f})',
                'lock_profit': False
            }

        return {'should_exit': False}

    def _check_profit_lock(self, position: Dict, current_pnl_pct: float) -> Dict:
        """Check if stop should be moved to breakeven (profit lock)"""
        if not self.PROFIT_LOCK_CONFIG['enabled']:
            return {'should_exit': False, 'lock_profit': False}

        # Activate profit lock after threshold
        if current_pnl_pct >= self.PROFIT_LOCK_CONFIG['activation_profit']:
            # Update stop loss to breakeven + 1%
            new_stop = position['entry_price'] * (1 + self.PROFIT_LOCK_CONFIG['lock_percentage'])

            logger.info(f"🔒 {position['symbol']}: Profit lock activated - stop moved to ₹{new_stop:.2f} (+{self.PROFIT_LOCK_CONFIG['lock_percentage']*100:.1f}%)")

            return {
                'should_exit': False,
                'exit_type': 'NONE',
                'exit_percentage': 0.0,
                'exit_price': 0,
                'reason': 'PROFIT_LOCK_ACTIVATED',
                'lock_profit': True,
                'new_stop_loss': new_stop
            }

        return {'should_exit': False, 'lock_profit': False}

    def _check_time_exit(self, symbol: str, days_held: int,
                        entry_price: float, current_price: float) -> Dict:
        """Check time-based exit conditions"""
        if not self.TIME_EXIT_CONFIG['enabled']:
            return {'should_exit': False}

        # Force exit after max hold days
        if days_held >= self.TIME_EXIT_CONFIG['max_hold_days']:
            logger.info(f"⏰ {symbol}: Max hold period reached ({days_held} days)")

            return {
                'should_exit': True,
                'exit_type': 'FULL',
                'exit_percentage': 1.0,
                'exit_price': current_price,
                'reason': f'MAX_HOLD_DAYS_{days_held}',
                'lock_profit': False
            }

        # Exit stale positions with minimal movement
        if days_held >= self.TIME_EXIT_CONFIG['stale_days']:
            price_movement = abs(current_price - entry_price) / entry_price

            if price_movement < self.TIME_EXIT_CONFIG['stale_min_movement']:
                logger.info(f"🥱 {symbol}: Stale position exit - only {price_movement*100:.1f}% movement in {days_held} days")

                return {
                    'should_exit': True,
                    'exit_type': 'FULL',
                    'exit_percentage': 1.0,
                    'exit_price': current_price,
                    'reason': f'STALE_POSITION_{days_held}D',
                    'lock_profit': False
                }

        return {'should_exit': False}

    def reset_position_tracking(self, symbol: str):
        """Reset tracking when position is fully closed"""
        if symbol in self.position_peaks:
            del self.position_peaks[symbol]
        if symbol in self.partial_exit_tracking:
            del self.partial_exit_tracking[symbol]
        logger.debug(f"Reset exit tracking for {symbol}")

    def get_position_stats(self, symbol: str) -> Dict:
        """Get current exit tracking stats for a position"""
        return {
            'peak_price': self.position_peaks.get(symbol, 0),
            'partial_exits_taken': self.partial_exit_tracking.get(symbol, []),
            'trailing_active': symbol in self.position_peaks
        }

    def update_config(self, config_type: str, new_config: Dict):
        """Update exit configuration dynamically"""
        if config_type == 'trailing_stop':
            self.TRAILING_STOP_CONFIG.update(new_config)
        elif config_type == 'partial_exit':
            self.PARTIAL_EXIT_CONFIG.update(new_config)
        elif config_type == 'profit_lock':
            self.PROFIT_LOCK_CONFIG.update(new_config)
        elif config_type == 'time_exit':
            self.TIME_EXIT_CONFIG.update(new_config)

        logger.info(f"✅ Updated {config_type} configuration")
