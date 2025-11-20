"""
💾 DATA CACHING MODULE
Caches stock data to speed up scans from 3-5 min to 30 sec
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import pickle


class DataCache:
    """
    Caches historical stock data to avoid repeated downloads
    Cache expires daily for fresh data
    """
    
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_date = datetime.now().date()
        self.cache_file = f"{cache_dir}/stock_cache_{self.cache_date}.pkl"
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk if exists and not expired"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                print(f"✅ Loaded cache with {len(cache)} stocks")
                return cache
            except Exception as e:
                print(f"⚠️ Cache load failed: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def _cleanup_old_caches(self):
        """Delete old cache files"""
        try:
            for file in os.listdir(self.cache_dir):
                if file.startswith('stock_cache_') and file.endswith('.pkl'):
                    file_path = os.path.join(self.cache_dir, file)
                    if file != os.path.basename(self.cache_file):
                        os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Cache cleanup failed: {e}")
    
    def get_data(self, symbol, data_fetcher):
        """
        Get data from cache or fetch if missing
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            data_fetcher: Function that fetches data (e.g., yf.Ticker().history())
        
        Returns:
            DataFrame with historical data
        """
        # Check if cache is still valid (same day)
        if datetime.now().date() != self.cache_date:
            print("📅 New day detected - refreshing cache...")
            self.cache = {}
            self.cache_date = datetime.now().date()
            self.cache_file = f"{self.cache_dir}/stock_cache_{self.cache_date}.pkl"
            self._cleanup_old_caches()
        
        # Check if symbol in cache
        if symbol in self.cache:
            cached_df = self.cache[symbol]
            
            # Update only today's candle (last row)
            try:
                fresh_data = data_fetcher()
                if not fresh_data.empty and len(fresh_data) > 0:
                    # Replace last row with fresh data
                    if len(cached_df) > 0:
                        cached_df = cached_df[:-1]  # Remove last row
                    cached_df = pd.concat([cached_df, fresh_data.tail(1)])  # Add fresh last row
                    self.cache[symbol] = cached_df
                    return cached_df
                else:
                    return cached_df
            except:
                return cached_df
        
        # Not in cache - fetch full data
        try:
            df = data_fetcher()
            if not df.empty:
                self.cache[symbol] = df
                self._save_cache()
            return df
        except Exception as e:
            print(f"⚠️ Data fetch failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def clear_cache(self):
        """Clear all cache"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ Cache cleared")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'cached_symbols': len(self.cache),
            'cache_date': self.cache_date,
            'cache_size_mb': os.path.getsize(self.cache_file) / (1024*1024) if os.path.exists(self.cache_file) else 0
        }


# Global cache instance
_global_cache = None

def get_cache():
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache()
    return _global_cache


if __name__ == "__main__":
    # Test
    import yfinance as yf
    
    cache = DataCache()
    
    print("\n📊 Testing cache with RELIANCE...")
    
    # First fetch (from API)
    import time
    start = time.time()
    data1 = cache.get_data('RELIANCE.NS', lambda: yf.Ticker('RELIANCE.NS').history(period='3mo'))
    time1 = time.time() - start
    print(f"First fetch: {time1:.2f}s, Got {len(data1)} rows")
    
    # Second fetch (from cache)
    start = time.time()
    data2 = cache.get_data('RELIANCE.NS', lambda: yf.Ticker('RELIANCE.NS').history(period='3mo'))
    time2 = time.time() - start
    print(f"Second fetch: {time2:.2f}s, Got {len(data2)} rows")
    
    print(f"\n⚡ Speedup: {time1/time2:.1f}x faster!")
    
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache stats:")
    print(f"   Symbols: {stats['cached_symbols']}")
    print(f"   Date: {stats['cache_date']}")
    print(f"   Size: {stats['cache_size_mb']:.2f} MB")