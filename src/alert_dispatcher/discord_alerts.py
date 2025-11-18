"""
📢 DISCORD ALERTS V4.0
Enhanced with quantity, time, and IST timezone
"""

import requests
import json
from datetime import datetime
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)


class DiscordAlerts:
    """
    Send trading alerts to Discord with full details
    """
    
    def __init__(self, webhook_url=None):
        # Get webhook from settings or use provided
        try:
            from config.settings import DISCORD_WEBHOOK_URL
            self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        except:
            self.webhook_url = webhook_url
        
        if not self.webhook_url:
            print("⚠️ Discord webhook not configured")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Discord alerts enabled")
    
    def send_buy_alert(self, opportunity):
        """
        Send BUY alert with full details
        
        Args:
            opportunity: dict with symbol, entry_price, shares, stop_loss, targets, strategy
        """
        if not self.enabled:
            return
        
        try:
            symbol = opportunity.get('symbol', 'UNKNOWN')
            entry_price = opportunity.get('entry_price', opportunity.get('current_price', 0))
            shares = opportunity.get('shares', 0)
            stop_loss = opportunity.get('stop_loss', 0)
            target1 = opportunity.get('target1', 0)
            target2 = opportunity.get('target2', 0)
            target3 = opportunity.get('target3', 0)
            strategy = opportunity.get('strategy', 'MOMENTUM')
            position_value = opportunity.get('position_value', entry_price * shares)
            
            # Calculate potential profit
            potential_profit_t1 = (target1 - entry_price) * shares
            potential_profit_t2 = (target2 - entry_price) * shares
            
            # Get IST time
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')
            
            embed = {
                "title": f"🟢 BUY SIGNAL - {symbol}",
                "description": f"**Strategy:** {strategy}",
                "color": 65280,  # Green
                "fields": [
                    {
                        "name": "📊 Trade Details",
                        "value": f"**Quantity:** {shares} shares\n"
                                f"**Entry Price:** ₹{entry_price:.2f}\n"
                                f"**Position Value:** ₹{position_value:,.0f}",
                        "inline": False
                    },
                    {
                        "name": "🎯 Targets",
                        "value": f"**T1:** ₹{target1:.2f} (₹{potential_profit_t1:+,.0f})\n"
                                f"**T2:** ₹{target2:.2f} (₹{potential_profit_t2:+,.0f})\n"
                                f"**T3:** ₹{target3:.2f}",
                        "inline": True
                    },
                    {
                        "name": "⛔ Stop Loss",
                        "value": f"**SL:** ₹{stop_loss:.2f}\n"
                                f"**Risk:** {((entry_price - stop_loss) / entry_price * 100):.1f}%",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Time: {current_time}"
                }
            }
            
            data = {
                "content": f"@everyone New {strategy} Trade!",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                print(f"✅ BUY alert sent to Discord: {symbol}")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Discord BUY alert error: {e}")
    
    def send_exit_alert(self, exit_data):
        """
        Send EXIT/SELL alert with P&L
        
        Args:
            exit_data: dict with symbol, exit_price, profit_loss, return_percent, reason
        """
        if not self.enabled:
            return
        
        try:
            symbol = exit_data.get('symbol', 'UNKNOWN')
            action = exit_data.get('action', 'EXIT')
            exit_price = exit_data.get('exit_price', 0)
            pnl = exit_data.get('profit_loss', 0)
            pnl_percent = exit_data.get('return_percent', 0)
            reason = exit_data.get('reason', 'Unknown')
            strategy = exit_data.get('strategy', 'MOMENTUM')
            
            # Get IST time
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')
            
            # Color based on profit/loss
            if pnl > 0:
                color = 65280  # Green
                emoji = "✅"
            else:
                color = 16711680  # Red
                emoji = "❌"
            
            embed = {
                "title": f"{emoji} {action} - {symbol}",
                "description": f"**Strategy:** {strategy}\n**Reason:** {reason}",
                "color": color,
                "fields": [
                    {
                        "name": "💰 P&L",
                        "value": f"**Amount:** ₹{pnl:+,.0f}\n"
                                f"**Return:** {pnl_percent:+.2f}%",
                        "inline": True
                    },
                    {
                        "name": "📊 Exit Price",
                        "value": f"₹{exit_price:.2f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Time: {current_time}"
                }
            }
            
            data = {
                "content": f"Trade Closed: {symbol}",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                print(f"✅ EXIT alert sent to Discord: {symbol}")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Discord EXIT alert error: {e}")
    
    def send_test_alert(self):
        """Send test alert"""
        if not self.enabled:
            print("❌ Discord alerts not enabled")
            return
        
        try:
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')
            
            embed = {
                "title": "🧪 TEST ALERT",
                "description": "Discord alerts are working correctly!",
                "color": 3447003,  # Blue
                "footer": {
                    "text": f"Time: {current_time}"
                }
            }
            
            data = {
                "content": "System Test",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                print("✅ Test alert sent successfully!")
            else:
                print(f"⚠️ Test failed: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Test alert error: {e}")


if __name__ == "__main__":
    # Test
    alerter = DiscordAlerts()
    alerter.send_test_alert()