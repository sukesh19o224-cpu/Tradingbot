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
MAX_RISK_PER_TRADE = 0.025  # 2.5% max risk per trade (BALANCED - increased for better position size)
MAX_PORTFOLIO_RISK = 0.15  # 15% max drawdown

# Drawdown-Based Dynamic Position Sizing (Risk Reduction)
DRAWDOWN_RISK_REDUCTION_ENABLED = True  # Reduce risk during drawdowns
DRAWDOWN_THRESHOLD_MINOR = 0.05  # At 5% drawdown, reduce to 75% size
DRAWDOWN_THRESHOLD_MAJOR = 0.10  # At 10% drawdown, reduce to 50% size

# Position Limits
MAX_POSITIONS = 7  # Maximum concurrent positions per portfolio (7 × ₹10k = ₹70k positional, 3 × ₹10k = ₹30k swing)
MAX_POSITION_SIZE = 0.25  # 25% max per position
MAX_SECTOR_EXPOSURE = 0.40  # 40% max per sector

# Market Circuit Breaker (Exit all positions if market crashes)
MARKET_CRASH_THRESHOLD = -0.035  # -3.5% - Exit all if NIFTY down >3.5% (more realistic)
NIFTY_SYMBOL = "^NSEI"  # NIFTY 50 index symbol
TRAILING_STOP_ACTIVATION = 0.03  # Activate trailing stop at +3% (STRICT - earlier activation)
TRAILING_STOP_DISTANCE = 0.02  # Trail by 2% (STRICT - tighter trailing)

# Stop Loss & Targets (REALISTIC & ACHIEVABLE)
SWING_STOP_LOSS = 0.035  # 3.5% stop loss for swing (IMPROVED - wider to avoid premature exits)
POSITIONAL_STOP_LOSS = 0.04  # 4% stop loss for positional

# Realistic targets based on actual market conditions
SWING_TARGETS = [0.025, 0.05, 0.075]  # 2.5%, 5%, 7.5% targets (IMPROVED - more room to develop)
POSITIONAL_TARGETS = [0.05, 0.10, 0.15]  # 5%, 10%, 15% targets (INTERMEDIATE - achievable in 1-2 weeks)

# ═══════════════════════════════════════════════════════════════
# 📊 TECHNICAL INDICATORS SETTINGS
# ═══════════════════════════════════════════════════════════════

# Moving Averages
EMA_PERIODS = [8, 13, 21, 50, 100, 200]
SMA_PERIODS = [20, 50, 200]

# RSI Settings - OPTIMIZED for better signal detection
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75  # Above this = extreme overbought (avoid buying)
RSI_OVERSOLD = 30    # Below this = oversold (potential reversal)
RSI_BULLISH_THRESHOLD = 45  # Above 45 = confirmed upward momentum (was 50)

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# ADX Settings - Trend strength thresholds
ADX_PERIOD = 14
ADX_MIN_TREND = 30       # Minimum for swing trades (STRICT - strong trend required)
ADX_STRONG_TREND = 25    # Strong trend (good for positional)
ADX_VERY_STRONG = 50     # Very strong trend (rare)

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

# Scoring System (0-10) - STRICT for swing, BALANCED for positional
MIN_SIGNAL_SCORE = 7.0  # Minimum score for positional (BALANCED - good quality)
MIN_SWING_SIGNAL_SCORE = 8.0  # Minimum score for swing (STRICT - only best setups)
HIGH_QUALITY_SCORE = 8.5  # High quality signal threshold (for auto-replacement)

# Signal Filtering (Prevent signal flood)
# STRICT swing limits (30% capital), BALANCED positional limits (70% capital)
MAX_SWING_SIGNALS_PER_SCAN = 2  # Max swing signals (STRICT - only top 2)
MAX_POSITIONAL_SIGNALS_PER_SCAN = 5  # Max positional signals (BALANCED - main strategy)

# Dynamic Capital Allocation (By Signal Type)
# DISABLED: Focus on signal quality, not signal type
DYNAMIC_ALLOCATION_ENABLED = False  # Disabled - use quality-based allocation only
MEAN_REVERSION_CAPITAL_PCT = 0.70  # 70% capital for mean reversion (common)
MOMENTUM_CAPITAL_PCT = 0.20  # 20% capital for momentum (less common)
BREAKOUT_CAPITAL_PCT = 0.10  # 10% capital for breakout (rare but valuable)

