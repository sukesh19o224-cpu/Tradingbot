"""
💬 DISCORD ALERTS - Rich Embedded Notifications
Beautiful, informative alerts for all trading signals
"""

import requests
import json
from datetime import datetime
from typing import Dict, List
import pytz
import yfinance as yf

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

        # Check strategy-specific Discord settings
        from config.settings import DISCORD_SWING_ALERTS_ENABLED, DISCORD_POSITIONAL_ALERTS_ENABLED
        strategy = signal.get('strategy', 'positional')

        # Skip alert if disabled for this strategy
        if strategy == 'swing' and not DISCORD_SWING_ALERTS_ENABLED:
            return  # Swing alerts disabled
        if strategy == 'positional' and not DISCORD_POSITIONAL_ALERTS_ENABLED:
            return  # Positional alerts disabled

        try:
            symbol = signal['symbol']
            entry_price = signal['entry_price']
            score = signal['score']
            trade_type = signal['trade_type']
            
            # CRITICAL FIX: Prevent duplicate alerts
            # Only send alert if signal was actually executed (has shares/position_size)
            # Check both shares and position_size to ensure execution happened
            has_shares = signal.get('shares', 0) > 0
            has_position_size = signal.get('position_size', 0) > 0
            if not (has_shares or has_position_size):
                # Signal not executed, don't send alert (prevents duplicate alerts)
                return
            
            # ADDITIONAL CHECK: Verify execution actually happened
            # If signal has 'executed' flag, only send if True
            if 'executed' in signal and not signal.get('executed', False):
                return
            
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
            
            # Determine strategy from trade_type OR signal field (more reliable)
            # CRITICAL FIX: Check signal['strategy'] first, then fallback to trade_type
            strategy = signal.get('strategy', 'positional')  # Get from signal if available
            if strategy not in ['swing', 'positional']:
                # Fallback to trade_type detection
                if 'SWING' in trade_type:
                    strategy = 'swing'
                elif 'POSITIONAL' in trade_type:
                    strategy = 'positional'
                else:
                    strategy = 'positional'  # default
            
            # Determine stop loss type - show ACTUAL calculated percentage
            # CRITICAL FIX: Use strategy-specific ATR ranges
            from config.settings import (
                USE_ATR_STOP_LOSS, 
                ATR_MIN_STOP_LOSS_SWING, ATR_MAX_STOP_LOSS_SWING,
                ATR_MIN_STOP_LOSS_POSITIONAL, ATR_MAX_STOP_LOSS_POSITIONAL,
                TRAILING_STOP_BREAKEVEN_ACTIVATION, TRAILING_STOP_ACTIVATION
            )
            signal_type = signal.get('signal_type', 'UNKNOWN')
            
            # Get ATR value if available (from indicators or signal)
            atr = signal.get('atr', 0)
            if atr == 0:
                indicators = signal.get('indicators', {})
                atr = indicators.get('atr', 0)
            
            # Determine strategy to use correct ATR ranges
            # CRITICAL FIX: Use same hardcoded values as paper_trader.py for consistency
            if strategy == 'swing':
                atr_min = ATR_MIN_STOP_LOSS_SWING
                atr_max = ATR_MAX_STOP_LOSS_SWING
                breakeven_threshold = 0.005 * 100  # 0.5% (swing - hardcoded in paper_trader.py)
                trailing_threshold = 0.007 * 100  # 0.7% (swing - hardcoded in paper_trader.py)
            else:  # positional
                atr_min = ATR_MIN_STOP_LOSS_POSITIONAL
                atr_max = ATR_MAX_STOP_LOSS_POSITIONAL
                breakeven_threshold = 0.02 * 100  # 2% (positional - hardcoded in paper_trader.py)
                trailing_threshold = 0.03 * 100  # 3% (positional - hardcoded in paper_trader.py)
            
            # Show actual calculated stop loss percentage
            # If USE_ATR_STOP_LOSS is enabled and risk is in strategy-specific ATR range, indicate ATR-based
            if USE_ATR_STOP_LOSS and atr_min * 100 <= risk_percent <= atr_max * 100:
                if atr > 0:
                    stop_type = f"ATR-based ({risk_percent:.1f}%, ATR: ₹{atr:.2f})"
                else:
                    stop_type = f"ATR-based ({risk_percent:.1f}%)"
            else:
                # Fixed percentage or outside ATR range
                stop_type = f"{risk_percent:.1f}%"
            
            # Add trailing stop information (strategy-specific)
            trailing_info = f"\n**Trailing:** Breakeven at +{breakeven_threshold:.0f}%, ATR trail at +{trailing_threshold:.0f}%"

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
            # Extract EMAs with fallback keys
            ema_20 = signal.get('ema_20', signal.get('ema20', 0))
            ema_50 = signal.get('ema_50', signal.get('ema50', 0))
            
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
                    "value": (
                        f"**Stop Loss:** ₹{signal['stop_loss']:.2f} (-{risk_percent:.1f}%)\n"
                        f"**Stop Type:** {str(stop_type)}{trailing_info}\n"
                        f"**R:R Ratio:** {f'1:{rr_ratio:.1f}' if rr_ratio > 0 else 'Calculating...'}"
                    ),
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
                    "text": f"Industry-Standard Trading System | {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}"
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
            import traceback
            print(f"❌ Discord BUY alert error: {e}")
            print(f"   Error type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                print(f"   Traceback: {traceback.format_exc()[:200]}")

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

        # Check strategy-specific Discord settings
        from config.settings import DISCORD_SWING_ALERTS_ENABLED, DISCORD_POSITIONAL_ALERTS_ENABLED

        # Determine strategy if not provided
        if not strategy:
            trade_type = exit_info.get('trade_type', '')
            if 'SWING' in trade_type:
                strategy = 'swing'
            elif 'POSITIONAL' in trade_type:
                strategy = 'positional'
            else:
                strategy = exit_info.get('strategy', 'positional')

        # Skip alert if disabled for this strategy
        if strategy == 'swing' and not DISCORD_SWING_ALERTS_ENABLED:
            return  # Swing alerts disabled
        if strategy == 'positional' and not DISCORD_POSITIONAL_ALERTS_ENABLED:
            return  # Positional alerts disabled

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
            
            # Get position details for better Discord display
            shares_sold = exit_info.get('shares_sold', shares)
            remaining_shares = exit_info.get('remaining_shares', 0)
            initial_shares = exit_info.get('initial_shares', shares_sold)
            exit_percentage = exit_info.get('exit_percentage', 0)

            # Parse which target was hit from reason
            target_hit = "UNKNOWN"
            trailing_stop_info = ""
            exit_details = ""
            
            if 'TARGET_1' in reason:
                target_hit = "🎯 T1 (First Target)"
                # Show partial exit details
                if exit_type == 'PARTIAL':
                    exit_details = f"\n**Partial Exit:** {shares_sold} shares ({exit_percentage:.0f}% of position)"
                    if remaining_shares > 0:
                        exit_details += f"\n**Remaining:** {remaining_shares} shares"
            elif 'TARGET_2' in reason:
                target_hit = "🎯 T2 (Second Target)"
                # Show partial exit details
                if exit_type == 'PARTIAL':
                    exit_details = f"\n**Partial Exit:** {shares_sold} shares ({exit_percentage:.0f}% of position)"
                    if remaining_shares > 0:
                        exit_details += f"\n**Remaining:** {remaining_shares} shares"
            elif 'TARGET_3' in reason:
                target_hit = "🎯 T3 (Final Target)"
                exit_details = f"\n**Full Exit:** {shares_sold} shares (100% of position)"
            elif 'STOP_LOSS' in reason:
                target_hit = "⛔ Stop Loss Hit"
                exit_details = f"\n**Full Exit:** {shares_sold} shares (100% of position)"
                # Check if it was a trailing stop
                initial_stop = exit_info.get('initial_stop_loss', 0)
                final_stop = exit_info.get('stop_loss', 0)
                if initial_stop > 0 and final_stop > initial_stop:
                    trailing_stop_info = f"\n**Trailing Stop:** ₹{initial_stop:.2f} → ₹{final_stop:.2f} (Profit Protected!)"
            elif 'MAX_HOLDING' in reason:
                target_hit = "⏰ Max Holding Period"
                exit_details = f"\n**Full Exit:** {shares_sold} shares (100% of position)"

            description = f"**Strategy:** {strategy_emoji} {strategy_name}\n" if strategy_name else ""
            description += f"**Result:** {result}\n**Exit Trigger:** {target_hit}{exit_details}{trailing_stop_info}\n**Exit Type:** {exit_type}"

            # Get targets if available
            t1 = exit_info.get('target1', 0)
            t2 = exit_info.get('target2', 0)
            t3 = exit_info.get('target3', 0)

            fields = [
                {
                    "name": "💰 Profit/Loss",
                    "value": f"**Amount:** ₹{pnl:+,.0f}\n"
                            f"**Return:** {pnl_percent:+.2f}%\n"
                            f"**Shares Sold:** {shares_sold}",
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
            
            # Add position details for partial exits
            if exit_type == 'PARTIAL' and remaining_shares > 0:
                fields.append({
                    "name": "📦 Position Status",
                    "value": f"**Initial:** {initial_shares} shares\n"
                            f"**Sold:** {shares_sold} shares ({exit_percentage:.0f}%)\n"
                            f"**Remaining:** {remaining_shares} shares",
                    "inline": True
                })

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
                    "text": f"Industry-Standard Trading System | {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}"
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

    def send_trailing_stop_alert(self, position_info: Dict, paper_trade: bool = False):
        """
        Send alert when trailing stop is activated (breakeven or ATR trailing)

        Args:
            position_info: Position information dict with symbol, current_price, entry_price,
                         stop_loss, initial_stop_loss, profit_pct, breakeven_active, trailing_active, atr
            paper_trade: Whether this is a paper trade
        """
        if not self.enabled:
            return

        # Check strategy-specific Discord settings
        from config.settings import DISCORD_SWING_ALERTS_ENABLED, DISCORD_POSITIONAL_ALERTS_ENABLED
        strategy = position_info.get('strategy', 'positional')

        # Skip alert if disabled for this strategy
        if strategy == 'swing' and not DISCORD_SWING_ALERTS_ENABLED:
            return  # Swing alerts disabled
        if strategy == 'positional' and not DISCORD_POSITIONAL_ALERTS_ENABLED:
            return  # Positional alerts disabled

        try:
            symbol = position_info['symbol']
            current_price = position_info['current_price']
            entry_price = position_info['entry_price']
            stop_loss = position_info['stop_loss']
            initial_stop_loss = position_info.get('initial_stop_loss', stop_loss)
            profit_pct = position_info.get('profit_pct', 0) * 100
            breakeven_active = position_info.get('breakeven_active', False)
            trailing_active = position_info.get('trailing_active', False)
            atr = position_info.get('atr', 0)
            
            # Mode indicator
            mode = " [PAPER]" if paper_trade else ""
            
            # Determine alert type
            if position_info.get('type') == 'PROFIT_MILESTONE':
                # Progressive profit milestone alert
                color = 16766720  # Gold/Yellow
                emoji = "🚀"
                milestone = position_info.get('milestone', 0)
                title = f"🚀 PROFIT MILESTONE REACHED{mode} - {symbol}"
                description = f"**Status:** New Profit High!\n**Milestone:** Hit +{milestone*100:.1f}%\n**Current Profit:** +{profit_pct:.2f}%\n**Action:** Secure profits & let it run!"
            elif breakeven_active and not trailing_active:
                # Breakeven activated
                color = 15844367  # Gold
                emoji = "✅"
                title = f"✅ BREAKEVEN STOP ACTIVATED{mode} - {symbol}"
                description = f"**Status:** Risk-Free Trade!\n**Stop Moved:** ₹{initial_stop_loss:.2f} → ₹{stop_loss:.2f} (Entry Price)\n**Current Profit:** +{profit_pct:.2f}%"
            elif trailing_active:
                # ATR trailing activated
                color = 5763719  # Green
                emoji = "🔒"
                title = f"🔒 ATR TRAILING STOP ACTIVATED{mode} - {symbol}"
                trailing_distance = atr * 1.5 if atr > 0 else 0
                description = f"**Status:** Profit Protection Active!\n**Stop Moved:** ₹{initial_stop_loss:.2f} → ₹{stop_loss:.2f}\n**Current Profit:** +{profit_pct:.2f}%\n**ATR:** ₹{atr:.2f} (Trailing: {trailing_distance:.2f} below price)"
            else:
                # Stop updated but not breakeven/trailing (shouldn't happen, but handle gracefully)
                return
            
            fields = [
                {
                    "name": "📊 Position Details",
                    "value": f"**Entry:** ₹{entry_price:.2f}\n**Current:** ₹{current_price:.2f}\n**Profit:** +{profit_pct:.2f}%",
                    "inline": True
                },
                {
                    "name": "⛔ Stop Loss",
                    "value": f"**Initial:** ₹{initial_stop_loss:.2f}\n**Current:** ₹{stop_loss:.2f}\n**Protected:** {profit_pct:.2f}% profit",
                    "inline": True
                }
            ]
            
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Hybrid Trailing Stop System | {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}"
                }
            }
            
            data = {
                "content": f"{emoji} **Trailing Stop Update:** {symbol}",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:
                print(f"✅ Discord trailing stop alert sent: {symbol}")
            else:
                print(f"⚠️ Discord trailing stop alert failed: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Discord trailing stop alert error: {e}")

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

    def _analyze_position_outlook(self, symbol: str, position: Dict, current_price: float) -> Dict:
        """
        Analyze position and predict outlook using FULL technical analysis
        
        Uses RSI, ADX, MACD, Moving Averages, Volume, and Trend Strength
        RETRIES with delays for accurate calculation
        
        Args:
            symbol: Stock symbol
            position: Position data from portfolio
            current_price: Current market price
            
        Returns:
            Dict with outlook prediction and reasoning
        """
        import time
        
        try:
            from src.data.enhanced_data_fetcher import EnhancedDataFetcher
            from src.strategies.multitimeframe_analyzer import MultiTimeframeAnalyzer
            from src.indicators.technical_indicators import TechnicalIndicators
            
            entry_price = position.get('entry_price', 0)
            # Safety check: ensure entry_price and current_price are valid
            if entry_price <= 0:
                raise ValueError(f"Invalid entry_price for {symbol}: {entry_price}")
            if current_price <= 0:
                raise ValueError(f"Invalid current_price for {symbol}: {current_price}")
            
            profit_pct = ((current_price - entry_price) / entry_price * 100)
            
            # Get daily data using SAME method as system (EnhancedDataFetcher - 75d period)
            max_retries = 3
            retry_delay = 2  # 2 seconds between retries
            daily_data = None
            
            # Use EnhancedDataFetcher (same as system) - fetches 75d (~52 trading days)
            fetcher = EnhancedDataFetcher(api_delay=0.2)
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(retry_delay)  # Wait before retry
                    
                    daily_data = fetcher._fetch_daily_data(symbol, max_retries=2, verbose=False)
                    
                    if daily_data is not None and not daily_data.empty and len(daily_data) >= 50:
                        break  # Success - got enough trading days
                    elif daily_data is not None and len(daily_data) < 50:
                        # 75d might not be enough, try longer period
                        ticker = yf.Ticker(symbol)
                        daily_data = ticker.history(period='90d', interval='1d')  # 90d = ~63 trading days
                        if daily_data is not None and not daily_data.empty and len(daily_data) >= 50:
                            break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise ValueError(f"Unable to fetch data for {symbol} after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_delay)
            
            # MUST have at least 50 trading days
            if daily_data is None or daily_data.empty or len(daily_data) < 50:
                raise ValueError(f"Insufficient trading days for {symbol}: got {len(daily_data) if daily_data is not None else 0} trading days, need 50+")
            
            # Calculate technical indicators with RETRIES
            calc_result = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(retry_delay)  # Wait before retry
                    
                    indicators = TechnicalIndicators()
                    calc_result = indicators.calculate_all(daily_data)
                    
                    if calc_result and len(calc_result) > 0:
                        break  # Success
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise ValueError(f"Failed to calculate indicators for {symbol} after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_delay)
            
            # MUST have indicators - no fallbacks
            if not calc_result or len(calc_result) == 0:
                raise ValueError(f"Indicator calculation returned empty for {symbol}")
            
            # Extract key indicators
            rsi = calc_result.get('rsi', 50)
            adx = calc_result.get('adx', 25)
            macd = calc_result.get('macd', 0)
            macd_signal = calc_result.get('macd_signal', 0)
            macd_hist = calc_result.get('macd_histogram', 0)
            ema_20 = calc_result.get('ema_20', current_price)
            ema_50 = calc_result.get('ema_50', current_price)
            volume_ratio = calc_result.get('volume_ratio', 1.0)
            
            # Determine outlook based on MULTIPLE technical factors
            outlook = 'NEUTRAL'
            prediction = '📊 Holding pattern'
            reasons = []
            bullish_signals = 0
            bearish_signals = 0
            
            # 1. RSI Analysis (comprehensive coverage)
            if rsi > 70:
                bearish_signals += 1
                reasons.append('RSI overbought (>70)')
            elif rsi < 30:
                bullish_signals += 1
                reasons.append('RSI oversold (<30)')
            elif 50 <= rsi <= 65:
                bullish_signals += 1
                reasons.append('RSI in bullish zone (50-65)')
            elif 35 <= rsi < 50:
                bearish_signals += 1
                reasons.append('RSI in bearish zone (35-50)')
            # RSI 30-35 and 65-70 are neutral zones (no signal added, which is correct)
            
            # 2. ADX (Trend Strength)
            if adx >= 25:
                if current_price > ema_20:
                    bullish_signals += 1
                    reasons.append(f'Strong uptrend (ADX {adx:.1f})')
                elif current_price < ema_20:
                    bearish_signals += 1
                    reasons.append(f'Strong downtrend (ADX {adx:.1f})')
                # If current_price == ema_20, no signal (neutral)
            elif adx < 20:
                reasons.append(f'Weak trend (ADX {adx:.1f})')
                # Weak trend doesn't add signals (correct)
            
            # 3. MACD Analysis
            if macd_hist > 0 and macd > macd_signal:
                bullish_signals += 1
                reasons.append('MACD bullish crossover')
            elif macd_hist < 0 and macd < macd_signal:
                bearish_signals += 1
                reasons.append('MACD bearish crossover')
            
            # 4. Moving Average Analysis
            if current_price > ema_20 > ema_50:
                bullish_signals += 1
                reasons.append('Price above 20-MA > 50-MA (bullish alignment)')
            elif current_price < ema_20 < ema_50:
                bearish_signals += 1
                reasons.append('Price below 20-MA < 50-MA (bearish alignment)')
            # Other MA combinations are neutral (no signal added - correct)
            
            # 5. Volume Analysis
            if volume_ratio >= 1.5:
                if bullish_signals > bearish_signals:
                    bullish_signals += 1
                    reasons.append(f'High volume ({volume_ratio:.1f}x) confirms bullish')
                elif bearish_signals > bullish_signals:
                    bearish_signals += 1
                    reasons.append(f'High volume ({volume_ratio:.1f}x) confirms bearish')
            elif volume_ratio < 0.8:
                reasons.append(f'Low volume ({volume_ratio:.1f}x) - weak conviction')
            
            # Determine overall outlook with CLEAR predictions (explicit movement sequences)
            if bullish_signals > bearish_signals + 1:
                outlook = 'BULLISH'
                if adx >= 25 and rsi >= 50 and volume_ratio >= 1.2:
                    prediction = '📈 Will continue UP (strong momentum)'
                elif adx >= 25 and rsi >= 50:
                    prediction = '📈 Will continue UP (good trend)'
                elif rsi >= 50 and macd_hist > 0:
                    prediction = '📈 May go SIDEWAYS briefly, then RISE'
                else:
                    prediction = '📈 May go SIDEWAYS then UP (moderate bullish)'
            elif bearish_signals > bullish_signals + 1:
                outlook = 'BEARISH'
                if adx >= 25 and rsi <= 50 and volume_ratio >= 1.2:
                    prediction = '📉 Will continue DOWN (strong downtrend)'
                elif adx >= 25 and rsi <= 50:
                    prediction = '📉 Will continue DOWN (downtrend)'
                elif rsi <= 50 and macd_hist < 0:
                    prediction = '📉 May go SIDEWAYS briefly, then FALL'
                else:
                    prediction = '📉 May go SIDEWAYS then DOWN (moderate bearish)'
            else:
                outlook = 'NEUTRAL'
                # Check for pullback scenarios with explicit sequences
                if profit_pct > 2 and rsi > 60:
                    prediction = '📊 Will go DOWN first (profit taking), then RISE'
                elif profit_pct < -1 and rsi < 40:
                    prediction = '📊 Will go DOWN slightly (oversold), then RISE'
                elif rsi > 70:
                    prediction = '📊 Will go DOWN first (overbought correction), then RISE'
                elif rsi < 30:
                    prediction = '📊 Will bounce UP from oversold, then RISE further'
                elif volume_ratio < 0.8 and adx < 20:
                    prediction = '📊 Will move SIDEWAYS, may RISE later (weak trend)'
                elif bearish_signals > bullish_signals:
                    prediction = '📊 May go SIDEWAYS then FALL (slight bearish bias)'
                elif bullish_signals > bearish_signals:
                    prediction = '📊 May go SIDEWAYS then RISE (slight bullish bias)'
                else:
                    prediction = '📊 Will move SIDEWAYS (horizontal, not much up/down)'
            
            # Distance to targets/stop loss (check FIRST before profit adjustments)
            target1 = position.get('target1', 0)
            stop_loss = position.get('stop_loss', 0)  # Current stop loss (may be trailing)
            
            # Calculate accurate distance to stop loss (relative to entry price for meaningful context)
            is_near_stop_loss = False
            dist_to_sl_pct = None
            if stop_loss > 0 and current_price > 0 and entry_price > 0:
                # Calculate distance as percentage of entry price (more meaningful)
                dist_to_sl_pct = ((current_price - stop_loss) / entry_price) * 100
                
                # Calculate how much of the risk range is remaining
                # Risk range = entry_price - stop_loss (the original risk)
                risk_range = entry_price - stop_loss
                if risk_range > 0:
                    remaining_risk = current_price - stop_loss
                    risk_remaining_pct = (remaining_risk / risk_range) * 100
                    
                    # Only show "near stop loss" if:
                    # 1. Less than 1% of entry price away from stop loss, OR
                    # 2. Less than 15% of the original risk range remaining
                    if dist_to_sl_pct < 1.0 or risk_remaining_pct < 15:
                        is_near_stop_loss = True
                        # Very close to stop loss - override prediction with explicit warning
                        if outlook == 'BEARISH':
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - Will FALL if breaks support'
                        elif outlook == 'BULLISH':
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - May go DOWN, then RISE'
                        else:
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - May FALL if breaks support'
                else:
                    # Fallback: if risk_range calculation fails, use strict threshold
                    if dist_to_sl_pct < 1.0:
                        is_near_stop_loss = True
                        if outlook == 'BEARISH':
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - Will FALL if breaks support'
                        elif outlook == 'BULLISH':
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - May go DOWN, then RISE'
                        else:
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - May FALL if breaks support'
            
            # Distance to targets
            if target1 > 0 and current_price > 0:
                dist_to_t1 = ((target1 - current_price) / current_price * 100)
                if dist_to_t1 < 2 and dist_to_t1 > 0:
                    prediction += ' (Near T1)'
                elif dist_to_t1 < 5 and dist_to_t1 > 0:
                    prediction += ' (Approaching T1)'
            
            # Profit-based adjustments (context-aware with explicit movement sequences)
            # Only adjust if not already overridden by stop loss warning
            if '⚠️ Near stop loss' not in prediction:
                if profit_pct > 3:
                    if outlook == 'BULLISH':
                        prediction = '📈 Will continue UP - Hold for targets'
                    elif outlook == 'BEARISH':
                        prediction = '🔒 Profit locked - May go DOWN slightly (pullback), then RISE (trailing stop active)'
                    else:
                        prediction = '✅ In profit - Will continue UP or move SIDEWAYS then UP'
                elif profit_pct < -1:
                    if outlook == 'BEARISH':
                        prediction = '⚠️ Will continue DOWN - Watch stop loss closely'
                    elif outlook == 'BULLISH':
                        prediction = '📊 Will go DOWN first (oversold), then RISE'
                    else:
                        # Only show "may fall" if actually close to stop loss (use same accurate calculation)
                        if is_near_stop_loss and dist_to_sl_pct is not None:
                            prediction = f'⚠️ Near stop loss ({dist_to_sl_pct:.1f}% from entry) - Will FALL if breaks support'
                        else:
                            # Neutral outlook with small loss - check signal bias for clearer prediction
                            if bearish_signals > bullish_signals:
                                prediction = '📊 Small loss - May go SIDEWAYS then DOWN slightly (monitor closely)'
                            elif bullish_signals > bearish_signals:
                                prediction = '📊 Small loss - May go SIDEWAYS then RISE (oversold recovery)'
                            else:
                                prediction = '📊 Small loss - Will move SIDEWAYS (not critical, monitor closely)'
                elif profit_pct > 0:
                    if outlook == 'BULLISH':
                        prediction = '📈 Will continue UP (in profit + bullish)'
                    elif outlook == 'BEARISH':
                        prediction = '📊 May go DOWN slightly, then RISE (profit protected)'
                    else:
                        prediction = '📊 In small profit - May go SIDEWAYS then UP'
            
            # Calculate predicted profit/loss percentage and confidence level
            # IMPORTANT: Calculate based on FINAL prediction text, not just outlook
            # This ensures prediction text and profit/loss match!
            predicted_profit_pct = 0.0  # Default to 0, never None
            confidence_pct = 50  # Default confidence
            
            # Calculate signal strength (difference between bullish and bearish signals)
            signal_strength = abs(bullish_signals - bearish_signals)
            total_signals = bullish_signals + bearish_signals
            
            # Analyze the FINAL prediction text to determine direction
            # IMPORTANT: Check in order - stop loss warnings first, then direction
            prediction_lower = prediction.lower()
            near_stop_loss_warning = '⚠️' in prediction or 'near stop loss' in prediction_lower
            
            # Check for UP direction (must not contain DOWN/FALL)
            will_go_up = (any(word in prediction_lower for word in ['up', 'rise', 'continue up', 'go further up', 'bounce up']) 
                         and not any(word in prediction_lower for word in ['down', 'fall', 'continue down']))
            
            # Check for DOWN direction (must not contain UP/RISE)
            will_go_down = (any(word in prediction_lower for word in ['down', 'fall', 'continue down', 'fall further']) 
                           and not any(word in prediction_lower for word in ['up', 'rise', 'bounce up']))
            
            # Check for SIDEWAYS
            will_sideways = any(word in prediction_lower for word in ['sideways', 'horizontal', 'holding pattern', 'same level'])
            
            # Determine confidence and predicted profit/loss based on FINAL prediction
            if near_stop_loss_warning and stop_loss > 0:
                # Near stop loss - high confidence it will hit stop loss
                confidence_pct = 85
                predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
            elif will_go_up and not will_go_down:
                # Prediction says will go UP - use target1 or bullish estimate
                if adx >= 25 and rsi >= 50 and volume_ratio >= 1.2 and signal_strength >= 3:
                    confidence_pct = 90
                    # Strong bullish - predict profit based on distance to T1 or 5-8% gain
                    if target1 > 0:
                        predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                        # If already above target1, predict further gains (use target2 or estimate)
                        if predicted_profit_pct < 0:
                            target2 = position.get('target2', 0)
                            if target2 > 0:
                                predicted_profit_pct = ((target2 - current_price) / current_price) * 100
                            else:
                                predicted_profit_pct = 3.0  # Conservative estimate for further gains
                        predicted_profit_pct = min(predicted_profit_pct, 8.0)
                    else:
                        predicted_profit_pct = 6.0
                elif adx >= 25 and rsi >= 50 and signal_strength >= 2:
                    confidence_pct = 80
                    if target1 > 0:
                        predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                        if predicted_profit_pct < 0:
                            target2 = position.get('target2', 0)
                            if target2 > 0:
                                predicted_profit_pct = ((target2 - current_price) / current_price) * 100
                            else:
                                predicted_profit_pct = 2.5
                        predicted_profit_pct = min(predicted_profit_pct, 6.0)
                    else:
                        predicted_profit_pct = 4.0
                elif signal_strength >= 2:
                    confidence_pct = 70
                    if target1 > 0:
                        predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                        if predicted_profit_pct < 0:
                            target2 = position.get('target2', 0)
                            if target2 > 0:
                                predicted_profit_pct = ((target2 - current_price) / current_price) * 100
                            else:
                                predicted_profit_pct = 2.0
                        predicted_profit_pct = min(predicted_profit_pct, 4.0)
                    else:
                        predicted_profit_pct = 2.5
                else:
                    confidence_pct = 60
                    if target1 > 0:
                        predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                        if predicted_profit_pct < 0:
                            target2 = position.get('target2', 0)
                            if target2 > 0:
                                predicted_profit_pct = ((target2 - current_price) / current_price) * 100
                            else:
                                predicted_profit_pct = 1.5
                        predicted_profit_pct = min(predicted_profit_pct, 3.0)
                    else:
                        predicted_profit_pct = 2.0
                        
            elif will_go_down and not will_go_up:
                # Prediction says will go DOWN - use stop_loss or bearish estimate
                if adx >= 25 and rsi <= 50 and volume_ratio >= 1.2 and signal_strength >= 3:
                    confidence_pct = 90
                    # Strong bearish - predict loss based on distance to stop loss or 3-5% loss
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
                        predicted_profit_pct = max(predicted_profit_pct, -5.0)  # Cap at -5%
                    else:
                        predicted_profit_pct = -4.0
                elif adx >= 25 and rsi <= 50 and signal_strength >= 2:
                    confidence_pct = 80
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
                        predicted_profit_pct = max(predicted_profit_pct, -4.0)
                    else:
                        predicted_profit_pct = -3.0
                elif signal_strength >= 2:
                    confidence_pct = 70
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
                        predicted_profit_pct = max(predicted_profit_pct, -3.0)
                    else:
                        predicted_profit_pct = -2.0
                else:
                    confidence_pct = 60
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
                        predicted_profit_pct = max(predicted_profit_pct, -2.0)
                    else:
                        predicted_profit_pct = -1.5
                        
            elif 'down first' in prediction_lower or 'down slightly' in prediction_lower or 'bounce' in prediction_lower:
                # Prediction says "DOWN first, then RISE" - predict recovery to target1
                # This means it will go down first, then recover, so net result should be positive
                confidence_pct = 65
                if target1 > 0:
                    # Predict it will reach target1 after the pullback
                    predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                    # But cap it reasonably (pullback then recovery scenario)
                    predicted_profit_pct = min(predicted_profit_pct, 5.0)
                    # Ensure it's positive (recovery scenario)
                    if predicted_profit_pct < 0:
                        predicted_profit_pct = 1.5  # At least some recovery expected
                else:
                    predicted_profit_pct = 2.0
                    
            elif will_sideways or 'holding pattern' in prediction_lower:
                # Prediction says SIDEWAYS - predict minimal movement
                confidence_pct = 50
                if bullish_signals > bearish_signals:
                    # Slight upward bias
                    if target1 > 0:
                        predicted_profit_pct = min(((target1 - current_price) / current_price) * 100 * 0.5, 1.5)
                    else:
                        predicted_profit_pct = 0.5
                elif bearish_signals > bullish_signals:
                    # Slight downward bias
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100 * 0.5
                        predicted_profit_pct = max(predicted_profit_pct, -1.5)
                    else:
                        predicted_profit_pct = -0.5
                else:
                    predicted_profit_pct = 0.0
            else:
                # Default fallback based on outlook
                if outlook == 'BULLISH':
                    confidence_pct = 60
                    if target1 > 0:
                        predicted_profit_pct = ((target1 - current_price) / current_price) * 100
                        if predicted_profit_pct < 0:
                            target2 = position.get('target2', 0)
                            if target2 > 0:
                                predicted_profit_pct = ((target2 - current_price) / current_price) * 100
                            else:
                                predicted_profit_pct = 1.5
                        predicted_profit_pct = min(predicted_profit_pct, 3.0)
                    else:
                        predicted_profit_pct = 2.0
                elif outlook == 'BEARISH':
                    confidence_pct = 60
                    if stop_loss > 0:
                        predicted_profit_pct = ((stop_loss - current_price) / current_price) * 100
                        predicted_profit_pct = max(predicted_profit_pct, -2.0)
                    else:
                        predicted_profit_pct = -1.5
                else:
                    confidence_pct = 50
                    predicted_profit_pct = 0.0
            
            # Format prediction with profit/loss and confidence
            # Show BOTH: prediction from CURRENT price AND total from ENTRY price
            # Ensure predicted_profit_pct is never None (safety check)
            if predicted_profit_pct is None:
                predicted_profit_pct = 0.0
                
            # Safety check: entry_price and current_price already validated above
            # Calculate predicted price from current price
            predicted_price = current_price * (1 + predicted_profit_pct / 100)
            
            # Calculate total profit/loss percentage from ENTRY price (opening price)
            # entry_price is guaranteed > 0 from validation above
            total_predicted_pct = ((predicted_price - entry_price) / entry_price) * 100
            
            # Current profit from entry
            current_profit_pct = profit_pct  # Already calculated earlier
            
            # Calculate prediction from CURRENT price (what will happen from now)
            predicted_from_current_pct = predicted_profit_pct  # This is already from current price
            
            # Ensure minimum meaningful prediction (at least 0.1% or show as 0%)
            if abs(total_predicted_pct) < 0.1:
                total_predicted_pct = 0.0
            if abs(predicted_from_current_pct) < 0.1:
                predicted_from_current_pct = 0.0
            
            # Format message clearly showing both perspectives
            # Show: "From Current: ±X% | From Entry: ±Y% (total) | Confidence"
            if predicted_from_current_pct > 0:
                from_current_str = f'+{predicted_from_current_pct:.1f}%'
            elif predicted_from_current_pct < 0:
                from_current_str = f'{predicted_from_current_pct:.1f}%'
            else:
                from_current_str = '0%'
            
            if total_predicted_pct > 0:
                from_entry_str = f'+{total_predicted_pct:.1f}%'
            elif total_predicted_pct < 0:
                from_entry_str = f'{total_predicted_pct:.1f}%'
            else:
                from_entry_str = '0%'
            
            prediction += f' (From Current: {from_current_str} | From Entry: {from_entry_str} total | {confidence_pct}% confidence)'
            
            return {
                'outlook': outlook,
                'prediction': prediction,
                'reason': ' | '.join(reasons[:3]) if reasons else 'Neutral market conditions',  # Limit to 3 reasons
                'rsi': rsi,
                'adx': adx,
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            # NO FALLBACKS - Return error so caller knows analysis failed
            # This ensures we always get accurate analysis or skip the position
            raise ValueError(f"Analysis failed for {symbol}: {str(e)}")

    def send_dual_portfolio_summary(self, summary: Dict, positions_data: Dict = None):
        """
        Send dual portfolio (swing + positional) summary with position analysis

        Args:
            summary: Combined portfolio summary from DualPortfolio
            positions_data: Optional dict with 'swing' and 'positional' positions with current prices
        """
        if not self.enabled:
            return

        try:
            import yfinance as yf
            
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

            # Build position analysis if positions_data provided
            position_analysis = ""
            all_positions = []  # Initialize outside if block
            if positions_data:
                
                # Get swing positions with error handling (skip if analysis fails)
                swing_pos = positions_data.get('swing', {}).get('positions', {})
                swing_prices = positions_data.get('swing', {}).get('current_prices', {})
                for symbol, position in swing_pos.items():
                    current_price = swing_prices.get(symbol, position.get('entry_price', 0))
                    if current_price > 0:
                        try:
                            analysis = self._analyze_position_outlook(symbol, position, current_price)
                            entry_price = position.get('entry_price', 0)
                            profit_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                            all_positions.append({
                                'symbol': symbol.replace('.NS', ''),
                                'type': '🔥 SWING',
                                'profit': profit_pct,
                                'analysis': analysis
                            })
                        except Exception as e:
                            # Skip positions where analysis fails (no fallback)
                            print(f"⚠️ Skipped {symbol}: Analysis failed - {str(e)[:50]}")
                            continue
                
                # Get positional positions with error handling (skip if analysis fails)
                pos_pos = positions_data.get('positional', {}).get('positions', {})
                pos_prices = positions_data.get('positional', {}).get('current_prices', {})
                for symbol, position in pos_pos.items():
                    current_price = pos_prices.get(symbol, position.get('entry_price', 0))
                    if current_price > 0:
                        try:
                            analysis = self._analyze_position_outlook(symbol, position, current_price)
                            entry_price = position.get('entry_price', 0)
                            profit_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                            all_positions.append({
                                'symbol': symbol.replace('.NS', ''),
                                'type': '📈 POS',
                                'profit': profit_pct,
                                'analysis': analysis
                            })
                        except Exception as e:
                            # Skip positions where analysis fails (no fallback)
                            print(f"⚠️ Skipped {symbol}: Analysis failed - {str(e)[:50]}")
                            continue
                
                # Format position analysis (show ALL positions)
                if all_positions:
                    # Sort by profit (best to worst)
                    all_positions.sort(key=lambda x: x['profit'], reverse=True)
                    
                    position_lines = []
                    for pos_info in all_positions:  # Show ALL positions, not just 5
                        profit_emoji = "🟢" if pos_info['profit'] > 0 else "🔴" if pos_info['profit'] < -1 else "🟡"
                        position_lines.append(
                            f"{profit_emoji} **{pos_info['symbol']}** ({pos_info['type']}): "
                            f"{pos_info['profit']:+.1f}% → {pos_info['analysis']['prediction']}"
                        )
                    
                    if position_lines:
                        position_analysis = "\n".join(position_lines)
            
            # PRIORITY: Show ALL positions - remove other fields if needed for space
            fields = []
            
            # Add position outlook FIRST (most important)
            if position_analysis:
                # Discord field value limit is 1024 characters per field
                # Try to fit all positions - if too long, remove other sections
                max_field_length = 1000  # Leave some buffer
                
                if len(position_analysis) > max_field_length:
                    # Try splitting into multiple fields if we have many positions
                    position_lines = position_analysis.split('\n')
                    
                    # Calculate how many fields we need (Discord allows up to 25 fields, 6000 chars total)
                    chars_per_field = 1000
                    num_fields_needed = (len(position_analysis) // chars_per_field) + 1
                    
                    if num_fields_needed <= 3:  # Split into multiple fields
                        for i in range(0, len(position_lines), len(position_lines) // num_fields_needed + 1):
                            chunk = '\n'.join(position_lines[i:i + len(position_lines) // num_fields_needed + 1])
                            field_num = (i // (len(position_lines) // num_fields_needed + 1)) + 1
                            fields.append({
                                "name": f"🔮 POSITION OUTLOOK - Part {field_num}/{num_fields_needed}",
                                "value": chunk,
                                "inline": False
                            })
                    else:
                        # Too many positions - truncate but show count
                        truncated = position_analysis[:max_field_length]
                        last_newline = truncated.rfind('\n')
                        if last_newline > max_field_length * 0.8:
                            truncated = truncated[:last_newline]
                        fields.append({
                            "name": f"🔮 POSITION OUTLOOK (Showing {len(truncated.split(chr(10)))} of {len(all_positions)} Positions)",
                            "value": truncated + f"\n\n... ({len(all_positions) - len(truncated.split(chr(10)))} more positions)",
                            "inline": False
                        })
                else:
                    # All positions fit in one field - add them
                    fields.append({
                        "name": f"🔮 POSITION OUTLOOK (All {len(all_positions)} Positions)",
                        "value": position_analysis,
                        "inline": False
                    })
            
            # Add summary fields ONLY if we have space (after position analysis)
            # Check total embed size - Discord limit is 6000 characters total
            current_size = sum(len(f.get('value', '')) for f in fields)
            remaining_space = 5000 - current_size  # Leave buffer
            
            if remaining_space > 500:  # Only add if we have reasonable space
                # Add compact summary
                summary_text = (
                    f"**Total:** ₹{total_value:,.0f} ({total_return_pct:+.2f}%) | "
                    f"**Trades:** {summary['total_trades']} | **WR:** {win_rate:.1f}%\n"
                    f"**Swing:** ₹{swing_value:,.0f} ({swing_return_pct:+.2f}%) | "
                    f"**Positional:** ₹{pos_value:,.0f} ({pos_return_pct:+.2f}%)"
                )
                
                if len(summary_text) <= remaining_space:
                    fields.insert(0, {
                        "name": "📊 PORTFOLIO SUMMARY",
                        "value": summary_text,
                        "inline": False
                    })

            embed = {
                "title": "💼 Daily Portfolio Summary - Market Close",
                "description": f"**Date:** {datetime.now(IST).strftime('%d %B %Y')}\n**Time:** {datetime.now(IST).strftime('%I:%M %p IST')}",
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Hybrid Trading System | End of Day Analysis"
                }
            }

            data = {
                "content": "📊 **End of Day Summary** - Market Performance & Position Analysis",
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:
                print("✅ Daily summary with position analysis sent to Discord")
            else:
                print(f"⚠️ Discord summary failed: Status {response.status_code}")
                print(f"Response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Error sending dual portfolio summary: {e}")
            import traceback
            traceback.print_exc()

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
