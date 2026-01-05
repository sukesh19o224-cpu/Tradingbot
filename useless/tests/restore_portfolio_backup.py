"""
🔄 Restore Portfolio from Backup

This script restores your portfolio from the most recent backup
created by the fix_portfolio_sl.py script.
"""

import json
import glob
from pathlib import Path
from datetime import datetime

def find_latest_backup(base_file):
    """Find the most recent backup for a file"""
    backup_pattern = f"{base_file}.backup_*"
    backups = glob.glob(backup_pattern)

    if not backups:
        return None

    # Sort by modification time (most recent first)
    backups.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return backups[0]

def restore_file(original_file, backup_file):
    """Restore original file from backup"""
    try:
        # Read backup
        with open(backup_file, 'r') as f:
            data = json.load(f)

        # Write to original
        with open(original_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Restored: {original_file}")
        print(f"   From: {backup_file}")

        # Show capital info
        capital = data.get('capital', 0)
        positions = len(data.get('positions', {}))
        print(f"   Capital: ₹{capital:,.2f}")
        print(f"   Positions: {positions}")

        return True
    except Exception as e:
        print(f"❌ Error restoring {original_file}: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🔄 RESTORE PORTFOLIO FROM BACKUP")
    print("="*70 + "\n")

    files_to_restore = [
        'data/swing_portfolio.json',
        'data/positional_portfolio.json'
    ]

    restored_count = 0

    for file_path in files_to_restore:
        print(f"\n📁 {file_path}")
        print("-" * 70)

        # Find latest backup
        backup = find_latest_backup(file_path)

        if backup:
            backup_time = datetime.fromtimestamp(Path(backup).stat().st_mtime)
            print(f"Found backup from: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Restore
            if restore_file(file_path, backup):
                restored_count += 1
        else:
            print(f"⚠️ No backup found for {file_path}")

    print("\n" + "="*70)
    if restored_count > 0:
        print(f"✅ RESTORED {restored_count} FILES")
        print("="*70)
        print("\n🎯 Your portfolio has been restored to the backup state!")
        print("   Check your capital and positions to verify.\n")
    else:
        print("❌ NO FILES RESTORED")
        print("="*70)
        print("\n⚠️ Could not find any backup files.")
        print("   Backup files should be named like:")
        print("   - data/swing_portfolio.json.backup_20241127_HHMMSS")
        print("   - data/positional_portfolio.json.backup_20241127_HHMMSS\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
