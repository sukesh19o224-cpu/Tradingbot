"""
🔍 LOGGING SYSTEM
Centralized logging with console + file output
Maintains all existing print statements for compatibility
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import sys


class TradingLogger:
    """
    Dual-mode logger: Console (like print) + File persistence
    Non-breaking: All existing print statements work as before
    """
    
    _instances = {}
    
    def __new__(cls, name='TradingSystem'):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name='TradingSystem'):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # File handler with rotation (10MB per file, keep 10 files)
        log_file = f'logs/trading_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler (maintains current behavior)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Detailed format for file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Simple format for console (like existing prints)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        """Log info (also prints to console)"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning"""
        self.logger.warning(f"⚠️ {message}")
    
    def error(self, message, exc_info=False):
        """Log error"""
        self.logger.error(f"❌ {message}", exc_info=exc_info)
    
    def success(self, message):
        """Log success"""
        self.logger.info(f"✅ {message}")
    
    def debug(self, message):
        """Log debug info"""
        self.logger.debug(message)
    
    def trade(self, message):
        """Log trade activity (special category)"""
        self.logger.info(f"💰 TRADE: {message}")
    
    def scan(self, message):
        """Log scan activity"""
        self.logger.info(f"🔍 SCAN: {message}")
    
    def position(self, message):
        """Log position updates"""
        self.logger.info(f"📊 POSITION: {message}")


# Convenience function
def get_logger(name='TradingSystem'):
    """Get or create logger instance"""
    return TradingLogger(name)


# Wrapper for existing print statements (optional migration)
class LoggingPrint:
    """
    Drop-in replacement for print that also logs to file
    Usage: print = LoggingPrint()
    """
    def __init__(self):
        self.logger = get_logger()
    
    def __call__(self, *args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        # Print to console (original behavior)
        print(message, **kwargs)
        # Also log to file (new feature)
        self.logger.info(message)


# Error context manager for safe operations
class SafeOperation:
    """
    Context manager for safe operations with automatic error logging
    
    Usage:
        with SafeOperation("Fetching stock data"):
            data = yf.download(symbol)
    """
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
    
    def __enter__(self):
        self.logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Failed: {self.operation_name} - {exc_val}",
                exc_info=True
            )
            return False  # Re-raise exception
        else:
            self.logger.debug(f"Completed: {self.operation_name}")
        return True


if __name__ == "__main__":
    # Test the logger
    logger = get_logger()
    
    logger.info("System starting...")
    logger.success("Portfolio loaded")
    logger.warning("High volatility detected")
    logger.trade("BUY RELIANCE @ 2500")
    logger.error("API connection failed")
    
    print("\n✅ Logger test complete. Check logs/ directory.")
