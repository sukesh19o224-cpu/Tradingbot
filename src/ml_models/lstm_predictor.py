"""
🤖 LSTM PRICE PREDICTOR - Machine Learning Price Forecasting
Deep learning model for predicting future price movements
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from config.settings import *

# Try to import TensorFlow, but make it optional
try:
    from tensorflow import keras
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow not available - ML predictions disabled")


class LSTMPredictor:
    """
    LSTM Neural Network for stock price prediction

    Features:
    - Multi-feature input (price, volume, indicators)
    - Sequence-based learning (60-day lookback)
    - Confidence scoring
    - 10-day ahead predictions
    """

    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler() if TF_AVAILABLE else None
        self.is_trained = False
        self.sequence_length = LSTM_SEQUENCE_LENGTH

    def predict(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Predict future price movement

        Args:
            df: Historical OHLCV data
            indicators: Technical indicators dictionary

        Returns:
            Dict with prediction, confidence, and direction
        """
        if not TF_AVAILABLE or not LSTM_ENABLED:
            # Return statistical prediction if ML not available
            return self._statistical_prediction(df, indicators)

        if df is None or len(df) < self.sequence_length:
            return {
                'predicted_return': 0,
                'confidence': 0,
                'direction': 'UNKNOWN',
                'method': 'INSUFFICIENT_DATA'
            }

        try:
            # If model not trained, use statistical approach
            if not self.is_trained:
                return self._statistical_prediction(df, indicators)

            # TODO: Implement actual LSTM prediction
            # For now, use statistical method
            return self._statistical_prediction(df, indicators)

        except Exception as e:
            print(f"❌ LSTM prediction error: {e}")
            return self._statistical_prediction(df, indicators)

    def _statistical_prediction(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Statistical prediction based on momentum and trend

        This is used when ML is not available or not trained
        More reliable than untrained ML models
        """
        try:
            recent = df.tail(20)
            current_price = df['Close'].iloc[-1]

            # Calculate momentum-based prediction
            momentum_5d = indicators.get('momentum_5d', 0)
            momentum_20d = indicators.get('momentum_20d', 0)
            rsi = indicators.get('rsi', 50)
            adx = indicators.get('adx', 0)

            # Price trend (20-day moving average slope)
            ma_20 = recent['Close'].rolling(20).mean().iloc[-1]
            ma_5 = recent['Close'].tail(5).mean()

            trend_strength = (ma_5 - ma_20) / ma_20 * 100 if ma_20 > 0 else 0

            # Weighted prediction
            # - Recent momentum (40%)
            # - Longer momentum (30%)
            # - Trend strength (30%)
            predicted_return_10d = (
                momentum_5d * 0.4 +
                momentum_20d * 0.3 +
                trend_strength * 0.3
            )

            # Clip to realistic range (-15% to +15% for 10 days)
            predicted_return_10d = np.clip(predicted_return_10d, -15, 15)

            # Calculate confidence based on consistency of signals
            confidence = 0.5  # Base confidence

            # Increase confidence if signals align
            if momentum_5d > 0 and momentum_20d > 0 and trend_strength > 0:
                confidence += 0.2
            if rsi > 50 and rsi < 70:  # Healthy bullish zone
                confidence += 0.1
            if adx > 25:  # Strong trend
                confidence += 0.1
            if abs(momentum_5d - momentum_20d) < 2:  # Consistent momentum
                confidence += 0.1

            confidence = min(confidence, 0.95)  # Cap at 95%

            # Determine direction
            if predicted_return_10d > 2:
                direction = 'BULLISH'
            elif predicted_return_10d < -2:
                direction = 'BEARISH'
            else:
                direction = 'NEUTRAL'

            return {
                'predicted_return': round(predicted_return_10d, 2),
                'confidence': round(confidence, 2),
                'direction': direction,
                'method': 'STATISTICAL',
                'components': {
                    'momentum_5d': momentum_5d,
                    'momentum_20d': momentum_20d,
                    'trend_strength': trend_strength
                }
            }

        except Exception as e:
            print(f"❌ Statistical prediction error: {e}")
            return {
                'predicted_return': 0,
                'confidence': 0.3,
                'direction': 'UNKNOWN',
                'method': 'ERROR'
            }

    def _prepare_features(self, df: pd.DataFrame, indicators: Dict) -> np.ndarray:
        """Prepare feature matrix for ML model"""
        try:
            # Extract relevant features
            df_features = df[['Close', 'Volume']].copy()

            # Add technical indicators
            df_features['RSI'] = indicators.get('rsi', 50)
            df_features['MACD'] = indicators.get('macd', 0)
            df_features['ADX'] = indicators.get('adx', 0)

            # Normalize features
            scaled_features = self.scaler.fit_transform(df_features.tail(self.sequence_length))

            return scaled_features

        except Exception as e:
            print(f"❌ Feature preparation error: {e}")
            return None

    def train_model(self, historical_data: pd.DataFrame, epochs: int = 50):
        """
        Train LSTM model on historical data

        Args:
            historical_data: DataFrame with historical price data
            epochs: Number of training epochs
        """
        if not TF_AVAILABLE:
            print("⚠️ TensorFlow not available - cannot train model")
            return False

        try:
            print("🧠 Training LSTM model...")

            # TODO: Implement actual LSTM training
            # This is a placeholder for future implementation

            print("⚠️ LSTM training not implemented yet - using statistical method")
            return False

        except Exception as e:
            print(f"❌ Model training error: {e}")
            return False


class SentimentAnalyzer:
    """
    Simple sentiment analysis for news and market sentiment

    Simplified version - can be enhanced with NLP models
    """

    def __init__(self):
        self.sentiment_keywords = {
            'positive': ['bullish', 'growth', 'profit', 'rally', 'surge', 'gain', 'high', 'strong'],
            'negative': ['bearish', 'loss', 'drop', 'fall', 'decline', 'weak', 'crash', 'sell']
        }

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text

        Args:
            text: News headline or article text

        Returns:
            Dict with sentiment score and label
        """
        if not text:
            return {'score': 0, 'label': 'NEUTRAL'}

        text_lower = text.lower()

        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text_lower)

        # Calculate sentiment score (-1 to +1)
        total = positive_count + negative_count
        if total == 0:
            score = 0
        else:
            score = (positive_count - negative_count) / total

        # Determine label
        if score > 0.3:
            label = 'POSITIVE'
        elif score < -0.3:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'

        return {
            'score': round(score, 2),
            'label': label,
            'positive_words': positive_count,
            'negative_words': negative_count
        }


