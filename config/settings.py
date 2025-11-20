"""
🎯 SUPER MATH TRADING SYSTEM - Configuration
Maximum Realistic Profit with Advanced Mathematical Models
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
# 🎯 RISK MANAGEMENT (Kelly Criterion Based)
# ═══════════════════════════════════════════════════════════════

# Position Sizing
KELLY_FRACTION = 0.25  # Use 1/4 Kelly (conservative)
MAX_RISK_PER_TRADE = 0.02  # 2% max risk per trade
MAX_PORTFOLIO_RISK = 0.15  # 15% max drawdown

# Position Limits
MAX_POSITIONS = 10  # Maximum concurrent positions
MAX_POSITION_SIZE = 0.25  # 25% max per position
MAX_SECTOR_EXPOSURE = 0.40  # 40% max per sector

# Market Circuit Breaker (Exit all positions if market crashes)
MARKET_CRASH_THRESHOLD = -0.02  # -2% - Exit all if NIFTY down >2%
NIFTY_SYMBOL = "^NSEI"  # NIFTY 50 index symbol
TRAILING_STOP_ACTIVATION = 0.05  # Activate trailing stop at +5%
TRAILING_STOP_DISTANCE = 0.03  # Trail by 3%

# Stop Loss & Targets
SWING_STOP_LOSS = 0.02  # 2% stop loss for swing
POSITIONAL_STOP_LOSS = 0.05  # 5% stop loss for positional

SWING_TARGETS = [0.03, 0.08, 0.12]  # 3%, 8%, 12% targets
POSITIONAL_TARGETS = [0.12, 0.20, 0.30]  # 12%, 20%, 30% targets

# ═══════════════════════════════════════════════════════════════
# 📊 TECHNICAL INDICATORS SETTINGS
# ═══════════════════════════════════════════════════════════════

# Moving Averages
EMA_PERIODS = [8, 13, 21, 50, 100, 200]
SMA_PERIODS = [20, 50, 200]

# RSI Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 30
RSI_BULLISH_THRESHOLD = 50

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# ADX Settings
ADX_PERIOD = 14
ADX_STRONG_TREND = 25
ADX_VERY_STRONG = 50

# Volume Settings
VOLUME_MA_PERIOD = 20
VOLUME_SURGE_MULTIPLIER = 1.5

# ═══════════════════════════════════════════════════════════════
# 🔬 ADVANCED MATHEMATICAL INDICATORS
# ═══════════════════════════════════════════════════════════════

# Fibonacci Retracements
FIBONACCI_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
FIBONACCI_EXTENSIONS = [1.272, 1.618, 2.618]

# Elliott Wave
ELLIOTT_WAVE_ENABLED = True
MIN_WAVE_BARS = 5  # Minimum bars for wave identification

# Gann Theory
GANN_ANGLES = [1, 2, 3, 4, 8]  # 1x1, 1x2, 1x3, 1x4, 1x8
GANN_SQUARE_OF_9_ENABLED = True

# ═══════════════════════════════════════════════════════════════
# 🤖 MACHINE LEARNING SETTINGS
# ═══════════════════════════════════════════════════════════════

# LSTM Model
LSTM_ENABLED = True
LSTM_SEQUENCE_LENGTH = 60  # 60 days lookback
LSTM_PREDICTION_DAYS = 10  # Predict next 10 days
LSTM_CONFIDENCE_THRESHOLD = 0.70  # 70% confidence minimum

# Feature Engineering
ML_FEATURES = [
    'close', 'volume', 'rsi', 'macd', 'bb_position',
    'adx', 'ema_8', 'ema_21', 'momentum_5d', 'momentum_20d'
]

# ═══════════════════════════════════════════════════════════════
# 🎯 SIGNAL GENERATION
# ═══════════════════════════════════════════════════════════════

# Scoring System (0-10)
MIN_SIGNAL_SCORE = 7.0  # Minimum score to generate alert
HIGH_QUALITY_SCORE = 8.5  # High quality signal threshold

# Signal Filtering (Prevent signal flood)
MAX_SWING_SIGNALS_PER_SCAN = 5  # Max swing signals to process per scan
MAX_POSITIONAL_SIGNALS_PER_SCAN = 3  # Max positional signals to process per scan

# Dynamic Capital Allocation (By Signal Type)
# Allocates more to common signals (MR), reserves capacity for rare signals (Momentum/BO)
DYNAMIC_ALLOCATION_ENABLED = True
MEAN_REVERSION_CAPITAL_PCT = 0.70  # 70% capital for mean reversion (common)
MOMENTUM_CAPITAL_PCT = 0.20  # 20% capital for momentum (less common)
BREAKOUT_CAPITAL_PCT = 0.10  # 10% capital for breakout (rare but valuable)

# Auto-exit mean reversion for high-quality momentum/breakout
AUTO_EXIT_MR_FOR_MOMENTUM = True  # Exit MR positions to free capital for momentum
MR_EXIT_THRESHOLD_SCORE = 8.5  # Only exit MR if momentum signal score >= 8.5

# Signal Weights
WEIGHTS = {
    'technical': 0.40,  # Technical indicators weight
    'mathematical': 0.30,  # Fibonacci, Elliott, Gann weight
    'ml_prediction': 0.20,  # ML model weight
    'volume': 0.10  # Volume analysis weight
}

# ═══════════════════════════════════════════════════════════════
# 📈 STRATEGY SETTINGS
# ═══════════════════════════════════════════════════════════════

# Swing Trading (3-15 days)
SWING_HOLD_DAYS_MIN = 3
SWING_HOLD_DAYS_MAX = 15
SWING_ENABLED = True

# Positional Trading (weeks to months)
POSITIONAL_HOLD_DAYS_MIN = 20
POSITIONAL_HOLD_DAYS_MAX = 90
POSITIONAL_ENABLED = True

# ═══════════════════════════════════════════════════════════════
# 📊 STOCK UNIVERSE
# ═══════════════════════════════════════════════════════════════

# NSE Stock Selection
NSE_INDEX = 'NIFTY200'  # Scan NIFTY 200 stocks
MIN_MARKET_CAP = 1000  # Minimum 1000 crore market cap
MIN_PRICE = 50  # Minimum stock price
MAX_PRICE = 5000  # Maximum stock price

# Liquidity Filters
MIN_AVG_VOLUME = 100000  # Minimum average daily volume
MIN_VALUE_TRADED = 5000000  # Minimum ₹50 lakh daily turnover

# Fundamental Filters
MAX_DEBT_TO_EQUITY = 1.5
MIN_ROE = 10  # Minimum 10% ROE

# ═══════════════════════════════════════════════════════════════
# 📱 DISCORD ALERTS
# ═══════════════════════════════════════════════════════════════

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
DISCORD_ENABLED = bool(DISCORD_WEBHOOK_URL)
DISCORD_MENTION_ON_HIGH_SCORE = True  # @everyone on score >= 8.5

# Alert Frequency
SEND_DAILY_SUMMARY = True
SEND_WEEKLY_REPORT = True
DAILY_SUMMARY_TIME = '15:45'  # 3:45 PM IST

# ═══════════════════════════════════════════════════════════════
# 📊 PAPER TRADING
# ═══════════════════════════════════════════════════════════════

PAPER_TRADING_ENABLED = True
PAPER_TRADING_AUTO_EXECUTE = True  # Automatically execute signals in paper portfolio
PAPER_TRADING_FILE = 'data/paper_portfolio.json'

# ═══════════════════════════════════════════════════════════════
# 🖥️ DASHBOARD
# ═══════════════════════════════════════════════════════════════

DASHBOARD_ENABLED = True
DASHBOARD_PORT = 8501
DASHBOARD_HOST = '0.0.0.0'
DASHBOARD_REFRESH_INTERVAL = 60  # Refresh every 60 seconds

# ═══════════════════════════════════════════════════════════════
# ⏰ MARKET TIMING (IST)
# ═══════════════════════════════════════════════════════════════

MARKET_OPEN_TIME = '09:15'
MARKET_CLOSE_TIME = '15:30'
PRE_MARKET_SCAN_TIME = '09:00'
POST_MARKET_SCAN_TIME = '15:45'

# Scanning Intervals
SCAN_INTERVAL_MINUTES = 10  # Scan every 10 minutes during market hours (safer for API limits)
POSITION_MONITOR_INTERVAL = 5  # Monitor positions every 5 minutes

# ═══════════════════════════════════════════════════════════════
# 💾 DATA & CACHING
# ═══════════════════════════════════════════════════════════════

CACHE_ENABLED = True
CACHE_DURATION_MINUTES = 10  # Cache data for 10 minutes (matches scan interval)
HISTORICAL_DATA_PERIOD = '6mo'  # 6 months historical data

# API Rate Limit Protection
API_RETRY_ATTEMPTS = 3  # Retry failed API calls 3 times
API_RETRY_DELAY = 2  # Wait 2 seconds between retries
API_REQUEST_DELAY = 0.1  # 100ms delay between requests (prevents rate limiting)

DATA_FOLDER = 'data'
CACHE_FOLDER = 'data/cache'
LOGS_FOLDER = 'logs'

# ═══════════════════════════════════════════════════════════════
# 🧪 BACKTESTING
# ═══════════════════════════════════════════════════════════════

BACKTEST_START_DATE = '2019-01-01'
BACKTEST_END_DATE = '2024-12-31'
BACKTEST_INITIAL_CAPITAL = 100000

# Performance Metrics Targets
TARGET_SHARPE_RATIO = 2.0
TARGET_MAX_DRAWDOWN = 0.15  # 15%
TARGET_WIN_RATE = 0.55  # 55%
TARGET_PROFIT_FACTOR = 2.0

# ═══════════════════════════════════════════════════════════════
# 🔧 SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════

DEBUG_MODE = False
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
TIMEZONE = 'Asia/Kolkata'

# API Settings
MAX_API_RETRIES = 3
API_TIMEOUT_SECONDS = 30

# ═══════════════════════════════════════════════════════════════
# 📋 STOCK WATCHLIST - COMPREHENSIVE MARKET COVERAGE
# ═══════════════════════════════════════════════════════════════

# Import comprehensive stock lists
from config.nse_universe import (
    NIFTY_200,
    HIGH_VOLUME_MIDCAPS,
    WATCHLIST_CONSERVATIVE,
    WATCHLIST_MODERATE,
    WATCHLIST_AGGRESSIVE,
    WATCHLIST_ULTRA
)

# ═══════════════════════════════════════════════════════════════
# 🎯 SELECT YOUR SCAN MODE:
# ═══════════════════════════════════════════════════════════════
# Choose based on your needs and scan time tolerance:
#
# CONSERVATIVE:  50 stocks  (~1-2 min)  - Top quality only
# MODERATE:     100 stocks  (~2-4 min)  - Good balance
# AGGRESSIVE:   200 stocks  (~4-6 min)  - Maximum opportunities ✅
# ULTRA:        300+ stocks (~8-12 min) - Everything
# ═══════════════════════════════════════════════════════════════

# ✅ RECOMMENDED: Aggressive mode (200 stocks from NIFTY 200)
DEFAULT_WATCHLIST = WATCHLIST_AGGRESSIVE

# Uncomment one of these to change:
# DEFAULT_WATCHLIST = WATCHLIST_CONSERVATIVE  # 50 stocks
# DEFAULT_WATCHLIST = WATCHLIST_MODERATE      # 100 stocks
# DEFAULT_WATCHLIST = WATCHLIST_ULTRA         # 300+ stocks

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

print("✅ Super Math Trading System - Configuration Loaded")
print(f"📊 Scanning: {len(DEFAULT_WATCHLIST)} stocks")
print(f"🎯 Min Signal Score: {MIN_SIGNAL_SCORE}/10")
print(f"💰 Initial Capital: ₹{INITIAL_CAPITAL:,.0f}")
print(f"📱 Discord Alerts: {'Enabled' if DISCORD_ENABLED else 'Disabled'}")
print(f"🤖 ML Predictions: {'Enabled' if LSTM_ENABLED else 'Disabled'}")
print(f"📄 Paper Trading: {'Enabled' if PAPER_TRADING_ENABLED else 'Disabled'}")
