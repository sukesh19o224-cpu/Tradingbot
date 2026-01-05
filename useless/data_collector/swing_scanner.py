# src/data_collector/swing_scanner.py

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *
from src.indicators.mathematical_indicators import MathematicalIndicators
from src.indicators.technical_indicators import TechnicalIndicators

class SwingScanner:
    """
    🚀 UPGRADED SWING SCANNER FOR 4-8% MONTHLY RETURNS
    
    Finds HIGH MOMENTUM stocks for 2-5 day swing trades by scanning a
    pre-screened daily watchlist.
    
    UPGRADED with:
    - Multi-timeframe confirmation (Tier 2 - Upgrade 5)
    - Gap handling logic (Tier 2 - Upgrade 6)
    - Trend strength filter (Tier 2 - Upgrade 9)
    - Phase 3 bonus scoring (10+ new bonuses)
    - Optimized thresholds for more opportunities
    
    Version: 2.0 - Fully Upgraded
    """
    
    def __init__(self, watchlist_file='data/daily_watchlist.csv'):
        print("--- SwingScanner initialized (FULLY UPGRADED - V2.0) ---")
        self.watchlist_file = watchlist_file
        self.math_indicators = MathematicalIndicators()
        self.tech_indicators = TechnicalIndicators()

    def _load_from_watchlist(self):
        try:
            if os.path.exists(self.watchlist_file):
                df = pd.read_csv(self.watchlist_file)
                return df['symbol'].tolist()
            else:
                return None
        except Exception as e:
            print(f"❌ Error loading daily watchlist file: {e}")
            return None

    def _fetch_from_nse(self):
        try:
            base_url = "https://www.nseindia.com/"
            api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
            session = requests.Session()
            session.get(base_url, headers=headers, timeout=10)
            time.sleep(0.5)
            response = session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [item['symbol'] for item in data['data']]
        except Exception as e:
            print(f"❌ Critical Error: Failed to fetch fallback stock list from NSE API: {e}")
            return None

    def get_all_stocks(self):
        print("🔄 Loading stock list for today's scan...")
        symbols = self._load_from_watchlist()
        if symbols:
            print(f"✅ Loaded {len(symbols)} stocks from the pre-screened daily watchlist.")
            return [f"{symbol}.NS" for symbol in symbols]
        print(f"⚠️ Daily watchlist file not found at '{self.watchlist_file}'.")
        print("Falling back to fetching the Nifty 500 list directly.")
        symbols = self._fetch_from_nse()
        if symbols:
            all_stocks = [f"{symbol}.NS" for symbol in symbols]
            print(f"✅ Successfully fetched {len(all_stocks)} fallback stocks from the NSE.")
            return list(set(all_stocks))
        else:
            print("❌ Fallback method also failed. Using a minimal hardcoded list.")
            fallback_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "TATAMOTORS", "MARUTI", "SUNPHARMA", "TATASTEEL", "HINDALCO", "INDUSINDBK", "TITAN", "ADANIENT", "ADANIPORTS", "ADANIGREEN", "ADANIPOWER", "IRCTC", "VEDL", "SAIL", "BANKBARODA", "PNB", "CANBK", "BHEL", "SUZLON", "RBLBANK", "IDFCFIRSTB", "HAL", "BEL", "GAIL", "NMDC", "DLF", "TATAPOWER", "NTPC", "INDIGO", "LTIM", "BSOFT"]
            return list(set([f"{stock}.NS" for stock in fallback_stocks]))
    
    def check_market_regime(self, end_date=None):
        """
        Checks the overall market health by comparing Nifty 50 to its 50-day moving average.
        Returns True if bullish (above MA), False if bearish (below MA).
        """
        print("1a. Checking overall market regime...")
        try:
            nifty = yf.Ticker("^NSEI")
            df = nifty.history(period="3mo", interval="1d", auto_adjust=True, end=end_date)

            if len(df) < 50:
                print("⚠️ Could not get enough Nifty 50 data. Being conservative - allowing trades with caution flag.")
                return True
            
            ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
            current_price = df['Close'].iloc[-1]

            if current_price > ma50:
                print(f"   ✅ Market Regime: BULLISH (Nifty at {current_price:,.0f} > 50-DMA at {ma50:,.0f})")
                return True
            else:
                print(f"   ❌ Market Regime: BEARISH (Nifty at {current_price:,.0f} < 50-DMA at {ma50:,.0f})")
                return False
        except Exception as e:
            print(f"⚠️ Error checking market regime: {e}. Allowing trades with caution.")
            return True

    def calculate_trend_strength(self, df):
        """
        Calculate how strong and consistent the trend is
        Returns: trend_strength score (0-100)
        """
        try:
            if len(df) < 20:
                return 0
            
            # Method 1: Directional Movement Consistency
            highs = df['High'].tail(20)
            lows = df['Low'].tail(20)
            
            higher_highs = sum([highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs))])
            higher_lows = sum([lows.iloc[i] > lows.iloc[i-1] for i in range(1, len(lows))])
            
            # Consistency score (what % of days showed higher highs/lows)
            trend_consistency = ((higher_highs + higher_lows) / (len(highs) * 2)) * 100
            
            # Method 2: Price Movement Efficiency
            price_range = df['High'].tail(20).max() - df['Low'].tail(20).min()
            net_move = abs(df['Close'].iloc[-1] - df['Close'].iloc[-20])
            
            # How efficiently price moved (straight vs choppy)
            efficiency = (net_move / price_range * 100) if price_range > 0 else 0
            
            # Combined trend strength score
            trend_strength = (trend_consistency + efficiency) / 2
            
            return round(trend_strength, 2)
        
        except Exception as e:
            return 0

    def check_weekly_alignment(self, stock, end_date=None):
        """
        Check weekly timeframe for trend confirmation
        Returns: (weekly_bullish: bool, weekly_momentum: float, bonus_score: int)
        """
        try:
            # Fetch weekly data
            weekly_df = stock.history(period="6mo", interval="1wk", auto_adjust=True, end=end_date)
            
            if weekly_df.empty or len(weekly_df) < 20:
                return False, 0, 0
            
            # Check weekly trend
            weekly_ma20 = weekly_df['Close'].rolling(20).mean().iloc[-1]
            current_price = weekly_df['Close'].iloc[-1]
            weekly_bullish = current_price > weekly_ma20
            
            # Check weekly momentum (last 4 weeks)
            if len(weekly_df) >= 5:
                weekly_momentum = ((current_price / weekly_df['Close'].iloc[-5]) - 1) * 100
            else:
                weekly_momentum = 0
            
            # Assign bonus/penalty
            if weekly_bullish and weekly_momentum > 5:
                bonus_score = 20  # Strong weekly alignment
            elif weekly_bullish and weekly_momentum > 0:
                bonus_score = 10  # Decent weekly alignment
            elif not weekly_bullish and weekly_momentum < -5:
                bonus_score = -15  # Strong counter-trend (penalty)
            elif not weekly_bullish:
                bonus_score = -5  # Weak counter-trend
            else:
                bonus_score = 0
            
            return weekly_bullish, round(weekly_momentum, 2), bonus_score
        
        except Exception as e:
            return False, 0, 0

    def detect_gap(self, df):
        """
        Detect if stock gapped up/down today
        Returns: (has_gap: bool, gap_percent: float, gap_direction: str)
        """
        try:
            if len(df) < 2:
                return False, 0, 'NONE'
            
            today_open = df['Open'].iloc[-1]
            yesterday_close = df['Close'].iloc[-2]
            
            gap_percent = ((today_open - yesterday_close) / yesterday_close) * 100
            
            if gap_percent > 2:
                return True, round(gap_percent, 2), 'UP'
            elif gap_percent < -2:
                return True, round(gap_percent, 2), 'DOWN'
            else:
                return False, round(gap_percent, 2), 'NONE'
        
        except Exception as e:
            return False, 0, 'NONE'

    def calculate_momentum_score(self, symbol, end_date=None):
        """
        🚀 FULLY UPGRADED SCORING ALGORITHM
        
        Performs detailed analysis on a single stock with:
        - Multi-timeframe confirmation
        - Gap handling
        - Trend strength
        - 10+ bonus scoring rules
        """
        print(f"\n--- Inside calculate_momentum_score for {symbol} (UPGRADED V2.0) ---")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="3mo", interval="1d", auto_adjust=True, end=end_date)
            
            print("1. Initial data check...")
            if df.empty or len(df) < 50:
                print(f"❌ EXIT: DataFrame is empty or too short. len(df) = {len(df) if not df.empty else 0}")
                return None
            print("   ✅ Data check passed.")

            print("2. Calculating key metrics...")
            current_price = df['Close'].iloc[-1]
            
            if len(df) < 21:
                print(f"❌ EXIT: Not enough data for momentum calculation. len(df) = {len(df)}")
                return None
            
            momentum_20d = ((current_price / df['Close'].iloc[-20]) - 1) * 100
            
            if len(df) >= 6:
                momentum_5d = ((current_price / df['Close'].iloc[-5]) - 1) * 100
            else:
                momentum_5d = momentum_20d
            
            avg_volume = df['Volume'].iloc[-20:].mean()
            if pd.isna(avg_volume) or avg_volume == 0:
                print(f"❌ EXIT: Invalid volume data (NaN or zero)")
                return None
            
            volume_ratio = df['Volume'].iloc[-1] / avg_volume
            
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            atr_rolling = true_range.rolling(14).mean()
            if pd.isna(atr_rolling.iloc[-1]) or current_price == 0:
                print(f"❌ EXIT: Invalid ATR data or zero price")
                return None
            
            atr_percent = (atr_rolling.iloc[-1] / current_price * 100)
            atr_value = atr_rolling.iloc[-1]
            
            if len(df) >= 20:
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                above_ma20 = current_price > ma20
            else:
                above_ma20 = False
                ma20 = current_price
            
            if len(df) >= 50:
                ma50 = df['Close'].rolling(50).mean().iloc[-1]
                above_ma50 = current_price > ma50
            else:
                above_ma50 = False
                ma50 = current_price
            
            # Calculate MA5 for momentum surge bonus
            if len(df) >= 5:
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
            else:
                ma5 = current_price
            
            nifty = yf.Ticker("^NSEI")
            nifty_df = nifty.history(period="1mo", auto_adjust=True, end=end_date)
            if not nifty_df.empty and len(nifty_df) >= 20:
                relative_strength = ((current_price / df['Close'].iloc[-20] - 1) - (nifty_df['Close'].iloc[-1] / nifty_df['Close'].iloc[-20] - 1)) * 100
            else:
                relative_strength = momentum_20d

            distance_from_high = (df['High'].max() - current_price) / df['High'].max() * 100 if df['High'].max() > 0 else 100
            is_breakout = current_price > df['High'].iloc[-21:-1].max() * 0.98 if len(df) > 21 else False
            
            # UPGRADE 5: Multi-timeframe check
            print("2a. UPGRADE 5: Checking weekly timeframe alignment...")
            weekly_bullish, weekly_momentum, timeframe_bonus = self.check_weekly_alignment(stock, end_date)
            print(f"   Weekly Bullish: {weekly_bullish}, Weekly Momentum: {weekly_momentum:.2f}%, Bonus: {timeframe_bonus}")
            
            # UPGRADE 6: Gap detection
            print("2b. UPGRADE 6: Checking for gaps...")
            has_gap, gap_percent, gap_direction = self.detect_gap(df)
            print(f"   Gap Detected: {has_gap}, Direction: {gap_direction}, Size: {gap_percent:.2f}%")
            
            # UPGRADE 9: Trend strength
            print("2c. UPGRADE 9: Calculating trend strength...")
            trend_strength = self.calculate_trend_strength(df)
            print(f"   Trend Strength: {trend_strength:.2f}/100")
            
            print(f"   - Current Price: {current_price:.2f}")
            print(f"   - Momentum (5d): {momentum_5d:.2f}%")
            print(f"   - Momentum (20d): {momentum_20d:.2f}%")
            print(f"   - Volume Ratio: {volume_ratio:.2f}")
            print(f"   - ATR Percent: {atr_percent:.2f}%")
            print(f"   - Above MA20: {above_ma20}")
            print(f"   - Above MA50: {above_ma50}")
            print(f"   - Relative Strength vs Nifty: {relative_strength:.2f}%")
            print(f"   - Distance from High: {distance_from_high:.2f}%")
            print(f"   - Is Breakout: {is_breakout}")

            print("3. Calculating base score with upgraded logic...")
            score = 0
            
            # Momentum scoring (early momentum sweet spot)
            if momentum_5d > 3 and momentum_5d < 7:
                score_mom_5d = 35
            elif momentum_5d >= 7:
                score_mom_5d = 20
            elif momentum_5d > 1:
                score_mom_5d = 10
            else:
                score_mom_5d = 0
            score += score_mom_5d
            print(f"   - Score (5d Momentum): {score_mom_5d}")

            # Volume scoring (lowered threshold)
            if volume_ratio > 3.0:
                score_vol = 25
            elif volume_ratio > 1.5:
                score_vol = 20
            elif volume_ratio > 1.2:
                score_vol = 10
            else:
                score_vol = 0
            score += score_vol
            print(f"   - Score (Volume Ratio): {score_vol}")

            score_mom_20d = (momentum_20d > 10) * 15
            score += score_mom_20d
            print(f"   - Score (20d Momentum > 10%): {score_mom_20d}")

            score_ma = (above_ma20 and above_ma50) * 10
            score += score_ma
            print(f"   - Score (MA Trend): {score_ma}")

            score_high = (distance_from_high < 5) * 10
            score += score_high
            print(f"   - Score (Near 52W High): {score_high}")

            score_breakout = is_breakout * 15
            score += score_breakout
            print(f"   - Score (Breakout): {score_breakout}")

            score_rs = (relative_strength > 5) * 10
            score += score_rs
            print(f"   - Score (Relative Strength > 5%): {score_rs}")
            
            # Apply timeframe bonus/penalty
            score += timeframe_bonus
            print(f"   - Score (Weekly Alignment): {timeframe_bonus}")
            
            # Apply gap penalty (avoid chasing)
            gap_penalty = 0
            if has_gap and gap_direction == 'UP' and gap_percent > 2:
                gap_penalty = -15
                score += gap_penalty
                print(f"   - Score (Gap Penalty): {gap_penalty}")
            
            # Apply trend strength bonus
            trend_bonus = 0
            if trend_strength > 70:
                trend_bonus = 15
            elif trend_strength > 50:
                trend_bonus = 8
            elif trend_strength < 30:
                trend_bonus = -10
            score += trend_bonus
            print(f"   - Score (Trend Strength): {trend_bonus}")

            print(f"   🔥 BASE SCORE: {score}")
            
            # ============================================
            # PHASE 3 BONUS SCORING
            # ============================================
            print("\n   💎 Applying Phase 3 Bonuses...")
            
            # BONUS 1: High Volume Surge
            if volume_ratio > 3:
                score += 10
                print(f"   - BONUS (High Volume): +10")
            
            # BONUS 2: Strong Relative Strength
            if relative_strength > 10:
                score += 10
                print(f"   - BONUS (Strong RS): +10")
            
            # BONUS 3: Tight Consolidation Breakout
            if atr_percent < 2.0 and is_breakout:
                score += 10
                print(f"   - BONUS (Tight Breakout): +10")
            
            # BONUS 4: Momentum Surge
            if momentum_5d > 8:
                score += 15
                print(f"   - BONUS (Momentum Surge): +15")
            
            # BONUS 5: Multi-Timeframe Confirmation
            if weekly_bullish and momentum_20d > 5:
                score += 10
                print(f"   - BONUS (Multi-TF): +10")
            
            # BONUS 6: Strong Trend
            if trend_strength > 70:
                score += 15
                print(f"   - BONUS (Strong Trend): +15")
            
            # BONUS 7: Above All Moving Averages
            if above_ma20 and above_ma50:
                if len(df) >= 200:
                    ma200 = df['Close'].rolling(200).mean().iloc[-1]
                    if current_price > ma200:
                        score += 10
                        print(f"   - BONUS (Above All MAs): +10")
            
            # BONUS 8: Volume Breakout Combination
            if is_breakout and volume_ratio > 1.5:
                score += 10
                print(f"   - BONUS (Volume Breakout): +10")
            
            # BONUS 9: Near High with Volume
            if distance_from_high < 3 and volume_ratio > 1.5:
                score += 10
                print(f"   - BONUS (High + Volume): +10")
            
            # BONUS 10: Consolidation Breakout Pattern
            consolidation_check = df['High'].iloc[-5:-1].max() - df['Low'].iloc[-5:-1].min()
            price_range = (consolidation_check / current_price) * 100 if current_price > 0 else 0
            if price_range < 3 and is_breakout:
                score += 15
                print(f"   - BONUS (Consolidation Break): +15")
            
            print(f"\n   🚀 FINAL SCORE WITH BONUSES: {score}")
            
            print("\n4. Checking final filters...")
            print(f"   - Price vs MIN_PRICE ({MIN_PRICE}): {current_price >= MIN_PRICE}")
            print(f"   - Price vs MAX_PRICE ({MAX_PRICE}): {current_price <= MAX_PRICE}")
            print(f"   - ATR vs MIN_DAILY_MOVE ({MIN_DAILY_MOVE}): {atr_percent >= MIN_DAILY_MOVE}")
            
            if current_price < MIN_PRICE or current_price > MAX_PRICE or atr_percent < MIN_DAILY_MOVE:
                print("❌ EXIT: Final filter failed.")
                return None
            print("   ✅ Final filters passed.")

            # Determine strategy type and calculate stop loss/targets
            pattern = self.identify_pattern(df)
            if pattern in ['BREAKOUT', 'FLAG']:
                strategy_config = BREAKOUT
                trade_type = 'BREAKOUT'
            else:
                strategy_config = MOMENTUM
                trade_type = 'MOMENTUM'

            # Calculate stop loss and targets
            entry_price = current_price
            stop_loss = entry_price * (1 - strategy_config['STOP_LOSS'])
            target1 = entry_price * (1 + strategy_config['TARGETS'][0])
            target2 = entry_price * (1 + strategy_config['TARGETS'][1])
            target3 = entry_price * (1 + strategy_config['TARGETS'][2])

            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

            # Calculate ADX
            high = df['High']
            low = df['Low']
            close = df['Close']

            plus_dm = high.diff()
            minus_dm = low.diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0

            tr1 = pd.DataFrame(high - low)
            tr2 = pd.DataFrame(abs(high - close.shift(1)))
            tr3 = pd.DataFrame(abs(low - close.shift(1)))
            tr = pd.concat([tr1, tr2, tr3], axis=1, join='inner').max(axis=1)
            atr_series = tr.rolling(ADX_PERIOD).mean()

            plus_di = 100 * (plus_dm.rolling(ADX_PERIOD).mean() / atr_series)
            minus_di = 100 * (abs(minus_dm).rolling(ADX_PERIOD).mean() / atr_series)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(ADX_PERIOD).mean()
            adx_value = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25

            # Calculate risk/reward ratio
            risk_amount = entry_price - stop_loss
            reward_amount = target1 - entry_price
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

            # Calculate REAL mathematical indicators
            math_result = self.math_indicators.calculate_all(df)
            if math_result:
                math_score = math_result.get('mathematical_score', score * 0.8)
                math_signals = math_result.get('signals', {})
                fib_signal = math_signals.get('fibonacci', 'NO_SIGNAL')
                elliott = math_result.get('elliott_wave', {})
                elliott_pattern = elliott.get('pattern', 'UNKNOWN')
            else:
                # Fallback if calculation fails
                math_score = round(score * 0.8, 1)
                fib_signal = 'BREAKOUT ZONE' if is_breakout else 'NO_SIGNAL'
                elliott_pattern = 'UNKNOWN'

            # Calculate REAL technical indicators (MACD)
            tech_result = self.tech_indicators.calculate_all(df)
            if tech_result:
                macd_value = tech_result.get('macd', 0)
                macd_sig = tech_result['signals'].get('macd_signal', 'NEUTRAL')
                ema_trend = tech_result['signals'].get('ema_trend', 'NEUTRAL')
            else:
                macd_value = 0
                macd_sig = 'BULLISH' if momentum_5d > 0 else 'NEUTRAL'
                ema_trend = 'BULLISH' if above_ma20 and above_ma50 else 'NEUTRAL'

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': round(current_price, 2),
                'today_change': round((current_price / df['Open'].iloc[-1] - 1) * 100, 2),
                '5d_momentum': round(momentum_5d, 2),
                '20d_momentum': round(momentum_20d, 2),
                'volume_ratio': round(volume_ratio, 2),
                'atr_percent': round(atr_percent, 2),
                'atr_value': round(atr_value, 2),
                'relative_strength': round(relative_strength, 2),
                'from_52w_high': round(distance_from_high, 2),
                'above_ma20': above_ma20,
                'above_ma50': above_ma50,
                'is_breakout': is_breakout,
                'score': round(score, 2),
                'pattern': pattern,
                'weekly_bullish': weekly_bullish,
                'weekly_momentum': weekly_momentum,
                'has_gap': has_gap,
                'gap_percent': gap_percent,
                'gap_direction': gap_direction,
                'trend_strength': trend_strength,

                # Required fields for paper trading
                'current_price': round(entry_price, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target1': round(target1, 2),
                'target2': round(target2, 2),
                'target3': round(target3, 2),
                'trade_type': f"🔥 SWING TRADE",
                'strategy': 'swing',
                'signal_type': trade_type,

                # Technical indicators (FLAT fields for Discord) - REAL calculated values!
                'rsi': round(rsi_value, 1),
                'adx': round(adx_value, 1),
                'macd': round(macd_value, 4),  # REAL MACD

                # Trend analysis - REAL values from technical analysis
                'ema_trend': ema_trend,
                'macd_signal': macd_sig,

                # Risk management
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'recommended_hold_days': 5,  # Swing: 2-5 days
                'risk_level': 'MODERATE',

                # Mathematical indicators - REAL calculated values per stock!
                'fibonacci_signal': fib_signal,
                'elliott_wave': elliott_pattern,
                'mathematical_score': round(math_score, 1),

                # ML predictions
                'predicted_return': 0,
                'ml_confidence': 0
            }
        
        except Exception as e:
            print(f"💥 UNEXPECTED ERROR in calculate_momentum_score for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_pullback_score(self, symbol, end_date=None):
        """
        Performs analysis to score a "Buy the Dip" opportunity.
        """
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="3mo", interval="1d", auto_adjust=True, end=end_date)
            
            if df.empty or len(df) < 50:
                return None

            price = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            
            score = 0
            if price > ma50:
                score += 45
            else:
                return None
            
            if price > ma20 * 0.98 and price < ma20 * 1.05:
                score += 35
            
            if len(df) >= 6:
                momentum_5d = ((price / df['Close'].iloc[-5]) - 1) * 100
            else:
                momentum_5d = 0
            
            if momentum_5d < 2 and momentum_5d > -5:
                score += 20
            
            last_3d_avg_vol = df['Volume'].tail(3).mean()
            prev_20d_avg_vol = df['Volume'].iloc[-20:-3].mean()
            
            if pd.notna(last_3d_avg_vol) and pd.notna(prev_20d_avg_vol) and prev_20d_avg_vol > 0 and last_3d_avg_vol < prev_20d_avg_vol:
                score += 15

            if score < 25:  # Was 50 - TOO STRICT!
                return None

            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr_value = true_range.rolling(14).mean().iloc[-1]
            
            if pd.isna(atr_value) or price == 0:
                return None
            
            atr_percent = (atr_value / price * 100)
            
            if len(df) >= 21:
                momentum_20d = ((price / df['Close'].iloc[-20]) - 1) * 100
            else:
                momentum_20d = 0

            # Use MEAN_REVERSION strategy config for pullbacks
            strategy_config = MEAN_REVERSION
            entry_price = price
            stop_loss = entry_price * (1 - strategy_config['STOP_LOSS'])
            target1 = entry_price * (1 + strategy_config['TARGETS'][0])
            target2 = entry_price * (1 + strategy_config['TARGETS'][1])
            target3 = entry_price * (1 + strategy_config['TARGETS'][2])

            # Calculate RSI for pullback
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 40

            # Calculate risk/reward ratio
            risk_amount = entry_price - stop_loss
            reward_amount = target1 - entry_price
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

            # Calculate REAL mathematical indicators
            math_result = self.math_indicators.calculate_all(df)
            if math_result:
                math_score = math_result.get('mathematical_score', score * 0.8)
                math_signals = math_result.get('signals', {})
                fib_signal = math_signals.get('fibonacci', 'NO_SIGNAL')
                elliott = math_result.get('elliott_wave', {})
                elliott_pattern = elliott.get('pattern', 'UNKNOWN')
            else:
                # Fallback if calculation fails
                math_score = round(score * 0.8, 1)
                fib_signal = 'PULLBACK ZONE'
                elliott_pattern = 'WAVE_2'

            # Calculate REAL technical indicators (MACD, EMA trend)
            tech_result = self.tech_indicators.calculate_all(df)
            if tech_result:
                macd_value = tech_result.get('macd', 0)
                adx_value = tech_result.get('adx', 20)
                macd_sig = tech_result['signals'].get('macd_signal', 'NEUTRAL')
                ema_trend = tech_result['signals'].get('ema_trend', 'NEUTRAL')
            else:
                macd_value = 0
                adx_value = 20
                macd_sig = 'NEUTRAL'
                ema_trend = 'NEUTRAL'

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': round(price, 2),
                'score': round(score, 2),
                'pattern': 'PULLBACK',
                '5d_momentum': round(momentum_5d, 2),
                '20d_momentum': round(momentum_20d, 2),
                'volume_ratio': 0,
                'atr_percent': round(atr_percent, 2),
                'atr_value': round(atr_value, 2),
                'relative_strength': 0,
                'from_52w_high': 0,
                'above_ma20': price > ma20,
                'above_ma50': price > ma50,
                'is_breakout': False,

                # Required fields for paper trading
                'current_price': round(entry_price, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target1': round(target1, 2),
                'target2': round(target2, 2),
                'target3': round(target3, 2),
                'trade_type': '🔥 SWING TRADE',
                'strategy': 'swing',
                'signal_type': 'MEAN_REVERSION',

                # Technical indicators (FLAT fields for Discord) - REAL calculated values!
                'rsi': round(rsi_value, 1),
                'adx': round(adx_value, 1),  # REAL ADX
                'macd': round(macd_value, 4),  # REAL MACD

                # Trend analysis - REAL values from technical analysis
                'ema_trend': ema_trend,
                'macd_signal': macd_sig,

                # Risk management
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'recommended_hold_days': 5,
                'risk_level': 'MODERATE',

                # Mathematical indicators - REAL calculated values per stock!
                'fibonacci_signal': fib_signal,
                'elliott_wave': elliott_pattern,
                'mathematical_score': round(math_score, 1),

                # ML predictions
                'predicted_return': 0,
                'ml_confidence': 0
            }

        except Exception:
            return None

    def identify_pattern(self, df):
        """Identifies the most likely pattern based on recent price action."""
        if len(df) < 50:
            return "UNKNOWN"
        
        price = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        last_3_days = df.tail(3)
        is_strong_uptrend = price > ma50 * 1.02
        is_pulling_back = price < ma20 * 1.03 and price > ma20 * 0.95
        has_dipped_recently = (last_3_days['Close'] < last_3_days['Open']).sum() >= 2
        
        if is_strong_uptrend and is_pulling_back and has_dipped_recently:
            return "PULLBACK"
        if price > df['High'].iloc[-10:-1].max():
            return "BREAKOUT"
        if df['Volume'].iloc[-1] > df['Volume'].iloc[-20:-1].mean() * 2.5:
            return "VOLUME_SURGE"
        if ((price - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100) > 7:
            return "MOMENTUM"
        
        if len(df) >= 16:
            sharp_rise = (df['Close'].iloc[-5] / df['Close'].iloc[-15] - 1) > 0.10
        else:
            sharp_rise = False
        
        recent_consolidation = (df.tail(5)['High'].max() - df.tail(5)['Low'].min()) < (price * 0.05)
        
        if sharp_rise and recent_consolidation:
            return "FLAG"
        
        return "CONSOLIDATION"
    
    def scan_market(self, end_date=None):
        print(f"\n{'='*60}\n🚀 UPGRADED DUAL-STRATEGY SCAN V2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}")
        all_stocks = self.get_all_stocks()
        if not all_stocks:
            print("❌ Could not obtain stock list. Aborting scan.")
            return []
        
        opportunities = []
        print(f"Scanning {len(all_stocks)} stocks for BOTH Breakouts and Pullbacks...")
        total_stocks = len(all_stocks)
        
        for i, symbol in enumerate(all_stocks):
            if i > 0 and i % 50 == 0:
                time.sleep(2)
            
            if i > 0 and i % 100 == 0:
                time.sleep(1)
            
            print(f"Progress: {i+1}/{total_stocks}", end='\r')
            
            # Use lower threshold (35 instead of 40) for more opportunities
            momentum_result = self.calculate_momentum_score(symbol, end_date=end_date)
            if momentum_result and momentum_result['score'] >= 35:  # UPGRADED: Lower threshold
                opportunities.append(momentum_result)
                continue
            
            pullback_result = self.calculate_pullback_score(symbol, end_date=end_date)
            if pullback_result and pullback_result['score'] >= 50:
                opportunities.append(pullback_result)
        
        print(f"\n\n✅ Found {len(opportunities)} total opportunities (Breakouts & Pullbacks)!")
        opportunities = sorted(opportunities, key=lambda x: x['score'], reverse=True)
        return opportunities

if __name__ == "__main__":
    scanner = SwingScanner()
    top_opportunities = scanner.scan_market()
    if top_opportunities:
        print("\n--- Top 5 Opportunities ---")
        df = pd.DataFrame(top_opportunities[:5])
        print(df)