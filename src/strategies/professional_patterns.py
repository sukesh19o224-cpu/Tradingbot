"""
🎯 PROFESSIONAL PATTERN DETECTORS
Detects Minervini VCP and O'Neil Pivot patterns as score boosters
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

from config.settings import MINERVINI_VCP_CONFIG, ONEIL_PIVOT_CONFIG


class ProfessionalPatternDetector:
    """
    Detect professional trading patterns
    
    Patterns detected:
    1. Minervini VCP (Volatility Contraction Pattern)
    2. O'Neil Pivot Point Breakout
    
    NOTE: These are SCORE BOOSTERS, not filters!
    System still finds signals without patterns.
    """
    
    def __init__(self):
        self.vcp_config = MINERVINI_VCP_CONFIG
        self.pivot_config = ONEIL_PIVOT_CONFIG
    
    def detect_vcp(self, df: pd.DataFrame) -> Tuple[bool, float, str]:
        """
        Detect Minervini's Volatility Contraction Pattern
        
        VCP Characteristics:
        1. Price consolidates in progressively tighter ranges
        2. Volume dries up during consolidation
        3. Breakout on expanding volume
        
        Args:
            df: Price data (must have at least 20 weeks of data)
            
        Returns:
            (is_vcp, score_boost, description)
        """
        try:
            if df is None or len(df) < 20:
                return False, 0.0, "Insufficient data"
            
            # Use weekly data for VCP (convert if daily)
            if len(df) > 100:  # Likely daily data
                df_weekly = df.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
            else:
                df_weekly = df
            
            if len(df_weekly) < 20:
                return False, 0.0, "Insufficient weekly data"
            
            # Check last 20 weeks for contraction
            recent_weeks = df_weekly.tail(20)
            
            # Calculate volatility (range) for each week
            recent_weeks['range'] = recent_weeks['High'] - recent_weeks['Low']
            recent_weeks['range_pct'] = recent_weeks['range'] / recent_weeks['Close']
            
            # Check for volatility contraction (simplified)
            # Look for decreasing volatility over time
            first_half_vol = recent_weeks['range_pct'].iloc[:10].mean()
            second_half_vol = recent_weeks['range_pct'].iloc[10:].mean()
            
            contraction_ratio = second_half_vol / first_half_vol if first_half_vol > 0 else 1.0
            
            # Check volume dryup
            avg_volume = recent_weeks['Volume'].mean()
            recent_volume = recent_weeks['Volume'].iloc[-5:].mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Check current breakout volume
            current_volume = df['Volume'].iloc[-1]
            breakout_volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Scoring (relaxed criteria)
            criteria_met = 0
            
            # 1. Volatility contraction
            if contraction_ratio <= self.vcp_config['CONTRACTION_THRESHOLD']:
                criteria_met += 1
            
            # 2. Volume dryup
            if volume_ratio <= self.vcp_config['VOLUME_DRYUP_THRESHOLD']:
                criteria_met += 1
            
            # 3. Breakout volume surge
            if breakout_volume_ratio >= self.vcp_config['BREAKOUT_VOLUME_SURGE']:
                criteria_met += 1
            
            # Determine boost
            if criteria_met >= 3:
                # Full VCP
                return True, self.vcp_config['VCP_SCORE_BOOST'], f"VCP detected (3/3 criteria)"
            elif criteria_met >= 2:
                # Partial VCP
                return True, self.vcp_config['PARTIAL_VCP_BOOST'], f"Partial VCP ({criteria_met}/3 criteria)"
            else:
                return False, 0.0, "No VCP pattern"
                
        except Exception as e:
            return False, 0.0, f"VCP detection error: {str(e)[:50]}"
    
    def detect_pivot_breakout(self, df: pd.DataFrame, indicators: Dict) -> Tuple[bool, float, str]:
        """
        Detect O'Neil's Pivot Point Breakout
        
        Pivot Characteristics:
        1. Stock consolidates for 5+ weeks (base formation)
        2. Price tightens near resistance
        3. Breaks above resistance on high volume
        4. Must be above 50-day MA
        
        Args:
            df: Price data
            indicators: Technical indicators dict
            
        Returns:
            (is_pivot, score_boost, description)
        """
        try:
            if df is None or len(df) < 25:
                return False, 0.0, "Insufficient data"
            
            # Use weekly data for base detection
            if len(df) > 100:  # Likely daily data
                df_weekly = df.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
            else:
                df_weekly = df
            
            if len(df_weekly) < 10:
                return False, 0.0, "Insufficient weekly data"
            
            # Check for base formation (last 10-20 weeks)
            base_weeks = min(20, len(df_weekly))
            base_data = df_weekly.tail(base_weeks)
            
            # Calculate base depth
            base_high = base_data['High'].max()
            base_low = base_data['Low'].min()
            base_depth = (base_high - base_low) / base_high
            
            # Check if price is tight (within 5% range recently)
            recent_5_weeks = base_data.tail(5)
            recent_high = recent_5_weeks['High'].max()
            recent_low = recent_5_weeks['Low'].min()
            recent_tightness = (recent_high - recent_low) / recent_high
            
            # Check volume surge on breakout
            avg_volume = df['Volume'].iloc[-20:].mean()
            current_volume = df['Volume'].iloc[-1]
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Check if above 50-MA
            ema_50 = indicators.get('ema_50', 0)
            current_price = df['Close'].iloc[-1]
            above_ma50 = current_price > ema_50 if ema_50 > 0 else False
            
            # Check if breaking out (near recent high)
            near_breakout = (current_price / base_high) >= 0.98  # Within 2% of high
            
            # Scoring (relaxed criteria)
            criteria_met = 0
            
            # 1. Base depth acceptable
            if base_depth <= self.pivot_config['BASE_DEPTH_MAX']:
                criteria_met += 1
            
            # 2. Price tightening
            if recent_tightness <= self.pivot_config['TIGHT_AREA_THRESHOLD']:
                criteria_met += 1
            
            # 3. Volume surge
            if volume_surge >= self.pivot_config['PIVOT_VOLUME_SURGE']:
                criteria_met += 1
            
            # 4. Above 50-MA (required)
            if above_ma50:
                criteria_met += 1
            else:
                # If not above MA50, can't be a valid pivot
                return False, 0.0, "Below 50-MA"
            
            # 5. Near breakout
            if near_breakout:
                criteria_met += 1
            
            # Determine boost
            if criteria_met >= 4:
                # Full Pivot
                return True, self.pivot_config['PIVOT_SCORE_BOOST'], f"Pivot breakout ({criteria_met}/5 criteria)"
            elif criteria_met >= 3:
                # Partial Pivot (base forming)
                return True, self.pivot_config['PARTIAL_PIVOT_BOOST'], f"Pivot forming ({criteria_met}/5 criteria)"
            else:
                return False, 0.0, "No pivot pattern"
                
        except Exception as e:
            return False, 0.0, f"Pivot detection error: {str(e)[:50]}"
    
    def analyze_patterns(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Analyze all patterns and return combined results
        
        Returns:
            Dict with pattern analysis and total score boost
        """
        results = {
            'vcp_detected': False,
            'vcp_boost': 0.0,
            'vcp_description': '',
            'pivot_detected': False,
            'pivot_boost': 0.0,
            'pivot_description': '',
            'total_boost': 0.0,
            'patterns_found': []
        }
        
        # Detect VCP
        vcp_found, vcp_boost, vcp_desc = self.detect_vcp(df)
        results['vcp_detected'] = vcp_found
        results['vcp_boost'] = vcp_boost
        results['vcp_description'] = vcp_desc
        
        if vcp_found:
            results['patterns_found'].append(f"VCP (+{vcp_boost:.1f})")
        
        # Detect Pivot
        pivot_found, pivot_boost, pivot_desc = self.detect_pivot_breakout(df, indicators)
        results['pivot_detected'] = pivot_found
        results['pivot_boost'] = pivot_boost
        results['pivot_description'] = pivot_desc
        
        if pivot_found:
            results['patterns_found'].append(f"Pivot (+{pivot_boost:.1f})")
        
        # Total boost
        results['total_boost'] = vcp_boost + pivot_boost
        
        return results


def test_pattern_detector():
    """Test the pattern detector"""
    print("🧪 Testing Professional Pattern Detector...\n")
    
    # Create sample data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
    sample_df = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    sample_indicators = {
        'ema_50': 100,
        'ema_21': 102
    }
    
    detector = ProfessionalPatternDetector()
    results = detector.analyze_patterns(sample_df, sample_indicators)
    
    print("📋 Pattern Analysis Results:")
    print(f"   VCP: {results['vcp_detected']} | Boost: +{results['vcp_boost']:.1f} | {results['vcp_description']}")
    print(f"   Pivot: {results['pivot_detected']} | Boost: +{results['pivot_boost']:.1f} | {results['pivot_description']}")
    print(f"   Total Boost: +{results['total_boost']:.1f}")
    print(f"   Patterns: {', '.join(results['patterns_found']) if results['patterns_found'] else 'None'}")


if __name__ == "__main__":
    test_pattern_detector()
