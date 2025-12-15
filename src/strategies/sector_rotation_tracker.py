"""
📊 SECTOR ROTATION TRACKER
Tracks Indian market sector performance vs Nifty 50
Identifies leading and lagging sectors for better signal selection
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from config.settings import SECTOR_ROTATION_CONFIG, NIFTY_SYMBOL


class SectorRotationTracker:
    """
    Track sector rotation in Indian market
    
    Identifies:
    - Leading sectors (outperforming Nifty 50)
    - Lagging sectors (underperforming Nifty 50)
    - Sector momentum trends
    """
    
    def __init__(self):
        self.config = SECTOR_ROTATION_CONFIG
        self.sectors = self.config['SECTORS']
        self.sector_performance = {}
        self.leading_sectors = []
        self.lagging_sectors = []
        
    def analyze_sectors(self, lookback_days: int = 30) -> Dict:
        """
        Analyze all sectors and rank by performance
        
        Args:
            lookback_days: Days to look back for performance calculation
            
        Returns:
            Dict with sector analysis results
        """
        try:
            print(f"\n📊 Analyzing sector rotation (last {lookback_days} days)...")
            
            # Get Nifty 50 performance as benchmark
            nifty_return = self._get_index_return(NIFTY_SYMBOL, lookback_days)
            
            if nifty_return is None:
                print("⚠️ Could not fetch Nifty data")
                return self._get_default_result()
            
            print(f"   Nifty 50: {nifty_return:+.2f}% (benchmark)")
            
            # Calculate each sector's performance
            sector_results = {}
            
            for sector_name, stocks in self.sectors.items():
                sector_return = self._calculate_sector_return(stocks, lookback_days)
                
                if sector_return is not None:
                    # Calculate Relative Strength vs Nifty
                    sector_rs = 100 + ((sector_return - nifty_return) / abs(nifty_return) * 100 if nifty_return != 0 else 0)
                    
                    sector_results[sector_name] = {
                        'return': sector_return,
                        'rs_rating': sector_rs,
                        'vs_nifty': sector_return - nifty_return
                    }
                    
                    # Status emoji
                    if sector_rs >= self.config['MIN_SECTOR_RS']:
                        status = '🟢 Leading'
                    elif sector_rs <= self.config['LAGGING_SECTOR_RS_THRESHOLD']:
                        status = '🔴 Lagging'
                    else:
                        status = '🟡 Neutral'
                    
                    print(f"   {sector_name:8s}: {sector_return:+6.2f}% | RS: {sector_rs:6.1f} | {status}")
            
            # Rank sectors
            sorted_sectors = sorted(sector_results.items(), key=lambda x: x[1]['rs_rating'], reverse=True)
            
            # Identify leading and lagging
            self.leading_sectors = [s[0] for s in sorted_sectors[:self.config['TOP_SECTORS_COUNT']]]
            self.lagging_sectors = [s[0] for s in sorted_sectors[-2:]]  # Bottom 2
            
            self.sector_performance = sector_results
            
            print(f"\n   🟢 Leading Sectors: {', '.join(self.leading_sectors)}")
            print(f"   🔴 Lagging Sectors: {', '.join(self.lagging_sectors)}")
            
            return {
                'sector_performance': sector_results,
                'leading_sectors': self.leading_sectors,
                'lagging_sectors': self.lagging_sectors,
                'nifty_return': nifty_return
            }
            
        except Exception as e:
            print(f"❌ Error analyzing sectors: {e}")
            return self._get_default_result()
    
    def _get_index_return(self, symbol: str, days: int) -> float:
        """Get index return over specified days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)  # Extra buffer
            
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data is None or len(data) < 2:
                return None
            
            # Get return over last N trading days
            if len(data) >= days:
                start_price = data['Close'].iloc[-days]
                end_price = data['Close'].iloc[-1]
            else:
                start_price = data['Close'].iloc[0]
                end_price = data['Close'].iloc[-1]
            
            return ((end_price - start_price) / start_price) * 100
            
        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {e}")
            return None
    
    def _calculate_sector_return(self, stocks: List[str], days: int) -> float:
        """Calculate average return for a sector"""
        try:
            returns = []
            
            for stock in stocks[:5]:  # Sample first 5 stocks for speed
                stock_return = self._get_index_return(stock, days)
                if stock_return is not None:
                    returns.append(stock_return)
            
            if len(returns) == 0:
                return None
            
            # Return average
            return sum(returns) / len(returns)
            
        except Exception as e:
            return None
    
    def _get_default_result(self) -> Dict:
        """Return default result when analysis fails"""
        return {
            'sector_performance': {},
            'leading_sectors': [],
            'lagging_sectors': [],
            'nifty_return': 0
        }
    
    def get_sector_for_stock(self, symbol: str) -> str:
        """Get sector name for a stock symbol"""
        for sector_name, stocks in self.sectors.items():
            if symbol in stocks:
                return sector_name
        return 'Other'
    
    def is_leading_sector(self, symbol: str) -> bool:
        """Check if stock is from a leading sector"""
        sector = self.get_sector_for_stock(symbol)
        return sector in self.leading_sectors
    
    def is_lagging_sector(self, symbol: str) -> bool:
        """Check if stock is from a lagging sector"""
        sector = self.get_sector_for_stock(symbol)
        return sector in self.lagging_sectors
    
    def get_sector_boost(self, symbol: str) -> float:
        """
        Get score boost for stocks in leading sectors
        
        Returns:
            Score boost (0.0 to 0.5)
        """
        if not self.config['BOOST_LEADING_SECTORS']:
            return 0.0
        
        if self.is_leading_sector(symbol):
            return self.config['LEADING_SECTOR_BOOST']
        
        return 0.0
    
    def should_skip_stock(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if stock should be skipped due to sector rotation
        
        Returns:
            (should_skip, reason)
        """
        if not self.config['AVOID_LAGGING_SECTORS']:
            return False, ""
        
        if self.is_lagging_sector(symbol):
            sector = self.get_sector_for_stock(symbol)
            return True, f"Lagging sector ({sector})"
        
        return False, ""


def test_sector_rotation():
    """Test the sector rotation tracker"""
    print("🧪 Testing Sector Rotation Tracker...\n")
    
    tracker = SectorRotationTracker()
    results = tracker.analyze_sectors(lookback_days=30)
    
    print(f"\n✅ Sector rotation analysis complete!")
    print(f"   Leading: {results['leading_sectors']}")
    print(f"   Lagging: {results['lagging_sectors']}")
    
    # Test stock classification
    test_stocks = ['TCS.NS', 'HDFCBANK.NS', 'SUNPHARMA.NS']
    print(f"\n📋 Stock Classification:")
    for stock in test_stocks:
        sector = tracker.get_sector_for_stock(stock)
        is_leading = tracker.is_leading_sector(stock)
        boost = tracker.get_sector_boost(stock)
        print(f"   {stock:15s} → {sector:8s} | Leading: {is_leading} | Boost: +{boost:.1f}")


if __name__ == "__main__":
    test_sector_rotation()
