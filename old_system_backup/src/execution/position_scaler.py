"""V5.5 ULTRA+ - Position Scaling"""
from typing import Dict

class PositionScaler:
    """Gradual entry and exit"""
    
    def __init__(self):
        self.scale_stages = [
            {'trigger': 'INITIAL', 'pct': 0.40},
            {'trigger': 'CONFIRM', 'pct': 0.60}
        ]
    
    def calculate_size(self, stage: str, total: int) -> int:
        """Calculate position size"""
        for s in self.scale_stages:
            if s['trigger'] == stage:
                return int(total * s['pct'])
        return total
