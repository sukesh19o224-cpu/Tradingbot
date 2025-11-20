"""
📊 STATISTICAL PREDICTOR V5.0
Advanced mathematical models for trade prediction and validation

Features:
- Linear Regression for trend prediction
- Z-Score normalization for signal quality
- Sharpe Ratio for risk-adjusted returns
- Kelly Criterion for optimal position sizing
- Bayesian probability scoring
- Monte Carlo simulation for confidence intervals
"""

import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
import yfinance as yf


class StatisticalPredictor:
    """
    Advanced statistical analysis for trading decisions

    Uses mathematical models to:
    1. Predict future price movement probability
    2. Calculate optimal position size
    3. Estimate confidence intervals
    4. Score trade quality using multiple statistical measures
    """

    def __init__(self):
        self.name = "STATISTICAL_PREDICTOR"
        print(f"📊 {self.name} Initialized - Advanced Math Models Loaded")

    def predict_price_trend(self, df, periods_ahead=5):
        """
        Use linear regression to predict price trend

        Returns:
            dict with predicted_return, confidence, trend_strength
        """
        try:
            if df.empty or len(df) < 20:
                return {'predicted_return': 0, 'confidence': 0, 'trend_strength': 0}

            # Prepare data for regression
            prices = df['Close'].values
            X = np.arange(len(prices)).reshape(-1, 1)
            y = prices

            # Linear regression
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)

            # Predict future prices
            future_X = np.arange(len(prices), len(prices) + periods_ahead).reshape(-1, 1)
            predicted_prices = model.predict(future_X)

            # Calculate expected return
            current_price = prices[-1]
            predicted_price = predicted_prices[-1]
            predicted_return = ((predicted_price - current_price) / current_price) * 100

            # Calculate R-squared (model confidence)
            r_squared = model.score(X, y)
            confidence = r_squared * 100  # Convert to percentage

            # Trend strength (slope coefficient)
            trend_strength = model.coef_[0]

            return {
                'predicted_return': round(predicted_return, 2),
                'confidence': round(confidence, 1),
                'trend_strength': round(trend_strength, 4),
                'r_squared': round(r_squared, 3),
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2)
            }

        except Exception as e:
            # Fallback if sklearn not available
            return self._simple_trend_prediction(df, periods_ahead)

    def _simple_trend_prediction(self, df, periods_ahead=5):
        """Simple moving average based prediction (fallback)"""
        try:
            prices = df['Close'].values
            current_price = prices[-1]

            # Simple linear fit using numpy
            X = np.arange(len(prices))
            slope, intercept = np.polyfit(X, prices, 1)

            # Predict
            future_idx = len(prices) + periods_ahead - 1
            predicted_price = slope * future_idx + intercept

            predicted_return = ((predicted_price - current_price) / current_price) * 100

            # Simple R-squared
            y_pred = slope * X + intercept
            ss_res = np.sum((prices - y_pred) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                'predicted_return': round(predicted_return, 2),
                'confidence': round(r_squared * 100, 1),
                'trend_strength': round(slope, 4),
                'r_squared': round(r_squared, 3),
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2)
            }
        except:
            return {'predicted_return': 0, 'confidence': 0, 'trend_strength': 0}

    def calculate_z_score(self, df, window=20):
        """
        Calculate Z-score to identify statistical anomalies

        Z-score > 2: Overbought (mean reversion opportunity)
        Z-score < -2: Oversold (mean reversion opportunity)

        Returns: current z-score
        """
        try:
            if len(df) < window:
                return 0

            prices = df['Close']
            rolling_mean = prices.rolling(window=window).mean()
            rolling_std = prices.rolling(window=window).std()

            current_price = prices.iloc[-1]
            current_mean = rolling_mean.iloc[-1]
            current_std = rolling_std.iloc[-1]

            if current_std == 0 or pd.isna(current_std):
                return 0

            z_score = (current_price - current_mean) / current_std

            return round(z_score, 2)
        except:
            return 0

    def calculate_sharpe_ratio(self, df, risk_free_rate=0.05):
        """
        Calculate Sharpe Ratio for risk-adjusted returns

        Sharpe > 1: Good risk-adjusted returns
        Sharpe > 2: Very good
        Sharpe > 3: Excellent

        Returns: annualized sharpe ratio
        """
        try:
            if len(df) < 20:
                return 0

            # Calculate daily returns
            returns = df['Close'].pct_change().dropna()

            if len(returns) == 0:
                return 0

            # Annualized metrics
            avg_return = returns.mean() * 252  # 252 trading days
            std_return = returns.std() * np.sqrt(252)

            if std_return == 0:
                return 0

            # Sharpe ratio
            sharpe = (avg_return - risk_free_rate) / std_return

            return round(sharpe, 2)
        except:
            return 0

    def kelly_criterion(self, win_rate, avg_win, avg_loss):
        """
        Calculate optimal position size using Kelly Criterion

        Formula: f* = (p * b - q) / b
        where:
        - p = win probability
        - q = loss probability (1 - p)
        - b = win/loss ratio

        Returns: optimal position size fraction (0-1)
        """
        try:
            if win_rate <= 0 or win_rate >= 1:
                return 0.015  # Default 1.5%

            if avg_loss == 0:
                return 0.015

            p = win_rate
            q = 1 - p
            b = abs(avg_win / avg_loss)

            kelly_fraction = (p * b - q) / b

            # Cap at 0.05 (5%) for safety - never bet more than 5% even if Kelly suggests
            kelly_fraction = max(0, min(kelly_fraction, 0.05))

            # If negative, return minimum
            if kelly_fraction <= 0:
                return 0.01  # Minimum 1%

            return round(kelly_fraction, 4)
        except:
            return 0.015  # Default fallback

    def bayesian_probability(self, prior_success, prior_failures, evidence_score):
        """
        Calculate Bayesian probability of success

        Uses historical success rate and current evidence to predict success probability

        Args:
            prior_success: Historical successful trades
            prior_failures: Historical failed trades
            evidence_score: Current opportunity score (0-100)

        Returns: probability of success (0-1)
        """
        try:
            # Prior probability (from history)
            total_prior = prior_success + prior_failures
            if total_prior == 0:
                prior_prob = 0.5  # No history = 50/50
            else:
                prior_prob = prior_success / total_prior

            # Likelihood (from evidence score)
            # Score 0-100 mapped to likelihood 0.3-0.9
            likelihood = 0.3 + (evidence_score / 100) * 0.6

            # Bayesian update
            # P(success|evidence) = P(evidence|success) * P(success) / P(evidence)
            p_evidence_given_success = likelihood
            p_evidence_given_failure = 1 - likelihood

            p_evidence = (p_evidence_given_success * prior_prob +
                         p_evidence_given_failure * (1 - prior_prob))

            if p_evidence == 0:
                return prior_prob

            posterior_prob = (p_evidence_given_success * prior_prob) / p_evidence

            return round(posterior_prob, 3)
        except:
            return 0.5  # Default 50%

    def monte_carlo_simulation(self, df, days_ahead=10, simulations=1000):
        """
        Run Monte Carlo simulation to estimate price range

        Returns:
            dict with predicted_range, confidence_90, expected_return
        """
        try:
            if len(df) < 20:
                return {'predicted_range': (0, 0), 'confidence_90': (0, 0), 'expected_return': 0}

            # Calculate daily returns
            returns = df['Close'].pct_change().dropna()

            if len(returns) == 0:
                return {'predicted_range': (0, 0), 'confidence_90': (0, 0), 'expected_return': 0}

            # Statistics
            mean_return = returns.mean()
            std_return = returns.std()
            current_price = df['Close'].iloc[-1]

            # Run simulations
            final_prices = []

            for _ in range(simulations):
                price = current_price
                for _ in range(days_ahead):
                    # Random return from normal distribution
                    daily_return = np.random.normal(mean_return, std_return)
                    price = price * (1 + daily_return)
                final_prices.append(price)

            final_prices = np.array(final_prices)

            # Calculate statistics
            expected_price = np.mean(final_prices)
            expected_return = ((expected_price - current_price) / current_price) * 100

            # 90% confidence interval (5th to 95th percentile)
            conf_90_low = np.percentile(final_prices, 5)
            conf_90_high = np.percentile(final_prices, 95)

            # Full range
            min_price = np.min(final_prices)
            max_price = np.max(final_prices)

            return {
                'expected_return': round(expected_return, 2),
                'expected_price': round(expected_price, 2),
                'predicted_range': (round(min_price, 2), round(max_price, 2)),
                'confidence_90': (round(conf_90_low, 2), round(conf_90_high, 2)),
                'current_price': round(current_price, 2)
            }
        except:
            return {'predicted_range': (0, 0), 'confidence_90': (0, 0), 'expected_return': 0}

    def calculate_risk_reward_ratio(self, entry_price, target_price, stop_loss):
        """
        Calculate risk/reward ratio

        Returns: ratio (e.g., 3.0 means 3:1 reward:risk)
        """
        try:
            potential_profit = target_price - entry_price
            potential_loss = entry_price - stop_loss

            if potential_loss <= 0:
                return 0

            ratio = potential_profit / potential_loss
            return round(ratio, 2)
        except:
            return 0

    def statistical_opportunity_score(self, symbol_ns, strategy_score):
        """
        MASTER FUNCTION: Calculate comprehensive statistical score

        Combines all statistical methods for super-validated scoring

        Args:
            symbol_ns: Stock symbol (e.g., 'RELIANCE.NS')
            strategy_score: Base score from strategy (0-100)

        Returns:
            dict with enhanced_score and statistical_metrics
        """
        try:
            # Fetch data
            ticker = yf.Ticker(symbol_ns)
            df = ticker.history(period='3mo', interval='1d')

            if df.empty or len(df) < 20:
                return {
                    'enhanced_score': strategy_score,
                    'statistical_confidence': 0,
                    'prediction_valid': False
                }

            # Run all statistical tests
            trend_pred = self.predict_price_trend(df, periods_ahead=5)
            z_score = self.calculate_z_score(df)
            sharpe = self.calculate_sharpe_ratio(df)
            monte_carlo = self.monte_carlo_simulation(df, days_ahead=10, simulations=500)

            # Calculate enhancements
            score_adjustments = 0

            # 1. Trend prediction boost
            if trend_pred['predicted_return'] > 5 and trend_pred['confidence'] > 70:
                score_adjustments += 15  # Strong predicted uptrend
            elif trend_pred['predicted_return'] > 3 and trend_pred['confidence'] > 60:
                score_adjustments += 10
            elif trend_pred['predicted_return'] > 0:
                score_adjustments += 5

            # 2. Sharpe ratio boost (risk-adjusted quality)
            if sharpe > 2:
                score_adjustments += 10  # Excellent risk-adjusted returns
            elif sharpe > 1:
                score_adjustments += 5

            # 3. Monte Carlo confidence
            mc_expected = monte_carlo.get('expected_return', 0)
            if mc_expected > 5:
                score_adjustments += 10
            elif mc_expected > 3:
                score_adjustments += 5

            # 4. Z-score penalty/boost
            if abs(z_score) > 3:
                score_adjustments -= 10  # Too extreme
            elif abs(z_score) > 2:
                score_adjustments -= 5

            # Calculate enhanced score
            enhanced_score = strategy_score + score_adjustments
            enhanced_score = max(0, min(enhanced_score, 100))  # Cap at 0-100

            # Overall statistical confidence
            stat_confidence = (
                trend_pred['confidence'] * 0.4 +
                (sharpe + 1) * 10 * 0.3 +  # Normalize sharpe to 0-100 scale
                (mc_expected + 5) * 5 * 0.3  # Normalize MC to 0-100 scale
            )
            stat_confidence = max(0, min(stat_confidence, 100))

            return {
                'enhanced_score': round(enhanced_score, 1),
                'original_score': strategy_score,
                'score_adjustment': score_adjustments,
                'statistical_confidence': round(stat_confidence, 1),
                'prediction_valid': trend_pred['confidence'] > 50,
                'metrics': {
                    'predicted_return_5d': trend_pred['predicted_return'],
                    'prediction_confidence': trend_pred['confidence'],
                    'sharpe_ratio': sharpe,
                    'z_score': z_score,
                    'monte_carlo_return_10d': mc_expected,
                    'mc_confidence_range': monte_carlo.get('confidence_90', (0, 0))
                }
            }

        except Exception as e:
            # Fallback - return original score
            return {
                'enhanced_score': strategy_score,
                'statistical_confidence': 0,
                'prediction_valid': False,
                'error': str(e)
            }


