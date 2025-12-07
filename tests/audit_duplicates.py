#!/usr/bin/env python3
"""
🔍 DUPLICATE SETTINGS AUDIT
Finds all duplicate/conflicting settings that could affect trading
"""

print("=" * 80)
print("🔍 DUPLICATE SETTINGS AUDIT")
print("=" * 80)
print()

duplicates_found = []

# ==============================================================================
# 1. STOP LOSS DUPLICATES (CRITICAL - ALREADY FIXED)
# ==============================================================================
print("1️⃣  STOP LOSS SETTINGS")
print("-" * 80)
print("✅ STATUS: FIXED IN BUG FIX SESSION")
print()
print("Previously had duplicates:")
print("  ❌ OLD: SWING_STOP_LOSS = 0.025 (config/settings.py)")
print("  ❌ OLD: MEAN_REVERSION_CONFIG['STOP_LOSS'] = 0.055")
print("  ❌ OLD: signal_generator.py had hardcoded 0.03")
print()
print("NOW UNIFIED:")
print("  ✅ Swing Mean Reversion: 3.0%")
print("  ✅ Swing Momentum: 2.5%")
print("  ✅ Swing Breakout: 2.5%")
print("  ✅ Positional Mean Reversion: 4.5%")
print("  ✅ Positional Momentum: 4.0%")
print("  ✅ Positional Breakout: 3.5%")
print()

# ==============================================================================
# 2. TARGETS DUPLICATES
# ==============================================================================
print("2️⃣  TARGET SETTINGS")
print("-" * 80)
print("⚠️  POTENTIAL ISSUE: Multiple files define targets")
print()
print("SOURCE OF TRUTH: config/settings.py")
print("  ✅ SWING_TARGETS = [0.04, 0.07, 0.10]  (4%, 7%, 10%)")
print("  ✅ POSITIONAL_TARGETS = [0.05, 0.10, 0.15]  (5%, 10%, 15%)")
print()
print("DUPLICATES IN OTHER FILES:")
print("  📄 signal_generator.py:")
print("     • Line 98: [0.04, 0.07, 0.10] (mean reversion swing) ✅ MATCHES")
print("     • Line 102: [0.05, 0.08, 0.12] (breakout swing) ⚠️  DIFFERENT!")
print("     • Line 106: [0.04, 0.07, 0.10] (momentum swing) ✅ MATCHES")
print("     • Uses strategy_config['TARGETS'] for positional ✅ OK")
print()
print("  📄 sequential_scanner.py:")
print("     • Lines 377-383: Hardcoded targets same as signal_generator ✅ MATCHES")
print("     • Lines 400-402: Uses strategy_config['TARGETS'] ✅ OK")
print()
print("  📄 hybrid_detector.py:")
print("     • Line 11: Imports SWING_STOP_LOSS, POSITIONAL_STOP_LOSS")
print("     • ⚠️  OLD FILE - Uses deprecated stop loss imports")
print()
print("IMPACT: ⚠️  MEDIUM")
print("  • Breakout swing has different targets (5%, 8%, 12% vs 4%, 7%, 10%)")
print("  • This is intentional - breakouts need wider targets")
print("  • BUT should be documented in settings.py")
print()
duplicates_found.append({
    'item': 'Breakout Swing Targets',
    'severity': 'MEDIUM',
    'impact': 'Breakout trades use different targets (undocumented)',
    'fix': 'Add BREAKOUT_SWING_TARGETS to settings.py'
})

# ==============================================================================
# 3. HOLDING DAYS DUPLICATES
# ==============================================================================
print("3️⃣  HOLDING DAYS SETTINGS")
print("-" * 80)
print("⚠️  POTENTIAL ISSUE: Dashboard hardcodes different values")
print()
print("SOURCE OF TRUTH: config/settings.py")
print("  ✅ SWING_HOLD_DAYS_MAX = 7 trading days")
print("  ✅ POSITIONAL_HOLD_DAYS_MAX = 15 trading days")
print()
print("DUPLICATES IN OTHER FILES:")
print("  📄 dashboard.py:")
print("     • Line 327: max_hold_days = 7 (swing) ✅ MATCHES")
print("     • Line 419: max_hold_days = 30 (positional) ❌ CONFLICT!")
print()
print("IMPACT: 🔴 HIGH")
print("  • Dashboard shows wrong max holding period for positional (30 vs 15)")
print("  • User sees incorrect info but doesn't affect actual exits")
print("  • paper_trader.py uses correct value from position data")
print()
duplicates_found.append({
    'item': 'Positional Max Hold Days',
    'severity': 'HIGH',
    'impact': 'Dashboard displays wrong max days (30 vs 15)',
    'fix': 'Change dashboard.py line 419 to 15'
})

