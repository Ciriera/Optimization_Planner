#!/usr/bin/env python3
"""
Backup script for Optimization Planner
Creates database and file backups
"""

import os
import sys
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


def create_backup_directory():
    """Create backup directory if it doesn't exist"""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def backup_database():
    """Backup SQLite database"""
    print("📦 Backing up database...")
    
    db_path = "optimization_planner.db"
    if not os.path.exists(db_path):
        print("   ⚠️ Database file not found")
        return None
    
    backup_dir = create_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"database_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_file)
        print(f"   ✅ Database backed up to: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"   ❌ Database backup failed: {str(e)}")
        return None


def backup_files():
    """Backup important files"""
    print("📦 Backing up files...")
    
    backup_dir = create_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_backup_dir = backup_dir / f"files_backup_{timestamp}"
    files_backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "requirements.txt",
        "alembic.ini",
        "docker-compose.yml",
        "Dockerfile",
        "nginx.conf",
        "Makefile",
        "README.md"
    ]
    
    backed_up_files = []
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, files_backup_dir / file_path)
                backed_up_files.append(file_path)
            except Exception as e:
                print(f"   ⚠️ Failed to backup {file_path}: {str(e)}")
    
    if backed_up_files:
        print(f"   ✅ Files backed up to: {files_backup_dir}")
        print(f"   📁 Backed up {len(backed_up_files)} files")
        return files_backup_dir
    else:
        print("   ⚠️ No files were backed up")
        return None


def backup_reports():
    """Backup generated reports"""
    print("📦 Backing up reports...")
    
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("   ⚠️ Reports directory not found")
        return None
    
    backup_dir = create_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_backup_dir = backup_dir / f"reports_backup_{timestamp}"
    
    try:
        shutil.copytree(reports_dir, reports_backup_dir)
        report_count = len(list(reports_backup_dir.rglob("*")))
        print(f"   ✅ Reports backed up to: {reports_backup_dir}")
        print(f"   📊 Backed up {report_count} report files")
        return reports_backup_dir
    except Exception as e:
        print(f"   ❌ Reports backup failed: {str(e)}")
        return None


def backup_logs():
    """Backup log files"""
    print("📦 Backing up logs...")
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("   ⚠️ Logs directory not found")
        return None
    
    backup_dir = create_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_backup_dir = backup_dir / f"logs_backup_{timestamp}"
    
    try:
        shutil.copytree(logs_dir, logs_backup_dir)
        log_count = len(list(logs_backup_dir.rglob("*.log")))
        print(f"   ✅ Logs backed up to: {logs_backup_dir}")
        print(f"   📝 Backed up {log_count} log files")
        return logs_backup_dir
    except Exception as e:
        print(f"   ❌ Logs backup failed: {str(e)}")
        return None


def create_backup_manifest(backup_items):
    """Create backup manifest file"""
    print("📝 Creating backup manifest...")
    
    backup_dir = create_backup_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_file = backup_dir / f"backup_manifest_{timestamp}.json"
    
    manifest = {
        "backup_date": datetime.now().isoformat(),
        "backup_type": "full",
        "items": backup_items,
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }
    }
    
    try:
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"   ✅ Backup manifest created: {manifest_file}")
        return manifest_file
    except Exception as e:
        print(f"   ❌ Failed to create manifest: {str(e)}")
        return None


def cleanup_old_backups():
    """Clean up old backup files"""
    print("🧹 Cleaning up old backups...")
    
    backup_dir = create_backup_directory()
    if not backup_dir.exists():
        return
    
    # Keep backups from the last 30 days
    cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    
    deleted_count = 0
    for backup_file in backup_dir.iterdir():
        if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_date:
            try:
                backup_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️ Failed to delete {backup_file}: {str(e)}")
        elif backup_file.is_dir() and backup_file.stat().st_mtime < cutoff_date:
            try:
                shutil.rmtree(backup_file)
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️ Failed to delete {backup_file}: {str(e)}")
    
    if deleted_count > 0:
        print(f"   ✅ Deleted {deleted_count} old backup files")
    else:
        print("   ℹ️ No old backup files to clean up")


def main():
    """Main backup function"""
    print("🔄 Starting backup process...")
    print("=" * 50)
    
    backup_items = {}
    
    try:
        # Backup database
        db_backup = backup_database()
        if db_backup:
            backup_items["database"] = str(db_backup)
        
        print()
        
        # Backup files
        files_backup = backup_files()
        if files_backup:
            backup_items["files"] = str(files_backup)
        
        print()
        
        # Backup reports
        reports_backup = backup_reports()
        if reports_backup:
            backup_items["reports"] = str(reports_backup)
        
        print()
        
        # Backup logs
        logs_backup = backup_logs()
        if logs_backup:
            backup_items["logs"] = str(logs_backup)
        
        print()
        
        # Create manifest
        manifest_file = create_backup_manifest(backup_items)
        if manifest_file:
            backup_items["manifest"] = str(manifest_file)
        
        print()
        
        # Cleanup old backups
        cleanup_old_backups()
        
        print()
        print("=" * 50)
        
        if backup_items:
            print("🎉 Backup completed successfully!")
            print()
            print("📦 Backup items:")
            for item_type, item_path in backup_items.items():
                print(f"   - {item_type}: {item_path}")
        else:
            print("⚠️ No items were backed up")
        
        print()
        print("💡 To restore from backup, use: python scripts/restore.py")
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
