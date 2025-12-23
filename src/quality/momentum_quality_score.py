"""
🎯 MOMENTUM QUALITY SCORE (MQS) FRAMEWORK
Advanced quality filter for momentum trades targeting 2% returns in 3-7 days

This module evaluates momentum sustainability through:
1. Volume Quality (delivery %, volume pattern)
2. Relative Strength (vs Nifty, sector context)
3. Institutional Activity (FII/DII, bulk deals)
4. Catalyst Assessment
5. Risk Flags (earnings, resistance, etc.)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class MomentumQualityScorer:
    """
    Calculate Momentum Quality Score (MQS) for stocks
    Score range: 0-8 points
    - 7-8: High conviction (100% position size)
    - 5-6: Good setup (75% position size)
    - 3-4: Cautious (50% position size)
    - <3: Skip trade
    """

    def __init__(self):
        self.nifty_data = None
        self.sector_data = {}

    def calculate_mqs(self, symbol: str, daily_data: pd.DataFrame,
                     sector: str = None, metadata: Dict = None) -> Dict:
        """
        Calculate complete MQS for a stock

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            daily_data: DataFrame with OHLCV + delivery data
            sector: Sector name (optional)
            metadata: Additional data (FII/DII, bulk deals, etc.)

        Returns:
            Dict with MQS breakdown and recommendation
        """
        try:
            if daily_data is None or len(daily_data) < 20:
                return self._invalid_mqs("Insufficient data")

            metadata = metadata or {}

            # Component 1: Volume Quality (0-2 points)
            volume_score, volume_details = self._score_volume_quality(daily_data)

            # Component 2: Relative Strength (0-2 points)
            rs_score, rs_details = self._score_relative_strength(
                symbol, daily_data, sector
            )

            # Component 3: Institutional Activity (0-2 points)
            inst_score, inst_details = self._score_institutional_activity(
                symbol, metadata
            )

            # Component 4: Catalyst Assessment (0-2 points)
            catalyst_score, catalyst_details = self._score_catalyst(
                symbol, metadata
            )

            # Component 5: Risk Flags (negative points)
            risk_deduction, risk_flags = self._calculate_risk_flags(
                symbol, daily_data, metadata
            )

            # Calculate total MQS
            total_mqs = (volume_score + rs_score + inst_score +
                        catalyst_score - risk_deduction)

            # FALLBACK BOOST: Add bonus points when delivery data unavailable
            # but other metrics are strong (allows trading in data outage)
            from config.settings import MQS_CONFIG
            if MQS_CONFIG.get('FALLBACK_MODE_ENABLED', False):
                # Check if delivery data was unavailable
                delivery_unavailable = volume_details.get('delivery_data_source') == 'Unavailable'

                if delivery_unavailable:
                    fallback_boosts = []

                    # Boost 1: Strong Relative Strength (outperforming market)
                    if rs_score >= 1.5:  # Strong RS
                        rs_boost = MQS_CONFIG.get('FALLBACK_RS_BOOST', 0.5)
                        total_mqs += rs_boost
                        fallback_boosts.append(f'RS boost +{rs_boost}')

                    # Boost 2: High Technical Score (from metadata if available)
                    technical_score = metadata.get('score', 0)
                    if technical_score >= 8.5:  # Very high technical score
                        tech_boost = MQS_CONFIG.get('FALLBACK_TECHNICAL_BOOST', 0.5)
                        total_mqs += tech_boost
                        fallback_boosts.append(f'Tech boost +{tech_boost}')

                    if fallback_boosts:
                        logger.info(f"{symbol}: Fallback boosts applied: {', '.join(fallback_boosts)}")

            total_mqs = max(0, min(8, total_mqs))  # Clamp to 0-8

            # Determine recommendation
            recommendation = self._get_recommendation(total_mqs)
            position_size = self._get_position_size(total_mqs)

            return {
                'symbol': symbol,
                'mqs_score': round(total_mqs, 2),
                'recommendation': recommendation,
                'position_size_pct': position_size,
                'components': {
                    'volume_quality': {
                        'score': round(volume_score, 2),
                        'max': 2,
                        'details': volume_details
                    },
                    'relative_strength': {
                        'score': round(rs_score, 2),
                        'max': 2,
                        'details': rs_details
                    },
                    'institutional': {
                        'score': round(inst_score, 2),
                        'max': 2,
                        'details': inst_details
                    },
                    'catalyst': {
                        'score': round(catalyst_score, 2),
                        'max': 2,
                        'details': catalyst_details
                    },
                    'risk_flags': {
                        'deduction': round(risk_deduction, 2),
                        'flags': risk_flags
                    }
                },
                'is_valid': total_mqs >= 3,  # Minimum threshold
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating MQS for {symbol}: {e}")
            return self._invalid_mqs(str(e))

    def _score_volume_quality(self, daily_data: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Score volume quality (0-2 points)

        Components:
        1. Delivery % (0-1 point)
        2. Volume pattern - up-day vs down-day (0-1 point)

        UPDATED: Fallback scoring when delivery data unavailable
        """
        from config.settings import MQS_CONFIG

        score = 0.0
        details = {}
        delivery_data_available = False

        try:
            # 1. Delivery Percentage (last 5 days average)
            if 'delivery_pct' in daily_data.columns:
                recent_delivery = daily_data['delivery_pct'].tail(5).dropna()

                if len(recent_delivery) > 0:
                    avg_delivery = recent_delivery.mean()
                    delivery_data_available = True

                    if avg_delivery > 45:
                        score += 1.0
                        details['delivery_grade'] = 'High'
                    elif avg_delivery >= 35:
                        score += 0.5
                        details['delivery_grade'] = 'Medium'
                    else:
                        details['delivery_grade'] = 'Low'

                    details['avg_delivery_pct'] = round(avg_delivery, 2)
                    details['delivery_data_source'] = 'NSE Bhavcopy'

            # FALLBACK: If no delivery data available
            if not delivery_data_available:
                details['delivery_grade'] = 'N/A'
                details['avg_delivery_pct'] = None
                details['delivery_data_source'] = 'Unavailable'

                # Check if fallback mode enabled
                if MQS_CONFIG.get('FALLBACK_MODE_ENABLED', False):
                    # Award partial score based on volume surge
                    last_5_volume = daily_data['Volume'].tail(5).mean()
                    avg_volume_50d = daily_data['Volume'].tail(50).mean()

                    if last_5_volume > avg_volume_50d * 1.5:  # 50% volume surge
                        fallback_boost = MQS_CONFIG.get('FALLBACK_VOLUME_BOOST', 0.5)
                        score += fallback_boost
                        details['fallback_volume_score'] = fallback_boost
                        details['delivery_grade'] = 'Fallback: High Volume'
                        logger.debug(f"Fallback volume boost: +{fallback_boost} (no delivery data)")
                    else:
                        details['delivery_grade'] = 'Fallback: Normal Volume'

            # 2. Volume Pattern (last 10 days)
            last_10 = daily_data.tail(10).copy()
            last_10['price_change'] = last_10['Close'].pct_change()

            up_days = last_10[last_10['price_change'] > 0]
            down_days = last_10[last_10['price_change'] < 0]

            if len(up_days) > 0 and len(down_days) > 0:
                avg_up_volume = up_days['Volume'].mean()
                avg_down_volume = down_days['Volume'].mean()

                volume_ratio = avg_up_volume / avg_down_volume if avg_down_volume > 0 else 1.0

                if volume_ratio > 1.2:  # Up-day volume 20% higher
                    score += 1.0
                    details['volume_pattern'] = 'Up-day dominant'
                elif volume_ratio > 0.9:
                    score += 0.5
                    details['volume_pattern'] = 'Mixed'
                else:
                    details['volume_pattern'] = 'Down-day dominant'

                details['volume_ratio'] = round(volume_ratio, 2)
            else:
                details['volume_pattern'] = 'Insufficient data'
                details['volume_ratio'] = None

        except Exception as e:
            logger.error(f"Error scoring volume quality: {e}")
            details['error'] = str(e)

        return score, details

    def _score_relative_strength(self, symbol: str, daily_data: pd.DataFrame,
                                 sector: str = None) -> Tuple[float, Dict]:
        """
        Score relative strength (0-2 points)

        Components:
        1. Stock vs Nifty 50 (20-day performance) (0-1 point)
        2. Sector strength context (0-1 point)
        """
        score = 0.0
        details = {}

        try:
            # 1. Stock vs Nifty 50 (20-day)
            if len(daily_data) >= 20:
                stock_return_20d = (
                    (daily_data['Close'].iloc[-1] / daily_data['Close'].iloc[-20] - 1) * 100
                )

                # Compare with Nifty (if available)
                nifty_return_20d = self._get_nifty_return_20d()

                if nifty_return_20d is not None:
                    outperformance = stock_return_20d - nifty_return_20d

                    if outperformance > 5:
                        score += 1.0
                        details['vs_nifty_grade'] = 'Strong outperformer'
                    elif outperformance > 2:
                        score += 0.5
                        details['vs_nifty_grade'] = 'Moderate outperformer'
                    else:
                        details['vs_nifty_grade'] = 'Underperformer'

                    details['outperformance_pct'] = round(outperformance, 2)
                else:
                    # If no Nifty data, use absolute return
                    if stock_return_20d > 10:
                        score += 1.0
                        details['vs_nifty_grade'] = 'Strong absolute return'
                    elif stock_return_20d > 5:
                        score += 0.5
                        details['vs_nifty_grade'] = 'Good absolute return'
                    else:
                        details['vs_nifty_grade'] = 'Weak absolute return'

                details['stock_return_20d'] = round(stock_return_20d, 2)

            # 2. Sector Context
            if sector:
                sector_strength = self._get_sector_strength(sector)

                if sector_strength == 'strong':
                    score += 1.0
                    details['sector_context'] = 'Sector leader in strong sector'
                elif sector_strength == 'neutral':
                    score += 0.5
                    details['sector_context'] = 'Stock strong, sector neutral'
                else:
                    details['sector_context'] = 'Isolated strength (sector weak)'
            else:
                details['sector_context'] = 'Sector data N/A'

        except Exception as e:
            logger.error(f"Error scoring relative strength: {e}")
            details['error'] = str(e)

        return score, details

    def _score_institutional_activity(self, symbol: str,
                                      metadata: Dict) -> Tuple[float, Dict]:
        """
        Score institutional activity (0-2 points)

        Components:
        1. FII/DII holding trend (0-1 point)
        2. Recent bulk/block deals (0-1 point)
        """
        score = 0.0
        details = {}

        try:
            # 1. FII/DII Holding Trend
            fii_dii_data = metadata.get('fii_dii_holdings', {})
            fii_trend = fii_dii_data.get('fii_trend', 'unknown')
            dii_trend = fii_dii_data.get('dii_trend', 'unknown')

            if fii_trend == 'increasing' and dii_trend == 'increasing':
                score += 1.0
                details['fii_dii_trend'] = 'Both increasing'
            elif fii_trend == 'increasing' or dii_trend == 'increasing':
                score += 0.5
                details['fii_dii_trend'] = 'One increasing'
            else:
                details['fii_dii_trend'] = 'Flat or decreasing'

            # 2. Bulk/Block Deals
            bulk_deals = metadata.get('bulk_deals', [])

            if bulk_deals and len(bulk_deals) > 0:
                # Check if deals are at current or higher prices
                recent_deal = bulk_deals[0]
                deal_price = recent_deal.get('price', 0)
                current_price = metadata.get('current_price', 0)

                if deal_price >= current_price * 0.98:  # Within 2%
                    score += 1.0
                    details['bulk_deals'] = f'Yes - at ₹{deal_price:.2f} (near CMP)'
                else:
                    score += 0.5
                    details['bulk_deals'] = f'Yes - at ₹{deal_price:.2f} (below CMP)'
            else:
                details['bulk_deals'] = 'None in last 30 days'

        except Exception as e:
            logger.error(f"Error scoring institutional activity: {e}")
            details['error'] = str(e)

        return score, details

    def _score_catalyst(self, symbol: str, metadata: Dict) -> Tuple[float, Dict]:
        """
        Score catalyst quality (0-2 points)

        Strong catalysts: +2 (earnings beat, order win, policy support)
        Moderate catalysts: +1 (analyst upgrades, positive commentary)
        Weak/no catalyst: 0
        """
        score = 0.0
        details = {}

        try:
            catalyst_data = metadata.get('catalyst', {})
            catalyst_type = catalyst_data.get('type', 'none')
            catalyst_description = catalyst_data.get('description', 'None identified')

            if catalyst_type == 'strong':
                score = 2.0
                details['catalyst_type'] = 'Strong'
            elif catalyst_type == 'moderate':
                score = 1.0
                details['catalyst_type'] = 'Moderate'
            else:
                score = 0.0
                details['catalyst_type'] = 'Weak/None'

            details['description'] = catalyst_description

        except Exception as e:
            logger.error(f"Error scoring catalyst: {e}")
            details['error'] = str(e)
            details['catalyst_type'] = 'Unknown'
            details['description'] = 'Error fetching catalyst'

        return score, details

    def _calculate_risk_flags(self, symbol: str, daily_data: pd.DataFrame,
                             metadata: Dict) -> Tuple[float, List[str]]:
        """
        Calculate risk flag deductions

        Flags:
        - Earnings within holding period: -2
        - Stock up >15% in 5 days: -1
        - Debt-to-equity >2: -1
        - Promoter holding <30%: -0.5
        - F&O ban: -1
        - Resistance within 2%: -0.5
        """
        deduction = 0.0
        flags = []

        try:
            # 1. Earnings announcement check
            earnings_date = metadata.get('earnings_date')
            if earnings_date:
                days_to_earnings = (earnings_date - datetime.now()).days
                if 0 <= days_to_earnings <= 7:
                    deduction += 2.0
                    flags.append(f'Earnings in {days_to_earnings} days')

            # 2. Stock already up >15% in 5 days
            if len(daily_data) >= 5:
                return_5d = (daily_data['Close'].iloc[-1] /
                           daily_data['Close'].iloc[-5] - 1) * 100
                if return_5d > 15:
                    deduction += 1.0
                    flags.append(f'Already up {return_5d:.1f}% in 5 days')

            # 3. Debt-to-equity ratio
            debt_to_equity = metadata.get('debt_to_equity', 0)
            if debt_to_equity > 2:
                deduction += 1.0
                flags.append(f'High D/E ratio: {debt_to_equity:.2f}')

            # 4. Promoter holding
            promoter_holding = metadata.get('promoter_holding', 100)
            if promoter_holding < 30:
                deduction += 0.5
                flags.append(f'Low promoter holding: {promoter_holding:.1f}%')

            # 5. F&O ban
            is_fo_ban = metadata.get('fo_ban', False)
            if is_fo_ban:
                deduction += 1.0
                flags.append('Stock in F&O ban')

            # 6. Resistance check (simple - check 52-week high)
            if len(daily_data) >= 252:
                high_52w = daily_data['High'].tail(252).max()
                current_price = daily_data['Close'].iloc[-1]
                distance_to_high = ((high_52w - current_price) / current_price) * 100

                if distance_to_high <= 2:
                    deduction += 0.5
                    flags.append(f'Near 52w high (resistance at {distance_to_high:.1f}%)')

        except Exception as e:
            logger.error(f"Error calculating risk flags: {e}")
            flags.append(f'Error: {str(e)}')

        return deduction, flags

    def _get_recommendation(self, mqs_score: float) -> str:
        """Get trade recommendation based on MQS score"""
        if mqs_score >= 7:
            return 'HIGH_CONVICTION'
        elif mqs_score >= 5:
            return 'GOOD'
        elif mqs_score >= 3:
            return 'CAUTIOUS'
        else:
            return 'SKIP'

    def _get_position_size(self, mqs_score: float) -> int:
        """Get position size percentage based on MQS score"""
        if mqs_score >= 7:
            return 100
        elif mqs_score >= 5:
            return 75
        elif mqs_score >= 3:
            return 50
        else:
            return 0

    def _get_nifty_return_20d(self) -> float:
        """Get Nifty 50 20-day return (placeholder - implement with real data)"""
        # TODO: Implement Nifty data fetching
        return None

    def _get_sector_strength(self, sector: str) -> str:
        """Get sector strength classification (placeholder)"""
        # TODO: Implement sector strength analysis
        return 'neutral'

    def _invalid_mqs(self, reason: str) -> Dict:
        """Return invalid MQS result"""
        return {
            'symbol': 'UNKNOWN',
            'mqs_score': 0,
            'recommendation': 'SKIP',
            'position_size_pct': 0,
            'is_valid': False,
            'error': reason,
            'timestamp': datetime.now().isoformat()
        }


