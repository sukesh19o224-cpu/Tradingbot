"""
🏦 BANK NIFTY VOLATILITY ADJUSTMENT
Adjusts risk parameters for banking stocks (1.5-1.7x more volatile than Nifty)
"""

from typing import Dict, Tuple
from config.settings import BANK_NIFTY_CONFIG


class BankNiftyAdjuster:
    """
    Adjust trading parameters for banking stocks
    
    Banking stocks are 1.5-1.7x more volatile than Nifty 50:
    - Wider stop losses (prevent premature exits)
    - Smaller position sizes (manage risk)
    - Higher quality thresholds (be selective)
    """
    
    def __init__(self):
        self.config = BANK_NIFTY_CONFIG
        self.banking_stocks = set(self.config['BANKING_STOCKS'])
    
    def is_banking_stock(self, symbol: str) -> bool:
        """Check if stock is a banking stock"""
        return symbol in self.banking_stocks
    
    def get_adjustments(self, symbol: str) -> Dict:
        """
        Get all adjustments for a stock
        
        Returns:
            Dict with adjustment multipliers
        """
        if not self.is_banking_stock(symbol):
            # No adjustments for non-banking stocks
            return {
                'stop_loss_multiplier': 1.0,
                'position_size_multiplier': 1.0,
                'quality_threshold_boost': 0,
                'min_score_boost': 0.0,
                'is_banking': False
            }
        
        # Banking stock adjustments
        return {
            'stop_loss_multiplier': self.config['STOP_LOSS_MULTIPLIER'],
            'position_size_multiplier': self.config['POSITION_SIZE_MULTIPLIER'],
            'quality_threshold_boost': self.config['QUALITY_THRESHOLD_BOOST'],
            'min_score_boost': self.config['MIN_SCORE_BOOST'],
            'is_banking': True
        }
    
    def adjust_stop_loss(self, symbol: str, base_stop_pct: float) -> float:
        """
        Adjust stop loss for banking stocks
        
        Args:
            symbol: Stock symbol
            base_stop_pct: Base stop loss percentage (e.g., 0.04 for 4%)
            
        Returns:
            Adjusted stop loss percentage
        """
        adjustments = self.get_adjustments(symbol)
        return base_stop_pct * adjustments['stop_loss_multiplier']
    
    def adjust_position_size(self, symbol: str, base_size: float) -> float:
        """
        Adjust position size for banking stocks
        
        Args:
            symbol: Stock symbol
            base_size: Base position size in rupees
            
        Returns:
            Adjusted position size
        """
        adjustments = self.get_adjustments(symbol)
        return base_size * adjustments['position_size_multiplier']
    
    def adjust_quality_threshold(self, symbol: str, base_threshold: int) -> int:
        """
        Adjust quality threshold for banking stocks
        
        Args:
            symbol: Stock symbol
            base_threshold: Base quality threshold (e.g., 60)
            
        Returns:
            Adjusted quality threshold
        """
        adjustments = self.get_adjustments(symbol)
        return base_threshold + adjustments['quality_threshold_boost']
    
    def adjust_min_score(self, symbol: str, base_score: float) -> float:
        """
        Adjust minimum score for banking stocks
        
        Args:
            symbol: Stock symbol
            base_score: Base minimum score (e.g., 7.0)
            
        Returns:
            Adjusted minimum score
        """
        adjustments = self.get_adjustments(symbol)
        return base_score + adjustments['min_score_boost']
    
    def should_apply_adjustments(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if adjustments should be applied
        
        Returns:
            (should_apply, reason)
        """
        if self.is_banking_stock(symbol):
            return True, "Banking stock (high volatility)"
        return False, ""
    
    def print_adjustment_summary(self, symbol: str):
        """Print adjustment summary for a stock"""
        adjustments = self.get_adjustments(symbol)
        
        if adjustments['is_banking']:
            print(f"\n   🏦 Banking Stock Adjustments Applied:")
            print(f"      Stop Loss: {adjustments['stop_loss_multiplier']:.1f}x wider")
            print(f"      Position Size: {adjustments['position_size_multiplier']:.0%} of normal")
            print(f"      Quality Threshold: +{adjustments['quality_threshold_boost']} points")
            print(f"      Min Score: +{adjustments['min_score_boost']:.1f}")


def test_bank_nifty_adjuster():
    """Test the Bank Nifty adjuster"""
    print("🧪 Testing Bank Nifty Volatility Adjuster...\n")
    
    adjuster = BankNiftyAdjuster()
    
    # Test stocks
    test_stocks = [
        ('HDFCBANK.NS', 'Banking'),
        ('TCS.NS', 'IT'),
        ('SBIN.NS', 'Banking')
    ]
    
    print("📋 Stock Adjustments:")
    for stock, sector in test_stocks:
        is_banking = adjuster.is_banking_stock(stock)
        adjustments = adjuster.get_adjustments(stock)
        
        print(f"\n{stock} ({sector}):")
        print(f"   Is Banking: {is_banking}")
        if is_banking:
            print(f"   Stop Loss: {adjustments['stop_loss_multiplier']:.1f}x (4% → {4 * adjustments['stop_loss_multiplier']:.1f}%)")
            print(f"   Position Size: {adjustments['position_size_multiplier']:.0%}")
            print(f"   Quality Boost: +{adjustments['quality_threshold_boost']}")
            print(f"   Score Boost: +{adjustments['min_score_boost']:.1f}")


if __name__ == "__main__":
    test_bank_nifty_adjuster()
