import requests
import json
from datetime import datetime
import sys
import os
import time
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import DISCORD_WEBHOOK_URL

class DiscordAlerter:
    """
    Sends trading alerts to Discord with rich formatting
    """
    
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL
        
        # BUGFIX BUG9: Implement rate limiting (Discord allows 30 requests/minute)
        self.rate_limit_window = 60  # 60 seconds
        self.max_requests_per_window = 25  # Conservative limit (Discord allows 30)
        self.request_times = deque()
        
        if not self.webhook_url or self.webhook_url == "your_webhook_url_here":
            print("⚠️ Discord webhook not configured!")
            print("Add your webhook URL to .env file")
        else:
            print("✅ Discord Alerter Ready!")
    
    # BUGFIX BUG9: Add rate limiting check method
    def _check_rate_limit(self):
        """Check if we're within rate limits, wait if necessary"""
        now = time.time()
        
        # Remove old requests outside the window
        while self.request_times and self.request_times[0] < now - self.rate_limit_window:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= self.max_requests_per_window:
            sleep_time = self.rate_limit_window - (now - self.request_times[0]) + 1
            if sleep_time > 0:
                print(f"⏳ Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                # Clear old requests after waiting
                self.request_times.clear()
        
        # Record this request
        self.request_times.append(now)
    
    def send_alert(self, alert_type, data):
        """Send formatted alert to Discord"""
        
        if not self.webhook_url or self.webhook_url == "your_webhook_url_here":
            print("❌ Discord webhook not configured")
            return False
        
        # BUGFIX BUG9: Check rate limit before sending
        self._check_rate_limit()
        
        # Create embed based on alert type
        if alert_type == "SWING_OPPORTUNITY":
            embed = self.create_swing_alert(data)
        elif alert_type == "ENTRY_SIGNAL":
            embed = self.create_entry_alert(data)
        elif alert_type == "EXIT_SIGNAL":
            embed = self.create_exit_alert(data)
        elif alert_type == "MARKET_SCAN":
            embed = self.create_scan_summary(data)
        else:
            embed = self.create_generic_alert(data)
        
        # Send to Discord
        try:
            response = requests.post(
                self.webhook_url,
                json={"embeds": [embed]},
                headers={"Content-Type": "application/json"},
                timeout=10  # Add timeout
            )
            
            if response.status_code == 204:
                print("✅ Alert sent to Discord!")
                return True
            else:
                print(f"❌ Discord error: {response.status_code}")
                # BUGFIX BUG7: Log error details to file
                self._log_error(f"Discord API returned {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send alert: {e}")
            # BUGFIX BUG7: Log network errors to file
            self._log_error(f"Network error sending alert: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self._log_error(f"Unexpected error: {e}")
            return False
    
    # BUGFIX BUG7: Add error logging to file
    def _log_error(self, error_message):
        """Log errors to a file for debugging"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "discord_alerts.log")
            
            with open(log_file, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {error_message}\n")
        except Exception as e:
            print(f"⚠️ Could not write to log file: {e}")
    
    def create_swing_alert(self, data):
        """Create swing trading opportunity alert"""
        
        # BUGFIX BUG8: Use .get() with defaults for all data access
        momentum_5d = data.get('momentum_5d', 0)
        
        # Color based on momentum
        if momentum_5d > 7:
            color = 0x00ff00  # Green for strong momentum
        elif momentum_5d > 3:
            color = 0xffa500  # Orange for moderate
        else:
            color = 0x0099ff  # Blue for normal
        
        embed = {
            "title": f"🎯 SWING OPPORTUNITY: {data.get('symbol', 'UNKNOWN')}",
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {
                    "name": "💰 Current Price",
                    "value": f"₹{data.get('current_price', 0)}",
                    "inline": True
                },
                {
                    "name": "📈 5-Day Momentum",
                    "value": f"{momentum_5d:+.1f}%",
                    "inline": True
                },
                {
                    "name": "📊 20-Day Momentum",
                    "value": f"{data.get('momentum_20d', 0):+.1f}%",
                    "inline": True
                },
                {
                    "name": "🎯 Entry Zone",
                    "value": f"₹{data.get('entry_low', 0)}-{data.get('entry_high', 0)}",
                    "inline": True
                },
                {
                    "name": "🛑 Stop Loss",
                    "value": f"₹{data.get('stop_loss', 0)} (-{data.get('stop_loss_pct', 7)}%)",
                    "inline": True
                },
                {
                    "name": "✨ Target 1",
                    "value": f"₹{data.get('target1', 0)} (+{data.get('target1_pct', 6)}%)",
                    "inline": True
                },
                {
                    "name": "🚀 Target 2",
                    "value": f"₹{data.get('target2', 0)} (+{data.get('target2_pct', 12)}%)",
                    "inline": True
                },
                {
                    "name": "📊 Volume",
                    "value": f"{data.get('volume_cr', 0)} Cr",
                    "inline": True
                },
                {
                    "name": "⚡ Score",
                    "value": f"{data.get('score', 0)}/100",
                    "inline": True
                },
                {
                    "name": "📋 Pattern",
                    "value": data.get('pattern', 'MOMENTUM'),
                    "inline": False
                },
                {
                    "name": "💡 Strategy",
                    "value": data.get('strategy', 'Enter on breakout above today\'s high'),
                    "inline": False
                }
            ],
            "footer": {
                "text": "Swing Trade (2-5 days) | Risk: 7% | Reward: 12%"
            }
        }
        
        return embed
    
    def create_entry_alert(self, data):
        """Create entry signal alert"""
        
        # BUGFIX BUG8: Use .get() with defaults
        embed = {
            "title": f"🚨 ENTRY SIGNAL: {data.get('symbol', 'UNKNOWN')}",
            "color": 0x00ff00,  # Green
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {
                    "name": "⚡ ACTION REQUIRED",
                    "value": "**BUY NOW**",
                    "inline": False
                },
                {
                    "name": "💰 Entry Price",
                    "value": f"₹{data.get('entry_price', 0)}",
                    "inline": True
                },
                {
                    "name": "📊 Quantity",
                    "value": f"{data.get('shares', 0)} shares",
                    "inline": True
                },
                {
                    "name": "💵 Position Value",
                    "value": f"₹{data.get('position_value', 0):,.0f}",
                    "inline": True
                },
                {
                    "name": "🛑 Stop Loss",
                    "value": f"₹{data.get('stop_loss', 0)}",
                    "inline": True
                },
                {
                    "name": "🎯 Target 1",
                    "value": f"₹{data.get('target1', 0)}",
                    "inline": True
                },
                {
                    "name": "🚀 Target 2",
                    "value": f"₹{data.get('target2', 0)}",
                    "inline": True
                },
                {
                    "name": "⚠️ Risk Amount",
                    "value": f"₹{data.get('risk_amount', 0):,.0f}",
                    "inline": True
                },
                {
                    "name": "💰 Potential Profit",
                    "value": f"₹{data.get('reward_amount', 0):,.0f}",
                    "inline": True
                },
                {
                    "name": "📈 Risk/Reward",
                    "value": f"1:{data.get('risk_reward', 0):.1f}",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Execute immediately | Set stop-loss first!"
            }
        }
        
        return embed
    
    def create_exit_alert(self, data):
        """Create exit signal alert"""
        
        # BUGFIX BUG8: Use .get() with defaults
        profit_loss = data.get('profit_loss', 0)
        color = 0x00ff00 if profit_loss > 0 else 0xff0000
        
        embed = {
            "title": f"🔔 EXIT SIGNAL: {data.get('symbol', 'UNKNOWN')}",
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {
                    "name": "⚡ ACTION",
                    "value": f"**{data.get('action', 'SELL')}**",
                    "inline": False
                },
                {
                    "name": "💰 Exit Price",
                    "value": f"₹{data.get('exit_price', 0)}",
                    "inline": True
                },
                {
                    "name": "📊 P&L",
                    "value": f"₹{profit_loss:+,.0f}",
                    "inline": True
                },
                {
                    "name": "📈 Return",
                    "value": f"{data.get('return_percent', 0):+.1f}%",
                    "inline": True
                },
                {
                    "name": "💡 Reason",
                    "value": data.get('reason', 'Target reached'),
                    "inline": False
                }
            ]
        }
        
        return embed
    
    def create_scan_summary(self, data):
        """Create market scan summary alert"""
        
        # BUGFIX BUG8: Use .get() with defaults
        embed = {
            "title": "📊 MARKET SCAN COMPLETE",
            "color": 0x0099ff,
            "timestamp": datetime.now().isoformat(),
            "description": f"Found **{data.get('total_opportunities', 0)}** opportunities",
            "fields": []
        }
        
        # Add top 5 opportunities
        top_stocks = data.get('top_stocks', [])
        for i, stock in enumerate(top_stocks[:5], 1):
            # BUGFIX BUG8: Use .get() for nested data too
            embed["fields"].append({
                "name": f"{i}. {stock.get('symbol', 'UNKNOWN')}",
                "value": f"₹{stock.get('current_price', 0)} | {stock.get('momentum_5d', 0):+.1f}% | Score: {stock.get('score', 0)}",
                "inline": False
            })
        
        embed["footer"] = {
            "text": f"Scanned {data.get('total_scanned', 0)} stocks"
        }
        
        return embed
    
    def create_generic_alert(self, data):
        """Create generic alert"""
        
        # BUGFIX BUG8: Use .get() with defaults
        return {
            "title": data.get('title', 'Trading Alert'),
            "description": data.get('message', ''),
            "color": data.get('color', 0x0099ff),
            "timestamp": datetime.now().isoformat()
        }
    
    def send_test_alert(self):
        """Send test alert to verify webhook"""
        
        test_data = {
            'symbol': 'TEST',
            'current_price': 1000,
            'momentum_5d': 5.5,
            'momentum_20d': 12.3,
            'entry_low': 995,
            'entry_high': 1005,
            'stop_loss': 930,
            'stop_loss_pct': 7,
            'target1': 1060,
            'target1_pct': 6,
            'target2': 1120,
            'target2_pct': 12,
            'volume_cr': 25.5,
            'score': 75,
            'pattern': 'BREAKOUT',
            'strategy': 'Test alert - Please ignore'
        }
        
        print("📤 Sending test alert to Discord...")
        return self.send_alert("SWING_OPPORTUNITY", test_data)

# Test the alerter
if __name__ == "__main__":
    alerter = DiscordAlerter()
    
    print("\n" + "="*50)
    print("DISCORD ALERT TEST")
    print("="*50)
    
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "your_webhook_url_here":
        print("\n⚠️ Please configure your Discord webhook first!")
        print("\nSteps:")
        print("1. Go to your Discord server")
        print("2. Click Server Settings → Integrations → Webhooks")
        print("3. Click 'New Webhook'")
        print("4. Name it 'Trading Alerts'")
        print("5. Copy the webhook URL")
        print("6. Open .env file and paste the URL")
        print("   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...")
    else:
        choice = input("\nSend test alert to Discord? (y/n): ")
        if choice.lower() == 'y':
            if alerter.send_test_alert():
                print("\n✅ Test successful! Check your Discord channel")
            else:
                print("\n❌ Test failed. Check your webhook URL")