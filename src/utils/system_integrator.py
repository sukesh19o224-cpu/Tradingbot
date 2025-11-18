"""
🔌 SYSTEM INTEGRATOR
Integrates all new features into existing system WITHOUT breaking functionality
Call this at startup to enable: logging, error handling, backups, health monitoring
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SystemIntegrator:
    """
    Integrates new features with existing system
    Non-breaking: All features are optional and enhance existing functionality
    """
    
    def __init__(self):
        self.logger = None
        self.health_monitor = None
        self.backup_manager = None
        self.db = None
        self.performance_tracker = None
        self.error_tracker = None
        
        self.features_enabled = {
            'logging': False,
            'health_monitoring': False,
            'backups': False,
            'database': False,
            'performance_tracking': False,
            'error_tracking': False,
            'config_validation': False
        }
    
    def initialize_all(self, silent=False):
        """
        Initialize all new features
        
        Args:
            silent: If True, suppress output
        
        Returns:
            dict with status of each feature
        """
        if not silent:
            print("\n" + "="*70)
            print("🔌 INITIALIZING ENHANCED FEATURES")
            print("="*70)
        
        # 1. Config Validation (always run first)
        self._init_config_validation(silent)
        
        # 2. Logging System
        self._init_logging(silent)
        
        # 3. Error Handling
        self._init_error_handling(silent)
        
        # 4. Database
        self._init_database(silent)
        
        # 5. Health Monitoring
        self._init_health_monitoring(silent)
        
        # 6. Backup System
        self._init_backup_system(silent)
        
        # 7. Performance Tracking
        self._init_performance_tracking(silent)
        
        if not silent:
            print("\n" + "="*70)
            self._display_status()
            print("="*70 + "\n")
        
        return self.features_enabled
    
    def _init_config_validation(self, silent):
        """Initialize configuration validation"""
        try:
            from src.utils.config_validator import validate_config
            
            is_valid, summary = validate_config()
            self.features_enabled['config_validation'] = True
            
            if not silent and not is_valid:
                print("\n⚠️  Configuration has issues. Review above warnings.")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Config validation: {e}")
    
    def _init_logging(self, silent):
        """Initialize logging system"""
        try:
            from src.utils.logger import get_logger
            
            self.logger = get_logger('TradingSystem')
            self.features_enabled['logging'] = True
            
            if not silent:
                print("✅ Logging system initialized")
                print("   └─ Logs will be saved to logs/ directory")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Logging: {e}")
    
    def _init_error_handling(self, silent):
        """Initialize error handling"""
        try:
            from src.utils.error_handler import get_error_tracker
            
            self.error_tracker = get_error_tracker()
            self.features_enabled['error_tracking'] = True
            
            if not silent:
                print("✅ Error handling initialized")
                print("   └─ Automatic retries enabled for API calls")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Error handling: {e}")
    
    def _init_database(self, silent):
        """Initialize database"""
        try:
            from src.utils.database import get_database
            
            self.db = get_database()
            self.features_enabled['database'] = True
            
            if not silent:
                print("✅ Database initialized")
                print("   └─ Trade history will be saved to database/trading.db")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Database: {e}")
    
    def _init_health_monitoring(self, silent):
        """Initialize health monitoring"""
        try:
            from src.utils.health_monitor import get_health_monitor
            
            self.health_monitor = get_health_monitor()
            self.features_enabled['health_monitoring'] = True
            
            if not silent:
                print("✅ Health monitoring initialized")
                print("   └─ System health will be tracked automatically")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Health monitoring: {e}")
    
    def _init_backup_system(self, silent):
        """Initialize backup system"""
        try:
            from src.utils.health_monitor import get_backup_manager
            
            self.backup_manager = get_backup_manager()
            self.features_enabled['backups'] = True
            
            # Create initial backup if portfolio exists
            if os.path.exists('data/portfolio.json'):
                self.backup_manager.backup_portfolio()
            
            if not silent:
                print("✅ Backup system initialized")
                print("   └─ Automatic backups enabled (data/backups/)")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Backup system: {e}")
    
    def _init_performance_tracking(self, silent):
        """Initialize performance tracking"""
        try:
            from src.utils.performance_tracker import get_performance_tracker
            
            self.performance_tracker = get_performance_tracker()
            self.features_enabled['performance_tracking'] = True
            
            if not silent:
                print("✅ Performance tracking initialized")
                print("   └─ Sharpe, Sortino, Alpha, Beta will be calculated")
        
        except Exception as e:
            if not silent:
                print(f"⚠️  Performance tracking: {e}")
    
    def _display_status(self):
        """Display feature status"""
        print("\n📊 FEATURE STATUS:")
        
        enabled_count = sum(1 for v in self.features_enabled.values() if v)
        total_count = len(self.features_enabled)
        
        for feature, enabled in self.features_enabled.items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}")
        
        print(f"\n   {enabled_count}/{total_count} features enabled")
    
    def record_activity(self, activity_type, details=""):
        """Record system activity (if health monitoring enabled)"""
        if self.health_monitor:
            self.health_monitor.record_activity(activity_type, details)
    
    def backup_portfolio(self):
        """Create portfolio backup (if backups enabled)"""
        if self.backup_manager:
            return self.backup_manager.backup_portfolio()
        return False
    
    def log_trade(self, trade_data):
        """Log trade to database (if database enabled)"""
        if self.db:
            try:
                self.db.add_trade(trade_data)
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to log trade: {e}")
                return False
        return False
    
    def sync_positions(self, positions_dict):
        """Sync positions to database (if database enabled)"""
        if self.db:
            try:
                self.db.sync_positions_from_json(positions_dict)
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to sync positions: {e}")
                return False
        return False
    
    def record_daily_performance(self, date, portfolio_value, **kwargs):
        """Record daily performance (if performance tracking enabled)"""
        if self.performance_tracker:
            try:
                self.performance_tracker.record_daily_performance(
                    date, portfolio_value, **kwargs
                )
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to record performance: {e}")
                return False
        return False
    
    def get_health_status(self):
        """Get current health status"""
        if self.health_monitor:
            return self.health_monitor.check_health()
        return True, []
    
    def display_performance(self):
        """Display performance metrics"""
        if self.performance_tracker:
            self.performance_tracker.display_performance()
        else:
            print("⚠️  Performance tracking not enabled")
    
    def get_enabled_features(self):
        """Get list of enabled features"""
        return [
            feature for feature, enabled in self.features_enabled.items()
            if enabled
        ]


# Global integrator instance
_integrator = None


def get_integrator():
    """Get or create global integrator instance"""
    global _integrator
    if _integrator is None:
        _integrator = SystemIntegrator()
    return _integrator


def initialize_enhancements(silent=False):
    """
    Convenience function to initialize all enhancements
    Call this in main_with_news.py
    
    Usage:
        from src.utils.system_integrator import initialize_enhancements
        integrator = initialize_enhancements()
    """
    integrator = get_integrator()
    integrator.initialize_all(silent=silent)
    return integrator


if __name__ == "__main__":
    # Test integration
    print("🧪 Testing System Integration...")
    
    integrator = initialize_enhancements(silent=False)
    
    print(f"\n📊 Enabled Features: {integrator.get_enabled_features()}")
    
    # Test health check
    is_healthy, issues = integrator.get_health_status()
    print(f"\n🏥 Health Status: {'✅ Healthy' if is_healthy else '⚠️ Issues'}")
    
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")
    
    print("\n✅ Integration test complete")
