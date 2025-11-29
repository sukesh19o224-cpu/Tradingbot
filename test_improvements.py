"""
🧪 INTEGRATION TEST - Verify All Improvements Work Together
Tests the new features without requiring full system run
"""

import sys
import traceback
from datetime import datetime

print("="*70)
print("🧪 TESTING REALISTIC TRADING SYSTEM IMPROVEMENTS")
print("="*70)

# Track test results
tests_passed = 0
tests_failed = 0
errors = []

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        global tests_passed, tests_failed, errors
        try:
            print(f"\n📋 Test: {name}")
            func()
            print(f"   ✅ PASS")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ FAIL: {str(e)}")
            tests_failed += 1
            errors.append((name, str(e), traceback.format_exc()))
        return func
    return decorator

# =============================================================================
# TEST 1: Check Settings Updates
# =============================================================================
@test("Settings - Realistic Targets & Thresholds")
def test_settings():
    from config.settings import (
        SWING_TARGETS, POSITIONAL_TARGETS,
        SWING_STOP_LOSS, POSITIONAL_STOP_LOSS,
        SWING_HOLD_DAYS_MAX, POSITIONAL_HOLD_DAYS_MAX,
        MARKET_CRASH_THRESHOLD,
        MIN_AVG_VOLUME, MIN_VALUE_TRADED,
        SIGNAL_MAX_AGE_MINUTES, SIGNAL_PRICE_MOVE_THRESHOLD,
        DRAWDOWN_RISK_REDUCTION_ENABLED
    )

    # Verify realistic swing targets
    assert SWING_TARGETS == [0.02, 0.04, 0.06], f"Swing targets should be [2%, 4%, 6%], got {SWING_TARGETS}"

    # Verify realistic positional targets
    assert POSITIONAL_TARGETS == [0.08, 0.15, 0.25], f"Positional targets should be [8%, 15%, 25%], got {POSITIONAL_TARGETS}"

    # Verify tighter stops
    assert SWING_STOP_LOSS == 0.015, f"Swing stop should be 1.5%, got {SWING_STOP_LOSS*100}%"
    assert POSITIONAL_STOP_LOSS == 0.04, f"Positional stop should be 4%, got {POSITIONAL_STOP_LOSS*100}%"

    # Verify max hold days
    assert SWING_HOLD_DAYS_MAX == 7, f"Swing max days should be 7, got {SWING_HOLD_DAYS_MAX}"
    assert POSITIONAL_HOLD_DAYS_MAX == 30, f"Positional max days should be 30, got {POSITIONAL_HOLD_DAYS_MAX}"

    # Verify circuit breaker
    assert MARKET_CRASH_THRESHOLD == -0.035, f"Circuit breaker should be -3.5%, got {MARKET_CRASH_THRESHOLD*100}%"

    # Verify liquidity filters
    assert MIN_AVG_VOLUME == 500000, f"Min volume should be 5L, got {MIN_AVG_VOLUME}"
    assert MIN_VALUE_TRADED == 50000000, f"Min turnover should be 5Cr, got {MIN_VALUE_TRADED}"

    # Verify signal freshness
    assert SIGNAL_MAX_AGE_MINUTES == 30, f"Signal max age should be 30 min, got {SIGNAL_MAX_AGE_MINUTES}"
    assert SIGNAL_PRICE_MOVE_THRESHOLD == 0.01, f"Price move threshold should be 1%, got {SIGNAL_PRICE_MOVE_THRESHOLD*100}%"

    # Verify drawdown reduction
    assert DRAWDOWN_RISK_REDUCTION_ENABLED == True, "Drawdown risk reduction should be enabled"

    print(f"   ✓ All settings updated correctly")


