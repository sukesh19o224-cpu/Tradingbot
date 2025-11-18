"""
📊 INTRADAY SCANNER - Finds new opportunities during market hours
Runs every 30 minutes, sends BUY alerts for fresh breakouts
"""

import sys, os
from datetime import datetime
import yfinance as yf
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *

class IntradayScanner:
    def __init__(self, swing_scanner=None, discord_alerts=None):
        self.swing_scanner = swing_scanner
        self.discord_alerts = discord_alerts
        self.sent_alerts = set()
        self.last_scan_time = None
        print("📊 Intraday Scanner initialized")
    
    def should_scan_now(self):
        """Check if it's time to scan"""
        if not ENABLE_INTRADAY_SCAN:
            return False
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Check if current time matches any scan time
        for scan_time in INTRADAY_SCAN_TIMES:
            if current_time == scan_time:
                # Avoid duplicate scans in same minute
                if self.last_scan_time != current_time:
                    self.last_scan_time = current_time
                    return True
        return False
    
    def scan_for_opportunities(self):
        """
        Scan for new breakout opportunities
        Uses swing_scanner if available, otherwise basic scan
        """
        if not self.swing_scanner:
            print("⚠️ No swing scanner available")
            return []
        
        try:
            print(f"\n📊 INTRADAY SCAN @ {datetime.now().strftime('%H:%M')}")
            
            # Use swing scanner to find opportunities
            opportunities = self.swing_scanner.run_eod_screening()
            
            # Filter by higher intraday score threshold
            intraday_opps = [
                opp for opp in opportunities 
                if opp.get('score', 0) >= INTRADAY_MIN_SCORE
            ]
            
            print(f"   Found {len(intraday_opps)} high-score opportunities")
            
            # Return top opportunities
            return intraday_opps[:10]  # Limit to top 10
            
        except Exception as e:
            print(f"   ❌ Scan error: {e}")
            return []
    
    def filter_new_opportunities(self, opportunities, existing_positions):
        """
        Filter out stocks already in portfolio or alerted
        """
        existing_symbols = {pos.get('symbol', '').replace('.NS', '') 
                          for pos in existing_positions}
        
        new_opps = []
        for opp in opportunities:
            symbol = opp['symbol'].replace('.NS', '')
            
            # Skip if already in portfolio
            if symbol in existing_symbols:
                continue
            
            # Skip if already alerted today
            alert_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d')}"
            if alert_key in self.sent_alerts:
                continue
            
            new_opps.append(opp)
        
        return new_opps
    
    def send_buy_alerts(self, opportunities):
        """Send BUY alerts for new opportunities"""
        if not SEND_BUY_ALERTS or not self.discord_alerts:
            return
        
        print(f"\n🔔 Sending alerts for {len(opportunities)} opportunities...")
        
        for opp in opportunities:
            symbol = opp['symbol'].replace('.NS', '')
            alert_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if alert_key in self.sent_alerts:
                continue
            
            try:
                # Prepare alert data
                alert_data = {
                    'symbol': symbol,
                    'current_price': opp.get('price', 0),
                    'score': opp.get('score', 0),
                    'pattern': opp.get('pattern', 'BREAKOUT'),
                    'volume_ratio': opp.get('volume_cr', 0),
                    'momentum_5d': opp.get('momentum_5d', 0),
                    'check_time': datetime.now().strftime('%H:%M')
                }
                
                self.discord_alerts.send_buy_alert(alert_data)
                self.sent_alerts.add(alert_key)
                print(f"   ✅ Alert sent: {symbol}")
                
            except Exception as e:
                print(f"   ⚠️ Alert failed for {symbol}: {e}")
            
            time.sleep(1)  # Rate limiting
    
    def run_intraday_scan(self, existing_positions):
        """
        Main function to run intraday scanning
        
        Args:
            existing_positions: Current open positions
        
        Returns:
            List of new opportunities
        """
        if not self.should_scan_now():
            return []
        
        print("\n" + "="*70)
        print(f"📊 INTRADAY SCAN @ {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        
        # Scan for opportunities
        opportunities = self.scan_for_opportunities()
        
        if not opportunities:
            print("   No opportunities found")
            print("="*70 + "\n")
            return []
        
        # Filter new ones
        new_opps = self.filter_new_opportunities(opportunities, existing_positions)
        
        print(f"   {len(new_opps)} new opportunities (not in portfolio)")
        
        # Send alerts for top 3
        if new_opps:
            self.send_buy_alerts(new_opps[:3])
        
        print("="*70 + "\n")
        
        return new_opps
    
    def reset_daily(self):
        """Reset for new day"""
        self.sent_alerts = set()
        self.last_scan_time = None
        print("🔄 Intraday scanner reset")
    
    def get_status(self):
        """Get scanner status"""
        return {
            'enabled': ENABLE_INTRADAY_SCAN,
            'interval': INTRADAY_SCAN_INTERVAL,
            'scan_times': INTRADAY_SCAN_TIMES,
            'alerts_sent_today': len(self.sent_alerts),
            'last_scan': self.last_scan_time
        }


def test_intraday_scanner():
    """Test function"""
    print("🧪 Testing Intraday Scanner...")
    
    scanner = IntradayScanner()
    
    # Test with empty positions
    test_positions = []
    
    # Manually trigger scan (override time check)
    scanner.last_scan_time = None
    INTRADAY_SCAN_TIMES[0] = datetime.now().strftime("%H:%M")
    
    results = scanner.run_intraday_scan(test_positions)
    
    print(f"\n✅ Test complete - Found {len(results)} opportunities")


if __name__ == "__main__":
    test_intraday_scanner()