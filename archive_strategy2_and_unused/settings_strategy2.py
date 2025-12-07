"""
🎯 STRATEGY 2 - 50/50 STRICTER SYSTEM
Top 2-3 Signals Per Scan - Higher Quality Than Strategy 1
Swing: ≥8.3 score, ADX ≥32 | Positional: ≥7.5 score, ADX ≥27
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# 💰 CAPITAL & PORTFOLIO SETTINGS
# ═══════════════════════════════════════════════════════════════

INITIAL_CAPITAL = 100000  # Starting capital (₹)
PAPER_TRADING_CAPITAL = 100000  # Paper trading capital

# ═══════════════════════════════════════════════════════════════
# 🎯 RISK MANAGEMENT (Ultra Conservative)
# ═══════════════════════════════════════════════════════════════

# Position Sizing - SLIGHTLY TIGHTER
KELLY_FRACTION = 0.23  # Use ~1/4 Kelly (vs 0.25 in Strategy 1)
MAX_RISK_PER_TRADE = 0.023  # 2.3% max risk per trade (vs 2.5% in Strategy 1)
MAX_PORTFOLIO_RISK = 0.13  # 13% max drawdown (vs 15% in Strategy 1)

# Drawdown-Based Dynamic Position Sizing
DRAWDOWN_RISK_REDUCTION_ENABLED = True
DRAWDOWN_THRESHOLD_MINOR = 0.04  # At 4% drawdown, reduce to 75% size (STRICTER)
DRAWDOWN_THRESHOLD_MAJOR = 0.08  # At 8% drawdown, reduce to 50% size (STRICTER)

# Position Limits - 50/50 Split
MAX_POSITIONS = 5  # Maximum concurrent positions per portfolio (5 swing + 5 positional)
MAX_POSITION_SIZE = 0.20  # 20% max per position (STRICTER)
MAX_SECTOR_EXPOSURE = 0.30  # 30% max per sector (STRICTER)

# Market Circuit Breaker
MARKET_CRASH_THRESHOLD = -0.03  # -3% - Exit all if NIFTY down >3% (STRICTER)
NIFTY_SYMBOL = "^NSEI"
TRAILING_STOP_ACTIVATION = 0.025  # Activate trailing stop at +2.5% (STRICTER - earlier)
TRAILING_STOP_DISTANCE = 0.015  # Trail by 1.5% (STRICTER - tighter)

# Stop Loss & Targets - SLIGHTLY TIGHTER
SWING_STOP_LOSS = 0.033  # 3.3% stop loss for swing (vs 3.5% in Strategy 1)
POSITIONAL_STOP_LOSS = 0.038  # 3.8% stop loss for positional (vs 4% in Strategy 1)

# Slightly conservative targets
SWING_TARGETS = [0.023, 0.045, 0.07]  # 2.3%, 4.5%, 7% targets
POSITIONAL_TARGETS = [0.045, 0.09, 0.14]  # 4.5%, 9%, 14% targets

# ═══════════════════════════════════════════════════════════════
# 📊 TECHNICAL INDICATORS SETTINGS
# ═══════════════════════════════════════════════════════════════

# Moving Averages
EMA_PERIODS = [8, 13, 21, 50, 100, 200]
SMA_PERIODS = [20, 50, 200]

# RSI Settings - SLIGHTLY STRICTER
RSI_PERIOD = 14
RSI_OVERBOUGHT = 72  # Slightly stricter (vs 75 in Strategy 1)
RSI_OVERSOLD = 32    # Slightly stricter (vs 30 in Strategy 1)
RSI_BULLISH_THRESHOLD = 47  # Above 47 (vs 45 in Strategy 1)

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# ADX Settings - STRICTER THAN STRATEGY 1
ADX_PERIOD = 14
ADX_MIN_TREND = 32       # Minimum for swing trades (vs 30 in Strategy 1)
ADX_STRONG_TREND = 27    # Strong trend for positional (vs 25 in Strategy 1)
ADX_VERY_STRONG = 50

# Volume Settings - SLIGHTLY STRICTER
VOLUME_MA_PERIOD = 20
VOLUME_SURGE_MULTIPLIER = 1.7  # Need 1.7x volume (vs 1.5 in Strategy 1)

# ═══════════════════════════════════════════════════════════════
# 🔬 ADVANCED MATHEMATICAL INDICATORS
# ═══════════════════════════════════════════════════════════════

# Fibonacci Retracements
FIBONACCI_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
FIBONACCI_EXTENSIONS = [1.272, 1.618, 2.618]

# Elliott Wave
ELLIOTT_WAVE_ENABLED = True
MIN_WAVE_BARS = 5

# Gann Theory
GANN_ANGLES = [1, 2, 3, 4, 8]
GANN_SQUARE_OF_9_ENABLED = True

# ═══════════════════════════════════════════════════════════════
# 🤖 MACHINE LEARNING SETTINGS
# ═══════════════════════════════════════════════════════════════

# LSTM Model - SLIGHTLY STRICTER
LSTM_ENABLED = True
LSTM_SEQUENCE_LENGTH = 60
LSTM_PREDICTION_DAYS = 10
LSTM_CONFIDENCE_THRESHOLD = 0.72  # 72% confidence (vs 70% in Strategy 1)

# Feature Engineering
ML_FEATURES = [
    'close', 'volume', 'rsi', 'macd', 'bb_position',
    'adx', 'ema_8', 'ema_21', 'momentum_5d', 'momentum_20d'
]

# ═══════════════════════════════════════════════════════════════
# 🎯 SIGNAL GENERATION - ULTRA STRICT
# ═══════════════════════════════════════════════════════════════

# Scoring System (0-10) - STRICTER THAN STRATEGY 1
MIN_SIGNAL_SCORE = 7.5  # Minimum score for positional (vs 7.0 in Strategy 1)
MIN_SWING_SIGNAL_SCORE = 8.3  # Minimum score for swing (vs 8.0 in Strategy 1)
HIGH_QUALITY_SCORE = 8.8  # High quality signal threshold

# Signal Filtering - 50/50 Split, MORE SELECTIVE
MAX_SWING_SIGNALS_PER_SCAN = 2  # Max 2 swing signals (vs 2 in Strategy 1)
MAX_POSITIONAL_SIGNALS_PER_SCAN = 3  # Max 3 positional signals (vs 5 in Strategy 1)

# Dynamic Capital Allocation
DYNAMIC_ALLOCATION_ENABLED = False
MEAN_REVERSION_CAPITAL_PCT = 0.50
MOMENTUM_CAPITAL_PCT = 0.30
BREAKOUT_CAPITAL_PCT = 0.20

# Smart P&L-Based Position Replacement - STRICTER
AUTO_EXIT_WEAK_FOR_QUALITY = True
QUALITY_REPLACEMENT_THRESHOLD = 9.5  # Only replace if new signal score >= 9.5
MIN_SCORE_DIFFERENCE = 1.0  # New signal must be 1.0 points better (STRICTER)

# Signal Weights
WEIGHTS = {
    'technical': 0.40,
    'mathematical': 0.30,
    'ml_prediction': 0.20,
    'volume': 0.10
}

# Signal Freshness
SIGNAL_MAX_AGE_MINUTES = 20  # Signals older than 20 min are stale (STRICTER)
SIGNAL_PRICE_MOVE_THRESHOLD = 0.008  # Reject if price moved >0.8% (STRICTER)

# ═══════════════════════════════════════════════════════════════
# 📈 STRATEGY SETTINGS - 50/50 BALANCED
# ═══════════════════════════════════════════════════════════════

# Swing Trading (3-7 days) - ULTRA STRICT (50% capital)
SWING_HOLD_DAYS_MIN = 3
SWING_HOLD_DAYS_MAX = 7
SWING_ENABLED = True  # ULTRA STRICT: score >= 9.0, ADX >= 35

# Positional Trading (5-15 days) - VERY STRICT (50% capital)
POSITIONAL_HOLD_DAYS_MIN = 5
POSITIONAL_HOLD_DAYS_MAX = 15
POSITIONAL_ENABLED = True  # VERY STRICT: score >= 8.5, ADX >= 30

# ═══════════════════════════════════════════════════════════════
# 📊 STOCK UNIVERSE
# ═══════════════════════════════════════════════════════════════

NSE_INDEX = 'NIFTY200'
MIN_MARKET_CAP = 1500  # Minimum 1500 crore (vs 1000 in Strategy 1)
MIN_PRICE = 75  # Minimum stock price (vs 50 in Strategy 1)
MAX_PRICE = 5000

# Liquidity Filters - SLIGHTLY STRICTER
MIN_AVG_VOLUME = 700000  # Minimum 7 lakh shares (vs 5 lakh in Strategy 1)
MIN_VALUE_TRADED = 70000000  # Minimum ₹7 crore daily turnover (vs ₹5 crore in Strategy 1)
MAX_BID_ASK_SPREAD = 0.004  # Max 0.4% spread (vs 0.5% in Strategy 1)
MIN_MARKET_DEPTH = 1500000  # Min ₹15L depth (vs ₹10L in Strategy 1)

# Fundamental Filters - SLIGHTLY STRICTER
MAX_DEBT_TO_EQUITY = 1.3  # Lower debt (vs 1.5 in Strategy 1)
MIN_ROE = 12  # Minimum 12% ROE (vs 10% in Strategy 1)

# ═══════════════════════════════════════════════════════════════
# 📱 DISCORD ALERTS - ENABLED WITH "STRATEGY 2" PREFIX
# ═══════════════════════════════════════════════════════════════

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')  # Same webhook as Strategy 1
DISCORD_ENABLED = True  # ✅ ENABLED - Sends alerts with "🎯 STRATEGY 2" prefix
DISCORD_MENTION_ON_HIGH_SCORE = True  # Mention on high quality signals

# Alert Frequency
SEND_DAILY_SUMMARY = True  # Send daily summary
SEND_WEEKLY_REPORT = False
DAILY_SUMMARY_TIME = '15:45'

# ═══════════════════════════════════════════════════════════════
# 📊 PAPER TRADING - SEPARATE FILES
# ═══════════════════════════════════════════════════════════════

PAPER_TRADING_ENABLED = True
PAPER_TRADING_AUTO_EXECUTE = True
PAPER_TRADING_FILE = 'data/strategy2_paper_portfolio.json'

# ═══════════════════════════════════════════════════════════════
# 🖥️ DASHBOARD - SEPARATE PORT
# ═══════════════════════════════════════════════════════════════

DASHBOARD_ENABLED = True
DASHBOARD_PORT = 8502  # Different port from Strategy 1 (8501)
DASHBOARD_HOST = '0.0.0.0'
DASHBOARD_REFRESH_INTERVAL = 60

# ═══════════════════════════════════════════════════════════════
# ⏰ MARKET TIMING (IST)
# ═══════════════════════════════════════════════════════════════

MARKET_OPEN_TIME = '09:15'
MARKET_CLOSE_TIME = '15:30'
PRE_MARKET_SCAN_TIME = '09:00'
POST_MARKET_SCAN_TIME = '15:45'

# Scanning Intervals
SCAN_INTERVAL_MINUTES = 10  # Same as Strategy 1
POSITION_MONITOR_INTERVAL = 5

# ═══════════════════════════════════════════════════════════════
# 💾 DATA & CACHING - SEPARATE CACHE
# ═══════════════════════════════════════════════════════════════

CACHE_ENABLED = True
CACHE_DURATION_MINUTES = 10
HISTORICAL_DATA_PERIOD = '6mo'

# API Rate Limit Protection
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 2
API_REQUEST_DELAY = 0.1

DATA_FOLDER = 'data'
CACHE_FOLDER = 'data/cache_strategy2'  # SEPARATE cache folder
LOGS_FOLDER = 'logs'

# ═══════════════════════════════════════════════════════════════
# 🧪 BACKTESTING
# ═══════════════════════════════════════════════════════════════

BACKTEST_START_DATE = '2019-01-01'
BACKTEST_END_DATE = '2024-12-31'
BACKTEST_INITIAL_CAPITAL = 100000

# Performance Metrics Targets - STRICTER
TARGET_SHARPE_RATIO = 2.5  # Higher Sharpe (was 2.0)
TARGET_MAX_DRAWDOWN = 0.12  # Lower drawdown (was 0.15)
TARGET_WIN_RATE = 0.60  # Higher win rate (was 0.55)
TARGET_PROFIT_FACTOR = 2.5  # Higher profit factor (was 2.0)

# ═══════════════════════════════════════════════════════════════
# 🔧 SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════

DEBUG_MODE = False
LOG_LEVEL = 'INFO'
TIMEZONE = 'Asia/Kolkata'

MAX_API_RETRIES = 3
API_TIMEOUT_SECONDS = 30

# ═══════════════════════════════════════════════════════════════
# 📋 STOCK WATCHLIST
# ═══════════════════════════════════════════════════════════════

# Uses same stock fetcher as Strategy 1

# Sector Classification
SECTORS = {
    'IT': ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS'],
    'BANKING': ['HDFCBANK.NS', 'ICICIBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'AXISBANK.NS'],
    'AUTO': ['MARUTI.NS', 'M&M.NS', 'TATAMOTORS.NS', 'BAJAJ-AUTO.NS'],
    'PHARMA': ['SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS'],
    'FMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS'],
    'ENERGY': ['RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS'],
    'METALS': ['TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS'],
    'CEMENT': ['ULTRACEMCO.NS', 'AMBUJACEM.NS', 'ACC.NS']
}

print("✅ STRATEGY 2 - 50/50 STRICTER Configuration Loaded")
print(f"📊 Strategy: 50% Swing (score ≥{MIN_SWING_SIGNAL_SCORE}, ADX ≥{ADX_MIN_TREND}) + 50% Positional (score ≥{MIN_SIGNAL_SCORE}, ADX ≥{ADX_STRONG_TREND})")
print(f"🎯 Higher Quality Than Strategy 1 - Top 2-3 signals per scan")
print(f"💰 Capital Split: ₹50k Swing + ₹50k Positional")
print(f"📈 Max Positions: {MAX_POSITIONS} per portfolio")
discord_status = "✅ (STRATEGY 2)" if DISCORD_ENABLED else "❌ DISABLED"
print(f"📱 Discord: {discord_status} • Dashboard: ✅ Port {DASHBOARD_PORT}")