# Smart P&L-Based Position Replacement
# Exit weak positions (losing/low-profit) to free capital for high-quality new signals
AUTO_EXIT_WEAK_FOR_QUALITY = True  # Exit weakest position for high-quality signals
QUALITY_REPLACEMENT_THRESHOLD = 8.5  # Only replace if new signal score >= 8.5
MIN_SCORE_DIFFERENCE = 0.5  # New signal must be at least 0.5 points better than weakest

# Signal Weights
WEIGHTS = {
    'technical': 0.40,  # Technical indicators weight
    'mathematical': 0.30,  # Fibonacci, Elliott, Gann weight
    'ml_prediction': 0.20,  # ML model weight
    'volume': 0.10  # Volume analysis weight
}

# Signal Freshness (Decay) - Prevent stale signals
SIGNAL_MAX_AGE_MINUTES = 30  # Signals older than 30 min are stale
SIGNAL_PRICE_MOVE_THRESHOLD = 0.01  # Reject if price moved >1% since signal

# ═══════════════════════════════════════════════════════════════
# 📈 STRATEGY SETTINGS
# ═══════════════════════════════════════════════════════════════

# Swing Trading (3-7 days) - STRICT quality only (30% capital)
SWING_HOLD_DAYS_MIN = 3
SWING_HOLD_DAYS_MAX = 7  # Exit after 7 days max
SWING_ENABLED = True  # ENABLED - STRICT criteria, only top-tier swing setups (score >= 8.0, ADX >= 30)

# Positional Trading (INTERMEDIATE) - High quality setups, faster exits
POSITIONAL_HOLD_DAYS_MIN = 5  # Minimum 5 days (was 10)
POSITIONAL_HOLD_DAYS_MAX = 15  # Maximum 15 days
POSITIONAL_ENABLED = True

# ═══════════════════════════════════════════════════════════════
# 📊 STOCK UNIVERSE
# ═══════════════════════════════════════════════════════════════

# NSE Stock Selection
NSE_INDEX = 'NIFTY200'  # Scan NIFTY 200 stocks
MIN_MARKET_CAP = 1000  # Minimum 1000 crore market cap
MIN_PRICE = 50  # Minimum stock price
MAX_PRICE = 5000  # Maximum stock price

# Liquidity Filters (PRACTICAL & REALISTIC)
MIN_AVG_VOLUME = 500000  # Minimum 5 lakh shares daily volume (good liquidity)
MIN_VALUE_TRADED = 50000000  # Minimum ₹5 crore daily turnover (tight spreads)
MAX_BID_ASK_SPREAD = 0.005  # Max 0.5% spread (ensures good execution)
MIN_MARKET_DEPTH = 1000000  # Min ₹10L depth at L1/L2 (reduces slippage)

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

# Using Top 50 Working stocks by default (see config/nse_top_50_working.py)
# System automatically loads from NSEStockFetcher - no manual import needed!

# ═══════════════════════════════════════════════════════════════
# 🎯 SCAN MODE: SIMPLE & RELIABLE
# ═══════════════════════════════════════════════════════════════
# System now uses Top 50 VERIFIED WORKING stocks by default
# See: config/nse_top_50_working.py
#
# ✅ 50 stocks (Large Cap, High Liquidity)
# ✅ ALL tested & working (Nov 2025)
# ✅ 3 threads (ultra-safe)
# ✅ ~2-3 min scan time
# ✅ ZERO errors!
# ═══════════════════════════════════════════════════════════════

# Stock list loaded automatically by NSEStockFetcher
# No manual watchlist configuration needed!

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

print("✅ INTERMEDIATE Positional Trading System - Configuration Loaded")
print(f"📊 Strategy: 70% Positional (5-14 days) + 30% Swing STRICT (score ≥8.0, ADX ≥30)")
print(f"🎯 Signal Scores: Positional ≥{MIN_SIGNAL_SCORE}/10, Swing ≥{MIN_SWING_SIGNAL_SCORE}/10")
print(f"💰 Capital Split: ₹{INITIAL_CAPITAL * 0.70:,.0f} Positional + ₹{INITIAL_CAPITAL * 0.30:,.0f} Swing")
print(f"📈 Max Positions: {MAX_POSITIONS} per portfolio (₹10k each)")
print(f"📱 Discord: {'✅' if DISCORD_ENABLED else '❌'} • ML: {'✅' if LSTM_ENABLED else '❌'} • Paper Trading: {'✅' if PAPER_TRADING_ENABLED else '❌'}")
