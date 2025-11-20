"""
💬 DISCORD ALERTS - Rich Embedded Notifications
Beautiful, informative alerts for all trading signals
"""

import requests
import json
from datetime import datetime
from typing import Dict, List
import pytz

from config.settings import *

IST = pytz.timezone('Asia/Kolkata')


class DiscordAlerts:
    """
    Send trading alerts to Discord with rich embeds

    Features:
    - Buy/Sell signal alerts
    - Portfolio updates
    - Daily summaries
    - Performance reports
    """

    def __init__(self, webhook_url: str = DISCORD_WEBHOOK_URL):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

        if not self.enabled:
            print("⚠️ Discord webhook not configured - alerts disabled")
        else:
            print("✅ Discord alerts enabled")

    def send_buy_signal(self, signal: Dict, paper_trade: bool = False):
        """
        Send BUY signal alert

        Args:
            signal: Signal dictionary
            paper_trade: Whether this is a paper trade
        """
        if not self.enabled:
            return

        try:
            symbol = signal['symbol']
            entry_price = signal['entry_price']
            score = signal['score']
            trade_type = signal['trade_type']

            # Choose emoji and color based on trade type
            if trade_type == 'SWING':
                emoji = '⚡'
                color = 3447003  # Blue
            else:  # POSITIONAL
                emoji = '📈'
                color = 10181046  # Purple

            # Mode indicator
            mode = " [PAPER]" if paper_trade else ""

            # Build description
            description_parts = []
            description_parts.append(f"**Type:** {emoji} {trade_type}")
            description_parts.append(f"**Score:** {score}/10 {'🔥' if score >= HIGH_QUALITY_SCORE else ''}")

            # Add ML prediction if available
            if signal.get('predicted_return', 0) > 0:
                pred_return = signal['predicted_return']
                ml_conf = signal['ml_confidence']
                description_parts.append(f"**AI Prediction:** +{pred_return:.1f}% ({ml_conf*100:.0f}% confidence)")

            description = "\n".join(description_parts)

            # Calculate potential profits
            target1_profit = ((signal['target1'] - entry_price) / entry_price * 100)
            target2_profit = ((signal['target2'] - entry_price) / entry_price * 100)
            target3_profit = ((signal['target3'] - entry_price) / entry_price * 100)

            # Risk metrics
            risk_percent = ((entry_price - signal['stop_loss']) / entry_price * 100)
            rr_ratio = signal.get('risk_reward_ratio', 0)

            # Build fields
            fields = [
                {
                    "name": "📊 Price & Entry",
                    "value": f"**Current:** ₹{entry_price:.2f}\n"
                            f"**RSI:** {signal.get('rsi', 0):.1f}\n"
                            f"**ADX:** {signal.get('adx', 0):.1f} (Trend Strength)",
                    "inline": True
                },
                {
                    "name": "🎯 Targets",
                    "value": f"**T1:** ₹{signal['target1']:.2f} (+{target1_profit:.1f}%)\n"
                            f"**T2:** ₹{signal['target2']:.2f} (+{target2_profit:.1f}%)\n"
                            f"**T3:** ₹{signal['target3']:.2f} (+{target3_profit:.1f}%)",
                    "inline": True
                },
                {
                    "name": "⛔ Risk Management",
                    "value": f"**Stop Loss:** ₹{signal['stop_loss']:.2f}\n"
                            f"**Risk:** {risk_percent:.1f}%\n"
                            f"**R:R Ratio:** {rr_ratio:.1f}:1",
                    "inline": True
                },
                {
                    "name": "📈 Technical Analysis",
                    "value": f"**Trend:** {signal.get('ema_trend', 'N/A')}\n"
                            f"**MACD:** {signal.get('macd_signal', 'N/A')}\n"
                            f"**Volume:** {signal.get('volume_ratio', 0):.1f}x avg",
                    "inline": True
                },
                {
                    "name": "🔬 Mathematical",
                    "value": f"**Fibonacci:** {signal.get('fibonacci_signal', 'N/A')}\n"
                            f"**Elliott Wave:** {signal.get('elliott_wave', 'N/A')}\n"
                            f"**Math Score:** {signal.get('mathematical_score', 0):.1f}/10",
                    "inline": True
                },
                {
                    "name": "⏱️ Hold Period",
                    "value": f"**Recommended:** {signal.get('recommended_hold_days', 0)} days\n"
                            f"**Risk Level:** {signal.get('risk_level', 'N/A')}",
                    "inline": True
                }
            ]

            embed = {
                "title": f"{emoji} BUY SIGNAL{mode} - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Super Math Trading System | {self._get_ist_time()}"
                },
                "thumbnail": {
                    "url": "https://cdn-icons-png.flaticon.com/512/2936/2936233.png"  # Chart icon
                }
            }

            # Mention @everyone for high-quality signals
            content = ""
            if score >= HIGH_QUALITY_SCORE and DISCORD_MENTION_ON_HIGH_SCORE:
                content = "@everyone 🔥 HIGH QUALITY SIGNAL!"

            data = {
                "content": content,
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                print(f"✅ Discord BUY alert sent: {symbol}")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord BUY alert error: {e}")

    def send_exit_alert(self, exit_info: Dict, paper_trade: bool = False, strategy: str = None):
        """
        Send EXIT alert

        Args:
            exit_info: Exit information dict
            paper_trade: Whether this is a paper trade
            strategy: 'swing' or 'positional' (optional)
        """
        if not self.enabled:
            return

        try:
            symbol = exit_info['symbol']
            exit_price = exit_info['exit_price']
            pnl = exit_info['pnl']
            pnl_percent = exit_info['pnl_percent']
            reason = exit_info['reason']

            # Mode indicator
            mode = " [PAPER]" if paper_trade else ""

            # Strategy indicator
            if strategy == 'swing':
                strategy_emoji = "🔥"
                strategy_name = "SWING"
            elif strategy == 'positional':
                strategy_emoji = "📈"
                strategy_name = "POSITIONAL"
            else:
                strategy_emoji = ""
                strategy_name = ""

            # Color and emoji based on profit/loss
            if pnl > 0:
                color = 65280  # Green
                emoji = "✅"
                result = "PROFIT"
            else:
                color = 16711680  # Red
                emoji = "❌"
                result = "LOSS"

            # Exit type
            exit_type = exit_info.get('exit_type', 'FULL')

            description = f"**Strategy:** {strategy_emoji} {strategy_name}\n" if strategy_name else ""
            description += f"**Result:** {result}\n**Reason:** {reason}\n**Exit Type:** {exit_type}"

            fields = [
                {
                    "name": "💰 Profit/Loss",
                    "value": f"**Amount:** ₹{pnl:+,.0f}\n"
                            f"**Return:** {pnl_percent:+.2f}%\n"
                            f"**Shares:** {exit_info.get('shares', 0)}",
                    "inline": True
                },
                {
                    "name": "📊 Exit Price",
                    "value": f"₹{exit_price:.2f}",
                    "inline": True
                }
            ]

            embed = {
                "title": f"{emoji} EXIT{mode} - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Super Math Trading System | {self._get_ist_time()}"
                }
            }

            data = {
                "content": f"Trade Closed: {symbol} ({result})",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                print(f"✅ Discord EXIT alert sent: {symbol}")
            else:
                print(f"⚠️ Discord alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord EXIT alert error: {e}")

    def send_daily_summary(self, summary: Dict):
        """
        Send daily trading summary

        Args:
            summary: Portfolio summary dict
        """
        if not self.enabled or not SEND_DAILY_SUMMARY:
            return

        try:
            portfolio_value = summary.get('portfolio_value', 0)
            total_return = summary.get('total_return_percent', 0)
            open_positions = summary.get('open_positions', 0)
            total_trades = summary.get('total_trades', 0)
            win_rate = summary.get('win_rate', 0)

            color = 65280 if total_return >= 0 else 16711680

            embed = {
                "title": "📊 Daily Paper Trading Summary",
                "description": f"Performance for {datetime.now(IST).strftime('%d %B %Y')}",
                "color": color,
                "fields": [
                    {
                        "name": "💼 Portfolio Status",
                        "value": f"**Value:** ₹{portfolio_value:,.0f}\n"
                                f"**Return:** {total_return:+.2f}%\n"
                                f"**Open Positions:** {open_positions}",
                        "inline": True
                    },
                    {
                        "name": "📈 Performance",
                        "value": f"**Total Trades:** {total_trades}\n"
                                f"**Win Rate:** {win_rate:.1f}%\n"
                                f"**Best Trade:** ₹{summary.get('best_trade', 0):+,.0f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Super Math Trading System | {self._get_ist_time()}"
                }
            }

            data = {
                "content": "📊 End of Day Summary",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                print("✅ Daily summary sent to Discord")
            else:
                print(f"⚠️ Discord summary failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Discord summary error: {e}")

    def send_test_alert(self):
        """Send test alert to verify Discord connection"""
        if not self.enabled:
            print("❌ Discord not enabled - check DISCORD_WEBHOOK_URL in .env")
            return

        try:
            embed = {
                "title": "🧪 Test Alert - System Active!",
                "description": "Super Math Trading System is operational!\n\n"
                              "**Features:**\n"
                              "✅ Technical Analysis (RSI, MACD, EMA, etc.)\n"
                              "✅ Mathematical Models (Fibonacci, Elliott Wave, Gann)\n"
                              "✅ Machine Learning Predictions\n"
                              "✅ Paper Trading Auto-Execution\n"
                              "✅ Real-time Discord Alerts",
                "color": 3447003,  # Blue
                "footer": {
                    "text": f"Super Math Trading System | {self._get_ist_time()}"
                }
            }

            data = {
                "content": "🚀 System Test",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 204:
                print("✅ Test alert sent successfully!")
                return True
            else:
                print(f"⚠️ Test failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Test alert error: {e}")
            return False

    def send_swing_signal(self, signal: Dict):
        """
        Send SWING trading signal alert

        Args:
            signal: Swing signal dictionary
        """
        if not self.enabled:
            return

        # Add swing-specific formatting
        signal['trade_type'] = signal.get('trade_type', '🔥 SWING TRADE')
        self.send_buy_signal(signal, paper_trade=True)

    def send_positional_signal(self, signal: Dict):
        """
        Send POSITIONAL trading signal alert

        Args:
            signal: Positional signal dictionary
        """
        if not self.enabled:
            return

        # Add positional-specific formatting
        signal['trade_type'] = signal.get('trade_type', '📈 POSITIONAL TRADE')
        self.send_buy_signal(signal, paper_trade=True)

    def send_dual_portfolio_summary(self, summary: Dict):
        """
        Send dual portfolio (swing + positional) summary

        Args:
            summary: Combined portfolio summary from DualPortfolio
        """
        if not self.enabled:
            return

        try:
            # Overall performance
            total_value = summary['total_portfolio_value']
            total_return = summary['total_return']
            total_return_pct = summary['total_return_pct']
            win_rate = summary['win_rate']

            # Swing portfolio
            swing = summary['swing']
            swing_value = swing['portfolio_value']
            swing_return_pct = swing['return_pct']
            swing_positions = swing['positions']
            swing_trades = swing['trades']
            swing_wr = swing['win_rate']

            # Positional portfolio
            pos = summary['positional']
            pos_value = pos['portfolio_value']
            pos_return_pct = pos['return_pct']
            pos_positions = pos['positions']
            pos_trades = pos['trades']
            pos_wr = pos['win_rate']

            # Determine color based on overall performance
            if total_return_pct > 5:
                color = 5763719  # Green
            elif total_return_pct > 0:
                color = 15844367  # Gold
            else:
                color = 15158332  # Red

            embed = {
                "title": "💼 Dual Portfolio Daily Summary",
                "description": "Swing Trading + Positional Trading Performance",
                "color": color,
                "fields": [
                    {
                        "name": "📊 OVERALL PERFORMANCE",
                        "value": f"**Total Value:** ₹{total_value:,.0f}\n"
                                f"**Return:** ₹{total_return:+,.0f} ({total_return_pct:+.2f}%)\n"
                                f"**Total Trades:** {summary['total_trades']}\n"
                                f"**Win Rate:** {win_rate:.1f}%",
                        "inline": False
                    },
                    {
                        "name": "🔥 SWING PORTFOLIO (60%)",
                        "value": f"**Value:** ₹{swing_value:,.0f}\n"
                                f"**Return:** {swing_return_pct:+.2f}%\n"
                                f"**Positions:** {swing_positions}\n"
                                f"**Trades:** {swing_trades} (WR: {swing_wr:.1f}%)\n"
                                f"**Avg Hold:** {swing['avg_holding_days']:.1f} days",
                        "inline": True
                    },
                    {
                        "name": "📈 POSITIONAL PORTFOLIO (40%)",
                        "value": f"**Value:** ₹{pos_value:,.0f}\n"
                                f"**Return:** {pos_return_pct:+.2f}%\n"
                                f"**Positions:** {pos_positions}\n"
                                f"**Trades:** {pos_trades} (WR: {pos_wr:.1f}%)\n"
                                f"**Avg Hold:** {pos['avg_holding_days']:.1f} days",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Hybrid Trading System | {self._get_ist_time()}"
                }
            }

            data = {
                "content": "📊 **End of Day Summary**",
                "embeds": [embed]
            }

            requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )

        except Exception as e:
            print(f"⚠️ Error sending dual portfolio summary: {e}")

    def _get_ist_time(self) -> str:
        """Get current time in IST"""
        return datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')


if __name__ == "__main__":
    # Test Discord alerts
    print("🧪 Testing Discord Alerts...")
    print("Make sure you have DISCORD_WEBHOOK_URL in your .env file!")

    alerter = DiscordAlerts()

    if alerter.enabled:
        # Send test alert
        success = alerter.send_test_alert()

        if success:
            print("\n✅ Discord alerts working correctly!")
            print("You should see a test message in your Discord channel.")
        else:
            print("\n❌ Discord alerts failed. Check your webhook URL.")
    else:
        print("\n❌ Discord not configured. Add DISCORD_WEBHOOK_URL to .env file")