# Singleton instance
_predictor_instance = None

def get_statistical_predictor():
    """Get singleton instance of statistical predictor"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = StatisticalPredictor()
    return _predictor_instance


if __name__ == "__main__":
    print("\n🧪 Testing Statistical Predictor\n")

    predictor = StatisticalPredictor()

    # Test with a stock
    test_symbol = 'RELIANCE.NS'

    print(f"Testing {test_symbol}...\n")

    # Get data
    df = yf.Ticker(test_symbol).history(period='3mo')

    # Test trend prediction
    trend = predictor.predict_price_trend(df)
    print(f"📈 Trend Prediction (5 days):")
    print(f"   Predicted Return: {trend['predicted_return']:+.2f}%")
    print(f"   Confidence: {trend['confidence']:.1f}%")
    print(f"   Current: ₹{trend['current_price']:.2f} → Predicted: ₹{trend['predicted_price']:.2f}")

    # Test Z-score
    z = predictor.calculate_z_score(df)
    print(f"\n📊 Z-Score: {z:.2f}")
    if z > 2:
        print(f"   Status: Overbought (mean reversion down)")
    elif z < -2:
        print(f"   Status: Oversold (mean reversion up)")
    else:
        print(f"   Status: Normal range")

    # Test Sharpe
    sharpe = predictor.calculate_sharpe_ratio(df)
    print(f"\n💎 Sharpe Ratio: {sharpe:.2f}")
    if sharpe > 2:
        print(f"   Quality: Excellent")
    elif sharpe > 1:
        print(f"   Quality: Good")
    else:
        print(f"   Quality: Average")

    # Test Monte Carlo
    mc = predictor.monte_carlo_simulation(df, days_ahead=10, simulations=1000)
    print(f"\n🎲 Monte Carlo (10 days, 1000 simulations):")
    print(f"   Expected Return: {mc['expected_return']:+.2f}%")
    print(f"   90% Confidence Range: ₹{mc['confidence_90'][0]:.2f} - ₹{mc['confidence_90'][1]:.2f}")

    # Test comprehensive scoring
    print(f"\n⭐ Comprehensive Statistical Score:")
    base_score = 65  # Example base score from strategy
    result = predictor.statistical_opportunity_score(test_symbol, base_score)
    print(f"   Original Score: {result['original_score']}")
    print(f"   Enhanced Score: {result['enhanced_score']}")
    print(f"   Adjustment: {result['score_adjustment']:+.1f}")
    print(f"   Statistical Confidence: {result['statistical_confidence']:.1f}%")
    print(f"   Prediction Valid: {result['prediction_valid']}")