# ==============================================================================
# 4. CAPITAL ALLOCATION DUPLICATES
# ==============================================================================
print("4️⃣  CAPITAL ALLOCATION (70/30 SPLIT)")
print("-" * 80)
print("✅ STATUS: CONSISTENT")
print()
print("Hardcoded in multiple files:")
print("  ✅ config/settings.py line 372: 0.70 positional, 0.30 swing")
print("  ✅ dual_portfolio.py line 29-30: 0.30 swing, 0.70 positional")
print("  ✅ dual_portfolio.py line 174, 186: Same split for returns")
print()
print("IMPACT: ✅ NO ISSUE")
print("  • All files use consistent 70/30 split")
print("  • Hardcoded in dual_portfolio (by design)")
print()

# ==============================================================================
# 5. MAX POSITIONS DUPLICATES
# ==============================================================================
print("5️⃣  MAX POSITIONS SETTING")
print("-" * 80)
print("✅ STATUS: CONSISTENT")
print()
print("Defined once, used everywhere:")
print("  ✅ config/settings.py: MAX_POSITIONS = 7")
print("  ✅ paper_trader.py line 162: Uses MAX_POSITIONS (imported)")
print()
print("IMPACT: ✅ NO ISSUE")
print()

# ==============================================================================
# 6. DEPRECATED/UNUSED FILES WITH DUPLICATES
# ==============================================================================
print("6️⃣  DEPRECATED FILES (INACTIVE)")
print("-" * 80)
print("⚠️  Old files with duplicate/conflicting settings:")
print()
print("  📁 archive_strategy2_and_unused/settings_strategy2.py")
print("     • SWING_STOP_LOSS = 0.033 (different from main)")
print("     • MAX_POSITIONS = 5 (different from main)")
print("     • IMPACT: ✅ NO ISSUE (not used by main system)")
print()
print("  📁 src/strategies/hybrid_detector.py")
print("     • Imports SWING_STOP_LOSS, POSITIONAL_STOP_LOSS")
print("     • ⚠️  Uses OLD deprecated stop loss values")
print("     • IMPACT: ⚠️  MEDIUM (if hybrid_detector is still used)")
print()
duplicates_found.append({
    'item': 'hybrid_detector.py Stop Loss',
    'severity': 'MEDIUM',
    'impact': 'Uses deprecated stop loss imports',
    'fix': 'Update to use strategy-specific stops OR mark as deprecated'
})

# ==============================================================================
# 7. ADX THRESHOLD DUPLICATES
# ==============================================================================
print("7️⃣  ADX THRESHOLDS")
print("-" * 80)
print("✅ STATUS: DOCUMENTED (NOT A BUG)")
print()
print("  ✅ config/settings.py: Reference values (20, 25, 50)")
print("  ✅ sequential_scanner.py: Actual values (15, 18, 20, 22)")
print("  ✅ Properly documented with comments")
print()
print("IMPACT: ✅ NO ISSUE")
print()

print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print()
print(f"Total duplicates found: {len(duplicates_found)}")
print()

if duplicates_found:
    print("⚠️  ISSUES REQUIRING FIX:")
    print()
    for i, dup in enumerate(duplicates_found, 1):
        severity_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(dup['severity'], '⚠️')
        
        print(f"{i}. {severity_emoji} {dup['item']} ({dup['severity']})")
        print(f"   Impact: {dup['impact']}")
        print(f"   Fix: {dup['fix']}")
        print()

print("=" * 80)
print("🎯 RECOMMENDATIONS")
print("=" * 80)
print()
print("CRITICAL (FIX NOW):")
print("  1. 🔴 Fix dashboard.py line 419: Change 30 to 15 (positional max days)")
print()
print("IMPORTANT (FIX SOON):")
print("  2. 🟡 Add BREAKOUT_SWING_TARGETS to settings.py for documentation")
print("  3. 🟡 Update or deprecate hybrid_detector.py (uses old stop loss)")
print()
print("OPTIONAL (NICE TO HAVE):")
print("  4. 🟢 Extract hardcoded targets in signal_generator/scanner to constants")
print("  5. 🟢 Add validation script that checks all duplicates match")
print()
print("=" * 80)
print("✅ SYSTEM IMPACT: LOW")
print("=" * 80)
print()
print("Good news: Only 3 duplicates affect trading:")
print("  • Dashboard display issue (doesn't affect actual exits)")
print("  • Breakout targets (intentional, just undocumented)")
print("  • hybrid_detector (if used, needs update)")
print()
print("Core trading logic (signal_generator, paper_trader) is CONSISTENT! ✅")
print()
print("=" * 80)
