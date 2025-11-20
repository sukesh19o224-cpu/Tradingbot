"""
V5.5 ULTRA - Advanced Risk Management
Portfolio-level risk controls and correlation analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import yfinance as yf

logger = logging.getLogger(__name__)


class AdvancedRiskManager:
    """Advanced risk management system"""

    def __init__(self, portfolio_manager):
        self.pm = portfolio_manager
        self.RISK_LIMITS = {
            'max_daily_loss_pct': 5.0,
            'max_portfolio_drawdown_pct': 15.0,
            'max_position_size_pct': 15.0,
            'max_sector_exposure_pct': 40.0,
            'max_correlation': 0.70,
            'min_diversification': 5,
        }
        self.portfolio_peak = self.pm.capital
        self.daily_start_value = self.pm.capital

    def check_risk_limits(self, opportunity: Dict, position_size: float) -> Dict:
        """Check if taking this trade violates any risk limits"""
        violations = []
        warnings = []

        if not self._check_daily_loss_limit():
            violations.append("Daily loss limit exceeded")

        if not self._check_portfolio_drawdown():
            violations.append("Portfolio drawdown limit exceeded")

        if not self._check_position_size(position_size):
            violations.append(f"Position size too large")

        return {
            'approved': len(violations) == 0,
            'violations': violations,
            'warnings': warnings
        }

    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been exceeded"""
        current_value = self._calculate_portfolio_value()
        daily_pnl_pct = (current_value - self.daily_start_value) / self.daily_start_value * 100
        return daily_pnl_pct >= -self.RISK_LIMITS['max_daily_loss_pct']

    def _check_portfolio_drawdown(self) -> bool:
        """Check portfolio drawdown from peak"""
        current_value = self._calculate_portfolio_value()
        if current_value > self.portfolio_peak:
            self.portfolio_peak = current_value
        drawdown_pct = (self.portfolio_peak - current_value) / self.portfolio_peak * 100
        return drawdown_pct <= self.RISK_LIMITS['max_portfolio_drawdown_pct']

    def _check_position_size(self, position_size: float) -> bool:
        """Check if position size is within limits"""
        portfolio_value = self._calculate_portfolio_value()
        position_pct = (position_size / portfolio_value) * 100
        return position_pct <= self.RISK_LIMITS['max_position_size_pct']

    def _calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        return self.pm.capital + sum(
            pos['quantity'] * pos['entry_price']
            for pos in self.pm.positions.values()
        )

    def reset_daily_tracking(self):
        """Reset daily tracking"""
        self.daily_start_value = self._calculate_portfolio_value()
        logger.info(f"📊 Daily risk tracking reset")

    def get_risk_summary(self) -> Dict:
        """Get current risk metrics summary"""
        portfolio_value = self._calculate_portfolio_value()
        drawdown_pct = (self.portfolio_peak - portfolio_value) / self.portfolio_peak * 100
        daily_pnl_pct = (portfolio_value - self.daily_start_value) / self.daily_start_value * 100

        return {
            'portfolio_value': portfolio_value,
            'drawdown_pct': drawdown_pct,
            'daily_pnl_pct': daily_pnl_pct,
            'num_positions': len(self.pm.positions)
        }
