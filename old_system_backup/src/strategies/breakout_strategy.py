"""
💥 BREAKOUT STRATEGY V4.0
For consolidation breakouts
Buy: Break above tight range with volume
Exit: Targets at 6%/10%/15%
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


class BreakoutStrategy:
    """
    Breakout strategy for consolidation patterns
    
    Entry Criteria:
    - 5+ days of consolidation (range < 5%)
    - Break above consolidation high
    - Volume surge (2x+ average)
    - ATR expansion
    - Confirmation (price 1%+ above high)
    
    Exit:
    - T1: 6%, T2: 10%, T3: 15%
    - Stop: 6%
    - Time stop: 4 days if false breakout
    """
    
    def __init__(self):
        self.name = "BREAKOUT"
        self.config = BREAKOUT
        print(f"💥 {self.name} Strategy Initialized")
    
    def scan_opportunities(self, stock_list):
        """
        Scan for breakout opportunities
        Returns: List of opportunities with scores
        """
        opportunities = []
        
        print(f"\n{'='*60}")
        print(f"💥 SCANNING BREAKOUT OPPORTUNITIES")
        print(f"{'='*60}")
        
        for symbol_ns in stock_list:
            result = self.analyze_stock(symbol_ns)
            if result:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n✅ Found {len(opportunities)} breakout opportunities")
        
        # Display top 5
        if opportunities:
            print(f"\n🏆 TOP 5 BREAKOUT PLAYS:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"   {i}. {opp['symbol']:12s} Score: {opp['score']:3.0f}  "
                      f"Range: {opp['consolidation_range']:.1f}%  Vol: {opp['volume_surge']:.1f}x")
        
        return opportunities
    
    def analyze_stock(self, symbol_ns):
        """
        Analyze single stock for breakout setup
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
            
            # Consolidation detection
            consol_days = self.config['CONSOLIDATION_DAYS']
            if len(df) < consol_days + 10:
                return None
            
            # Get consolidation period (exclude today for clean check)
            consol_period = df.iloc[-(consol_days+1):-1]
            
            consol_high = consol_period['High'].max()
            consol_low = consol_period['Low'].min()
            consol_range = ((consol_high - consol_low) / consol_low) * 100
            
            # Today's data
            today_high = df['High'].iloc[-1]
            today_low = df['Low'].iloc[-1]
            
            # Is this a breakout?
            breakout_level = consol_high
            is_breakout = price > breakout_level * (1 + self.config['BREAKOUT_CONFIRMATION'])
            
            # Volume
            avg_volume = df['Volume'].iloc[-(consol_days+20):-(consol_days+1)].mean()
            recent_volume = df['Volume'].tail(consol_days).mean()
            today_volume = df['Volume'].iloc[-1]
            
            if avg_volume == 0 or pd.isna(avg_volume):
                return None
            
            volume_surge = today_volume / avg_volume
            avg_vol_ratio = recent_volume / avg_volume
            
            # ATR expansion
            atr_consol = self._calculate_atr_period(consol_period)
            atr_recent = self._calculate_atr_period(df.tail(5))
            
            if atr_consol > 0:
                atr_expansion = atr_recent / atr_consol
            else:
                atr_expansion = 1.0
            
            # Moving averages (quality filter)
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            above_ma50 = price > ma50
            
            # Momentum before consolidation (should be positive)
            if len(df) >= consol_days + 20:
                pre_consol_price = df['Close'].iloc[-(consol_days+20)]
                pre_consol_momentum = ((consol_period['Close'].iloc[0] / pre_consol_price) - 1) * 100
            else:
                pre_consol_momentum = 0
            
            # Recent price action
            if len(df) >= 6:
                momentum_5d = ((price / df['Close'].iloc[-6]) - 1) * 100
            else:
                momentum_5d = 0
            
            # ENTRY FILTERS
            # Filter 1: Consolidation range (must be tight)
            if consol_range > self.config['MAX_CONSOLIDATION_RANGE'] * 100:
                return None
            
            # Filter 2: Must be breakout
            if not is_breakout:
                return None
            
            # Filter 3: Volume surge
            if volume_surge < self.config['MIN_VOLUME_SURGE']:
                return None
            
            # Filter 4: ATR expansion (if required)
            if self.config['REQUIRE_ATR_EXPANSION']:
                if atr_expansion < 1.2:  # 20% expansion
                    return None
            
            # Filter 5: Quality (prefer above MA50)
            # Not strict requirement, but affects scoring
            
            # SCORING
            score = 0
            
            # Consolidation tightness (max 30)
            if consol_range < 2:
                score += 30
            elif consol_range < 3:
                score += 25
            elif consol_range < 4:
                score += 20
            elif consol_range < 5:
                score += 15
            
            # Volume surge (max 30)
            if volume_surge > 4:
                score += 30
            elif volume_surge > 3:
                score += 25
            elif volume_surge > 2:
                score += 20
            elif volume_surge > 1.5:
                score += 15
            
            # ATR expansion (max 15)
            if atr_expansion > 1.5:
                score += 15
            elif atr_expansion > 1.3:
                score += 10
            elif atr_expansion > 1.2:
                score += 5
            
            # Prior momentum (max 15)
            if pre_consol_momentum > 10:
                score += 15
            elif pre_consol_momentum > 5:
                score += 10
            elif pre_consol_momentum > 0:
                score += 5
            
            # Quality (max 10)
            if above_ma50:
                score += 10
            elif price > ma20:
                score += 5
            
            # Bonus: Clean breakout
            if price > consol_high * 1.02:  # 2%+ above
                score += 10
            
            # Check minimum score
            if score < STRATEGIES['BREAKOUT']['min_score']:
                return None
            
            return {
                'symbol': symbol,
                'strategy': 'BREAKOUT',
                'price': round(price, 2),
                'score': round(score, 0),
                'consolidation_range': round(consol_range, 2),
                'consolidation_high': round(consol_high, 2),
                'consolidation_low': round(consol_low, 2),
                'consolidation_days': consol_days,
                'breakout_level': round(breakout_level, 2),
                'volume_surge': round(volume_surge, 2),
                'atr_expansion': round(atr_expansion, 2),
                'pre_consol_momentum': round(pre_consol_momentum, 2),
                'momentum_5d': round(momentum_5d, 2),
                'above_ma50': above_ma50,
                'targets': self.config['TARGETS'],
                'stop_loss_pct': self.config['STOP_LOSS'],
                'time_stop_days': self.config['TIME_STOP_DAYS']
            }
        
        except Exception as e:
            return None
    
    def _calculate_atr_period(self, df, period=14):
        """Calculate ATR for a period"""
        try:
            if len(df) < period:
                period = len(df)
            
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
        Calculate entry, stop, targets for breakout trade
        """
        price = opportunity['price']
        consol_low = opportunity['consolidation_low']
        
        # Stop loss (below consolidation or 6%)
        stop_below_consol = consol_low * 0.98
        stop_percent = price * (1 - self.config['STOP_LOSS'])
        stop_loss = max(stop_below_consol, stop_percent)  # Use tighter stop
        
        # Targets (larger for breakouts)
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
            'strategy': 'BREAKOUT',
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
        stop = position.get('stop_loss', entry * 0.94)
        
        # Stop loss
        if current_price <= stop:
            return True, 'Stop Loss', stop
        
        # Calculate profit/loss
        profit_pct = ((current_price - entry) / entry) * 100
        
        # Smart loss management - check at day 3
        if days_held >= 3 and profit_pct < 0:
            recovery_signs = self._check_recovery_pattern(position, current_price)
            
            if recovery_signs < 2:  # Less than 2 recovery signals
                return True, f'Early Exit ({days_held}d, failed breakout)', current_price
            else:
                # Has recovery signs, hold till max days
                pass
        
        # Time stop (check for false breakout)
        if days_held >= self.config['TIME_STOP_DAYS']:
            if profit_pct < 2:  # Breakout failed
                return True, f'Time Stop ({days_held}d, false breakout)', current_price
        
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
        ENHANCED trailing stop for breakout trades
        Aggressive trailing as breakouts can run far
        """
        entry = position['entry_price']
        current_stop = position.get('stop_loss', entry * 0.94)
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
        if profit_pct >= 15:  # At T3
            new_stop = max(current_stop, entry * 1.10)  # Lock in 10%
        elif profit_pct >= 10:  # At T2
            new_stop = max(current_stop, entry * 1.06)  # Lock in 6%
        elif profit_pct >= 6:  # At T1
            new_stop = max(current_stop, entry * 1.03)  # Lock in 3%
        elif profit_pct >= 4:
            new_stop = max(current_stop, entry)  # Breakeven
        else:
            new_stop = current_stop
        
        return round(new_stop, 2)


if __name__ == "__main__":
    print("\n🧪 Testing Breakout Strategy\n")
    
    strategy = BreakoutStrategy()
    
    # Test stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'TATAMOTORS.NS']
    
    opportunities = strategy.scan_opportunities(test_stocks)
    
    if opportunities:
        print("\n💡 Position Parameters for top opportunity:")
        params = strategy.calculate_position_params(opportunities[0], 25000)
        if params:
            for key, val in params.items():
                print(f"   {key}: {val}")