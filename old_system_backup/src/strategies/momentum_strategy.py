"""
🚀 MOMENTUM STRATEGY V4.0
For trending/bull markets
Buy: Strong upward momentum with volume
Exit: Targets at 5%/8%/12%
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *

# Import caching if available
try:
    from src.data_collector.data_cache import get_cache
    CACHE_AVAILABLE = True
except:
    CACHE_AVAILABLE = False

# Import multi-timeframe if available
try:
    from src.analyzers.multi_timeframe_analyzer import MultiTimeframeAnalyzer
    MTF_AVAILABLE = True
except:
    MTF_AVAILABLE = False


class MomentumStrategy:
    """
    Momentum strategy for trending markets
    
    Entry Criteria:
    - 5-day momentum > 3%
    - 20-day momentum > 5%
    - Volume ratio > 1.5x
    - Price above MA20 and MA50
    - Strong trend (ADX-like)
    
    Exit:
    - T1: 5%, T2: 8%, T3: 12%
    - Stop: 7%
    - Time stop: 5 days if no momentum
    """
    
    def __init__(self):
        self.name = "MOMENTUM"
        self.config = MOMENTUM
        
        # Initialize multi-timeframe analyzer
        if MTF_AVAILABLE:
            self.mtf_analyzer = MultiTimeframeAnalyzer()
            print(f"🚀 {self.name} Strategy Initialized (with Multi-Timeframe)")
        else:
            self.mtf_analyzer = None
            print(f"🚀 {self.name} Strategy Initialized")
    
    def scan_opportunities(self, stock_list):
        """
        Scan for momentum opportunities
        Returns: List of opportunities with scores
        """
        opportunities = []
        
        print(f"\n{'='*60}")
        print(f"🚀 SCANNING MOMENTUM OPPORTUNITIES")
        print(f"{'='*60}")
        
        for symbol_ns in stock_list:
            result = self.analyze_stock(symbol_ns)
            if result:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ Found {len(opportunities)} momentum opportunities")
        
        # Display top 5
        if opportunities:
            print(f"\n🏆 TOP 5 MOMENTUM PLAYS:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"   {i}. {opp['symbol']:12s} Score: {opp['score']:3.0f}  "
                      f"Mom: {opp['momentum_5d']:+.1f}%  Vol: {opp['volume_ratio']:.1f}x")
        
        return opportunities
    
    def analyze_stock(self, symbol_ns):
        """
        Analyze single stock for momentum setup
        """
        try:
            symbol = symbol_ns.replace('.NS', '')
            
            # Fetch data with caching
            if CACHE_AVAILABLE:
                cache = get_cache()
                df = cache.get_data(
                    symbol_ns,
                    lambda: yf.Ticker(symbol_ns).history(period='3mo', interval='1d', auto_adjust=True)
                )
            else:
                ticker = yf.Ticker(symbol_ns)
                df = ticker.history(period='3mo', interval='1d')
            
            if df.empty or len(df) < 50:
                return None
            
            # Calculate metrics
            price = df['Close'].iloc[-1]
            
            # Price filters
            if price < MIN_PRICE or price > MAX_PRICE:
                return None
            
            # Momentum
            if len(df) >= 6:
                momentum_5d = ((price / df['Close'].iloc[-6]) - 1) * 100
            else:
                return None
            
            if len(df) >= 21:
                momentum_20d = ((price / df['Close'].iloc[-21]) - 1) * 100
            else:
                return None
            
            # Volume
            avg_volume = df['Volume'].tail(20).mean()
            if avg_volume == 0 or pd.isna(avg_volume):
                return None
            
            volume_ratio = df['Volume'].iloc[-1] / avg_volume
            
            # Moving averages
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            above_ma20 = price > ma20
            above_ma50 = price > ma50
            
            # Trend strength
            trend_strength = self._calculate_trend_strength(df)
            
            # ATR
            atr_value = self._calculate_atr(df)
            atr_percent = (atr_value / price) * 100
            
            # Weekly check
            weekly_bullish = self._check_weekly(ticker)
            
            # Gap check
            if len(df) >= 2:
                today_open = df['Open'].iloc[-1]
                yesterday_close = df['Close'].iloc[-2]
                gap_percent = ((today_open - yesterday_close) / yesterday_close) * 100
            else:
                gap_percent = 0
            
            # ENTRY FILTERS
            # Filter 1: Momentum
            if momentum_5d < self.config['MIN_5D_MOMENTUM']:
                return None
            
            if momentum_20d < self.config['MIN_20D_MOMENTUM']:
                return None
            
            # Filter 2: Volume
            if volume_ratio < self.config['MIN_VOLUME_RATIO']:
                return None
            
            # Filter 3: Gap (avoid chasing)
            if gap_percent > self.config['MAX_GAP_UP'] * 100:
                return None
            
            # Filter 4: MA alignment (if required)
            if self.config['REQUIRE_MA_ALIGNMENT']:
                if not (above_ma20 and above_ma50):
                    return None
            
            # Filter 5: Trend strength
            if trend_strength < self.config['MIN_TREND_STRENGTH']:
                return None
            
            # SCORING
            score = 0
            
            # Momentum scoring (max 50)
            if momentum_5d > 7:
                score += 40
            elif momentum_5d > 5:
                score += 30
            elif momentum_5d > 3:
                score += 20
            
            if momentum_20d > 15:
                score += 10
            elif momentum_20d > 10:
                score += 7
            elif momentum_20d > 5:
                score += 5
            
            # Volume scoring (max 25)
            if volume_ratio > 3:
                score += 25
            elif volume_ratio > 2:
                score += 20
            elif volume_ratio > 1.5:
                score += 15
            
            # Trend scoring (max 15)
            if trend_strength > 70:
                score += 15
            elif trend_strength > 60:
                score += 10
            elif trend_strength > 50:
                score += 5
            
            # MA alignment (max 10)
            if above_ma20 and above_ma50:
                score += 10
            elif above_ma20:
                score += 5
            
            # Weekly alignment (bonus 10)
            if weekly_bullish:
                score += 10
            
            # Check minimum score
            if score < STRATEGIES['MOMENTUM']['min_score']:
                return None
            
            # Multi-timeframe confirmation
            mtf_conf = {'confirmed': True, 'confidence': 70, 'entry_signal': 'NOW', 'reason': 'MTF not available'}
            if self.mtf_analyzer:
                mtf_conf = self.mtf_analyzer.analyze(symbol_ns, 'MOMENTUM')
                
                # If MTF says WAIT, skip this stock
                if not mtf_conf['confirmed']:
                    return None
                
                # Boost score if excellent MTF confirmation
                if mtf_conf['confidence'] > 85:
                    score += 5
            
            return {
                'symbol': symbol,
                'strategy': 'MOMENTUM',
                'price': round(price, 2),
                'score': round(score, 0),
                'momentum_5d': round(momentum_5d, 2),
                'momentum_20d': round(momentum_20d, 2),
                'volume_ratio': round(volume_ratio, 2),
                'trend_strength': round(trend_strength, 1),
                'above_ma20': above_ma20,
                'above_ma50': above_ma50,
                'weekly_bullish': weekly_bullish,
                'atr_value': round(atr_value, 2),
                'atr_percent': round(atr_percent, 2),
                'gap_percent': round(gap_percent, 2),
                'mtf_signal': mtf_conf['entry_signal'],  # NEW
                'mtf_confidence': mtf_conf['confidence'],  # NEW
                'mtf_reason': mtf_conf['reason'],  # NEW
                'targets': self.config['TARGETS'],
                'stop_loss_pct': self.config['STOP_LOSS'],
                'time_stop_days': self.config['TIME_STOP_DAYS']
            }
        
        except Exception as e:
            return None
    
    def _calculate_trend_strength(self, df):
        """Calculate trend strength (0-100)"""
        try:
            if len(df) < 20:
                return 0
            
            # Higher highs and higher lows
            highs = df['High'].tail(20)
            lows = df['Low'].tail(20)
            
            higher_highs = sum([highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs))])
            higher_lows = sum([lows.iloc[i] > lows.iloc[i-1] for i in range(1, len(lows))])
            
            consistency = ((higher_highs + higher_lows) / (len(highs) * 2)) * 100
            
            # Price efficiency
            price_range = df['High'].tail(20).max() - df['Low'].tail(20).min()
            net_move = abs(df['Close'].iloc[-1] - df['Close'].iloc[-20])
            efficiency = (net_move / price_range * 100) if price_range > 0 else 0
            
            return (consistency + efficiency) / 2
        except:
            return 0
    
    def _calculate_atr(self, df, period=14):
        """Calculate ATR"""
        try:
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean().iloc[-1]
            return atr if not pd.isna(atr) else 0
        except:
            return 0
    
    def _check_weekly(self, ticker):
        """Check weekly timeframe"""
        try:
            weekly = ticker.history(period='6mo', interval='1wk')
            if weekly.empty or len(weekly) < 20:
                return False
            
            price = weekly['Close'].iloc[-1]
            ma20 = weekly['Close'].rolling(20).mean().iloc[-1]
            
            return price > ma20
        except:
            return False
    
    def calculate_position_params(self, opportunity, capital_allocated):
        """
        Calculate entry, stop, targets for momentum trade
        """
        price = opportunity['price']
        atr = opportunity['atr_value']
        
        # Stop loss
        stop_loss = price * (1 - self.config['STOP_LOSS'])
        
        # Targets
        target1 = price * (1 + self.config['TARGETS'][0])
        target2 = price * (1 + self.config['TARGETS'][1])
        target3 = price * (1 + self.config['TARGETS'][2])
        
        # Position size (risk-based)
        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            return None
        
        risk_amount = capital_allocated * MAX_RISK_PER_TRADE
        shares = int(risk_amount / risk_per_share)
        
        # Check max position
        position_value = shares * price
        max_position = capital_allocated * MAX_PER_STOCK
        
        if position_value > max_position:
            shares = int(max_position / price)
            position_value = shares * price
        
        if shares <= 0:
            return None
        
        return {
            'symbol': opportunity['symbol'],
            'strategy': 'MOMENTUM',
            'entry_price': price,
            'shares': shares,
            'position_value': round(position_value, 2),
            'stop_loss': round(stop_loss, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2),
            'target3': round(target3, 2),
            'risk_amount': round(risk_per_share * shares, 2),
            'time_stop_days': self.config['TIME_STOP_DAYS']
        }
    
    def check_exit_conditions(self, position, current_price, days_held):
        """
        ENHANCED exit conditions with smart loss management
        Returns: (should_exit, reason, exit_price)
        """
        entry = position['entry_price']
        stop = position.get('stop_loss', entry * 0.93)
        
        # Stop loss
        if current_price <= stop:
            return True, 'Stop Loss', stop
        
        # Calculate profit/loss
        profit_pct = ((current_price - entry) / entry) * 100
        
        # Smart loss management - check at day 3
        if days_held >= 3 and profit_pct < 0:
            recovery_signs = self._check_recovery_pattern(position, current_price)
            
            if recovery_signs < 2:  # Less than 2 recovery signals
                return True, f'Early Exit ({days_held}d, no recovery)', current_price
            else:
                # Has recovery signs, hold till max days
                pass
        
        # Time stop
        if days_held >= self.config['TIME_STOP_DAYS']:
            if profit_pct < 2:
                return True, f'Time Stop ({days_held}d, low momentum)', current_price
        
        # Max hold
        if days_held >= MAX_HOLD_DAYS:
            return True, f'Max Hold ({days_held}d)', current_price
        
        return False, None, None
    
    def _check_recovery_pattern(self, position, current_price):
        """
        Check for recovery signs in losing position
        Returns: Number of positive signals (0-3)
        """
        try:
            from config.settings import LOSS_RECOVERY_CONFIG
            if not LOSS_RECOVERY_CONFIG.get('enabled', True):
                return 0
            
            signals = 0
            symbol = position['symbol']
            
            # Get recent data
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(period='5d', interval='1d')
            
            if df.empty or len(df) < 3:
                return 0
            
            # Check 1: Higher lows pattern
            if LOSS_RECOVERY_CONFIG.get('check_higher_lows', True):
                recent_lows = df['Low'].tail(3).values
                if len(recent_lows) >= 2 and recent_lows[-1] > recent_lows[-2]:
                    signals += 1
            
            # Check 2: Volume increasing (buyers coming in)
            if LOSS_RECOVERY_CONFIG.get('check_volume_increase', True):
                avg_vol = df['Volume'].iloc[:-1].mean()
                current_vol = df['Volume'].iloc[-1]
                if current_vol > avg_vol * 1.2:
                    signals += 1
            
            # Check 3: RSI turning up
            if LOSS_RECOVERY_CONFIG.get('check_rsi_turning', True):
                if len(df) >= 14:
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    if not rsi.empty and len(rsi) >= 2:
                        if rsi.iloc[-1] > rsi.iloc[-2] and rsi.iloc[-1] < 40:
                            signals += 1
            
            return signals
        
        except:
            return 0
    
    def update_trailing_stop(self, position, current_price):
        """
        ENHANCED trailing stop for momentum trades
        Locks in profits progressively from +2% onwards
        """
        entry = position['entry_price']
        current_stop = position.get('stop_loss', entry * 0.93)
        highest = position.get('highest_price', entry)
        
        # Update highest price
        if current_price > highest:
            highest = current_price
            position['highest_price'] = highest
        
        profit_pct = ((current_price - entry) / entry) * 100
        
        # Enhanced trailing logic
        try:
            from config.settings import TRAILING_STOP_CONFIG
            if TRAILING_STOP_CONFIG.get('enabled', True):
                if profit_pct >= 5:  # Aggressive trailing at +5%
                    trail_distance = TRAILING_STOP_CONFIG.get('aggressive_distance', 0.025)
                    new_stop = highest * (1 - trail_distance)  # Trail 2.5% below peak
                elif profit_pct >= 2:  # Start trailing at +2%
                    trail_distance = TRAILING_STOP_CONFIG.get('trail_distance', 0.015)
                    new_stop = highest * (1 - trail_distance)  # Trail 1.5% below peak
                else:
                    new_stop = current_stop  # Keep original stop
                
                # Never lower the stop
                new_stop = max(new_stop, current_stop)
                return round(new_stop, 2)
        except:
            pass
        
        # Fallback to old logic if config not available
        if profit_pct >= 12:  # At T3
            new_stop = max(current_stop, entry * 1.08)  # Lock in 8%
        elif profit_pct >= 8:  # At T2
            new_stop = max(current_stop, entry * 1.05)  # Lock in 5%
        elif profit_pct >= 5:  # At T1
            new_stop = max(current_stop, entry * 1.02)  # Lock in 2%
        elif profit_pct >= 3:
            new_stop = max(current_stop, entry)  # Breakeven
        else:
            new_stop = current_stop
        
        return round(new_stop, 2)


if __name__ == "__main__":
    print("\n🧪 Testing Momentum Strategy\n")
    
    strategy = MomentumStrategy()
    
    # Test stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
    
    opportunities = strategy.scan_opportunities(test_stocks)
    
    if opportunities:
        print("\n💡 Position Parameters for top opportunity:")
        params = strategy.calculate_position_params(opportunities[0], 40000)
        if params:
            for key, val in params.items():
                print(f"   {key}: {val}")