"""
💾 DATABASE MODULE
SQLite database for trade history and analytics
DUAL MODE: Saves to both DB and JSON (backward compatible)
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import get_logger
    logger = get_logger('Database')
except:
    logger = None
    print("⚠️ Logger not available for database module")


class TradingDatabase:
    """
    Trading database with automatic initialization
    Dual-mode: Works alongside JSON files (non-breaking)
    """
    
    def __init__(self, db_path='database/trading.db'):
        self.db_path = db_path
        self._ensure_database_exists()
        self._initialize_tables()
    
    def _ensure_database_exists(self):
        """Create database directory if needed"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access by column name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            if logger:
                logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _initialize_tables(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Trades table (completed trades)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    shares INTEGER,
                    initial_shares INTEGER,
                    entry_time TIMESTAMP,
                    exit_time TIMESTAMP,
                    hold_days INTEGER,
                    exit_reason TEXT,
                    profit_loss REAL,
                    profit_loss_percent REAL,
                    targets_hit TEXT,
                    stop_loss REAL,
                    highest_price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Positions table (current open positions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    strategy TEXT,
                    entry_price REAL,
                    shares INTEGER,
                    initial_shares INTEGER,
                    stop_loss REAL,
                    target1 REAL,
                    target2 REAL,
                    target3 REAL,
                    position_value REAL,
                    entry_time TIMESTAMP,
                    days_held INTEGER,
                    targets_hit TEXT,
                    highest_price REAL,
                    status TEXT DEFAULT 'OPEN',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    starting_capital REAL,
                    ending_capital REAL,
                    daily_pnl REAL,
                    daily_return_pct REAL,
                    total_positions INTEGER,
                    trades_taken INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    benchmark_return_pct REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Strategy performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    date DATE,
                    trades INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    avg_win REAL DEFAULT 0,
                    avg_loss REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(strategy, date)
                )
            """)
            
            # Error log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    error_message TEXT,
                    context TEXT,
                    traceback TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                ON trades(symbol)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_strategy 
                ON trades(strategy)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_exit_time 
                ON trades(exit_time)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_performance_date 
                ON daily_performance(date)
            """)
            
            conn.commit()
            
        if logger:
            logger.success("Database initialized")
        else:
            print("✅ Database initialized")
    
    def add_trade(self, trade_data):
        """
        Add completed trade to database
        
        Args:
            trade_data: dict with trade information
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades (
                    symbol, strategy, entry_price, exit_price, shares, 
                    initial_shares, entry_time, exit_time, hold_days,
                    exit_reason, profit_loss, profit_loss_percent,
                    targets_hit, stop_loss, highest_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data.get('symbol'),
                trade_data.get('strategy', 'MOMENTUM'),
                trade_data.get('entry_price'),
                trade_data.get('exit_price'),
                trade_data.get('shares'),
                trade_data.get('initial_shares'),
                trade_data.get('entry_time'),
                trade_data.get('exit_time', datetime.now().isoformat()),
                trade_data.get('hold_days', 0),
                trade_data.get('exit_reason', 'Manual'),
                trade_data.get('profit_loss', 0),
                trade_data.get('profit_loss_percent', 0),
                json.dumps(trade_data.get('targets_hit', [])),
                trade_data.get('stop_loss'),
                trade_data.get('highest_price')
            ))
            
            conn.commit()
    
    def sync_positions_from_json(self, positions_dict):
        """
        Sync positions from portfolio.json to database
        Non-breaking: Just mirrors the JSON data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear current positions
            cursor.execute("DELETE FROM positions")
            
            # Insert current positions
            for symbol, pos in positions_dict.items():
                if pos.get('status') == 'OPEN':
                    cursor.execute("""
                        INSERT OR REPLACE INTO positions (
                            symbol, strategy, entry_price, shares, initial_shares,
                            stop_loss, target1, target2, target3, position_value,
                            entry_time, days_held, targets_hit, highest_price, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol,
                        pos.get('strategy', 'MOMENTUM'),
                        pos.get('entry_price'),
                        pos.get('shares'),
                        pos.get('initial_shares'),
                        pos.get('stop_loss'),
                        pos.get('target1'),
                        pos.get('target2'),
                        pos.get('target3'),
                        pos.get('position_value'),
                        pos.get('entry_time'),
                        pos.get('days_held', 0),
                        json.dumps(pos.get('targets_hit', [])),
                        pos.get('highest_price'),
                        'OPEN'
                    ))
            
            conn.commit()
    
    def get_trade_history(self, days=30, strategy=None):
        """Get recent trade history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if strategy:
                cursor.execute("""
                    SELECT * FROM trades 
                    WHERE exit_time >= datetime('now', '-' || ? || ' days')
                    AND strategy = ?
                    ORDER BY exit_time DESC
                """, (days, strategy))
            else:
                cursor.execute("""
                    SELECT * FROM trades 
                    WHERE exit_time >= datetime('now', '-' || ? || ' days')
                    ORDER BY exit_time DESC
                """, (days,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_metrics(self, days=30):
        """Calculate performance metrics from trade history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(profit_loss) as total_pnl,
                    AVG(CASE WHEN profit_loss > 0 THEN profit_loss END) as avg_win,
                    AVG(CASE WHEN profit_loss < 0 THEN profit_loss END) as avg_loss,
                    AVG(hold_days) as avg_hold_days
                FROM trades
                WHERE exit_time >= datetime('now', '-' || ? || ' days')
            """, (days,))
            
            row = cursor.fetchone()
            if row:
                metrics = dict(row)
                # Calculate win rate
                if metrics['total_trades'] > 0:
                    metrics['win_rate'] = (metrics['wins'] / metrics['total_trades']) * 100
                else:
                    metrics['win_rate'] = 0
                
                return metrics
            
            return {}
    
    def get_strategy_performance(self, days=30):
        """Get performance breakdown by strategy"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    strategy,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss_percent) as avg_return_pct
                FROM trades
                WHERE exit_time >= datetime('now', '-' || ? || ' days')
                GROUP BY strategy
            """, (days,))
            
            results = []
            for row in cursor.fetchall():
                metrics = dict(row)
                if metrics['total_trades'] > 0:
                    metrics['win_rate'] = (metrics['wins'] / metrics['total_trades']) * 100
                else:
                    metrics['win_rate'] = 0
                results.append(metrics)
            
            return results
    
    def log_error(self, error_type, error_message, context="", traceback_str=""):
        """Log error to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_log (error_type, error_message, context, traceback)
                VALUES (?, ?, ?, ?)
            """, (error_type, error_message, context, traceback_str))
            conn.commit()


# Global database instance
_db_instance = None


def get_database():
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TradingDatabase()
    return _db_instance


if __name__ == "__main__":
    # Test database
    print("🧪 Testing database...")
    
    db = get_database()
    
    # Test trade insertion
    test_trade = {
        'symbol': 'TEST',
        'strategy': 'MOMENTUM',
        'entry_price': 100.0,
        'exit_price': 105.0,
        'shares': 100,
        'initial_shares': 100,
        'entry_time': datetime.now().isoformat(),
        'exit_time': datetime.now().isoformat(),
        'hold_days': 2,
        'exit_reason': 'Target Hit',
        'profit_loss': 500.0,
        'profit_loss_percent': 5.0,
        'targets_hit': ['T1'],
        'stop_loss': 95.0,
        'highest_price': 106.0
    }
    
    db.add_trade(test_trade)
    print("✅ Test trade added")
    
    # Get metrics
    metrics = db.get_performance_metrics(days=30)
    print(f"\n📊 Performance Metrics: {metrics}")
    
    print("\n✅ Database test complete")
