"""V5.5 ULTRA+ - Smart Watchlist Manager"""
import json
import os
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SmartWatchlist:
    """Smart watchlist with scoring and alerts"""
    
    def __init__(self, watchlist_file='data/smart_watchlist.json'):
        self.file = watchlist_file
        self.watchlist = self._load()
    
    def add_symbol(self, symbol: str, reason: str = '', priority: int = 5):
        """Add symbol to watchlist"""
        self.watchlist[symbol] = {
            'added_date': datetime.now().isoformat(),
            'reason': reason,
            'priority': priority,
            'last_score': 0,
            'alert_triggered': False
        }
        self._save()
        logger.info(f"✅ Added {symbol} to watchlist")
    
    def update_score(self, symbol: str, score: float):
        """Update symbol score"""
        if symbol in self.watchlist:
            self.watchlist[symbol]['last_score'] = score
            self.watchlist[symbol]['last_updated'] = datetime.now().isoformat()
            self._save()
    
    def get_top_opportunities(self, count: int = 10) -> List[str]:
        """Get top N symbols by score"""
        sorted_symbols = sorted(
            self.watchlist.items(),
            key=lambda x: x[1].get('last_score', 0),
            reverse=True
        )
        return [s[0] for s in sorted_symbols[:count]]
    
    def _load(self) -> Dict:
        """Load watchlist from file"""
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        """Save watchlist to file"""
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, 'w') as f:
            json.dump(self.watchlist, f, indent=2)
