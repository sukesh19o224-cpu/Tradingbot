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
            
            # Check if this is Strategy 2
            strategy_prefix = ""
            if 'strategy_name' in signal:
                strategy_prefix = "🎯 STRATEGY 2 - "

            # Choose emoji and color based on trade type
            if 'SWING' in trade_type:
                emoji = '⚡'
                color = 3447003  # Blue
            else:  # POSITIONAL
                emoji = '📈'
                color = 10181046  # Purple

            # Mode indicator
            mode = " [PAPER]" if paper_trade else ""

            # Build description with industry-standard metrics
            description_parts = []
            description_parts.append(f"**Type:** {emoji} {trade_type}")
            description_parts.append(f"**Signal Score:** {score}/10 {'🔥' if score >= HIGH_QUALITY_SCORE else ''}")

            # Add strategy type with industry-standard explanations
            strategy_type = signal.get('signal_type', 'UNKNOWN')
            
            # Get quality score based on strategy type
            if strategy_type == 'MEAN_REVERSION':
                quality_score = signal.get('mean_reversion_score', 0)
                quality_valid = signal.get('mean_reversion_valid', False)
            elif strategy_type == 'BREAKOUT':
                quality_score = signal.get('breakout_score', 0)
                quality_valid = signal.get('breakout_valid', False)
            else:  # MOMENTUM
                quality_score = signal.get('momentum_score', 0)
                quality_valid = signal.get('momentum_valid', False)
            
            strategy_explanations = {
                'MOMENTUM': '📈 Strong upward price action (RSI 60-70, ADX ≥25, above 50-MA)',
                'BREAKOUT': '💥 Breaking above resistance with strong momentum',
                'MEAN_REVERSION': '🔄 Pullback to support in uptrend (RSI 30-45, price <20-MA, >50-MA)'
            }
            strategy_emoji_map = {
                'MOMENTUM': '📈',
                'BREAKOUT': '💥',
                'MEAN_REVERSION': '🔄'
            }
            
            # Quality thresholds
            min_quality = 50 if strategy_type == 'MEAN_REVERSION' else 60
            quality_status = '✅' if quality_valid and quality_score >= min_quality else '⚠️'
            
            strategy_emoji = strategy_emoji_map.get(strategy_type, '📊')
            strategy_reason = strategy_explanations.get(strategy_type, 'Technical setup identified')
            description_parts.append(f"**Strategy:** {strategy_emoji} {strategy_type}")
            description_parts.append(f"**Quality Score:** {quality_score}/100 {quality_status} (min {min_quality})")
            description_parts.append(f"*{strategy_reason}*")

            # Add RS (Relative Strength) rating if available
            rs_rating = signal.get('rs_rating', 0)
            if rs_rating > 0:
                if rs_rating >= 120:
                    rs_status = '🚀 Exceptional'
                elif rs_rating >= 110:
                    rs_status = '⭐ Strong'
                elif rs_rating >= 100:
                    rs_status = '👍 Good'
                else:
                    rs_status = '⚠️ Weak'
                description_parts.append(f"**RS Rating:** {rs_rating:.0f} {rs_status} (vs Nifty 50)")

            description = "\n".join(description_parts)

            # Calculate potential profits
            target1_profit = ((signal['target1'] - entry_price) / entry_price * 100)
            target2_profit = ((signal['target2'] - entry_price) / entry_price * 100)
            target3_profit = ((signal['target3'] - entry_price) / entry_price * 100)

            # Risk metrics
            risk_percent = ((entry_price - signal['stop_loss']) / entry_price * 100)
            rr_ratio = signal.get('risk_reward_ratio', 0)
            # Calculate R:R if not provided
            if rr_ratio == 0 and risk_percent > 0:
                rr_ratio = target2_profit / risk_percent
            
            # Determine strategy from trade_type
            strategy = 'positional'  # default
            if 'SWING' in trade_type:
                strategy = 'swing'
            elif 'POSITIONAL' in trade_type:
                strategy = 'positional'
            
            # Determine stop loss type based on strategy and signal type
            signal_type = signal.get('signal_type', 'UNKNOWN')
            if strategy == 'swing':
                stop_type = "Swing (2.5-3%)"
            elif strategy == 'positional':
                if 'MEAN_REVERSION' in signal_type:
                    stop_type = "Mean Reversion (4.5%)"
                elif 'MOMENTUM' in signal_type:
                    stop_type = "Momentum (4%)"
                elif 'BREAKOUT' in signal_type:
                    stop_type = "Breakout (3.5%)"
                else:
                    stop_type = f"ATR-based ({risk_percent:.1f}%)"
            else:
                stop_type = f"ATR-based ({risk_percent:.1f}%)"

            # Build fields
            shares = signal.get('shares', 0)
            position_size = signal.get('position_size', 0)

            # Get quality reasons based on strategy type
            if strategy_type == 'MEAN_REVERSION':
                quality_reasons = signal.get('mean_reversion_reasons', [])
            elif strategy_type == 'BREAKOUT':
                quality_reasons = signal.get('breakout_reasons', [])
            else:  # MOMENTUM
                quality_reasons = signal.get('momentum_reasons', [])
            quality_text = "\n".join(f"• {reason}" for reason in quality_reasons[:3]) if quality_reasons else "Industry-standard filters applied"
            
            # Get ADX and momentum indicators
            rsi = signal.get('rsi', 0)
            adx = signal.get('adx', 0)
            volume_ratio = signal.get('volume_ratio', 1.0)  # Default to 1.0 instead of 0
            
            # ADX strength indicator
            if adx >= 40:
                adx_status = '💪 Very Strong'
            elif adx >= 25:
                adx_status = '👍 Strong'
            elif adx >= 20:
                adx_status = '⚠️ Moderate'
            elif adx > 0:
                adx_status = '❌ Weak'
            else:
                adx_status = 'N/A'
            
            # RSI status based on strategy
            if rsi > 0:  # Only show status if RSI is available
                if strategy_type == 'MEAN_REVERSION':
                    if 30 <= rsi <= 40:
                        rsi_status = '✅ Optimal'
                    elif 40 < rsi <= 50:
                        rsi_status = '👍 Good'
                    else:
                        rsi_status = '⚠️ Check'
                else:  # MOMENTUM
                    if 60 <= rsi <= 68:
                        rsi_status = '✅ Optimal'
                    elif 50 <= rsi < 60 or 68 < rsi <= 70:
                        rsi_status = '👍 Good'
                    else:
                        rsi_status = '⚠️ Check'
            else:
                rsi_status = ''
            
            # MA position
            ema_20 = signal.get('ema_20', 0)
            ema_50 = signal.get('ema_50', 0)
            price_to_ema20 = ((entry_price - ema_20) / ema_20 * 100) if ema_20 > 0 else 0
            price_to_ema50 = ((entry_price - ema_50) / ema_50 * 100) if ema_50 > 0 else 0
            
            # MACD signal
            macd_signal = signal.get('macd_signal', '')
            if not macd_signal or macd_signal == 'N/A':
                macd_value = signal.get('macd', 0)
                macd_hist = signal.get('macd_histogram', 0)
                if macd_hist > 0:
                    macd_signal = '✅ Bullish'
                elif macd_hist < 0:
                    macd_signal = '⚠️ Bearish'
                else:
                    macd_signal = 'Neutral'
            
            fields = [
                {
                    "name": "📊 Price & Position",
                    "value": f"**Entry Price:** ₹{entry_price:.2f}\n"
                            f"**Shares to Buy:** {shares}\n"
                            f"**Investment:** ₹{position_size:,.0f}",
                    "inline": True
                },
                {
                    "name": "📈 Key Indicators",
                    "value": (f"**RSI:** {rsi:.1f} {rsi_status}\n" if rsi > 0 else "**RSI:** N/A\n") +
                            (f"**ADX:** {adx:.1f} {adx_status}\n" if adx > 0 else "**ADX:** N/A\n") +
                            f"**Volume:** {volume_ratio:.1f}x avg",
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
                    "value": f"**Stop Loss:** ₹{signal['stop_loss']:.2f} (-{risk_percent:.1f}%)\n"
                            f"**Stop Type:** {stop_type}\n"
                            (f"**R:R Ratio:** 1:{rr_ratio:.1f}" if rr_ratio > 0 else "**R:R Ratio:** Calculating..."),
                    "inline": True
                },
                {
                    "name": "📍 Price Position",
                    "value": (f"**20-MA:** ₹{ema_20:.2f} ({price_to_ema20:+.1f}%)\n" if ema_20 > 0 else "**20-MA:** N/A\n") +
                            (f"**50-MA:** ₹{ema_50:.2f} ({price_to_ema50:+.1f}%)\n" if ema_50 > 0 else "**50-MA:** N/A\n") +
                            f"**MACD:** {macd_signal}",
                    "inline": True
                },
                {
                    "name": "✅ Quality Factors",
                    "value": quality_text,
                    "inline": True
                },
                {
                    "name": "⏱️ Hold Period",
                    "value": f"**Recommended:** {signal.get('recommended_hold_days', 7)} days\n"
                            f"**Max Holding:** {signal.get('max_hold_days', 15)} days",
                    "inline": True
                }
            ]

            embed = {
                "title": f"{strategy_prefix}{emoji} BUY SIGNAL{mode} - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Industry-Standard Trading System | {self._get_ist_time()}"
                },
                "thumbnail": {
                    "url": "https://cdn-icons-png.flaticon.com/512/2936/2936233.png"  # Chart icon
                }
            }

            # Mention @everyone for A+ quality signals (quality score ≥70 and signal score ≥8.5)
            content = ""
            if quality_score >= 70 and score >= 8.5 and DISCORD_MENTION_ON_HIGH_SCORE:
                content = "@everyone 🔥 A+ QUALITY SIGNAL! (Industry Standard)"

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
            entry_price = exit_info.get('entry_price', 0)
            pnl = exit_info['pnl']
            pnl_percent = exit_info['pnl_percent']
            reason = exit_info['reason']
            shares = exit_info.get('shares', 0)

            # Mode indicator
            mode = " [PAPER]" if paper_trade else ""
            
            # Check if this is Strategy 2
            strategy_prefix = ""
            if 'strategy_name' in exit_info:
                strategy_prefix = "🎯 STRATEGY 2 - "

            # Strategy indicator - try from exit_info first, then parameter
            trade_type = exit_info.get('trade_type', '')
            if not strategy:
                if 'SWING' in trade_type:
                    strategy = 'swing'
                elif 'POSITIONAL' in trade_type:
                    strategy = 'positional'

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

            # Parse which target was hit from reason
            target_hit = "UNKNOWN"
            if 'TARGET_1' in reason:
                target_hit = "🎯 T1 (First Target)"
            elif 'TARGET_2' in reason:
                target_hit = "🎯 T2 (Second Target)"
            elif 'TARGET_3' in reason:
                target_hit = "🎯 T3 (Final Target)"
            elif 'STOP_LOSS' in reason:
                target_hit = "⛔ Stop Loss Hit"
            elif 'MAX_HOLDING' in reason:
                target_hit = "⏰ Max Holding Period"

            description = f"**Strategy:** {strategy_emoji} {strategy_name}\n" if strategy_name else ""
            description += f"**Result:** {result}\n**Exit Trigger:** {target_hit}\n**Exit Type:** {exit_type}"

            # Get targets if available
            t1 = exit_info.get('target1', 0)
            t2 = exit_info.get('target2', 0)
            t3 = exit_info.get('target3', 0)

            fields = [
                {
                    "name": "💰 Profit/Loss",
                    "value": f"**Amount:** ₹{pnl:+,.0f}\n"
                            f"**Return:** {pnl_percent:+.2f}%\n"
                            f"**Shares Sold:** {shares}",
                    "inline": True
                },
                {
                    "name": "📊 Price Details",
                    "value": f"**Entry:** ₹{entry_price:.2f}\n"
                            f"**Exit:** ₹{exit_price:.2f}\n"
                            f"**Move:** {pnl_percent:+.2f}%",
                    "inline": True
                }
            ]

            # Add targets field if available
            if t1 > 0 and t2 > 0 and t3 > 0:
                fields.append({
                    "name": "🎯 Targets (Reference)",
                    "value": f"**T1:** ₹{t1:.2f}\n"
                            f"**T2:** ₹{t2:.2f}\n"
                            f"**T3:** ₹{t3:.2f}",
                    "inline": True
                })

            embed = {
                "title": f"{strategy_prefix}{emoji} EXIT{mode} - {symbol}",
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Industry-Standard Trading System | {self._get_ist_time()}"
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
                    "text": f"Industry-Standard Trading System | {self._get_ist_time()}"
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
                "description": "Industry-Standard Trading System is operational!\n\n"
                              "**Features:**\n"
                              "✅ Mean Reversion: RSI 30-45, Price <20-MA, >50-MA\n"
                              "✅ Momentum: RSI 60-70, ADX ≥25 mandatory\n"
                              "✅ Relative Strength (RS) vs Nifty 50 benchmark\n"
                              "✅ Quality Scoring: 50+ MR, 60+ Momentum\n"
                              "✅ Paper Trading Auto-Execution\n"
                              "✅ Real-time Discord Alerts",
                "color": 3447003,  # Blue
                "footer": {
                    "text": f"Industry-Standard Trading System | {self._get_ist_time()}"
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
