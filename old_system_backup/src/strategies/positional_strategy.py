"""
📈 POSITIONAL/MONTHLY STRATEGY V5.0
For medium to long-term trades (10-45 days)

Solves the problem: Missing profits by exiting too early

Features:
- Holds positions 10-45 days (vs 3-5 days in swing)
- Focuses on quality stocks with sustainable trends
- Lower trading frequency, higher win rate target
- Different risk parameters than swing strategies
- Uses statistical prediction for entry validation
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *

# Import advanced analytics
try:
    from src.analyzers.statistical_predictor import get_statistical_predictor
    from src.analyzers.position_timeframe_classifier import get_timeframe_classifier
    ADVANCED_ANALYTICS_AVAILABLE = True
except:
    ADVANCED_ANALYTICS_AVAILABLE = False
    print("⚠️ Advanced analytics not available for Positional Strategy")

# Import caching
try:
    from src.data_collector.data_cache import get_cache
    CACHE_AVAILABLE = True
except:
    CACHE_AVAILABLE = False


class PositionalStrategy:
    """
    Positional/Monthly strategy for longer-term trades

    Entry Criteria:
    - Strong multi-month uptrend
    - Quality fundamentals (above long-term MAs)
    - Statistical prediction confirms 10+ day upside
    - Lower volatility for safer holding
    - Institutional-level volume

    Exit:
    - Targets: 8%, 15%, 25% (vs 5%, 8%, 12% in swing)
    - Stop: 10% (wider than swing)
    - Time stop: 15-30 days (dynamic based on trend)
    - NO forced day-3 or day-5 exits!
    """

    def __init__(self):
        self.name = "POSITIONAL"
        self.config = POSITIONAL if 'POSITIONAL' in globals() else self._default_config()

        if ADVANCED_ANALYTICS_AVAILABLE:
            self.predictor = get_statistical_predictor()
            self.classifier = get_timeframe_classifier()
            print(f"📈 {self.name} Strategy Initialized (with Advanced Analytics)")
        else:
            self.predictor = None
            self.classifier = None
            print(f"📈 {self.name} Strategy Initialized")

    def _default_config(self):
        """Default configuration if not in settings"""
        return {
            'MIN_UPTREND_DAYS': 20,       # Minimum days in uptrend
            'REQUIRE_MA_ALIGNMENT': True,  # Must be above MA50, MA100, MA200
            'MIN_SHARPE_RATIO': 0.5,      # Minimum risk-adjusted returns
            'MIN_PREDICTED_RETURN': 5.0,  # Minimum predicted return %
            'MIN_PREDICTION_CONFIDENCE': 60,  # Minimum prediction confidence
            'MAX_VOLATILITY': 60,          # Maximum volatility score
            'MIN_VOLUME_RATIO': 1.2,       # Volume vs average
            'TARGETS': [0.08, 0.15, 0.25], # 8%, 15%, 25%
            'STOP_LOSS': 0.10,             # 10% stop
            'MIN_HOLD_DAYS': 10,           # Minimum holding period
            'MAX_HOLD_DAYS': 45,           # Maximum holding period
            'DYNAMIC_TIME_STOP': True,     # Use dynamic time stops
        }

    def scan_opportunities(self, stock_list):
        """
        Scan for positional/monthly opportunities

        Returns: List of opportunities with scores
        """
        opportunities = []

        print(f"\n{'='*60}")
        print(f"📈 SCANNING POSITIONAL OPPORTUNITIES (10-45 DAY HOLDS)")
        print(f"{'='*60}")

        for symbol_ns in stock_list:
            result = self.analyze_stock(symbol_ns)
            if result:
                opportunities.append(result)

        # Sort by enhanced score
        opportunities.sort(key=lambda x: x.get('enhanced_score', x['score']), reverse=True)

        print(f"\n✅ Found {len(opportunities)} positional opportunities")

        # Display top 5
        if opportunities:
            print(f"\n🏆 TOP 5 POSITIONAL PLAYS:")
            for i, opp in enumerate(opportunities[:5], 1):
                enhanced = opp.get('enhanced_score', opp['score'])
                pred_ret = opp.get('predicted_return_10d', 0)
                print(f"   {i}. {opp['symbol']:12s} Score: {enhanced:3.0f}  "
                      f"Predicted: {pred_ret:+.1f}%  Hold: {opp['recommended_hold_days']}d")

        return opportunities

    def analyze_stock(self, symbol_ns):
        """
        Analyze single stock for positional setup

        More stringent criteria than swing trading
        """
        try:
            symbol = symbol_ns.replace('.NS', '')

            # Fetch data (need more history for positional)
            if CACHE_AVAILABLE:
                cache = get_cache()
                df = cache.get_data(
                    symbol_ns,
                    lambda: yf.Ticker(symbol_ns).history(period='1y', interval='1d', auto_adjust=True)
                )
            else:
                ticker = yf.Ticker(symbol_ns)
                df = ticker.history(period='1y', interval='1d')

            if df.empty or len(df) < 100:
                return None

            # Basic metrics
            price = df['Close'].iloc[-1]

            # Price filters (same as swing)
            if price < MIN_PRICE or price > MAX_PRICE:
                return None

            # Calculate comprehensive metrics
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma100 = df['Close'].rolling(100).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1] if len(df) >= 200 else ma100

            above_ma50 = price > ma50
            above_ma100 = price > ma100
            above_ma200 = price > ma200

            # Long-term momentum
            if len(df) >= 51:
                momentum_50d = ((price / df['Close'].iloc[-51]) - 1) * 100
            else:
                momentum_50d = 0

            if len(df) >= 101:
                momentum_100d = ((price / df['Close'].iloc[-101]) - 1) * 100
            else:
                momentum_100d = 0

            # Volume (institutional participation)
            avg_volume = df['Volume'].tail(50).mean()
            if avg_volume == 0 or pd.isna(avg_volume):
                return None

            volume_ratio = df['Volume'].iloc[-1] / avg_volume

            # Trend consistency
            uptrend_days = self._count_uptrend_days(df)

            # ATR for volatility
            atr_value = self._calculate_atr(df)
            atr_percent = (atr_value / price) * 100

            # ENTRY FILTERS (MORE STRINGENT)

            # Filter 1: MA Alignment (quality)
            if self.config['REQUIRE_MA_ALIGNMENT']:
                if not (above_ma50 and above_ma100):
                    return None

            # Filter 2: Long-term uptrend
            if uptrend_days < self.config['MIN_UPTREND_DAYS']:
                return None

            # Filter 3: Momentum (must be positive long-term)
            if momentum_50d < 5:  # Need at least 5% gain in 50 days
                return None

            # Filter 4: Volume (institutional interest)
            if volume_ratio < self.config['MIN_VOLUME_RATIO']:
                return None

            # ADVANCED ANALYTICS (if available)
            if ADVANCED_ANALYTICS_AVAILABLE and self.predictor and self.classifier:
                # Statistical prediction
                ticker_obj = yf.Ticker(symbol_ns)
                pred_df = ticker_obj.history(period='3mo')

                if not pred_df.empty:
                    # Get prediction
                    prediction = self.predictor.predict_price_trend(pred_df, periods_ahead=10)
                    predicted_return = prediction['predicted_return']
                    pred_confidence = prediction['confidence']

                    # Filter 5: Must have positive prediction
                    if predicted_return < self.config['MIN_PREDICTED_RETURN']:
                        return None

                    if pred_confidence < self.config['MIN_PREDICTION_CONFIDENCE']:
                        return None

                    # Get Sharpe ratio
                    sharpe = self.predictor.calculate_sharpe_ratio(pred_df)
                    if sharpe < self.config['MIN_SHARPE_RATIO']:
                        return None

                    # Get volatility profile
                    classification = self.classifier.classify_position(symbol_ns, 'POSITIONAL')
                    volatility_score = classification['metrics']['volatility_score']

                    # Filter 6: Not too volatile
                    if volatility_score > self.config['MAX_VOLATILITY']:
                        return None

                    # Get recommended holding period
                    recommended_hold_days = classification['recommended_hold_days']
                    timeframe = classification['timeframe']

                    # Only accept MEDIUM_TERM or LONG_TERM
                    if timeframe == 'SHORT_TERM':
                        return None

                else:
                    return None  # Need data for predictions

            else:
                # Fallback if no advanced analytics
                predicted_return = momentum_50d * 0.5  # Rough estimate
                pred_confidence = 50
                sharpe = 0
                volatility_score = 50
                recommended_hold_days = 20
                timeframe = 'MEDIUM_TERM'

            # SCORING (Similar to other strategies but different weights)
            score = 0

            # Long-term trend strength (max 40)
            if momentum_100d > 20:
                score += 40
            elif momentum_100d > 15:
                score += 30
            elif momentum_100d > 10:
                score += 20
            elif momentum_100d > 5:
                score += 10

            # Uptrend consistency (max 25)
            if uptrend_days > 60:
                score += 25
            elif uptrend_days > 40:
                score += 20
            elif uptrend_days > 30:
                score += 15
            elif uptrend_days > 20:
                score += 10

            # MA alignment (max 20)
            if above_ma50 and above_ma100 and above_ma200:
                score += 20
            elif above_ma50 and above_ma100:
                score += 15
            elif above_ma50:
                score += 10

            # Sharpe ratio (max 15)
            if sharpe > 2:
                score += 15
            elif sharpe > 1:
                score += 10
            elif sharpe > 0.5:
                score += 5

            # Check minimum score
            min_score = STRATEGIES.get('POSITIONAL', {}).get('min_score', 50)
            if score < min_score:
                return None

            # Apply statistical enhancement
            if ADVANCED_ANALYTICS_AVAILABLE and self.predictor:
                stat_result = self.predictor.statistical_opportunity_score(symbol_ns, score)
                enhanced_score = stat_result['enhanced_score']
                stat_confidence = stat_result['statistical_confidence']
            else:
                enhanced_score = score
                stat_confidence = 50

            return {
                'symbol': symbol,
                'strategy': 'POSITIONAL',
                'price': round(price, 2),
                'score': round(score, 0),
                'enhanced_score': round(enhanced_score, 1),
                'statistical_confidence': stat_confidence,
                'momentum_50d': round(momentum_50d, 2),
                'momentum_100d': round(momentum_100d, 2),
                'uptrend_days': uptrend_days,
                'volume_ratio': round(volume_ratio, 2),
                'above_ma50': above_ma50,
                'above_ma100': above_ma100,
                'above_ma200': above_ma200,
                'sharpe_ratio': round(sharpe, 2),
                'predicted_return_10d': round(predicted_return, 2),
                'prediction_confidence': round(pred_confidence, 1),
                'volatility_score': volatility_score,
                'timeframe_classification': timeframe,
                'recommended_hold_days': recommended_hold_days,
                'atr_value': round(atr_value, 2),
                'atr_percent': round(atr_percent, 2),
                'targets': self.config['TARGETS'],
                'stop_loss_pct': self.config['STOP_LOSS'],
                'min_hold_days': self.config['MIN_HOLD_DAYS']
            }

        except Exception as e:
            return None

    def _count_uptrend_days(self, df):
        """Count consecutive days in uptrend"""
        try:
            ma20 = df['Close'].rolling(20).mean()
            days = 0
            for i in range(len(df)-1, max(0, len(df)-100), -1):
                if not pd.isna(ma20.iloc[i]) and df['Close'].iloc[i] > ma20.iloc[i]:
                    days += 1
                else:
                    break
            return days
        except:
            return 0

    def _calculate_atr(self, df, period=14):
        """Calculate ATR"""
        try:
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean().iloc[-1]
            return atr if not pd.isna(atr) else 0
        except:
            return 0

    def calculate_position_params(self, opportunity, capital_allocated):
        """
        Calculate entry, stop, targets for positional trade
        """
        price = opportunity['price']
        atr = opportunity['atr_value']

        # Wider stop loss for longer holds
        stop_loss = price * (1 - self.config['STOP_LOSS'])

        # Targets (larger for positional)
        target1 = price * (1 + self.config['TARGETS'][0])
        target2 = price * (1 + self.config['TARGETS'][1])
        target3 = price * (1 + self.config['TARGETS'][2])

        # Position size (still risk-based but can be larger)
        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            return None

        # Use 2% risk for positional (vs 1.5% for swing) - higher quality trades
        positional_risk = 0.02
        risk_amount = capital_allocated * positional_risk
        shares = int(risk_amount / risk_per_share)

        # Check max position (can use more capital for high-quality positional)
        position_value = shares * price
        max_position = capital_allocated * 0.30  # 30% vs 25% for swing

        if position_value > max_position:
            shares = int(max_position / price)
            position_value = shares * price

        if shares <= 0:
            return None

        return {
            'symbol': opportunity['symbol'],
            'strategy': 'POSITIONAL',
            'entry_price': price,
            'shares': shares,
            'position_value': round(position_value, 2),
            'stop_loss': round(stop_loss, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2),
            'target3': round(target3, 2),
            'risk_amount': round(risk_per_share * shares, 2),
            'min_hold_days': opportunity['recommended_hold_days'],
            'timeframe': opportunity['timeframe_classification']
        }

    def check_exit_conditions(self, position, current_price, days_held):
        """
        DYNAMIC exit conditions - NO FORCED EARLY EXITS!

        Returns: (should_exit, reason, exit_price)
        """
        entry = position['entry_price']
        stop = position.get('stop_loss', entry * 0.90)

        # Stop loss
        if current_price <= stop:
            return True, 'Stop Loss', stop

        # Calculate profit/loss
        profit_pct = ((current_price - entry) / entry) * 100

        # Get recommended holding period
        min_hold = position.get('min_hold_days', 15)

        # CRITICAL: NO EARLY EXITS ON LOSSES!
        # Only exit if:
        # 1. Stop loss hit
        # 2. Target hit (handled elsewhere)
        # 3. Minimum hold period reached AND no recovery potential

        if days_held >= min_hold:
            # Check if we should extend
            if profit_pct < 0 and ADVANCED_ANALYTICS_AVAILABLE and self.classifier:
                symbol = position['symbol']
                extension = self.classifier.should_extend_holding(
                    f"{symbol}.NS",
                    days_held,
                    profit_pct
                )

                if extension['should_extend']:
                    # Extend the hold period
                    print(f"   🔄 Extending hold for {symbol}: {extension['reason']}")
                    return False, None, None  # Don't exit yet

        # Max hold (absolute limit)
        max_hold = position.get('max_hold_days', self.config['MAX_HOLD_DAYS'])
        if days_held >= max_hold:
            return True, f'Max Hold ({days_held}d)', current_price

        # Don't exit otherwise - let it develop
        return False, None, None

    def update_trailing_stop(self, position, current_price):
        """
        Conservative trailing stop for positional trades
        """
        entry = position['entry_price']
        current_stop = position.get('stop_loss', entry * 0.90)
        highest = position.get('highest_price', entry)

        # Update highest price
        if current_price > highest:
            highest = current_price
            position['highest_price'] = highest

        profit_pct = ((current_price - entry) / entry) * 100

        # Trail conservatively (larger distance than swing)
        if profit_pct >= 15:  # At T2
            new_stop = max(current_stop, highest * 0.95)  # Trail 5% below peak
        elif profit_pct >= 8:  # At T1
            new_stop = max(current_stop, highest * 0.97)  # Trail 3% below peak
        elif profit_pct >= 5:
            new_stop = max(current_stop, entry)  # Breakeven
        else:
            new_stop = current_stop

        return round(new_stop, 2)


if __name__ == "__main__":
    print("\n🧪 Testing Positional Strategy\n")

    strategy = PositionalStrategy()

    # Test stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS']

    opportunities = strategy.scan_opportunities(test_stocks)

    if opportunities:
        print("\n💡 Position Parameters for top opportunity:")
        params = strategy.calculate_position_params(opportunities[0], 100000)
        if params:
            for key, val in params.items():
                print(f"   {key}: {val}")