def format_mqs_output(mqs_result: Dict) -> str:
    """
    Format MQS result for display

    Returns formatted string matching the MQS output template
    """
    if not mqs_result.get('is_valid'):
        return f"STOCK: {mqs_result.get('symbol', 'UNKNOWN')}\nERROR: {mqs_result.get('error', 'Unknown error')}\n"

    components = mqs_result.get('components', {})

    output = f"""
STOCK: {mqs_result['symbol']}
MOMENTUM QUALITY SCORE BREAKDOWN:
├── Volume Quality:        {components['volume_quality']['score']:.1f}/2
│   ├── Delivery %:        {components['volume_quality']['details'].get('avg_delivery_pct', 'N/A')}% (5-day avg)
│   └── Volume Pattern:    {components['volume_quality']['details'].get('volume_pattern', 'N/A')}
├── Relative Strength:     {components['relative_strength']['score']:.1f}/2
│   ├── vs Nifty 50:       {components['relative_strength']['details'].get('outperformance_pct', components['relative_strength']['details'].get('stock_return_20d', 'N/A'))}% over 20 days
│   └── Sector Context:    {components['relative_strength']['details'].get('sector_context', 'N/A')}
├── Institutional:         {components['institutional']['score']:.1f}/2
│   ├── FII/DII Trend:     {components['institutional']['details'].get('fii_dii_trend', 'N/A')}
│   └── Bulk Deals:        {components['institutional']['details'].get('bulk_deals', 'N/A')}
├── Catalyst:              {components['catalyst']['score']:.1f}/2
│   └── Identified:        {components['catalyst']['details'].get('description', 'None')}
├── Risk Deductions:       -{components['risk_flags']['deduction']:.1f}
│   └── Flags:             {', '.join(components['risk_flags']['flags']) if components['risk_flags']['flags'] else 'None'}

TOTAL MQS:                 {mqs_result['mqs_score']:.1f}/8
RECOMMENDATION:            {mqs_result['recommendation']}
SUGGESTED POSITION:        {mqs_result['position_size_pct']}%
"""

    return output