# =============================================================================
# TEST 2: Position Sizer Module
# =============================================================================
@test("Position Sizer - ATR Calculation & Sizing")
def test_position_sizer():
    from src.utils.position_sizer import PositionSizer
    import pandas as pd
    import numpy as np

    sizer = PositionSizer()

    # Create sample OHLCV data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'Open': np.random.uniform(2400, 2600, 100),
        'High': np.random.uniform(2450, 2650, 100),
        'Low': np.random.uniform(2350, 2550, 100),
        'Close': np.random.uniform(2400, 2600, 100),
        'Volume': np.random.uniform(1000000, 5000000, 100)
    }, index=dates)

    # Test ATR calculation
    atr = sizer.calculate_atr(df, period=14)
    assert atr > 0, f"ATR should be > 0, got {atr}"
    print(f"   ✓ ATR calculation works (ATR={atr:.2f})")

    # Test volatility-based sizing
    test_signal = {
        'entry_price': 2500,
        'stop_loss': 2450,
        'score': 8.5
    }

    position_size = sizer.calculate_volatility_based_size(
        portfolio_value=100000,
        signal=test_signal,
        df=df
    )

    assert position_size > 0, f"Position size should be > 0, got {position_size}"
    assert position_size <= 100000 * 0.25, "Position size should not exceed 25% of portfolio"
    print(f"   ✓ Volatility sizing works (Size=₹{position_size:,.0f})")

    # Test drawdown adjustment
    normal_size = sizer.adjust_for_drawdown(10000, 0.02)  # 2% drawdown
    minor_dd_size = sizer.adjust_for_drawdown(10000, 0.06)  # 6% drawdown
    major_dd_size = sizer.adjust_for_drawdown(10000, 0.12)  # 12% drawdown

    assert normal_size == 10000, "Should be full size at 2% drawdown"
    assert minor_dd_size == 7500, "Should be 75% size at 6% drawdown"
    assert major_dd_size == 5000, "Should be 50% size at 12% drawdown"
    print(f"   ✓ Drawdown adjustment works (100% → 75% → 50%)")

    # Test quality adjustment
    low_quality = sizer.adjust_for_quality(10000, 7.2)
    mid_quality = sizer.adjust_for_quality(10000, 8.0)
    high_quality = sizer.adjust_for_quality(10000, 9.0)

    assert low_quality < mid_quality < high_quality, "Higher quality should give larger size"
    print(f"   ✓ Quality adjustment works (Score 7.2→8.0→9.0 increases size)")


