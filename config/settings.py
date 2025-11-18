"""
🚀 MULTI-STRATEGY TRADING SYSTEM V4.0 - SETTINGS
Complete configuration file with descriptions
Last Updated: 2025-11-11
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 💰 CAPITAL MANAGEMENT
# ============================================
INITIAL_CAPITAL = 100000  # Starting capital (₹)

# ============================================
# 🛡️ RISK MANAGEMENT
# ============================================
MAX_RISK_PER_TRADE = 0.015      # 1.5% risk per trade (how much you can lose per position)
MAX_DAILY_LOSS = 0.06           # 6% max loss per day (stops trading if hit)
MAX_DRAWDOWN_PERCENT = 0.15     # 15% max drawdown (pauses trading if capital drops this much)

# ============================================
# 🎯 ENHANCED EXIT MANAGEMENT (NEW!)
# ============================================
# Trailing Stop Configuration
TRAILING_STOP_CONFIG = {
    'enabled': True,                    # Enable enhanced trailing stops
    'start_profit': 0.02,              # Start trailing at +2% profit
    'trail_distance': 0.015,           # Trail 1.5% below peak price
    'aggressive_trail_at': 0.05,       # More aggressive trailing at +5%
    'aggressive_distance': 0.025       # Trail 2.5% below peak at high profits
}

# Smart Loss Management
LOSS_RECOVERY_CONFIG = {
    'enabled': True,                    # Enable recovery detection
    'check_higher_lows': True,         # Check for higher low pattern
    'check_volume_increase': True,     # Check for increasing volume
    'check_rsi_turning': True,         # Check for RSI turning up
    'min_signals_for_hold': 2,         # Need 2+ signals to hold longer
    'max_hold_days': 5,                # Maximum 5 days
    'early_exit_no_recovery': False    # Disabled - no day 3 exit
}

# ============================================
# 📊 POSITION LIMITS
# ============================================
MAX_POSITIONS = 15              # Maximum total open positions at once (increased for better capital use)
MAX_ENTRIES_PER_DAY = 10        # Maximum new entries in one day
MAX_PER_STOCK = 0.25            # Maximum 25% capital per single stock

# ============================================
# 🔄 DYNAMIC CAPITAL ALLOCATION (NEW!)
# ============================================
ENABLE_DYNAMIC_ALLOCATION = True    # Enable smart capital reallocation
DYNAMIC_ALLOCATION_CONFIG = {
    'max_capital_utilization': 0.90,    # Use up to 90% of capital
    'reallocation_threshold': 0.15,     # Reallocate if need 15%+ more capital
    'min_profit_to_keep': 0.02,         # Keep positions with 2%+ profit
    'max_loss_to_exit': -0.02,          # Exit losing positions > -2%
    'allow_strategy_switching': True    # Allow exiting low-priority positions
}

# ============================================
# 📈 STOCK FILTERS (Applied to ALL strategies)
# ============================================
MIN_PRICE = 20                  # Minimum stock price (₹)
MAX_PRICE = 10000              # Maximum stock price (₹)
MIN_VOLUME_CR = 2              # Minimum daily volume (in crores)
MIN_DAILY_MOVE = 0.8           # Minimum daily price movement (%)

# ============================================
# ⏰ TIMING SETTINGS
# ============================================
MARKET_OPEN = "09:15"          # Market opening time (IST)
MARKET_CLOSE = "15:30"         # Market closing time (IST)
SCAN_TIME = "15:45"            # EOD scan time (IST) - Builds watchlist for next day

ENABLE_MORNING_CHECK = True    # Enable morning entry checks
MORNING_CHECK_TIMES = ["09:15", "09:45"]  # Pre-market entry checks

# Monitoring intervals (in minutes)
POSITION_MONITOR_INTERVAL = 3   # How often to check stops/targets (3 min = 20 checks/hour)
SCAN_INTERVAL = 10              # How often to scan for new opportunities (10 min = 6 scans/hour)

# ============================================
# 🎯 REGIME DETECTION
# ============================================
# System detects market condition and activates appropriate strategy
ENABLE_REGIME_DETECTION = True  # True = Auto-switch strategies based on market
                                # False = Run all strategies always

REGIME_LOOKBACK_DAYS = 20      # Days of data to analyze for regime
REGIME_CHECK_INTERVAL = 60     # How often to check regime (minutes)

REGIME_INDICATORS = {
    'ADX_PERIOD': 14,                    # Period for ADX calculation
    'ADX_TRENDING_THRESHOLD': 25,        # Above this = trending market
    'VOLATILITY_LOOKBACK': 20,           # Days to calculate volatility
    'MA_PERIODS': [20, 50]               # Moving average periods to check
}

# ============================================
# 🚀 STRATEGY 1: MOMENTUM
# ============================================
# For trending/bull markets
# Buys stocks with strong upward momentum and volume

MOMENTUM = {
    # Entry criteria
    'MIN_5D_MOMENTUM': 3.0,              # Stock must be up 3%+ in last 5 days
    'MIN_20D_MOMENTUM': 5.0,             # Stock must be up 5%+ in last 20 days
    'MIN_VOLUME_RATIO': 1.5,             # Volume must be 1.5x above average
    'MAX_GAP_UP': 0.03,                  # Reject if gap up > 3% (too risky)
    'REQUIRE_MA_ALIGNMENT': True,        # Must be above MA20 and MA50
    'REQUIRE_WEEKLY_BULLISH': False,     # Weekly trend must also be bullish
    'MIN_TREND_STRENGTH': 50,            # Trend strength score (0-100)
    
    # Exit criteria
    'TARGETS': [0.05, 0.08, 0.12],       # Target levels: 5%, 8%, 12%
    'STOP_LOSS': 0.07,                   # Stop loss: 7% below entry
    'TIME_STOP_DAYS': 5,                 # Exit after 5 trading days if no momentum
    
    # Position limits (Dynamic: Adjusts based on regime)
    'max_positions': 10,                 # Max 10 momentum positions (was 3)
    'min_score': 35,                     # Minimum score to qualify (lowered)
    
    # Capital allocation (if not using regime detection)
    'capital_allocation': 0.40,          # 40% of capital for momentum
    
    # When to use this strategy
    'market_regimes': ['TRENDING_UP', 'STRONG_BULL']
}

# ============================================
# 🔄 STRATEGY 2: MEAN REVERSION
# ============================================
# For choppy/ranging markets
# Buys quality stocks that have temporarily dipped

MEAN_REVERSION = {
    # Entry criteria
    'MAX_DISTANCE_FROM_MA': 0.05,        # Stock 2-5% below MA20
    'MIN_DISTANCE_FROM_MA': 0.02,        # At least 2% below MA20
    'REQUIRE_ABOVE_MA50': True,          # Must be above MA50 (quality filter)
    'MAX_RSI': 35,                       # RSI below 35 (oversold)
    'MIN_SUPPORT_BOUNCES': 2,            # Bounced at support 2+ times
    'ENTRY_BELOW_MA': True,              # Entry when below MA20
    
    # Exit criteria
    'TARGETS': [0.03, 0.05, 0.08],       # Target levels: 3%, 5%, 8%
    'STOP_LOSS': 0.05,                   # Stop loss: 5% below entry
    'TIME_STOP_DAYS': 5,                 # Exit after 5 days (was 3) - allow time to develop
    
    # Position limits (Dynamic: Adjusts based on regime)
    'max_positions': 12,                 # Max 12 mean reversion positions (was 3)
    'min_score': 35,                     # Minimum score to qualify (lowered from 40)
    
    # Capital allocation (if not using regime detection)
    'capital_allocation': 0.35,          # 35% of capital for mean reversion
    
    # When to use this strategy
    'market_regimes': ['CHOPPY', 'RANGING', 'WEAK']
}

# ============================================
# 💥 STRATEGY 3: BREAKOUT
# ============================================
# For consolidation periods
# Buys stocks breaking out of tight ranges

BREAKOUT = {
    # Entry criteria
    'CONSOLIDATION_DAYS': 5,             # Must consolidate for 5+ days
    'MAX_CONSOLIDATION_RANGE': 0.05,     # Range must be within 5%
    'MIN_VOLUME_SURGE': 2.0,             # Volume 2x+ on breakout
    'REQUIRE_ATR_EXPANSION': True,       # ATR must be expanding
    'BREAKOUT_CONFIRMATION': 0.01,       # Must break 1% above high
    
    # Exit criteria
    'TARGETS': [0.06, 0.10, 0.15],       # Target levels: 6%, 10%, 15%
    'STOP_LOSS': 0.06,                   # Stop loss: 6% below entry
    'TIME_STOP_DAYS': 4,                 # Exit after 4 trading days if no momentum
    
    # Position limits (Dynamic: Adjusts based on regime)
    'max_positions': 5,                  # Max 5 breakout positions (was 2)
    'min_score': 40,                     # Minimum score to qualify
    
    # Capital allocation (if not using regime detection)
    'capital_allocation': 0.25,          # 25% of capital for breakout
    
    # When to use this strategy
    'market_regimes': ['CONSOLIDATION', 'NEUTRAL']
}

# ============================================
# 🎯 MULTI-STRATEGY CONFIGURATION
# ============================================
# Combine all strategies into one config
STRATEGIES = {
    'MOMENTUM': {
        'enabled': True,                 # Enable/disable this strategy
        'capital_allocation': MOMENTUM['capital_allocation'],
        'max_positions': MOMENTUM['max_positions'],
        'min_score': MOMENTUM['min_score'],
        'market_regimes': MOMENTUM['market_regimes']
    },
    'MEAN_REVERSION': {
        'enabled': True,
        'capital_allocation': MEAN_REVERSION['capital_allocation'],
        'max_positions': MEAN_REVERSION['max_positions'],
        'min_score': MEAN_REVERSION['min_score'],
        'market_regimes': MEAN_REVERSION['market_regimes']
    },
    'BREAKOUT': {
        'enabled': True,
        'capital_allocation': BREAKOUT['capital_allocation'],
        'max_positions': BREAKOUT['max_positions'],
        'min_score': BREAKOUT['min_score'],
        'market_regimes': BREAKOUT['market_regimes']
    }
}

# ============================================
# 🎯 TARGET CONFIGURATION (For partial exits)
# ============================================
# NOT USED - Strategy-specific targets above are used instead
# This is kept for backward compatibility
TARGETS = {
    'T1': {'level': 0.03, 'exit_percent': 0.40},  # Sell 40% at 3%
    'T2': {'level': 0.05, 'exit_percent': 0.40},  # Sell 40% at 5%
    'T3': {'level': 0.08, 'exit_percent': 0.20}   # Sell 20% at 8%
}

# ============================================
# ⏰ TIME STOPS (For backward compatibility)
# ============================================
# NOT USED - Strategy-specific time stops above are used instead
MAX_HOLD_DAYS = 5  # Maximum hold period

# ============================================
# 🔔 DISCORD ALERTS
# ============================================
# Get webhook URL from .env file
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# To set up Discord alerts:
# 1. Create .env file in project root
# 2. Add: DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
# 3. Restart system

# ============================================
# 📊 SCANNER SETTINGS
# ============================================
TOP_STOCKS = 20                # Top stocks from EOD scan for morning checks
EOD_SCAN_LIMIT = 500          # How many stocks to save in daily watchlist

# Minimum score to consider (0-100)
# Lower = more opportunities, Higher = better quality
MIN_SCORE = 35

# ============================================
# 🎯 SECTOR & CORRELATION FILTERS
# ============================================
# Prevent concentration in one sector or correlated stocks
ENABLE_SECTOR_CHECK = True         # Set False to disable sector limits
MAX_SECTOR_ALLOCATION = 0.50       # Max 50% capital in one sector (was 40%)
ENABLE_CORRELATION_CHECK = True    # Set False to disable correlation checks
MAX_CORRELATION = 0.70             # Reject if correlation > 0.70 with existing positions
MIN_SECTOR_DIVERSITY = 2           # Need positions in at least 2 different sectors

# ============================================
# ⚡ MULTI-TIMEFRAME SETTINGS (NEW!)
# ============================================
# Uses both daily and 15-min candles for better entry timing
ENABLE_MULTI_TIMEFRAME = True  # Enable 15-min confirmation

MTF_CANDLE_INTERVAL = '15m'    # Intraday timeframe (15m recommended)
MTF_LOOKBACK_CANDLES = 10      # Number of 15-min candles to analyze

# ============================================
# 💾 DATA CACHING (NEW!)
# ============================================
# Speeds up scans from 3-5 min to 30 seconds
ENABLE_CACHING = True          # Enable data caching
CACHE_DIR = 'data/cache'       # Cache storage location

# ============================================
# 📅 TRADING DAYS CALCULATION (NEW!)
# ============================================
# Counts only trading days (Mon-Fri), excludes weekends
USE_TRADING_DAYS = True        # True = Count only trading days
                               # False = Count calendar days (includes weekends)

# ============================================
# 📝 IMPORTANT NOTES
# ============================================
"""
QUICK TUNING GUIDE:

🎯 To get MORE opportunities:
- Lower min_score values (35 → 30)
- Increase max_positions (3 → 5)
- Lower MIN_5D_MOMENTUM (3.0 → 2.0)
- Raise MAX_RSI (35 → 40)

🎯 To get BETTER quality (fewer trades):
- Raise min_score values (35 → 45)
- Decrease max_positions (3 → 2)
- Raise MIN_5D_MOMENTUM (3.0 → 4.0)
- Lower MAX_RSI (35 → 30)

🎯 To be more AGGRESSIVE:
- Increase MAX_RISK_PER_TRADE (0.015 → 0.02)
- Increase MAX_POSITIONS (8 → 10)
- Widen stop losses (0.07 → 0.08)

🎯 To be more CONSERVATIVE:
- Decrease MAX_RISK_PER_TRADE (0.015 → 0.01)
- Decrease MAX_POSITIONS (8 → 5)
- Tighten stop losses (0.07 → 0.05)

🎯 For faster monitoring (more API calls):
- POSITION_MONITOR_INTERVAL = 1  # Every 1 min
- SCAN_INTERVAL = 5              # Every 5 min

🎯 For slower monitoring (fewer API calls):
- POSITION_MONITOR_INTERVAL = 5  # Every 5 min
- SCAN_INTERVAL = 15             # Every 15 min
"""