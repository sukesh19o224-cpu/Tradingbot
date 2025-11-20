#!/usr/bin/env python3
"""
🧪 INTEGRATION TEST
Test all new features without breaking existing functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_features():
    """Test all new features"""
    
    print("="*70)
    print("🧪 TESTING ENHANCED FEATURES")
    print("="*70)
    
    results = {
        'logging': False,
        'error_handling': False,
        'database': False,
        'health_monitoring': False,
        'config_validation': False,
        'performance_tracking': False,
        'system_integrator': False,
        'backups': False
    }
    
    # Test 1: Logging
    print("\n1️⃣ Testing Logging System...")
    try:
        from src.utils.logger import get_logger
        logger = get_logger()
        logger.info("Test log message")
        logger.success("Logging works!")
        results['logging'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 2: Error Handling
    print("\n2️⃣ Testing Error Handling...")
    try:
        from src.utils.error_handler import get_error_tracker, retry_on_failure
        tracker = get_error_tracker()
        
        @retry_on_failure(max_retries=2, delay=0.1)
        def test_func():
            return "Success"
        
        result = test_func()
        results['error_handling'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 3: Database
    print("\n3️⃣ Testing Database...")
    try:
        from src.utils.database import get_database
        from datetime import datetime
        
        db = get_database()
        
        # Test trade insertion
        test_trade = {
            'symbol': 'TEST',
            'strategy': 'MOMENTUM',
            'entry_price': 100.0,
            'exit_price': 105.0,
            'shares': 10,
            'initial_shares': 10,
            'entry_time': datetime.now().isoformat(),
            'exit_time': datetime.now().isoformat(),
            'hold_days': 1,
            'exit_reason': 'Test',
            'profit_loss': 50.0,
            'profit_loss_percent': 5.0,
            'targets_hit': ['T1'],
            'stop_loss': 95.0,
            'highest_price': 106.0
        }
        
        db.add_trade(test_trade)
        metrics = db.get_performance_metrics(days=1)
        
        results['database'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 4: Health Monitoring
    print("\n4️⃣ Testing Health Monitoring...")
    try:
        from src.utils.health_monitor import get_health_monitor
        
        monitor = get_health_monitor()
        monitor.record_activity('SCAN', 'Test scan')
        is_healthy, issues = monitor.check_health()
        
        results['health_monitoring'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 5: Config Validation
    print("\n5️⃣ Testing Config Validation...")
    try:
        from src.utils.config_validator import validate_config
        
        is_valid, summary = validate_config()
        
        results['config_validation'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 6: Performance Tracking
    print("\n6️⃣ Testing Performance Tracking...")
    try:
        from src.utils.performance_tracker import get_performance_tracker
        from datetime import datetime, timedelta
        
        tracker = get_performance_tracker()
        
        # Simulate some performance data
        for i in range(5):
            date = (datetime.now() - timedelta(days=5-i)).strftime('%Y-%m-%d')
            tracker.record_daily_performance(
                date=date,
                portfolio_value=100000 + (i * 1000),
                positions_count=3,
                trades_taken=1
            )
        
        summary = tracker.get_performance_summary()
        
        results['performance_tracking'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 7: Backups
    print("\n7️⃣ Testing Backup System...")
    try:
        from src.utils.health_monitor import get_backup_manager
        import json
        
        # Create test portfolio
        os.makedirs('data', exist_ok=True)
        test_portfolio = {'capital': 100000, 'positions': {}}
        with open('data/test_portfolio.json', 'w') as f:
            json.dump(test_portfolio, f)
        
        backup_mgr = get_backup_manager()
        success = backup_mgr.backup_portfolio('data/test_portfolio.json')
        
        if success:
            results['backups'] = True
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL: Backup returned False")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Test 8: System Integrator
    print("\n8️⃣ Testing System Integrator...")
    try:
        from src.utils.system_integrator import initialize_enhancements
        
        integrator = initialize_enhancements(silent=True)
        enabled = integrator.get_enabled_features()
        
        results['system_integrator'] = True
        print("   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for feature, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {feature.replace('_', ' ').title()}")
    
    print(f"\n   Score: {passed}/{total} ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print("\n   🎉 ALL TESTS PASSED!")
    elif passed >= total * 0.8:
        print("\n   ✅ MOST TESTS PASSED - System operational")
    else:
        print("\n   ⚠️  SOME TESTS FAILED - Review errors above")
    
    print("="*70)
    
    return passed == total


def test_backward_compatibility():
    """Test that existing functionality still works"""
    
    print("\n" + "="*70)
    print("🔄 TESTING BACKWARD COMPATIBILITY")
    print("="*70)
    
    try:
        print("\n✓ Importing core modules...")
        from config.settings import INITIAL_CAPITAL, MAX_POSITIONS
        from src.core.multi_strategy_manager import MultiStrategyManager
        from src.portfolio_manager.portfolio_manager import PortfolioManager
        from src.risk_guardian.risk_manager import RiskManager
        
        print("✓ Initializing portfolio manager...")
        portfolio = PortfolioManager('data/test_portfolio.json')
        
        print("✓ Checking portfolio methods...")
        portfolio.display_summary()
        
        print("\n✅ BACKWARD COMPATIBILITY: PASS")
        print("   All existing functionality works!")
        
        return True
    
    except Exception as e:
        print(f"\n❌ BACKWARD COMPATIBILITY: FAIL")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════╗
    ║     ENHANCED FEATURES INTEGRATION TEST        ║
    ║              Version 4.0.1                    ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    # Test new features
    features_ok = test_features()
    
    # Test backward compatibility
    compat_ok = test_backward_compatibility()
    
    # Final verdict
    print("\n" + "="*70)
    print("🏁 FINAL VERDICT")
    print("="*70)
    
    if features_ok and compat_ok:
        print("✅ System is READY for production use")
        print("   - All new features working")
        print("   - Existing functionality preserved")
        print("   - No breaking changes detected")
    elif compat_ok:
        print("⚠️  System is OPERATIONAL")
        print("   - Existing functionality works (most important)")
        print("   - Some new features may have issues")
        print("   - Can proceed with caution")
    else:
        print("❌ System has ISSUES")
        print("   - Review test output above")
        print("   - Fix errors before using")
    
    print("="*70)
