"""
✅ CONFIGURATION VALIDATOR
Validates settings.py and environment variables on startup
Prevents misconfigurations that could cause issues
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ConfigValidator:
    """
    Validates configuration before system starts
    Non-breaking: Just warns about issues, doesn't stop system
    """
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """Run all validation checks"""
        print("\n" + "="*70)
        print("✅ VALIDATING CONFIGURATION")
        print("="*70)
        
        self._validate_capital_settings()
        self._validate_risk_settings()
        self._validate_strategy_settings()
        self._validate_timing_settings()
        self._validate_environment()
        self._validate_directories()
        
        self._display_results()
        
        return len(self.errors) == 0
    
    def _validate_capital_settings(self):
        """Validate capital and position settings"""
        try:
            from config.settings import (
                INITIAL_CAPITAL, MAX_POSITIONS, MAX_PER_STOCK,
                MAX_ENTRIES_PER_DAY
            )
            
            # Check reasonable capital
            if INITIAL_CAPITAL < 10000:
                self.warnings.append(
                    f"INITIAL_CAPITAL ({INITIAL_CAPITAL}) is very low. Consider 50,000+ for better diversification."
                )
            
            if INITIAL_CAPITAL > 10000000:
                self.warnings.append(
                    f"INITIAL_CAPITAL ({INITIAL_CAPITAL:,.0f}) is very high. Ensure liquidity handling."
                )
            
            # Check position limits
            if MAX_POSITIONS < 1:
                self.errors.append("MAX_POSITIONS must be at least 1")
            
            if MAX_POSITIONS > 20:
                self.warnings.append(
                    f"MAX_POSITIONS ({MAX_POSITIONS}) is high. May be hard to monitor all positions."
                )
            
            # Check per-stock allocation
            if MAX_PER_STOCK > 0.5:
                self.warnings.append(
                    f"MAX_PER_STOCK ({MAX_PER_STOCK*100}%) is high. Risk concentration in single stock."
                )
            
            # Check daily entries
            if MAX_ENTRIES_PER_DAY > 15:
                self.warnings.append(
                    f"MAX_ENTRIES_PER_DAY ({MAX_ENTRIES_PER_DAY}) is high. May overtrade."
                )
            
        except ImportError as e:
            self.errors.append(f"Failed to import capital settings: {e}")
    
    def _validate_risk_settings(self):
        """Validate risk management settings"""
        try:
            from config.settings import (
                MAX_RISK_PER_TRADE, MAX_DAILY_LOSS, 
                MAX_DRAWDOWN_PERCENT, STOP_LOSS_PERCENT
            )
            
            # Check risk per trade
            if MAX_RISK_PER_TRADE > 0.03:
                self.warnings.append(
                    f"MAX_RISK_PER_TRADE ({MAX_RISK_PER_TRADE*100}%) is aggressive. Consider 1-2%."
                )
            
            if MAX_RISK_PER_TRADE < 0.005:
                self.warnings.append(
                    f"MAX_RISK_PER_TRADE ({MAX_RISK_PER_TRADE*100}%) is very conservative. Growth may be slow."
                )
            
            # Check daily loss limit
            if MAX_DAILY_LOSS > 0.10:
                self.warnings.append(
                    f"MAX_DAILY_LOSS ({MAX_DAILY_LOSS*100}%) is high. Consider 5-8% max."
                )
            
            # Check drawdown limit
            if MAX_DRAWDOWN_PERCENT > 0.25:
                self.warnings.append(
                    f"MAX_DRAWDOWN_PERCENT ({MAX_DRAWDOWN_PERCENT*100}%) is high. Psychological stress risk."
                )
            
            # Check stop loss
            if STOP_LOSS_PERCENT > 0.10:
                self.warnings.append(
                    f"STOP_LOSS_PERCENT ({STOP_LOSS_PERCENT*100}%) is wide. May give up too much profit."
                )
            
            if STOP_LOSS_PERCENT < 0.03:
                self.warnings.append(
                    f"STOP_LOSS_PERCENT ({STOP_LOSS_PERCENT*100}%) is tight. May get stopped out frequently."
                )
            
        except ImportError as e:
            self.errors.append(f"Failed to import risk settings: {e}")
    
    def _validate_strategy_settings(self):
        """Validate strategy configurations"""
        try:
            from config.settings import STRATEGIES, MOMENTUM, MEAN_REVERSION, BREAKOUT
            
            # Check if at least one strategy is enabled
            enabled_strategies = [name for name, config in STRATEGIES.items() if config.get('enabled')]
            
            if not enabled_strategies:
                self.errors.append("No strategies enabled! Enable at least one strategy.")
            
            # Check capital allocation totals
            total_allocation = sum(
                config.get('capital_allocation', 0) 
                for config in STRATEGIES.values() 
                if config.get('enabled')
            )
            
            if abs(total_allocation - 1.0) > 0.01:
                self.warnings.append(
                    f"Total capital allocation is {total_allocation*100:.0f}% (should be ~100%)"
                )
            
            # Validate individual strategies
            for strategy_name in ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT']:
                config = locals()[strategy_name]
                
                # Check targets make sense
                targets = config.get('TARGETS', [])
                if len(targets) >= 2:
                    if targets[0] >= targets[1]:
                        self.warnings.append(
                            f"{strategy_name}: Target levels should be increasing"
                        )
                
                # Check stop loss vs targets
                stop_loss = config.get('STOP_LOSS', 0)
                if targets and stop_loss > targets[0]:
                    self.warnings.append(
                        f"{strategy_name}: Stop loss ({stop_loss*100}%) wider than first target"
                    )
            
        except ImportError as e:
            self.errors.append(f"Failed to import strategy settings: {e}")
    
    def _validate_timing_settings(self):
        """Validate timing configurations"""
        try:
            from config.settings import (
                MARKET_OPEN, MARKET_CLOSE, SCAN_TIME,
                POSITION_MONITOR_INTERVAL, SCAN_INTERVAL
            )
            
            # Validate time format
            for time_str, name in [(MARKET_OPEN, 'MARKET_OPEN'), 
                                    (MARKET_CLOSE, 'MARKET_CLOSE'),
                                    (SCAN_TIME, 'SCAN_TIME')]:
                try:
                    datetime.strptime(time_str, "%H:%M")
                except ValueError:
                    self.errors.append(f"{name} has invalid format: {time_str}. Use HH:MM")
            
            # Check intervals are reasonable
            if POSITION_MONITOR_INTERVAL < 1:
                self.warnings.append(
                    f"POSITION_MONITOR_INTERVAL ({POSITION_MONITOR_INTERVAL}min) is very frequent. High API usage."
                )
            
            if POSITION_MONITOR_INTERVAL > 10:
                self.warnings.append(
                    f"POSITION_MONITOR_INTERVAL ({POSITION_MONITOR_INTERVAL}min) is slow. May miss stops."
                )
            
            if SCAN_INTERVAL < 5:
                self.warnings.append(
                    f"SCAN_INTERVAL ({SCAN_INTERVAL}min) is very frequent. High system load."
                )
            
        except ImportError as e:
            self.errors.append(f"Failed to import timing settings: {e}")
    
    def _validate_environment(self):
        """Validate environment variables"""
        # Check for .env file
        if not os.path.exists('.env'):
            self.warnings.append(
                "No .env file found. Discord alerts may not work. Create .env with DISCORD_WEBHOOK_URL."
            )
        else:
            # Check if Discord webhook is configured
            from dotenv import load_dotenv
            load_dotenv()
            
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
            if not webhook_url:
                self.warnings.append(
                    "DISCORD_WEBHOOK_URL not set in .env. Discord alerts disabled."
                )
            elif not webhook_url.startswith('https://discord.com/api/webhooks/'):
                self.warnings.append(
                    "DISCORD_WEBHOOK_URL may be invalid. Should start with https://discord.com/api/webhooks/"
                )
    
    def _validate_directories(self):
        """Validate required directories exist"""
        required_dirs = [
            'data',
            'data/cache',
            'data/backups',
            'database',
            'logs'
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                self.warnings.append(f"Directory '{dir_path}' doesn't exist. Will be created automatically.")
                # Create it
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    self.errors.append(f"Failed to create directory '{dir_path}': {e}")
    
    def _display_results(self):
        """Display validation results"""
        print()
        
        if self.errors:
            print("❌ ERRORS FOUND:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All configuration checks passed!")
        elif self.errors:
            print("❌ Configuration has ERRORS. Fix before running.")
        else:
            print("✅ Configuration valid (with warnings)")
        
        print("="*70 + "\n")
    
    def get_summary(self):
        """Get validation summary"""
        return {
            'passed': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


def validate_config():
    """Convenience function to validate configuration"""
    validator = ConfigValidator()
    is_valid = validator.validate_all()
    return is_valid, validator.get_summary()


if __name__ == "__main__":
    # Test validator
    print("🧪 Testing Configuration Validator...")
    is_valid, summary = validate_config()
    
    print(f"\n📊 Summary:")
    print(f"   Passed: {summary['passed']}")
    print(f"   Errors: {summary['error_count']}")
    print(f"   Warnings: {summary['warning_count']}")