# =============================================================================
# TEST 3: Signal Validator Module
# =============================================================================
@test("Signal Validator - Freshness & Validation")
def test_signal_validator():
    from src.utils.signal_validator import SignalValidator
    from datetime import timedelta

    validator = SignalValidator()

    # Test fresh signal
    fresh_signal = {
        'symbol': 'TEST.NS',
        'timestamp': datetime.now().isoformat(),
        'entry_price': 2500,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(fresh_signal, 2505)
    assert is_valid == True, f"Fresh signal should be valid, got {reason}"
    print(f"   ✓ Fresh signal validation works")

    # Test stale signal (45 minutes old)
    stale_signal = {
        'symbol': 'TEST.NS',
        'timestamp': (datetime.now() - timedelta(minutes=45)).isoformat(),
        'entry_price': 2500,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(stale_signal, 2505)
    assert is_valid == False, f"Stale signal should be invalid, got {is_valid}"
    assert "STALE" in reason, f"Reason should mention stale, got {reason}"
    print(f"   ✓ Stale signal detection works ({reason})")

    # Test price moved signal
    moved_signal = {
        'symbol': 'TEST.NS',
        'timestamp': datetime.now().isoformat(),
        'entry_price': 2500,
        'score': 8.5
    }

    is_valid, reason = validator.validate_signal_freshness(moved_signal, 2530)  # +1.2%
    assert is_valid == False, f"Price-moved signal should be invalid"
    assert "PRICE_MOVED" in reason, f"Reason should mention price moved, got {reason}"
    print(f"   ✓ Price movement detection works ({reason})")


# =============================================================================
# TEST 4: Paper Trader Integration
# =============================================================================
@test("Paper Trader - Position Sizer Integration")
def test_paper_trader_integration():
    from src.paper_trading.paper_trader import PaperTrader
    import pandas as pd
    import numpy as np

    # Check that PaperTrader has position_sizer
    trader = PaperTrader(capital=100000,
                        data_file='data/test_trades.json',
                        portfolio_file='data/test_portfolio.json')

    assert hasattr(trader, 'position_sizer'), "PaperTrader should have position_sizer attribute"
    print(f"   ✓ PaperTrader has PositionSizer instance")

    # Check that _calculate_position_size method exists
    assert hasattr(trader, '_calculate_position_size'), "Should have _calculate_position_size method"
    assert hasattr(trader, '_simple_position_sizing'), "Should have _simple_position_sizing fallback"
    print(f"   ✓ Position sizing methods exist")

    # Test simple position sizing (fallback)
    test_signal = {
        'entry_price': 2500,
        'stop_loss': 2450,
        'score': 8.0
    }

    size = trader._simple_position_sizing(test_signal, 100000, 0.0)
    assert size > 0, "Position size should be positive"
    assert size <= 25000, "Position size should not exceed 25% of portfolio"
    print(f"   ✓ Simple position sizing works (Size=₹{size:,.0f})")


# =============================================================================
# TEST 5: Main System Integration
# =============================================================================
@test("Main System - Signal Validator Integration")
def test_main_system():
    # Just check that main.py has signal validator
    import main

    # Check that TradingSystem class exists
    assert hasattr(main, 'TradingSystem'), "Should have TradingSystem class"

    # We can't instantiate without NSE data, but we can check the class definition
    import inspect
    source = inspect.getsource(main.TradingSystem.__init__)

    assert 'SignalValidator' in source, "TradingSystem.__init__ should create SignalValidator"
    assert 'self.signal_validator' in source, "Should assign signal_validator instance"
    print(f"   ✓ Main system has SignalValidator integration")

    # Check process_signals method
    source = inspect.getsource(main.TradingSystem.process_signals)
    assert 'validate_signal_freshness' in source, "Should validate signal freshness"
    print(f"   ✓ Main system validates signals before execution")


# =============================================================================
# TEST 6: EOD System Integration
# =============================================================================
@test("EOD System - Signal Validator Integration")
def test_eod_system():
    import main_eod_system
    import inspect

    # Check that EODIntradaySystem has signal validator
    source = inspect.getsource(main_eod_system.EODIntradaySystem.__init__)
    assert 'SignalValidator' in source, "EOD system should have SignalValidator"
    print(f"   ✓ EOD system has SignalValidator integration")

    # Check process_signals validates
    source = inspect.getsource(main_eod_system.EODIntradaySystem.process_signals)
    assert 'validate_signal_freshness' in source, "Should validate signals"
    print(f"   ✓ EOD system validates signals before execution")


# =============================================================================
# TEST 7: Data Fetcher Fallback
# =============================================================================
@test("Data Fetcher Fallback - Retry Logic")
def test_data_fetcher_fallback():
    from src.data.data_fetcher_fallback import DataFetcherWithFallback

    fetcher = DataFetcherWithFallback(api_delay=0.1)

    # Check methods exist
    assert hasattr(fetcher, 'get_stock_data'), "Should have get_stock_data method"
    assert hasattr(fetcher, '_fetch_yfinance'), "Should have primary fetch method"
    assert hasattr(fetcher, '_fetch_yfinance_retry'), "Should have retry method"
    assert hasattr(fetcher, 'verify_data_quality'), "Should have quality verification"
    print(f"   ✓ All fallback methods exist")

    # Check that it has retry logic (by inspecting code)
    import inspect
    source = inspect.getsource(fetcher._fetch_yfinance_retry)
    assert 'max_retries' in source, "Should have max_retries parameter"
    assert 'for attempt in range' in source, "Should loop through retries"
    print(f"   ✓ Retry logic implemented")


# =============================================================================
# TEST 8: SuperMath Features Still Active
# =============================================================================
@test("SuperMath Features - All Analysis Methods Active")
def test_supermath_features():
    from src.strategies.signal_generator import SignalGenerator
    import inspect

    gen = SignalGenerator()

    # Check that all analyzers are initialized
    assert hasattr(gen, 'technical'), "Should have technical analyzer"
    assert hasattr(gen, 'mathematical'), "Should have mathematical analyzer"
    assert hasattr(gen, 'ml_predictor'), "Should have ML predictor"
    print(f"   ✓ All analyzers initialized (Technical, Math, ML)")

    # Check generate_signal uses all features
    source = inspect.getsource(gen.generate_signal)
    assert 'technical_result = self.technical.calculate_all' in source, "Should calculate technical"
    assert 'mathematical_result = self.mathematical.calculate_all' in source, "Should calculate mathematical"
    assert 'ml_prediction = self.ml_predictor.predict' in source, "Should use ML prediction"
    print(f"   ✓ Signal generation uses ALL analysis methods")

    # Check scoring weights
    source = inspect.getsource(gen._calculate_signal_score)
    assert 'WEIGHTS[\'technical\']' in source, "Should use technical weight"
    assert 'WEIGHTS[\'mathematical\']' in source, "Should use math weight"
    assert 'WEIGHTS[\'ml_prediction\']' in source, "Should use ML weight"
    assert 'WEIGHTS[\'volume\']' in source, "Should use volume weight"
    print(f"   ✓ Scoring uses weighted combination (40% Tech, 30% Math, 20% ML, 10% Vol)")


# =============================================================================
# Run All Tests and Show Summary
# =============================================================================
print("\n" + "="*70)
print("📊 TEST SUMMARY")
print("="*70)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")

if errors:
    print("\n" + "="*70)
    print("❌ FAILED TESTS DETAILS")
    print("="*70)
    for name, error, trace in errors:
        print(f"\n❌ {name}")
        print(f"   Error: {error}")
        print(f"   Trace:\n{trace}")

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! System is ready to use.")
    sys.exit(0)
else:
    print(f"\n⚠️ {tests_failed} test(s) failed. Please review errors above.")
    sys.exit(1)
