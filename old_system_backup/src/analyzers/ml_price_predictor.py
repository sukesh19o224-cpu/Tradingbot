"""
V5.5 ULTRA - Machine Learning Price Predictor
Uses LSTM/GRU neural networks for advanced price prediction
More accurate than simple linear regression
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import logging
import pickle
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from sklearn.preprocessing import MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not available - ML predictor will use fallback methods")
    TENSORFLOW_AVAILABLE = False

from sklearn.model_selection import train_test_split


class MLPricePredictor:
    """
    Advanced ML-based price prediction using LSTM/GRU networks

    Features:
    - LSTM/GRU neural networks for sequence prediction
    - Multi-feature input (price, volume, indicators)
    - Model caching and retraining
    - Confidence scoring based on prediction variance
    - Fallback to statistical methods if ML unavailable
    """

    def __init__(self, model_dir='data/ml_models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        # Model configuration
        self.SEQUENCE_LENGTH = 20  # Use 20 days of history
        self.PREDICTION_DAYS = 5   # Predict 5 days ahead
        self.MODEL_TYPE = 'LSTM'   # 'LSTM' or 'GRU'

        # Training configuration
        self.EPOCHS = 50
        self.BATCH_SIZE = 32
        self.VALIDATION_SPLIT = 0.2

        # Model cache (symbol -> model)
        self.models = {}
        self.scalers = {}
        self.last_trained = {}

        # Retraining policy
        self.RETRAIN_DAYS = 30  # Retrain every 30 days
        self.MIN_DATA_POINTS = 100  # Need at least 100 days of data

    def predict_price(self, symbol: str, df: pd.DataFrame, days_ahead: int = 5) -> Dict:
        """
        Main prediction function - uses ML if available, falls back to statistical methods

        Returns:
        {
            'predicted_return': float,      # Expected return %
            'confidence': float,            # 0-100
            'predicted_price': float,       # Predicted price
            'prediction_range': tuple,      # (low, high) with 90% confidence
            'method': str                   # 'LSTM', 'GRU', or 'FALLBACK'
        }
        """
        if len(df) < self.MIN_DATA_POINTS:
            logger.debug(f"{symbol}: Insufficient data ({len(df)} days) - using fallback")
            return self._fallback_prediction(df, days_ahead)

        if TENSORFLOW_AVAILABLE:
            try:
                return self._ml_prediction(symbol, df, days_ahead)
            except Exception as e:
                logger.warning(f"{symbol}: ML prediction failed - {e}. Using fallback")
                return self._fallback_prediction(df, days_ahead)
        else:
            return self._fallback_prediction(df, days_ahead)

    def _ml_prediction(self, symbol: str, df: pd.DataFrame, days_ahead: int) -> Dict:
        """Use LSTM/GRU neural network for prediction"""
        # Check if we need to train/retrain model
        needs_training = (
            symbol not in self.models or
            symbol not in self.last_trained or
            (datetime.now() - self.last_trained[symbol]).days >= self.RETRAIN_DAYS
        )

        if needs_training:
            logger.info(f"🧠 Training ML model for {symbol}...")
            self._train_model(symbol, df)

        # Prepare input data
        X_input = self._prepare_input(symbol, df)

        if X_input is None:
            return self._fallback_prediction(df, days_ahead)

        # Make prediction
        model = self.models[symbol]
        scaler = self.scalers[symbol]

        # Predict multiple times for confidence estimation
        predictions = []
        for _ in range(10):  # Monte Carlo dropout
            pred = model.predict(X_input, verbose=0)
            predictions.append(pred[0][0])

        # Calculate statistics
        predicted_scaled = np.mean(predictions)
        prediction_std = np.std(predictions)

        # Inverse transform to get actual price
        predicted_price = scaler.inverse_transform([[predicted_scaled]])[0][0]
        current_price = df['Close'].iloc[-1]

        # Calculate return and confidence
        predicted_return = (predicted_price - current_price) / current_price
        confidence = self._calculate_confidence(prediction_std, df)

        # Prediction range (90% confidence interval)
        lower_bound = scaler.inverse_transform([[predicted_scaled - 1.645 * prediction_std]])[0][0]
        upper_bound = scaler.inverse_transform([[predicted_scaled + 1.645 * prediction_std]])[0][0]

        logger.info(f"🎯 {symbol} ML Prediction: {predicted_return*100:+.2f}% (Confidence: {confidence:.0f}%)")

        return {
            'predicted_return': predicted_return,
            'confidence': confidence,
            'predicted_price': predicted_price,
            'prediction_range': (lower_bound, upper_bound),
            'method': self.MODEL_TYPE,
            'current_price': current_price
        }

    def _train_model(self, symbol: str, df: pd.DataFrame):
        """Train LSTM/GRU model for a specific symbol"""
        try:
            # Prepare features
            features = self._create_features(df)

            # Scale data
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(features)

            # Create sequences
            X, y = self._create_sequences(scaled_data)

            if len(X) < 50:  # Need minimum data for training
                logger.warning(f"{symbol}: Insufficient sequences for training")
                return

            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=False
            )

            # Build model
            model = self._build_model(X_train.shape[1], X_train.shape[2])

            # Train
            history = model.fit(
                X_train, y_train,
                epochs=self.EPOCHS,
                batch_size=self.BATCH_SIZE,
                validation_data=(X_test, y_test),
                verbose=0,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
                ]
            )

            # Evaluate
            train_loss = history.history['loss'][-1]
            val_loss = history.history['val_loss'][-1]

            logger.info(f"✅ {symbol} Model trained - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Save model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            self.last_trained[symbol] = datetime.now()

            # Persist to disk
            model_path = os.path.join(self.model_dir, f'{symbol}_model.h5')
            scaler_path = os.path.join(self.model_dir, f'{symbol}_scaler.pkl')

            model.save(model_path)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)

        except Exception as e:
            logger.error(f"❌ Failed to train model for {symbol}: {e}")

    def _build_model(self, sequence_length: int, n_features: int):
        """Build LSTM or GRU model architecture"""
        model = Sequential([
            # First layer
            LSTM(50, return_sequences=True, input_shape=(sequence_length, n_features))
            if self.MODEL_TYPE == 'LSTM' else
            GRU(50, return_sequences=True, input_shape=(sequence_length, n_features)),

            Dropout(0.2),

            # Second layer
            LSTM(50, return_sequences=False) if self.MODEL_TYPE == 'LSTM' else GRU(50, return_sequences=False),

            Dropout(0.2),

            # Output layer
            Dense(25, activation='relu'),
            Dense(1)  # Predict next price
        ])

        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mean_squared_error',
            metrics=['mae']
        )

        return model

    def _create_features(self, df: pd.DataFrame) -> np.ndarray:
        """Create feature matrix from dataframe"""
        features = pd.DataFrame()

        # Price features
        features['Close'] = df['Close']
        features['Returns'] = df['Close'].pct_change()
        features['High_Low'] = (df['High'] - df['Low']) / df['Close']

        # Volume features
        features['Volume'] = df['Volume']
        features['Volume_MA'] = df['Volume'].rolling(10).mean()

        # Technical indicators
        features['SMA_20'] = df['Close'].rolling(20).mean()
        features['SMA_50'] = df['Close'].rolling(50).mean()

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['RSI'] = 100 - (100 / (1 + rs))

        # Fill NaN and return
        features = features.fillna(method='bfill').fillna(0)

        return features.values

    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for time series prediction"""
        X, y = [], []

        for i in range(self.SEQUENCE_LENGTH, len(data) - self.PREDICTION_DAYS):
            X.append(data[i - self.SEQUENCE_LENGTH:i])
            y.append(data[i + self.PREDICTION_DAYS - 1, 0])  # Predict close price

        return np.array(X), np.array(y)

    def _prepare_input(self, symbol: str, df: pd.DataFrame) -> Optional[np.ndarray]:
        """Prepare the most recent data as model input"""
        try:
            features = self._create_features(df)
            scaler = self.scalers[symbol]
            scaled = scaler.transform(features)

            # Get last sequence
            X_input = scaled[-self.SEQUENCE_LENGTH:]
            X_input = X_input.reshape(1, self.SEQUENCE_LENGTH, -1)

            return X_input

        except Exception as e:
            logger.error(f"Failed to prepare input for {symbol}: {e}")
            return None

    def _calculate_confidence(self, std: float, df: pd.DataFrame) -> float:
        """Calculate prediction confidence score"""
        # Lower std = higher confidence
        base_confidence = max(0, 100 - (std * 1000))

        # Adjust based on recent volatility
        recent_volatility = df['Close'].pct_change().tail(20).std()
        volatility_penalty = min(20, recent_volatility * 1000)

        confidence = max(0, min(100, base_confidence - volatility_penalty))

        return confidence

    def _fallback_prediction(self, df: pd.DataFrame, days_ahead: int) -> Dict:
        """Fallback to simple statistical prediction when ML unavailable"""
        from scipy import stats

        # Use linear regression on log prices
        prices = df['Close'].tail(60).values
        if len(prices) < 20:
            return {
                'predicted_return': 0,
                'confidence': 0,
                'predicted_price': prices[-1],
                'prediction_range': (prices[-1], prices[-1]),
                'method': 'FALLBACK_INSUFFICIENT_DATA'
            }

        x = np.arange(len(prices))
        slope, intercept, r_value, _, _ = stats.linregress(x, np.log(prices))

        # Predict
        future_x = len(prices) + days_ahead
        predicted_log_price = slope * future_x + intercept
        predicted_price = np.exp(predicted_log_price)

        current_price = prices[-1]
        predicted_return = (predicted_price - current_price) / current_price

        # Confidence from R-squared
        confidence = max(0, min(100, r_value ** 2 * 100))

        # Range estimation
        std_error = np.std(np.log(prices) - (slope * x + intercept))
        lower = np.exp(predicted_log_price - 1.645 * std_error)
        upper = np.exp(predicted_log_price + 1.645 * std_error)

        return {
            'predicted_return': predicted_return,
            'confidence': confidence,
            'predicted_price': predicted_price,
            'prediction_range': (lower, upper),
            'method': 'FALLBACK_LINEAR_REGRESSION',
            'current_price': current_price
        }

    def load_models(self):
        """Load saved models from disk on startup"""
        if not TENSORFLOW_AVAILABLE:
            return

        for filename in os.listdir(self.model_dir):
            if filename.endswith('_model.h5'):
                symbol = filename.replace('_model.h5', '')
                try:
                    model_path = os.path.join(self.model_dir, filename)
                    scaler_path = os.path.join(self.model_dir, f'{symbol}_scaler.pkl')

                    self.models[symbol] = load_model(model_path)
                    with open(scaler_path, 'rb') as f:
                        self.scalers[symbol] = pickle.load(f)

                    logger.info(f"📥 Loaded ML model for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to load model for {symbol}: {e}")

    def get_model_info(self, symbol: str) -> Dict:
        """Get information about a symbol's model"""
        return {
            'has_model': symbol in self.models,
            'last_trained': self.last_trained.get(symbol, None),
            'days_since_training': (datetime.now() - self.last_trained[symbol]).days
            if symbol in self.last_trained else None,
            'needs_retraining': symbol not in self.models or
                              (datetime.now() - self.last_trained.get(symbol, datetime.now())).days >= self.RETRAIN_DAYS
        }
