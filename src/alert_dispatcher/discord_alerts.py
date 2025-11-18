"""
📢 DISCORD ALERTS V5.0
Enhanced with:
- Strategy information (MOMENTUM, MEAN_REVERSION, BREAKOUT, POSITIONAL)
- Statistical confidence scores (V5.0)
- Price predictions (V5.0)
- Holding period recommendations (V5.0)
- IST timezone
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
    Send trading alerts to Discord with full V5.0 details
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
            print("✅ Discord alerts enabled (V5.0)")

    def send_buy_alert(self, opportunity):
        """
        Send BUY alert with full V5.0 details

        Args:
            opportunity: dict with symbol, entry_price, shares, stop_loss, targets, strategy,
                        enhanced_score, predicted_return, confidence, recommended_hold_days
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

            # V5.0 NEW: Statistical data
            enhanced_score = opportunity.get('enhanced_score', opportunity.get('score', 0))
            predicted_return = opportunity.get('predicted_return_10d', 0)
            confidence = opportunity.get('prediction_confidence', 0)
            recommended_hold = opportunity.get('recommended_hold_days', 5)
            timeframe = opportunity.get('timeframe_classification', strategy)

            # Calculate potential profit
            potential_profit_t1 = (target1 - entry_price) * shares
            potential_profit_t2 = (target2 - entry_price) * shares
            potential_profit_t3 = (target3 - entry_price) * shares

            # Get IST time
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')

            # Strategy-specific emoji and color
            strategy_config = {
                'MOMENTUM': {'emoji': '🚀', 'color': 65280},  # Green
                'MEAN_REVERSION': {'emoji': '🔄', 'color': 3447003},  # Blue
                'BREAKOUT': {'emoji': '💥', 'color': 15105570},  # Orange
                'POSITIONAL': {'emoji': '📈', 'color': 10181046}  # Purple (NEW!)
            }

            config = strategy_config.get(strategy, {'emoji': '📊', 'color': 65280})
            emoji = config['emoji']
            color = config['color']

            # Build description with V5.0 data
            description_parts = [f"**Strategy:** {emoji} {strategy}"]

            if predicted_return > 0 and confidence > 0:
                description_parts.append(f"**Predicted Return:** +{predicted_return:.1f}% ({confidence:.0f}% confidence)")

            if recommended_hold > 5:
                description_parts.append(f"**Hold Period:** {recommended_hold} days ({timeframe})")

            description = "\n".join(description_parts)

            # Build fields
            fields = [
                {
                    "name": "📊 Trade Details",
                    "value": f"**Quantity:** {shares} shares\n"
                            f"**Entry Price:** ₹{entry_price:.2f}\n"
                            f"**Position Value:** ₹{position_value:,.0f}\n"
                            f"**Score:** {enhanced_score:.0f}/100",
                    "inline": False
                },
                {
                    "name": "🎯 Targets",
                    "value": f"**T1:** ₹{target1:.2f} (₹{potential_profit_t1:+,.0f})\n"
                            f"**T2:** ₹{target2:.2f} (₹{potential_profit_t2:+,.0f})\n"
                            f"**T3:** ₹{target3:.2f} (₹{potential_profit_t3:+,.0f})",
                    "inline": True
                },
                {
                    "name": "⛔ Stop Loss",
                    "value": f"**SL:** ₹{stop_loss:.2f}\n"
                            f"**Risk:** {((entry_price - stop_loss) / entry_price * 100):.1f}%\n"
                            f"**R:R:** {((target2 - entry_price) / (entry_price - stop_loss)):.1f}:1",
                    "inline": True
                }
            ]

            embed = {
                "title": f"{emoji} BUY SIGNAL - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Multi-Strategy Trading System V5.0 | {current_time}"
                }
            }

            # Mention @everyone for high-quality trades
            content = f"@everyone New {strategy} Trade!" if enhanced_score >= 70 else f"New {strategy} Trade"

            data = {
                "content": content,
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 204:
                print(f"✅ BUY alert sent to Discord: {symbol} ({strategy})")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord BUY alert error: {e}")

    def send_exit_alert(self, exit_data):
        """
        Send EXIT/SELL alert with P&L and strategy info

        Args:
            exit_data: dict with symbol, strategy, exit_price, profit_loss, return_percent, reason
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
            days_held = exit_data.get('hold_days', 0)

            # Get IST time
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')

            # Color and emoji based on profit/loss
            if pnl > 0:
                color = 65280  # Green
                emoji = "✅"
                result_text = "PROFIT"
            else:
                color = 16711680  # Red
                emoji = "❌"
                result_text = "LOSS"

            # Strategy emoji
            strategy_emoji = {
                'MOMENTUM': '🚀',
                'MEAN_REVERSION': '🔄',
                'BREAKOUT': '💥',
                'POSITIONAL': '📈'
            }.get(strategy, '📊')

            description = f"**Strategy:** {strategy_emoji} {strategy}\n**Reason:** {reason}"

            if days_held > 0:
                description += f"\n**Days Held:** {days_held} days"

            fields = [
                {
                    "name": "💰 P&L",
                    "value": f"**Amount:** ₹{pnl:+,.0f}\n"
                            f"**Return:** {pnl_percent:+.2f}%\n"
                            f"**Result:** {result_text}",
                    "inline": True
                },
                {
                    "name": "📊 Exit Price",
                    "value": f"₹{exit_price:.2f}",
                    "inline": True
                }
            ]

            embed = {
                "title": f"{emoji} {action} - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Multi-Strategy Trading System V5.0 | {current_time}"
                }
            }

            data = {
                "content": f"Trade Closed: {symbol} ({result_text})",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 204:
                print(f"✅ EXIT alert sent to Discord: {symbol} ({strategy}, {pnl:+.0f})")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord EXIT alert error: {e}")

    def send_daily_summary(self, summary_data):
        """
        Send daily performance summary (NEW V5.0)

        Args:
            summary_data: dict with trades_today, pnl_today, open_positions, capital
        """
        if not self.enabled:
            return

        try:
            trades_today = summary_data.get('trades_today', 0)
            pnl_today = summary_data.get('pnl_today', 0)
            open_positions = summary_data.get('open_positions', 0)
            capital = summary_data.get('capital', 0)
            win_rate_today = summary_data.get('win_rate_today', 0)

            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')

            color = 65280 if pnl_today >= 0 else 16711680
            emoji = "📊"

            embed = {
                "title": f"{emoji} Daily Trading Summary",
                "description": f"Performance for {get_ist_now().strftime('%Y-%m-%d')}",
                "color": color,
                "fields": [
                    {
                        "name": "📈 Today's Performance",
                        "value": f"**Trades:** {trades_today}\n"
                                f"**P&L:** ₹{pnl_today:+,.0f}\n"
                                f"**Win Rate:** {win_rate_today:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "📊 Portfolio Status",
                        "value": f"**Open Positions:** {open_positions}\n"
                                f"**Total Capital:** ₹{capital:,.0f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Multi-Strategy Trading System V5.0 | {current_time}"
                }
            }

            data = {
                "content": "End of Day Summary",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 204:
                print(f"✅ Daily summary sent to Discord")
            else:
                print(f"⚠️ Discord summary failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord summary error: {e}")

    def send_test_alert(self):
        """Send test alert"""
        if not self.enabled:
            print("❌ Discord alerts not enabled")
            return

        try:
            current_time = get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')

            embed = {
                "title": "🧪 TEST ALERT - System V5.0",
                "description": "Discord alerts are working correctly!\n\n"
                              "**New V5.0 Features:**\n"
                              "✅ Statistical confidence scores\n"
                              "✅ Price predictions\n"
                              "✅ Strategy-specific alerts\n"
                              "✅ Holding period recommendations",
                "color": 3447003,  # Blue
                "footer": {
                    "text": f"Multi-Strategy Trading System V5.0 | {current_time}"
                }
            }

            data = {
                "content": "System Test - V5.0",
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
