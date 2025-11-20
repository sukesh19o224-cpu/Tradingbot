"""
🛡️ ERROR HANDLING & RETRY LOGIC
Decorator and utilities for robust error handling
"""

import time
import functools
from datetime import datetime
import traceback
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import get_logger
    logger = get_logger('ErrorHandler')
except:
    logger = None


def retry_on_failure(max_retries=3, delay=2, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator for functions that may fail due to network/API issues
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Usage:
        @retry_on_failure(max_retries=3, delay=2)
        def fetch_stock_data(symbol):
            return yf.Ticker(symbol).history(period='1mo')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        error_msg = f"❌ {func.__name__} failed after {max_retries} attempts: {e}"
                        if logger:
                            logger.error(error_msg, exc_info=True)
                        else:
                            print(error_msg)
                        raise
                    
                    # Retry
                    warning_msg = f"⚠️ {func.__name__} attempt {attempt+1}/{max_retries} failed: {e}. Retrying in {current_delay}s..."
                    if logger:
                        logger.warning(warning_msg)
                    else:
                        print(warning_msg)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func, default_return=None, error_prefix="Operation"):
    """
    Execute function safely with error handling
    Returns default_return if function fails
    
    Usage:
        data = safe_execute(
            lambda: yf.Ticker(symbol).history(period='1mo'),
            default_return=pd.DataFrame(),
            error_prefix="Fetching stock data"
        )
    """
    try:
        return func()
    except Exception as e:
        error_msg = f"❌ {error_prefix} failed: {e}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)
        return default_return


class ErrorTracker:
    """
    Track errors to detect systemic issues
    """
    def __init__(self):
        self.errors = []
        self.error_counts = {}
        self.max_errors_to_keep = 100
    
    def log_error(self, error_type, error_message, context=""):
        """Log an error occurrence"""
        error_entry = {
            'timestamp': datetime.now(),
            'type': error_type,
            'message': str(error_message),
            'context': context
        }
        
        self.errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors_to_keep:
            self.errors = self.errors[-self.max_errors_to_keep:]
        
        # Count by type
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def get_recent_errors(self, minutes=60):
        """Get errors from last N minutes"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        return [
            e for e in self.errors 
            if e['timestamp'].timestamp() > cutoff_time
        ]
    
    def get_error_rate(self, error_type, minutes=60):
        """Get error rate for specific type"""
        recent_errors = self.get_recent_errors(minutes)
        type_errors = [e for e in recent_errors if e['type'] == error_type]
        return len(type_errors)
    
    def is_healthy(self, max_errors_per_hour=10):
        """Check if error rate is acceptable"""
        recent_errors = self.get_recent_errors(60)
        return len(recent_errors) < max_errors_per_hour
    
    def get_summary(self):
        """Get error summary"""
        recent = self.get_recent_errors(60)
        return {
            'total_errors_last_hour': len(recent),
            'error_counts': self.error_counts,
            'is_healthy': self.is_healthy(),
            'recent_errors': recent[-5:]  # Last 5 errors
        }


# Global error tracker
_error_tracker = ErrorTracker()


def get_error_tracker():
    """Get global error tracker instance"""
    return _error_tracker


class SafeYFinance:
    """
    Wrapper for yfinance with automatic retry and error handling
    Drop-in replacement for yf.Ticker()
    """
    def __init__(self, symbol, max_retries=3):
        self.symbol = symbol
        self.max_retries = max_retries
        self.error_tracker = get_error_tracker()
    
    @retry_on_failure(max_retries=3, delay=2)
    def history(self, **kwargs):
        """Get historical data with retry"""
        import yfinance as yf
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(**kwargs)
            
            if df.empty:
                self.error_tracker.log_error(
                    'EmptyDataFrame',
                    f'No data returned for {self.symbol}',
                    context='yfinance.history'
                )
            
            return df
        except Exception as e:
            self.error_tracker.log_error(
                'YFinanceError',
                str(e),
                context=f'yfinance.history({self.symbol})'
            )
            raise
    
    @retry_on_failure(max_retries=3, delay=2)
    def info(self):
        """Get stock info with retry"""
        import yfinance as yf
        try:
            ticker = yf.Ticker(self.symbol)
            return ticker.info
        except Exception as e:
            self.error_tracker.log_error(
                'YFinanceError',
                str(e),
                context=f'yfinance.info({self.symbol})'
            )
            raise


def handle_critical_error(error, context="System"):
    """
    Handle critical errors that should stop the system
    """
    error_msg = f"""
    {'='*70}
    🚨 CRITICAL ERROR IN {context}
    {'='*70}
    Error: {error}
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Traceback:
    {traceback.format_exc()}
    {'='*70}
    """
    
    if logger:
        logger.error(error_msg)
    else:
        print(error_msg)
    
    # Save error log
    try:
        os.makedirs('logs', exist_ok=True)
        with open(f'logs/critical_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 'w') as f:
            f.write(error_msg)
    except:
        pass


if __name__ == "__main__":
    # Test retry decorator
    @retry_on_failure(max_retries=3, delay=1)
    def test_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise Exception("Random failure")
        return "Success!"
    
    try:
        result = test_function()
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Final failure: {e}")
    
    # Test error tracker
    tracker = get_error_tracker()
    tracker.log_error('TestError', 'This is a test', context='test')
    print(f"\n📊 Error Summary: {tracker.get_summary()}")
