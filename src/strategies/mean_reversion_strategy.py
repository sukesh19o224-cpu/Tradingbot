"""
🔄 MEAN REVERSION STRATEGY V4.0
For choppy/ranging markets
Buy: Quality stocks pulled back to support
Exit: Targets at 3%/5%/8%
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


class MeanReversionStrategy:
    """
    Mean reversion strategy for choppy/ranging markets
    
    Entry Criteria:
    - Price 2-5% below MA20
    - Above MA50 (quality filter)
    - RSI < 35 (oversold)
    - Multiple support bounces
    - Low recent momentum
    
    Exit:
    - T1: 3%, T2: 5%, T3: 8%
    - Stop: 5%
    - Time stop: 3 days if no bounce
    """
    
    def __init__(self):
        self.name = "MEAN_REVERSION"
        self.config = MEAN_REVERSION
        
        # Initialize multi-timeframe analyzer
        if MTF_AVAILABLE:
            self.mtf_analyzer = MultiTimeframeAnalyzer()
            print(f"🔄 {self.name} Strategy Initialized (with Multi-Timeframe)")
        else:
            self.mtf_analyzer = None
            print(f"🔄 {self.name} Strategy Initialized")
    
    def scan_opportunities(self, stock_list):
        """
        Scan for mean reversion opportunities
        Returns: List of opportunities with scores
        """
        opportunities = []
        
        print(f"\n{'='*60}")
        print(f"🔄 SCANNING MEAN REVERSION OPPORTUNITIES")
        print(f"{'='*60}")
        
        for symbol_ns in stock_list:
            result = self.analyze_stock(symbol_ns)
            if result:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ Found {len(opportunities)} mean reversion opportunities")
        
        # Display top 5
        if opportunities:
            print(f"\n🏆 TOP 5 MEAN REVERSION PLAYS:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"   {i}. {opp['symbol']:12s} Score: {opp['score']:3.0f}  "
                      f"Below MA: {opp['dist_from_ma20']:.1f}%  RSI: {opp['rsi']:.0f}")
        
        return opportunities
    
    def analyze_stock(self, symbol_ns):
        """
        Analyze single stock for mean reversion setup
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
            
            # Moving averages
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            
            above_ma50 = price > ma50
            
            # Distance from MA20
            dist_from_ma20 = ((price - ma20) / ma20) * 100
            
            # RSI
            rsi = self._calculate_rsi(df)
            
            # Support level
            support_level, support_touches = self._find_support(df, price)
            
            # Momentum (should be low for mean reversion)
            if len(df) >= 6:
                momentum_5d = ((price / df['Close'].iloc[-6]) - 1) * 100
            else:
                return None
            
            # Volume
            avg_volume = df['Volume'].tail(20).mean()
            if avg_volume == 0 or pd.isna(avg_volume):
                return None
            
            volume_ratio = df['Volume'].iloc[-1] / avg_volume
            
            # ATR
            atr_value = self._calculate_atr(df)
            atr_percent = (atr_value / price) * 100
            
            # Quality check - long term trend
            if len(df) >= 100:
                ma100 = df['Close'].rolling(100).mean().iloc[-1]
                above_ma100 = price > ma100
            else:
                above_ma100 = False
            
            # ENTRY FILTERS
            # Filter 1: Must be below MA20 (pullback)
            if dist_from_ma20 > 0:
                return None
            
            # Filter 2: Must be above MA50 (quality)
            if self.config['REQUIRE_ABOVE_MA50'] and not above_ma50:
                return None
            
            # Filter 3: Distance from MA20 (sweet spot)
            if dist_from_ma20 < -self.config['MAX_DISTANCE_FROM_MA'] * 100:
                return None  # Too far below
            
            if dist_from_ma20 > -self.config['MIN_DISTANCE_FROM_MA'] * 100:
                return None  # Not enough pullback
            
            # Filter 4: RSI (oversold)
            if rsi > self.config['MAX_RSI']:
                return None
            
            # Filter 5: Support touches
            if support_touches < self.config['MIN_SUPPORT_BOUNCES']:
                return None
            
            # Filter 6: Momentum (should be weak/negative)
            if momentum_5d > 2:
                return None  # Too much momentum = not mean reversion
            
            # SCORING - Enhanced for better stock selection
            score = 0
            
            # Pullback scoring (max 45) - Increased importance
            pullback_size = abs(dist_from_ma20)
            if pullback_size >= 5:  # Deeper pullback
                score += 45
            elif pullback_size >= 4:
                score += 38
            elif pullback_size >= 3:
                score += 28
            elif pullback_size >= 2:
                score += 18
            
            # RSI scoring (max 30) - More weight on oversold
            if rsi < 20:  # Extremely oversold
                score += 30
            elif rsi < 25:
                score += 25
            elif rsi < 30:
                score += 20
            elif rsi < 35:
                score += 12
            
            # Support scoring (max 20)
            if support_touches >= 5:  # Very strong support
                score += 20
            elif support_touches >= 4:
                score += 16
            elif support_touches >= 3:
                score += 12
            elif support_touches >= 2:
                score += 8
            
            # Quality scoring (max 15)
            if above_ma50 and above_ma100:
                score += 15
            elif above_ma50:
                score += 10
            
            # Volume scoring (max 15) - Increased from 10
            if volume_ratio > 2.0:  # Strong selling exhaustion
                score += 15
            elif volume_ratio > 1.5:
                score += 12
            elif volume_ratio < 0.7:
                score += 8  # Quiet pullback (also good)
            
            # Momentum filter bonus (max 5)
            if -2 < momentum_5d < 0:  # Slight down = perfect entry
                score += 5
            
            # Check minimum score
            if score < STRATEGIES['MEAN_REVERSION']['min_score']:
                return None
            
            # Multi-timeframe confirmation
            mtf_conf = {'confirmed': True, 'confidence': 70, 'entry_signal': 'NOW', 'reason': 'MTF not available'}
            if self.mtf_analyzer:
                mtf_conf = self.mtf_analyzer.analyze(symbol_ns, 'MEAN_REVERSION')
                
                # If MTF says WAIT (still falling), skip
                if not mtf_conf['confirmed']:
                    return None
                
                # Boost score for perfect bounce
                if mtf_conf['confidence'] > 90:
                    score += 5
            
            return {
                'symbol': symbol,
                'strategy': 'MEAN_REVERSION',
                'price': round(price, 2),
                'score': round(score, 0),
                'dist_from_ma20': round(dist_from_ma20, 2),
                'ma20': round(ma20, 2),
                'ma50': round(ma50, 2),
                'rsi': round(rsi, 1),
                'support_level': round(support_level, 2),
                'support_touches': support_touches,
                'momentum_5d': round(momentum_5d, 2),
                'volume_ratio': round(volume_ratio, 2),
                'above_ma50': above_ma50,
                'above_ma100': above_ma100,
                'atr_value': round(atr_value, 2),
                'atr_percent': round(atr_percent, 2),
                'mtf_signal': mtf_conf['entry_signal'],  # NEW
                'mtf_confidence': mtf_conf['confidence'],  # NEW
                'mtf_reason': mtf_conf['reason'],  # NEW
                'targets': self.config['TARGETS'],
                'stop_loss_pct': self.config['STOP_LOSS'],
                'time_stop_days': self.config['TIME_STOP_DAYS']
            }
        
        except Exception as e:
            return None
    
    def _calculate_rsi(self, df, period=14):
        """Calculate RSI"""
        try:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def _find_support(self, df, current_price):
        """
        Find support level and count touches
        Returns: (support_level, touches)
        """
        try:
            # Look at last 50 days
            recent_lows = df['Low'].tail(50)
            
            # Support is near the lowest lows
            support_level = recent_lows.min()
            
            # Count touches (price came within 2% of support)
            touches = 0
            for low in recent_lows:
                if abs(low - support_level) / support_level < 0.02:
                    touches += 1
            
            # Also check if current price is near support
            if abs(current_price - support_level) / support_level < 0.03:
                touches += 1
            
            return support_level, min(touches, 10)  # Cap at 10
        except:
            return current_price * 0.95, 0
    
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
    
    def calculate_position_params(self, opportunity, capital_allocated):
        """
        Calculate entry, stop, targets for mean reversion trade
        """
        price = opportunity['price']
        support = opportunity['support_level']
        
        # Stop loss (below support or 5%)
        stop_below_support = support * 0.98
        stop_percent = price * (1 - self.config['STOP_LOSS'])
        stop_loss = max(stop_below_support, stop_percent)  # Use tighter stop
        
        # Targets (smaller for mean reversion)
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
            'strategy': 'MEAN_REVERSION',
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
        stop = position.get('stop_loss', entry * 0.95)
        
        # Stop loss
        if current_price <= stop:
            return True, 'Stop Loss', stop
        
        # Calculate profit/loss
        profit_pct = ((current_price - entry) / entry) * 100
        
        # DISABLED: Early exit at day 3 - let positions develop
        # Old logic forced exit too early, missing profits
        # if days_held >= 3 and profit_pct < 0:
        #     recovery_signs = self._check_recovery_pattern(position, current_price)
        #     if recovery_signs < 2:
        #         return True, f'Early Exit ({days_held}d, no recovery)', current_price
        
        # CRITICAL: TIME_STOP completely removed!
        # System now ONLY exits on:
        # 1. Stop loss hit
        # 2. Target hit  
        # 3. MAX_HOLD_DAYS reached (5 days)
        # No other time-based exits allowed!
        
        # Max hold (ONLY time-based exit)
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
        ENHANCED trailing stop for mean reversion trades
        Conservative trailing to lock in bounce profits
        """
        entry = position['entry_price']
        current_stop = position.get('stop_loss', entry * 0.95)
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
        
        # Fallback to old logic
        if profit_pct >= 8:  # At T3
            new_stop = max(current_stop, entry * 1.04)  # Lock in 4%
        elif profit_pct >= 5:  # At T2
            new_stop = max(current_stop, entry * 1.02)  # Lock in 2%
        elif profit_pct >= 3:  # At T1
            new_stop = max(current_stop, entry)  # Breakeven
        else:
            new_stop = current_stop
        
        return round(new_stop, 2)


if __name__ == "__main__":
    print("\n🧪 Testing Mean Reversion Strategy\n")
    
    strategy = MeanReversionStrategy()
    
    # Test stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS']
    
    opportunities = strategy.scan_opportunities(test_stocks)
    
    if opportunities:
        print("\n💡 Position Parameters for top opportunity:")
        params = strategy.calculate_position_params(opportunities[0], 35000)
        if params:
            for key, val in params.items():
                print(f"   {key}: {val}")