"""
🎯 ENHANCED FILTERS - Improved Entry & Exit Criteria
Implements all research-backed improvements for realistic profits
"""

from typing import Dict, List
from datetime import datetime, timedelta
import pandas as pd

from config.settings import *


class EnhancedFilters:
    """
    Enhanced filtering for higher quality signals

    Features:
    - Market regime detection
    - Dynamic entry filters
    - Correlation checks
    - Time-based exits
    - Performance-based adjustments
    """

    def __init__(self):
        self.recent_trades = []
        self.sector_limits = {}

    def enhanced_entry_check(self, signal: Dict, open_positions: List[Dict]) -> Dict:
        """
        Enhanced entry criteria - ALL must pass

        Returns:
            Dict with 'approved': bool and 'reason': str
        """
        checks = {
            'score': self._check_score(signal),
            'ml_confidence': self._check_ml_confidence(signal),
            'volume': self._check_volume(signal),
            'rsi': self._check_rsi(signal),
            'trend_strength': self._check_trend_strength(signal),
            'risk_reward': self._check_risk_reward(signal),
            'correlation': self._check_correlation(signal, open_positions),
            'sector_limit': self._check_sector_limit(signal, open_positions)
        }

        # All checks must pass
        all_passed = all(check['pass'] for check in checks.values())

        failed_checks = [name for name, check in checks.items() if not check['pass']]

        return {
            'approved': all_passed,
            'checks': checks,
            'failed': failed_checks,
            'reason': ', '.join(failed_checks) if failed_checks else 'All checks passed'
        }

    def _check_score(self, signal: Dict) -> Dict:
        """Score must be ≥ 7.5 (raised from 7.0)"""
        score = signal.get('score', 0)
        return {
            'pass': score >= 7.5,
            'value': score,
            'threshold': 7.5,
            'message': f"Score: {score:.1f} (need ≥7.5)"
        }

    def _check_ml_confidence(self, signal: Dict) -> Dict:
        """ML confidence must be > 65%"""
        confidence = signal.get('ml_confidence', 0)
        return {
            'pass': confidence > 0.65,
            'value': confidence,
            'threshold': 0.65,
            'message': f"ML Confidence: {confidence*100:.0f}% (need >65%)"
        }

    def _check_volume(self, signal: Dict) -> Dict:
        """Volume must be > 1.3x average"""
        volume_ratio = signal.get('volume_ratio', 0)
        return {
            'pass': volume_ratio > 1.3,
            'value': volume_ratio,
            'threshold': 1.3,
            'message': f"Volume: {volume_ratio:.1f}x (need >1.3x)"
        }

    def _check_rsi(self, signal: Dict) -> Dict:
        """RSI must be < 75 (not overbought)"""
        rsi = signal.get('rsi', 50)
        return {
            'pass': rsi < 75,
            'value': rsi,
            'threshold': 75,
            'message': f"RSI: {rsi:.1f} (need <75)"
        }

    def _check_trend_strength(self, signal: Dict) -> Dict:
        """ADX must be > 20 (clear trend)"""
        adx = signal.get('adx', 0)
        return {
            'pass': adx > 20,
            'value': adx,
            'threshold': 20,
            'message': f"ADX: {adx:.1f} (need >20)"
        }

    def _check_risk_reward(self, signal: Dict) -> Dict:
        """Risk-Reward must be ≥ 3:1"""
        rr = signal.get('risk_reward_ratio', 0)
        return {
            'pass': rr >= 3.0,
            'value': rr,
            'threshold': 3.0,
            'message': f"R:R: {rr:.1f}:1 (need ≥3:1)"
        }

    def _check_correlation(self, signal: Dict, open_positions: List[Dict]) -> Dict:
        """Check if too correlated with existing positions"""
        # Simplified: check same sector
        symbol = signal['symbol']
        sector = self._get_sector(symbol)

        same_sector_count = sum(
            1 for pos in open_positions
            if self._get_sector(pos['symbol']) == sector
        )

        # Allow max 2 positions per sector
        return {
            'pass': same_sector_count < 2,
            'value': same_sector_count,
            'threshold': 2,
            'message': f"Sector {sector}: {same_sector_count}/2 positions"
        }

    def _check_sector_limit(self, signal: Dict, open_positions: List[Dict]) -> Dict:
        """Check sector exposure limit"""
        sector = self._get_sector(signal['symbol'])

        # Count positions in this sector
        sector_positions = [
            pos for pos in open_positions
            if self._get_sector(pos['symbol']) == sector
        ]

        # Max 40% of portfolio in one sector
        max_sector_positions = int(MAX_POSITIONS * 0.4)

        return {
            'pass': len(sector_positions) < max_sector_positions,
            'value': len(sector_positions),
            'threshold': max_sector_positions,
            'message': f"Sector limit: {len(sector_positions)}/{max_sector_positions}"
        }

    def _get_sector(self, symbol: str) -> str:
        """Get sector for a symbol"""
        # Simplified sector mapping
        from config.settings import SECTORS

        for sector, stocks in SECTORS.items():
            if symbol in stocks:
                return sector

        return 'OTHER'

    def check_time_exit(self, position: Dict, current_date: datetime) -> Dict:
        """
        Check if position should be exited based on time

        Swing: Exit after 15 days if not profitable
        Positional: Exit after 60 days if <5% profit
        """
        entry_date = datetime.fromisoformat(position['entry_date'])
        days_held = (current_date - entry_date).days

        current_price = position.get('current_price', position['entry_price'])
        pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100

        should_exit = False
        reason = ""

        if position['trade_type'] == 'SWING':
            if days_held > 15 and pnl_pct < 2:
                should_exit = True
                reason = f"TIME_EXIT: {days_held} days, {pnl_pct:.1f}% profit"

        elif position['trade_type'] == 'POSITIONAL':
            if days_held > 60 and pnl_pct < 5:
                should_exit = True
                reason = f"TIME_EXIT: {days_held} days, {pnl_pct:.1f}% profit"

        return {
            'should_exit': should_exit,
            'reason': reason,
            'days_held': days_held,
            'pnl_pct': pnl_pct
        }

    def get_dynamic_position_size(self, signal: Dict, base_size: float) -> float:
        """
        Adjust position size based on signal quality

        Args:
            signal: Signal dictionary
            base_size: Base position size (Kelly 1/4)

        Returns:
            Adjusted position size
        """
        multiplier = 1.0

        # Scale based on score
        score = signal.get('score', 7.0)
        if score >= 8.5:
            multiplier *= 1.2  # +20% for excellent signals
        elif score < 7.5:
            multiplier *= 0.8  # -20% for lower quality

        # Scale based on ML confidence
        ml_conf = signal.get('ml_confidence', 0.5)
        ml_multiplier = 0.8 + (ml_conf * 0.4)  # 0.8 to 1.2 range
        multiplier *= ml_multiplier

        # Scale based on risk-reward
        rr = signal.get('risk_reward_ratio', 2.0)
        if rr >= 4.0:
            multiplier *= 1.1  # +10% for great R:R

        # Never exceed 1.5x or go below 0.6x
        multiplier = max(0.6, min(1.5, multiplier))

        return base_size * multiplier

    def calculate_dynamic_stop(self, signal: Dict) -> float:
        """
        Calculate dynamic stop loss based on ATR

        Returns:
            Stop loss price
        """
        entry_price = signal['entry_price']
        atr = signal.get('_technical_details', {}).get('df', pd.DataFrame()).get('ATR', pd.Series([0])).iloc[-1]

        if atr == 0:
            # Fallback to fixed percentage
            if signal['trade_type'] == 'SWING':
                return entry_price * (1 - SWING_STOP_LOSS)
            else:
                return entry_price * (1 - POSITIONAL_STOP_LOSS)

        # ATR-based stop (2x ATR)
        atr_stop = entry_price - (atr * 2.0)

        # Fixed percentage stop
        if signal['trade_type'] == 'SWING':
            fixed_stop = entry_price * (1 - SWING_STOP_LOSS)
        else:
            fixed_stop = entry_price * (1 - POSITIONAL_STOP_LOSS)

        # Use wider stop (less whipsaw)
        stop = min(atr_stop, fixed_stop)

        # But never wider than 4%
        max_stop = entry_price * 0.96

        return max(stop, max_stop)

    def calculate_dynamic_targets(self, signal: Dict) -> List[float]:
        """
        Calculate dynamic targets based on signal quality and volatility

        Returns:
            List of 3 target prices
        """
        entry = signal['entry_price']
        score = signal.get('score', 7.0)

        # High quality signals get larger targets
        if score >= 8.5:
            percentages = [0.04, 0.10, 0.15]  # 4%, 10%, 15%
        elif score >= 8.0:
            percentages = [0.035, 0.09, 0.13]  # 3.5%, 9%, 13%
        else:
            # Standard targets
            if signal['trade_type'] == 'SWING':
                percentages = SWING_TARGETS
            else:
                percentages = POSITIONAL_TARGETS

        return [entry * (1 + pct) for pct in percentages]


if __name__ == "__main__":
    # Test enhanced filters
    print("🧪 Testing Enhanced Filters...")

    filters = EnhancedFilters()

    # Test signal
    test_signal = {
        'symbol': 'RELIANCE.NS',
        'score': 8.2,
        'ml_confidence': 0.72,
        'volume_ratio': 1.6,
        'rsi': 58,
        'adx': 28,
        'risk_reward_ratio': 3.5,
        'trade_type': 'SWING',
        'entry_price': 2500
    }

    result = filters.enhanced_entry_check(test_signal, [])

    print(f"\n📊 Enhanced Entry Check:")
    print(f"   Approved: {result['approved']}")
    print(f"   Reason: {result['reason']}")

    for check_name, check_result in result['checks'].items():
        status = "✅" if check_result['pass'] else "❌"
        print(f"   {status} {check_name}: {check_result['message']}")
