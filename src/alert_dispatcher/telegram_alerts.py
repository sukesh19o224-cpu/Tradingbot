"""
V5.5 ULTRA - Telegram Alerts
Faster alerts via Telegram with custom filters
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramAlerter:
    """
    Send trading alerts via Telegram

    Features:
    - Faster than Discord
    - Custom alert filters
    - Configurable message templates
    - Image support for charts
    - Priority alerts
    """

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram alerter

        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Your Telegram chat ID (use @userinfobot to get)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)

        # Alert filters
        self.FILTERS = {
            'min_score': 70,            # Only alert if score >= 70
            'strategies': ['ALL'],       # ['MOMENTUM', 'POSITIONAL'] or ['ALL']
            'min_investment': 0,         # Minimum investment amount
            'priority_only': False       # Only send high-priority alerts
        }

        if self.enabled:
            logger.info("✅ Telegram alerts enabled")
        else:
            logger.warning("⚠️ Telegram alerts disabled (missing token or chat_id)")

    def send_buy_alert(self, opportunity: Dict, investment: float) -> bool:
        """Send BUY alert to Telegram"""
        if not self.enabled:
            return False

        # Check filters
        if not self._should_send_alert(opportunity, investment):
            return False

        # Build message
        message = self._format_buy_message(opportunity, investment)

        # Send
        return self._send_message(message, priority=self._is_priority_trade(opportunity))

    def send_sell_alert(self, trade_result: Dict) -> bool:
        """Send SELL alert to Telegram"""
        if not self.enabled:
            return False

        message = self._format_sell_message(trade_result)
        return self._send_message(message)

    def send_daily_summary(self, summary: Dict) -> bool:
        """Send end-of-day summary"""
        if not self.enabled:
            return False

        message = self._format_daily_summary(summary)
        return self._send_message(message)

    def send_custom_alert(self, title: str, message: str, priority: bool = False) -> bool:
        """Send custom alert"""
        if not self.enabled:
            return False

        formatted = f"🔔 *{title}*\n\n{message}"
        return self._send_message(formatted, priority=priority)

    def _should_send_alert(self, opportunity: Dict, investment: float) -> bool:
        """Check if alert passes filters"""
        # Score filter
        if opportunity.get('score', 0) < self.FILTERS['min_score']:
            return False

        # Strategy filter
        if 'ALL' not in self.FILTERS['strategies']:
            if opportunity.get('strategy') not in self.FILTERS['strategies']:
                return False

        # Investment filter
        if investment < self.FILTERS['min_investment']:
            return False

        # Priority filter
        if self.FILTERS['priority_only']:
            if not self._is_priority_trade(opportunity):
                return False

        return True

    def _is_priority_trade(self, opportunity: Dict) -> bool:
        """Determine if trade is high-priority"""
        score = opportunity.get('score', 0)
        predicted_return = opportunity.get('predicted_return', 0)

        return score >= 85 or predicted_return >= 0.10  # Score 85+ or 10%+ return

    def _format_buy_message(self, opportunity: Dict, investment: float) -> str:
        """Format BUY alert message"""
        strategy_emoji = {
            'MOMENTUM': '🚀',
            'MEAN_REVERSION': '🔄',
            'BREAKOUT': '💥',
            'POSITIONAL': '📈'
        }

        emoji = strategy_emoji.get(opportunity.get('strategy', ''), '📊')
        symbol = opportunity.get('symbol', 'N/A')
        strategy = opportunity.get('strategy', 'N/A')
        score = opportunity.get('score', 0)
        price = opportunity.get('current_price', 0)
        predicted_return = opportunity.get('predicted_return', 0) * 100
        confidence = opportunity.get('confidence', 0)

        message = f"""
{emoji} *BUY SIGNAL*

*Symbol:* {symbol}
*Strategy:* {strategy}
*Score:* {score:.1f}/100

*Entry Price:* ₹{price:.2f}
*Investment:* ₹{investment:,.2f}

*Prediction:* +{predicted_return:.1f}% 
*Confidence:* {confidence:.0f}%

🎯 *Targets:*
"""

        targets = opportunity.get('targets', [])
        for i, target in enumerate(targets, 1):
            message += f"   T{i}: ₹{target:.2f} (+{(target/price - 1)*100:.1f}%)\n"

        stop_loss = opportunity.get('stop_loss', 0)
        message += f"\n🛑 *Stop Loss:* ₹{stop_loss:.2f} (-{(1 - stop_loss/price)*100:.1f}%)"

        return message

    def _format_sell_message(self, trade_result: Dict) -> str:
        """Format SELL alert message"""
        symbol = trade_result.get('symbol', 'N/A')
        pnl = trade_result.get('pnl', 0)
        pnl_pct = trade_result.get('pnl_pct', 0)
        reason = trade_result.get('exit_reason', 'MANUAL')
        days_held = trade_result.get('days_held', 0)

        emoji = "✅" if pnl > 0 else "❌"

        message = f"""
{emoji} *SELL EXECUTED*

*Symbol:* {symbol}
*P&L:* ₹{pnl:,.2f} ({pnl_pct:+.2f}%)
*Days Held:* {days_held}
*Exit Reason:* {reason}

*Entry:* ₹{trade_result.get('entry_price', 0):.2f}
*Exit:* ₹{trade_result.get('exit_price', 0):.2f}
"""

        return message

    def _format_daily_summary(self, summary: Dict) -> str:
        """Format daily summary message"""
        message = f"""
📊 *DAILY SUMMARY*
{datetime.now().strftime('%Y-%m-%d')}

*Portfolio Value:* ₹{summary.get('total_value', 0):,.2f}
*Today's P&L:* ₹{summary.get('daily_pnl', 0):,.2f}

*Open Positions:* {summary.get('open_positions', 0)}
*Trades Today:* {summary.get('trades_today', 0)}

*Capital:* ₹{summary.get('capital', 0):,.2f}
*Invested:* ₹{summary.get('invested', 0):,.2f}
"""

        return message

    def _send_message(self, message: str, priority: bool = False) -> bool:
        """Send message via Telegram API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            # Priority messages get notification
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': not priority
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.debug(f"✅ Telegram alert sent")
                return True
            else:
                logger.error(f"❌ Telegram alert failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Telegram alert error: {e}")
            return False

    def update_filters(self, new_filters: Dict):
        """Update alert filters"""
        self.FILTERS.update(new_filters)
        logger.info("✅ Telegram filters updated")

    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        return self._send_message("🤖 *TraDc V5.5 ULTRA*\n\nTelegram alerts are working!")
