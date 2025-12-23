"""
🎯 SUPER MATH TRADING SYSTEM - Configuration
Maximum Realistic Profit with Advanced Mathematical Models
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# 💰 CAPITAL & PORTFOLIO SETTINGS - DUAL INDEPENDENT PORTFOLIOS
# ═══════════════════════════════════════════════════════════════

# POSITIONAL Portfolio (REAL MONEY - Primary Strategy)
INITIAL_CAPITAL = 50000  # Positional capital (₹50,000) - REAL MONEY
PAPER_TRADING_CAPITAL = 50000  # Positional paper trading

# SWING/INTRADAY Portfolio (PAPER TRADING - Testing Phase)
SWING_CAPITAL = 50000  # Swing/Intraday capital (₹50,000) - PAPER ONLY for now - INTRADAY SYSTEM
# NOTE: Swing = ONE DAY TRADER (INTRADAY ONLY) - closes ALL positions before 3:30 PM (NO overnight holds, force exit at 3:25 PM)
# Once proven profitable in paper trading, can deploy with real money

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

# Position Limits (Per Portfolio)
MAX_POSITIONS = 7  # Positional: 7 positions max (7 × ₹7.1K = ₹50K)
MAX_POSITIONS_SWING = 10  # Swing: 10 positions max (high-frequency rotation - more opportunities for quick 1-2% profits)
MAX_POSITION_SIZE = 0.20  # 20% max per position (₹10K from ₹50K)
MAX_SECTOR_EXPOSURE = 0.40  # 40% max per sector

# Market Circuit Breaker (Exit all positions if market crashes)
MARKET_CRASH_THRESHOLD = -0.035  # -3.5% - Exit all if NIFTY down >3.5% (more realistic)
NIFTY_SYMBOL = "^NSEI"  # NIFTY 50 index symbol
# Hybrid Trailing Stop (Breakeven + ATR-based)
# NOTE: These are DEFAULT/SWING values - positional uses strategy-specific overrides in code
# Swing: Quick profit-taking - tighter trailing stops
TRAILING_STOP_BREAKEVEN_ACTIVATION = 0.005  # Swing: Move stop to breakeven at +0.5% (ULTRA-QUICK risk-free)
TRAILING_STOP_ACTIVATION = 0.01  # Swing: Activate ATR-based trailing at +1% (quick profits)
TRAILING_STOP_DISTANCE = 0.008  # Swing fallback: Trail by 0.8% if ATR unavailable (ultra-tight)
TRAILING_STOP_ATR_MULTIPLIER = 0.8  # Swing: Trail by 0.8x ATR (ultra-tight for quick profit-taking)

# Positional Trailing Stops (hardcoded in paper_trader.py check_exits - NOT using settings above)
# Positional uses: breakeven at +2%, trailing at +3%, ATR multiplier 0.8x (same as setting)
# NOTE: Positional fallback uses TRAILING_STOP_DISTANCE (0.8%) - should use wider value
# This is handled in code with strategy-specific overrides

# Stop Loss & Targets - ONE DAY TRADER (INTRADAY ONLY - same day exits, quick profit-taking)
SWING_STOP_LOSS = 0.01  # 1.0% stop loss for swing (ULTRA-TIGHT - quick exits, frequent trades, preserves capital)
POSITIONAL_STOP_LOSS = 0.04  # 4% stop loss for positional

# ATR-Based Dynamic Stop Loss (Volatility-Adjusted)
# Adapts stop loss to each stock's volatility - prevents premature exits
USE_ATR_STOP_LOSS = True  # Enable ATR-based stop loss (recommended)
ATR_PERIOD = 14  # 14-day ATR calculation period
ATR_MULTIPLIER_SWING = 1.0  # 1.0x ATR for swing (ultra-tight stops for quick profits, fast exits)
ATR_MULTIPLIER_POSITIONAL = 2.5  # 2.5x ATR for positional (wider stop) - UNTOUCHED

# ATR Stop Loss Clamps (Strategy-Specific)
# Swing: Tight range for quick trades
ATR_MIN_STOP_LOSS_SWING = 0.008  # Minimum 0.8% stop loss (ultra-tight for quick trades)
ATR_MAX_STOP_LOSS_SWING = 0.015  # Maximum 1.5% stop loss (tight ceiling for quick exits)

# Positional: Wider range to allow proper ATR-based stops (2.5x ATR typically gives 2-6% stops)
ATR_MIN_STOP_LOSS_POSITIONAL = 0.02  # Minimum 2% stop loss (allows proper ATR calculation)
ATR_MAX_STOP_LOSS_POSITIONAL = 0.06  # Maximum 6% stop loss (prevents excessive stops)

# Backward compatibility (will be overridden in code based on strategy)
ATR_MIN_STOP_LOSS = 0.02  # Default: Use positional values (wider range)
ATR_MAX_STOP_LOSS = 0.06  # Default: Use positional values (wider range)

# SWING/INTRADAY: INTRADAY targets (1.0%/1.5%/2.0%) - hit within same day, close all positions before 3:30 PM
# Strategy: ONE DAY TRADER - Many small wins (1.0-2.0% each) = High total profit through frequent trades (daily reset)
# Risk/Reward: 1.0% risk → 1.0%/1.5%/2.0% reward = 1:1 to 2:1 ratio (excellent for intraday)
# Optimized for: 60%+ win rate with daily reset, no overnight risk, quick exits at 1.0-2.0% profit (same day only)
SWING_TARGETS = [0.01, 0.015, 0.02]  # 1.0%, 1.5%, 2.0% targets (INTRADAY - same day exits only, force exit at 3:25 PM)
POSITIONAL_TARGETS = [0.05, 0.10, 0.15]  # 5%, 10%, 15% targets (INTERMEDIATE - achievable in 1-2 weeks)

# ═══════════════════════════════════════════════════════════════
# 🎯 STRATEGY-SPECIFIC CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════

# MEAN REVERSION Strategy - Buy the dip, wait for bounce
# AGGRESSIVE: Expanded RSI range to catch earlier pullbacks
MEAN_REVERSION_CONFIG = {
    'STOP_LOSS': 0.045,  # 4.5% stop loss (tighter for better R/R - was 5.5%)
    'TARGETS': [0.05, 0.10, 0.15],  # 5%, 10%, 15% targets
    'MIN_PULLBACK_PCT': 5.0,  # Minimum 5% pullback (was 8% - more lenient)
    'MAX_PULLBACK_PCT': 25.0,  # Maximum 25% pullback (deeper = riskier)
    'REQUIRE_UPTREND': True,  # Must be above 50-day MA
    'MIN_RSI_BOUNCE': 30,  # RSI must bounce above 30 (more lenient)
    'MAX_RSI': 55,  # RSI should be < 55 for mean reversion (expanded from 50)
    'VOLUME_SPIKE_MIN': 1.2,  # Minimum 1.2x volume (was 1.3x - more lenient)
}

# MOMENTUM Strategy - Ride strong trends
MOMENTUM_CONFIG = {
    'STOP_LOSS': 0.04,  # 4% stop loss (tighter = better R/R)
    'TARGETS': [0.05, 0.10, 0.15],  # 5%, 10%, 15% targets
    'MIN_ADX': 25,  # Strong trend
    'MIN_RSI': 50,  # Above 50
    'MAX_RSI': 68,  # Below 68 (avoid overbought - was 70)
    'MAX_DISTANCE_FROM_MA20': 12.0,  # Not more than 12% above 20-day MA (avoid extended)
    'MIN_VOLUME_RATIO': 1.3,  # Minimum 1.3x volume (balanced - not too strict)
    'REQUIRE_ABOVE_MA50': True,  # Must be above 50-day MA
    'TRAILING_STOP_ACTIVATION': 0.02,  # Activate trailing at +2% (was +3%)
}

# BREAKOUT Strategy - Breaking resistance
BREAKOUT_CONFIG = {
    'STOP_LOSS': 0.035,  # 3.5% stop loss
    'TARGETS': [0.06, 0.12, 0.18],  # 6%, 12%, 18% targets
    'MIN_VOLUME_SURGE': 2.0,  # 2x volume on breakout
}

# ═══════════════════════════════════════════════════════════════
# 📊 TECHNICAL INDICATORS SETTINGS
# ═══════════════════════════════════════════════════════════════

# Moving Averages
EMA_PERIODS = [8, 13, 21, 50, 100, 200]
SMA_PERIODS = [20, 50, 200]

# RSI Settings - SWING optimized for 1-2% quick moves
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70  # Above 70 = overbought (avoid for swing - too late)
RSI_OVERSOLD = 30    # Below this = oversold (potential reversal)
RSI_BULLISH_THRESHOLD = 50  # Swing needs RSI 50-70 (strong momentum zone)
RSI_SWING_MAX = 68   # Swing max RSI (optimized - catch stocks about to move, not already overbought)
RSI_SWING_MIN = 40   # Swing min RSI (expanded for more opportunities - catch quick momentum)
RSI_SWING_MAX = 72   # Swing max RSI (expanded - RSI 68-72 can still make 1-2% moves)
# Note: RSI 40-72 range allows more opportunities while still catching 1-2% quick moves

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# ADX Settings - SWING optimized for 1-2% quick moves (not strong trends)
ADX_PERIOD = 14
ADX_MIN_TREND = 12       # Lower ADX for swing - catch stocks ABOUT TO move (not already in strong trend) - 1-2% quick moves
ADX_STRONG_TREND = 25    # Strong trend (good for positional) - UNTOUCHED
ADX_VERY_STRONG = 50     # Very strong trend (rare) - UNTOUCHED
# Note: Low ADX (<20) often precedes quick 1-2% moves before strong trend develops

# Volume Settings - SWING optimized for 1-2% quick moves
VOLUME_MA_PERIOD = 20
VOLUME_SURGE_MULTIPLIER = 2.0  # Swing needs 2x volume (fast-moving stocks)
VOLUME_SWING_MULTIPLIER = 0.8   # Minimum 0.8x volume for swing (low threshold - catch volume spikes starting)
# Note: We want to catch volume SPIKES (sudden interest) not sustained high volume

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
MIN_SIGNAL_SCORE = 7.0  # Positional: Good quality (balanced - allows MR + Momentum) - UNTOUCHED
MIN_SWING_SIGNAL_SCORE = 5.5  # Swing: Lower threshold for 1-2% quick moves (catch more opportunities, exit fast)
HIGH_QUALITY_SCORE = 8.5  # High quality signal threshold (for auto-replacement)
# Note: Lower score threshold for swing because we're targeting smaller moves (1-2%) that happen more frequently

# Signal Filtering (Prevent signal flood)
# HIGH-FREQUENCY swing limits (30% capital), BALANCED positional limits (70% capital) - UNTOUCHED
MAX_SWING_SIGNALS_PER_SCAN = 5  # Max swing signals (optimized for ₹50K capital - ensures all signals can execute without running out of capital)
MAX_POSITIONAL_SIGNALS_PER_SCAN = 5  # Max positional signals (BALANCED - main strategy) - UNTOUCHED

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
QUALITY_REPLACEMENT_THRESHOLD_BREAKOUT = 8.0  # Lower for breakouts (rare but powerful)
MIN_SCORE_DIFFERENCE = 0.5  # New signal must be at least 0.5 points better than weakest

# ═══════════════════════════════════════════════════════════════
# 📊 MARKET REGIME DETECTION (Professional Feature)
# ═══════════════════════════════════════════════════════════════

# MASTER SWITCH - Turn ON/OFF market regime detection
MARKET_REGIME_DETECTION_ENABLED = True  # Set to True to enable (DEFAULT: OFF for testing)

# Market Regime Detection Settings
MARKET_REGIME_CONFIG = {
    # Detection Parameters
    'LOOKBACK_PERIOD': '3mo',  # Analyze last 3 months of Nifty data
    'EMA_SHORT': 50,  # 50-day EMA
    'EMA_LONG': 200,  # 200-day EMA
    'ADX_PERIOD': 14,  # ADX calculation period
    'ADX_STRONG_TREND': 25,  # ADX > 25 = strong trend
    'ADX_WEAK_TREND': 20,  # ADX < 20 = weak trend/sideways
    
    # BULL MARKET Adjustments (Normal Operation)
    'BULL': {
        'quality_multiplier': 1.0,  # Normal quality thresholds
        'max_positions_multiplier': 1.0,  # Normal max positions
        'position_size_multiplier': 1.0,  # Normal position size
        'description': 'Strong uptrend - Trade aggressively'
    },
    
    # SIDEWAYS MARKET Adjustments (Be Selective)
    'SIDEWAYS': {
        'quality_multiplier': 1.5,  # 50% higher quality required (50 → 75, 60 → 90)
        'max_positions_multiplier': 0.5,  # Half the positions (6 → 3)
        'position_size_multiplier': 0.75,  # 75% position size
        'min_rs_rating': 110,  # Only stocks outperforming market
        'description': 'Choppy market - Only A+ setups'
    },
    
    # BEAR MARKET Adjustments (Defensive)
    'BEAR': {
        'quality_multiplier': 1.7,  # 70% higher quality required (60 → 102, effectively stops most trades)
        'max_positions_multiplier': 0.17,  # 1/6 positions (6 → 1)
        'position_size_multiplier': 0.25,  # Quarter position size
        'min_rs_rating': 120,  # Only strongest market leaders
        'tighten_stops': True,  # Reduce stops to 2% (from 2.5-5%)
        'description': 'Downtrend - Preserve capital'
    }
}

# Regime Detection Display
SHOW_REGIME_IN_LOGS = True  # Show current market regime in scan logs

# ═══════════════════════════════════════════════════════════════
# 🇮🇳 INDIA-SPECIFIC FEATURES (Professional Enhancements)
# ═══════════════════════════════════════════════════════════════

# 1. SECTOR ROTATION TRACKING
SECTOR_ROTATION_ENABLED = False # Set to True to enable (DEFAULT: OFF for testing)

SECTOR_ROTATION_CONFIG = {
    # Indian Market Sectors
    'SECTORS': {
        'IT': ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS', 'LTIM.NS', 'PERSISTENT.NS'],
        'Banking': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 
                   'INDUSINDBK.NS', 'BANKBARODA.NS', 'PNB.NS', 'CANBK.NS', 'UNIONBANK.NS'],
        'Pharma': ['SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'LUPIN.NS', 
                  'TORNTPHARM.NS', 'ZYDUSLIFE.NS', 'MANKIND.NS'],
        'Auto': ['MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS', 
                'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'MOTHERSON.NS'],
        'FMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS', 
                'MARICO.NS', 'GODREJCP.NS', 'TATACONSUM.NS', 'VBL.NS'],
        'Metals': ['TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'VEDL.NS', 'JINDALSTEL.NS', 
                  'NMDC.NS', 'SAIL.NS']
    },
    
    # Sector Rotation Settings
    'MIN_SECTOR_RS': 105,  # Minimum sector RS vs Nifty to be considered "leading"
    'TOP_SECTORS_COUNT': 3,  # Focus on top 3 leading sectors
    'BOOST_LEADING_SECTORS': True,  # Boost signals from leading sectors
    'LEADING_SECTOR_BOOST': 0.5,  # Add 0.5 to signal score if from leading sector
    'AVOID_LAGGING_SECTORS': True,  # Skip signals from bottom 2 sectors
    'LAGGING_SECTOR_RS_THRESHOLD': 95,  # Sector RS < 95 = lagging
}

# 2. BANK NIFTY VOLATILITY ADJUSTMENT
BANK_NIFTY_VOLATILITY_ADJUSTMENT = True  # Set to True to enable (DEFAULT: OFF for testing)

BANK_NIFTY_CONFIG = {
    # Banking Stocks (Higher Volatility)
    'BANKING_STOCKS': [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'INDUSINDBK.NS', 'BANKBARODA.NS', 'PNB.NS', 'CANBK.NS', 'UNIONBANK.NS',
        'IDFCFIRSTB.NS', 'FEDERALBNK.NS', 'BANDHANBNK.NS', 'AUBANK.NS'
    ],
    
    # Volatility Adjustments for Banking Stocks
    'STOP_LOSS_MULTIPLIER': 1.5,  # 1.5x wider stops (4% → 6%)
    'POSITION_SIZE_MULTIPLIER': 0.75,  # 75% of normal position size
    'QUALITY_THRESHOLD_BOOST': 10,  # Require 10 points higher quality (60 → 70)
    'MIN_SCORE_BOOST': 0.3,  # Require 0.3 higher score (7.0 → 7.3)
    
    # Rationale: Bank Nifty is 1.5-1.7x more volatile than Nifty 50
    # Wider stops prevent premature exits, smaller size manages risk
}

# ═══════════════════════════════════════════════════════════════
# 🎯 PROFESSIONAL TRADING PATTERNS (Optional Enhancements)
# ═══════════════════════════════════════════════════════════════

# 3. MINERVINI VCP (Volatility Contraction Pattern)
MINERVINI_VCP_ENABLED = True   # Set to True to enable (DEFAULT: OFF for testing)

MINERVINI_VCP_CONFIG = {
    # VCP Detection Parameters
    'MIN_CONSOLIDATION_WEEKS': 4,  # Minimum 4 weeks consolidation (relaxed from 7)
    'MAX_CONSOLIDATION_WEEKS': 20,  # Maximum 20 weeks
    'CONTRACTION_THRESHOLD': 0.7,  # Each phase should be 70% of previous range
    'MIN_PHASES': 2,  # Minimum 2 contraction phases (relaxed from 3)
    'VOLUME_DRYUP_THRESHOLD': 0.8,  # Volume should drop to 80% of average
    'BREAKOUT_VOLUME_SURGE': 1.3,  # Breakout volume should be 1.3x average (relaxed from 2x)
    
    # Score Boost (Enhancement, not filter!)
    'VCP_SCORE_BOOST': 0.8,  # Add 0.8 to signal score if VCP detected
    'PARTIAL_VCP_BOOST': 0.4,  # Add 0.4 if partial VCP (2 of 3 criteria met)
    
    # Rationale: VCP catches stocks BEFORE explosive breakouts
    # Using as enhancement (not filter) to avoid being too strict
}

# 4. O'NEIL PIVOT POINT BREAKOUT
ONEIL_PIVOT_ENABLED = True  # Set to True to enable (DEFAULT: OFF for testing)

ONEIL_PIVOT_CONFIG = {
    # Pivot Detection Parameters
    'MIN_BASE_WEEKS': 5,  # Minimum 5 weeks base (relaxed from 7)
    'MAX_BASE_WEEKS': 30,  # Maximum 30 weeks
    'BASE_DEPTH_MAX': 0.25,  # Base depth max 25% (relaxed from 20%)
    'TIGHT_AREA_THRESHOLD': 0.05,  # Price within 5% range = tight
    'PIVOT_VOLUME_SURGE': 1.4,  # Breakout volume 1.4x average (relaxed from 1.5x)
    'ABOVE_MA50_REQUIRED': True,  # Must be above 50-day MA
    
    # Score Boost (Enhancement, not filter!)
    'PIVOT_SCORE_BOOST': 0.7,  # Add 0.7 to signal score if pivot breakout
    'PARTIAL_PIVOT_BOOST': 0.3,  # Add 0.3 if partial pivot (base formed, waiting for breakout)
    
    # Rationale: O'Neil's pivot catches institutional accumulation
    # Using as enhancement (not filter) to avoid being too strict
}

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

# Swing Trading - ONE DAY TRADER (INTRADAY ONLY - same day exits)
# Strategy: Catch stocks ABOUT TO move 1.0-2.0% within same day, close all positions before 3:30 PM
# Key difference: Lower ADX (12-25), focused RSI (42-68), short-term momentum
# NOT looking for strong trends (those go to positional), looking for quick intraday moves
# OPTIMIZED FOR: 50-60 trades/month, 60%+ win rate, 1.0-2.0% profit per trade (same day)
# IMPORTANT: ALL positions exit same day - NO overnight holds (force exit at 3:25 PM)
SWING_HOLD_DAYS_MIN = 1  # Same day exit only (intraday trader)
SWING_HOLD_DAYS_MAX = 1  # Same day exit only (intraday trader) - NOTE: Code forces exit at 3:25 PM regardless
SWING_ENABLED = True  # ENABLED - OPTIMIZED FOR INTRADAY: score ≥5.5, ADX 12-25, RSI 42-68, Volume ≥0.8x (stocks ABOUT TO move same day)

# Positional Trading (INTERMEDIATE) - High quality setups, faster exits
POSITIONAL_HOLD_DAYS_MIN = 5  # Minimum 5 days (was 10)
POSITIONAL_HOLD_DAYS_MAX = 15  # Maximum 15 days - FAST PROFIT TAKING
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
POSITION_MONITOR_INTERVAL = 5  # Monitor positions every 5 minutes (legacy - use strategy-specific below)
SWING_MONITOR_INTERVAL = 1  # Swing/Intraday: Monitor positions every 1 minute (ultra-fast for intraday)
POSITIONAL_MONITOR_INTERVAL = 2  # Positional: Monitor positions every 2 minutes (faster monitoring for better exits)

# INTRADAY TIME-BASED EXITS (Swing/Intraday only)
INTRADAY_PROFIT_EXIT_TIME = "15:00"  # 3:00 PM - Exit all profitable positions
INTRADAY_BREAKEVEN_EXIT_TIME = "15:15"  # 3:15 PM - Exit all positions at breakeven (if in small loss)
INTRADAY_FORCE_EXIT_TIME = "15:25"  # 3:25 PM - Force exit ALL remaining positions (no overnight risk)
INTRADAY_ENTRY_CUTOFF_TIME = "14:00"  # 2:00 PM - Last entry time (allows 1.5 hours for exit)

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
print(f"📊 Strategy: 70% Positional (5-14 days) + 30% Swing HIGH-FREQ (score ≥{MIN_SWING_SIGNAL_SCORE}, ADX ≥{ADX_MIN_TREND})")
print(f"🎯 Signal Scores: Positional ≥{MIN_SIGNAL_SCORE}/10, Swing ≥{MIN_SWING_SIGNAL_SCORE}/10 (1-2% quick profits, frequent trades)")
print(f"💰 Capital Split: ₹{INITIAL_CAPITAL * 0.70:,.0f} Positional + ₹{INITIAL_CAPITAL * 0.30:,.0f} Swing")
print(f"📈 Max Positions: {MAX_POSITIONS} per portfolio (₹10k each)")
print(f"📱 Discord: {'✅' if DISCORD_ENABLED else '❌'} • ML: {'✅' if LSTM_ENABLED else '❌'} • Paper Trading: {'✅' if PAPER_TRADING_ENABLED else '❌'}")