def test_ml_predictor():
    """Test the ML predictor module"""
    import yfinance as yf

    print("🧪 Testing ML Predictor...")

    # Fetch sample data
    ticker = yf.Ticker('RELIANCE.NS')
    df = ticker.history(period='6mo')

    if df.empty:
        print("❌ Failed to fetch data")
        return

    # Mock indicators for testing
    mock_indicators = {
        'rsi': 55,
        'macd': 0.5,
        'adx': 30,
        'momentum_5d': 3.5,
        'momentum_20d': 6.2
    }

    # Test predictor
    predictor = LSTMPredictor()
    result = predictor.predict(df, mock_indicators)

    print(f"\n✅ Prediction generated!")
    print(f"📈 Predicted 10-day Return: {result['predicted_return']:+.2f}%")
    print(f"🎯 Confidence: {result['confidence']*100:.0f}%")
    print(f"📊 Direction: {result['direction']}")
    print(f"🔧 Method: {result['method']}")

    # Test sentiment analyzer
    print(f"\n🧪 Testing Sentiment Analyzer...")
    sentiment = SentimentAnalyzer()

    test_texts = [
        "Company shows strong growth and bullish momentum",
        "Stock crashes amid bearish sentiment and losses",
        "Market remains stable with neutral outlook"
    ]

    for text in test_texts:
        result = sentiment.analyze_sentiment(text)
        print(f"   '{text[:40]}...' -> {result['label']} ({result['score']:+.2f})")


if __name__ == "__main__":
    test_ml_predictor()
