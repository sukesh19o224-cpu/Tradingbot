"""V5.5 ULTRA+ - Enhanced Trade Journal"""
import json
import os
from typing import Dict
from datetime import datetime

class TradeJournal:
    """Detailed trade logging"""
    
    def __init__(self, journal_file='data/trade_journal.json'):
        self.file = journal_file
        self.entries = self._load()
    
    def log_trade(self, trade: Dict, notes: str = ''):
        """Log trade with notes"""
        entry_id = f"{trade['symbol']}_{trade['entry_date']}"
        self.entries[entry_id] = {
            'trade': trade, 'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        self._save()
    
    def _load(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, 'w') as f:
            json.dump(self.entries, f, indent=2)
