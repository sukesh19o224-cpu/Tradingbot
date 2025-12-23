"""
🎯 MQS INTEGRATOR

Integrates Momentum Quality Score (MQS) with existing technical analysis system.
MQS acts as a quality filter ON TOP OF existing signals - it doesn't replace them.

Flow:
1. Existing system finds technically valid signals (0-212 points)
2. MQS evaluates TOP candidates for quality (0-8 points)
3. Final selection: Best signals with MQS ≥ 5
4. Position sizing: Adjusted by MQS score
"""

import pandas as pd
import logging
from typing import Dict, Optional, List
from datetime import datetime

from src.quality.momentum_quality_score import MomentumQualityScorer
from src.data.nse_delivery_data import get_delivery_fetcher
from src.data.nifty_data import get_nifty_fetcher

logger = logging.getLogger(__name__)


class MQSIntegrator:
    """
    Integrate MQS into existing trading system

    This adds MQS scoring as a second-pass filter without breaking existing logic
    """

    def __init__(self):
        self.mqs_scorer = MomentumQualityScorer()
        self.delivery_fetcher = get_delivery_fetcher()
        self.nifty_fetcher = get_nifty_fetcher()

        # Cache for Nifty data (refresh once per day)
        self.nifty_cache = {}
        self.nifty_cache_date = None

    def enhance_signal_with_mqs(self, symbol: str, daily_df: pd.DataFrame,
                               signal_data: Dict, sector: str = None) -> Dict:
        """
        Add MQS scoring to an existing signal

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            daily_df: Daily OHLCV DataFrame
            signal_data: Existing signal quality data from technical analysis
            sector: Sector name (optional)

        Returns:
            Enhanced signal data with MQS added
        """
        try:
            # Add delivery data to DataFrame
            enhanced_df = self._add_delivery_data(daily_df, symbol)

            # Prepare metadata for MQS
            metadata = self._prepare_metadata(symbol, daily_df, signal_data)

            # Calculate MQS
            mqs_result = self.mqs_scorer.calculate_mqs(
                symbol=symbol,
                daily_data=enhanced_df,
                sector=sector,
                metadata=metadata
            )

            # Add MQS to signal data
            signal_data['mqs'] = mqs_result
            signal_data['mqs_score'] = mqs_result.get('mqs_score', 0)
            signal_data['mqs_recommendation'] = mqs_result.get('recommendation', 'SKIP')
            signal_data['mqs_position_size'] = mqs_result.get('position_size_pct', 0)

            # Adjust final validity based on MQS
            # If MQS < 3, mark as invalid regardless of technical score
            if mqs_result.get('mqs_score', 0) < 3:
                signal_data['mqs_reject'] = True
                signal_data['mqs_reject_reason'] = 'MQS below minimum threshold (3.0)'
            else:
                signal_data['mqs_reject'] = False

            return signal_data

        except Exception as e:
            logger.error(f"Error enhancing signal with MQS for {symbol}: {e}")
            # Return original signal data if MQS fails
            signal_data['mqs'] = None
            signal_data['mqs_score'] = 0
            signal_data['mqs_recommendation'] = 'ERROR'
            signal_data['mqs_position_size'] = 75  # Default to 75% on error
            signal_data['mqs_reject'] = False
            return signal_data

    def batch_enhance_signals(self, signals: List[Dict], daily_data_cache: Dict = None) -> List[Dict]:
        """
        Enhance multiple signals with MQS in batch

        Args:
            signals: List of signal dictionaries (each with symbol, daily_df, signal_data)
            daily_data_cache: Optional cache of daily DataFrames to avoid refetching

        Returns:
            List of enhanced signals sorted by MQS score
        """
        enhanced_signals = []

        for sig in signals:
            symbol = sig.get('symbol')
            daily_df = sig.get('daily_df')
            signal_data = sig.get('signal_data', {})
            sector = sig.get('sector')

            # Skip if missing required data
            if not symbol or daily_df is None:
                continue

            # Enhance with MQS
            enhanced = self.enhance_signal_with_mqs(
                symbol=symbol,
                daily_df=daily_df,
                signal_data=signal_data,
                sector=sector
            )

            enhanced_signals.append(enhanced)

        # Sort by MQS score (highest first)
        enhanced_signals.sort(
            key=lambda x: x.get('mqs_score', 0),
            reverse=True
        )

        return enhanced_signals

    def filter_by_mqs_threshold(self, signals: List[Dict], min_mqs: float = 5.0) -> List[Dict]:
        """
        Filter signals by minimum MQS threshold

        Args:
            signals: List of enhanced signals
            min_mqs: Minimum MQS score (default: 5.0)

        Returns:
            Filtered list of signals
        """
        return [s for s in signals if s.get('mqs_score', 0) >= min_mqs]

    def _add_delivery_data(self, daily_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add delivery percentage data to DataFrame"""
        try:
            # Only fetch last 10 days of delivery data (faster)
            enhanced_df = self.delivery_fetcher.add_delivery_to_dataframe(
                daily_df.tail(30).copy(),
                symbol
            )
            return enhanced_df

        except Exception as e:
            logger.debug(f"Could not add delivery data for {symbol}: {e}")
            # Return original if delivery fetch fails
            daily_df['delivery_pct'] = None
            return daily_df

    def _prepare_metadata(self, symbol: str, daily_df: pd.DataFrame,
                         signal_data: Dict) -> Dict:
        """
        Prepare metadata dictionary for MQS calculation

        Extracts relevant data from existing signal and adds market context
        """
        metadata = {}

        try:
            # Current price
            metadata['current_price'] = signal_data.get('current_price',
                                                        daily_df['Close'].iloc[-1])

            # Technical score (for fallback boost calculation)
            metadata['score'] = signal_data.get('score', 0)

            # FII/DII holdings (placeholder - requires external data source)
            # TODO: Integrate with Screener.in or Trendlyne API
            metadata['fii_dii_holdings'] = {
                'fii_trend': 'unknown',
                'dii_trend': 'unknown'
            }

            # Bulk deals (placeholder - requires NSE bulk deal data)
            # TODO: Integrate with NSE bulk deal reports
            metadata['bulk_deals'] = []

            # Catalyst (placeholder - requires news API or manual input)
            # TODO: Integrate with news API or create manual input interface
            metadata['catalyst'] = {
                'type': 'none',
                'description': 'No catalyst identified (auto-mode)'
            }

            # Earnings date (placeholder - requires corporate actions data)
            # TODO: Integrate with NSE corporate actions calendar
            metadata['earnings_date'] = None

            # Fundamental data (if available)
            metadata['debt_to_equity'] = signal_data.get('debt_to_equity', 0)
            metadata['promoter_holding'] = signal_data.get('promoter_holding', 50)

            # F&O ban status (placeholder)
            metadata['fo_ban'] = False

        except Exception as e:
            logger.error(f"Error preparing metadata: {e}")

        return metadata

    def get_nifty_20d_return(self) -> Optional[float]:
        """Get cached Nifty 20-day return"""
        try:
            # Check cache
            today = datetime.now().date()

            if (self.nifty_cache_date == today and
                'return_20d' in self.nifty_cache):
                return self.nifty_cache['return_20d']

            # Fetch fresh data
            nifty_return = self.nifty_fetcher.get_nifty_return(days=20)

            # Cache it
            if nifty_return is not None:
                self.nifty_cache['return_20d'] = nifty_return
                self.nifty_cache_date = today

            return nifty_return

        except Exception as e:
            logger.error(f"Error getting Nifty return: {e}")
            return None


# Singleton instance
_mqs_integrator = None


def get_mqs_integrator() -> MQSIntegrator:
    """Get singleton MQS integrator"""
    global _mqs_integrator

    if _mqs_integrator is None:
        _mqs_integrator = MQSIntegrator()

    return _mqs_integrator
