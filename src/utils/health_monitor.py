"""
🏥 SYSTEM HEALTH MONITOR
Monitors system health and provides alerts
"""

import os
import sys
import json
import shutil
from datetime import datetime, timedelta
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.logger import get_logger
    logger = get_logger('HealthMonitor')
except:
    logger = None


class HealthMonitor:
    """
    Monitor system health and detect issues
    """
    
    def __init__(self):
        self.last_scan_time = None
        self.last_data_fetch_time = None
        self.last_position_update_time = None
        self.api_error_count = 0
        self.scan_count = 0
        self.position_update_count = 0
        
        # Track recent activities (keep last 100)
        self.recent_activities = deque(maxlen=100)
        
        self.health_history = []
        self.max_history = 1000
    
    def record_activity(self, activity_type, details=""):
        """Record system activity"""
        activity = {
            'timestamp': datetime.now(),
            'type': activity_type,
            'details': details
        }
        self.recent_activities.append(activity)
        
        # Update specific counters
        if activity_type == 'SCAN':
            self.last_scan_time = datetime.now()
            self.scan_count += 1
        elif activity_type == 'POSITION_UPDATE':
            self.last_position_update_time = datetime.now()
            self.position_update_count += 1
        elif activity_type == 'DATA_FETCH':
            self.last_data_fetch_time = datetime.now()
        elif activity_type == 'API_ERROR':
            self.api_error_count += 1
    
    def check_health(self):
        """
        Check overall system health
        Returns: (is_healthy, issues_list)
        """
        issues = []
        now = datetime.now()
        
        # Check if scans are running (should run at least every 15 min during market)
        if self.last_scan_time:
            time_since_scan = (now - self.last_scan_time).seconds / 60
            if time_since_scan > 20:  # 20 minutes without scan
                issues.append(f"No scans in last {time_since_scan:.0f} minutes")
        
        # Check API error rate
        if self.api_error_count > 20:
            issues.append(f"High API error count: {self.api_error_count}")
        
        # Check position updates
        if self.last_position_update_time:
            time_since_update = (now - self.last_position_update_time).seconds / 60
            if time_since_update > 10:  # 10 minutes without update during market
                issues.append(f"No position updates in last {time_since_update:.0f} minutes")
        
        is_healthy = len(issues) == 0
        
        # Record health check
        health_record = {
            'timestamp': now,
            'is_healthy': is_healthy,
            'issues': issues,
            'stats': self.get_stats()
        }
        self.health_history.append(health_record)
        
        # Limit history size
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        
        return is_healthy, issues
    
    def get_stats(self):
        """Get health statistics"""
        now = datetime.now()
        
        stats = {
            'total_scans': self.scan_count,
            'total_position_updates': self.position_update_count,
            'api_error_count': self.api_error_count,
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'last_position_update': self.last_position_update_time.isoformat() if self.last_position_update_time else None,
            'last_data_fetch': self.last_data_fetch_time.isoformat() if self.last_data_fetch_time else None,
        }
        
        # Calculate time since last activity
        if self.last_scan_time:
            stats['minutes_since_last_scan'] = (now - self.last_scan_time).seconds / 60
        
        return stats
    
    def get_recent_activities(self, minutes=60):
        """Get activities from last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            act for act in self.recent_activities 
            if act['timestamp'] > cutoff_time
        ]
    
    def display_health_status(self):
        """Display health status"""
        is_healthy, issues = self.check_health()
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("🏥 SYSTEM HEALTH STATUS")
        print("="*70)
        
        if is_healthy:
            print("✅ System Status: HEALTHY")
        else:
            print("⚠️ System Status: ISSUES DETECTED")
            print("\n🚨 Issues:")
            for issue in issues:
                print(f"   - {issue}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total Scans: {stats['total_scans']}")
        print(f"   Position Updates: {stats['total_position_updates']}")
        print(f"   API Errors: {stats['api_error_count']}")
        
        if stats['last_scan']:
            print(f"   Last Scan: {stats.get('minutes_since_last_scan', 0):.0f} minutes ago")
        
        print("="*70)
    
    def reset_error_count(self):
        """Reset API error counter (call daily)"""
        self.api_error_count = 0


class BackupManager:
    """
    Automatic backup for portfolio and important data
    """
    
    def __init__(self, backup_dir='data/backups'):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup_portfolio(self, portfolio_file='data/portfolio.json'):
        """
        Create timestamped backup of portfolio
        Keeps last 30 backups
        """
        if not os.path.exists(portfolio_file):
            if logger:
                logger.warning(f"Portfolio file not found: {portfolio_file}")
            return False
        
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'portfolio_{timestamp}.json')
            
            # Copy file
            shutil.copy2(portfolio_file, backup_file)
            
            if logger:
                logger.success(f"Portfolio backed up: {backup_file}")
            else:
                print(f"✅ Portfolio backed up: {backup_file}")
            
            # Cleanup old backups (keep last 30)
            self._cleanup_old_backups()
            
            return True
        
        except Exception as e:
            if logger:
                logger.error(f"Backup failed: {e}")
            else:
                print(f"❌ Backup failed: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count=30):
        """Keep only the most recent N backups"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('portfolio_') and file.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, file)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Delete old backups
            for filepath, _ in backup_files[keep_count:]:
                os.remove(filepath)
                if logger:
                    logger.info(f"Deleted old backup: {filepath}")
        
        except Exception as e:
            if logger:
                logger.error(f"Backup cleanup failed: {e}")
    
    def restore_latest_backup(self, portfolio_file='data/portfolio.json'):
        """Restore from latest backup"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('portfolio_') and file.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, file)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            if not backup_files:
                print("❌ No backups found")
                return False
            
            # Get latest backup
            backup_files.sort(key=lambda x: x[1], reverse=True)
            latest_backup = backup_files[0][0]
            
            # Restore
            shutil.copy2(latest_backup, portfolio_file)
            print(f"✅ Portfolio restored from: {latest_backup}")
            
            return True
        
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def list_backups(self):
        """List all available backups"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('portfolio_') and file.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, file)
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    size = os.path.getsize(filepath)
                    backup_files.append({
                        'file': file,
                        'path': filepath,
                        'modified': mtime,
                        'size_kb': size / 1024
                    })
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            
            print("\n📁 Available Backups:")
            print("="*70)
            for i, backup in enumerate(backup_files[:10], 1):  # Show last 10
                print(f"{i}. {backup['file']}")
                print(f"   Time: {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Size: {backup['size_kb']:.1f} KB")
            print("="*70)
            
            return backup_files
        
        except Exception as e:
            print(f"❌ Failed to list backups: {e}")
            return []


# Global instances
_health_monitor = None
_backup_manager = None


def get_health_monitor():
    """Get global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def get_backup_manager():
    """Get global backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


if __name__ == "__main__":
    # Test health monitor
    print("🧪 Testing Health Monitor...")
    
    monitor = get_health_monitor()
    
    # Simulate activities
    monitor.record_activity('SCAN', 'EOD Scan')
    monitor.record_activity('POSITION_UPDATE', 'Updated 5 positions')
    monitor.record_activity('DATA_FETCH', 'Fetched NIFTY data')
    
    # Check health
    monitor.display_health_status()
    
    # Test backup manager
    print("\n🧪 Testing Backup Manager...")
    backup_mgr = get_backup_manager()
    
    # Create test portfolio file
    test_portfolio = {'capital': 100000, 'positions': {}}
    os.makedirs('data', exist_ok=True)
    with open('data/test_portfolio.json', 'w') as f:
        json.dump(test_portfolio, f)
    
    # Backup
    backup_mgr.backup_portfolio('data/test_portfolio.json')
    
    # List backups
    backup_mgr.list_backups()
    
    print("\n✅ Tests complete")
