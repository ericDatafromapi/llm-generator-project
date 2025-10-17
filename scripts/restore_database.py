#!/usr/bin/env python3
"""
Restore Database from Backup
Can restore from local backup or Google Cloud Storage
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from google.cloud import storage
from google.oauth2 import service_account

# Configuration
LOCAL_BACKUP_DIR = "/opt/llmready/backups/database"
GCS_BUCKET_NAME = os.getenv("GCS_BACKUP_BUCKET", "")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH", "/opt/llmready/gcs-credentials.json")
DB_NAME = "llmready_prod"


def list_local_backups():
    """List available local backups"""
    backups = sorted(Path(LOCAL_BACKUP_DIR).glob("llmready_*.sql.gz"), reverse=True)
    
    if not backups:
        print("No local backups found")
        return []
    
    print("\n📁 Local Backups:")
    print("="*60)
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / 1024 / 1024  # MB
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. {backup.name}")
        print(f"   Size: {size:.2f} MB | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups


def list_gcs_backups():
    """List available GCS backups"""
    if not GCS_BUCKET_NAME or not os.path.exists(GCS_CREDENTIALS_PATH):
        print("\n⚠️  GCS not configured")
        return []
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GCS_CREDENTIALS_PATH
        )
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        blobs = list(bucket.list_blobs(prefix="database-backups/"))
        blobs.sort(key=lambda x: x.time_created, reverse=True)
        
        if not blobs:
            print("\n☁️  No GCS backups found")
            return []
        
        print("\n☁️  Google Cloud Storage Backups:")
        print("="*60)
        for i, blob in enumerate(blobs, 1):
            size = blob.size / 1024 / 1024  # MB
            print(f"{i}. {blob.name.split('/')[-1]}")
            print(f"   Size: {size:.2f} MB | Created: {blob.time_created.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return blobs
        
    except Exception as e:
        print(f"\n❌ Error listing GCS backups: {e}")
        return []


def download_from_gcs(blob, local_path):
    """Download backup from GCS"""
    try:
        print(f"\n📥 Downloading from GCS: {blob.name}")
        blob.download_to_filename(local_path)
        print(f"✅ Downloaded to: {local_path}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def restore_backup(backup_path, db_name=DB_NAME):
    """Restore database from backup file"""
    print(f"\n🔄 Restoring database: {db_name}")
    print(f"   From: {backup_path}")
    print("")
    
    # Confirm restoration
    print("⚠️  WARNING: This will REPLACE the current database!")
    print("   Current data will be lost unless you have a backup.")
    print("")
    response = input("Type 'RESTORE' to confirm: ")
    
    if response != "RESTORE":
        print("❌ Restoration cancelled")
        return False
    
    try:
        # Get postgres container
        postgres_container = subprocess.check_output(
            ['docker', 'ps', '-qf', 'name=postgres'],
            text=True
        ).strip()
        
        if not postgres_container:
            print("❌ PostgreSQL container not found")
            return False
        
        # Drop existing database (be careful!)
        print(f"\n1️⃣ Dropping existing database: {db_name}")
        subprocess.run([
            'docker', 'exec', '-i', postgres_container,
            'psql', '-U', 'postgres',
            '-c', f'DROP DATABASE IF EXISTS {db_name};'
        ], check=True)
        
        # Create fresh database
        print(f"2️⃣ Creating fresh database: {db_name}")
        subprocess.run([
            'docker', 'exec', '-i', postgres_container,
            'psql', '-U', 'postgres',
            '-c', f'CREATE DATABASE {db_name};'
        ], check=True)
        
        # Restore from backup
        print(f"3️⃣ Restoring from backup...")
        with open(backup_path, 'rb') as f:
            subprocess.run([
                'docker', 'exec', '-i', postgres_container,
                'pg_restore',
                '-U', 'postgres',
                '-d', db_name,
                '--no-owner',
                '--no-acl'
            ], stdin=f, check=True)
        
        print(f"\n✅ Database restored successfully!")
        print(f"\n4️⃣ Restarting backend service...")
        subprocess.run(['sudo', 'systemctl', 'restart', 'llmready-backend'], check=True)
        
        print("\n✅ Restoration complete!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Restoration failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Restoration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Restore LLMReady database from backup')
    parser.add_argument('--source', choices=['local', 'gcs'], default='local',
                       help='Backup source (local or gcs)')
    parser.add_argument('--file', help='Specific backup file to restore')
    parser.add_argument('--list', action='store_true', help='List available backups')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔄 LLMReady Database Restore")
    print("="*60)
    
    # List backups if requested
    if args.list:
        local_backups = list_local_backups()
        gcs_backups = list_gcs_backups()
        return
    
    # Get backup file
    if args.file:
        if args.source == 'local':
            backup_path = os.path.join(LOCAL_BACKUP_DIR, args.file)
            if not os.path.exists(backup_path):
                print(f"❌ Backup file not found: {backup_path}")
                sys.exit(1)
        else:  # GCS
            print(f"Downloading from GCS: {args.file}")
            # Download from GCS first
            temp_path = f"/tmp/{args.file}"
            # Implementation needed
            backup_path = temp_path
    else:
        # Interactive selection
        if args.source == 'local':
            backups = list_local_backups()
            if not backups:
                sys.exit(1)
            
            try:
                choice = int(input("\nSelect backup number to restore: "))
                if 1 <= choice <= len(backups):
                    backup_path = str(backups[choice - 1])
                else:
                    print("Invalid selection")
                    sys.exit(1)
            except ValueError:
                print("Invalid input")
                sys.exit(1)
        else:  # GCS
            gcs_backups = list_gcs_backups()
            if not gcs_backups:
                sys.exit(1)
            
            try:
                choice = int(input("\nSelect backup number to restore: "))
                if 1 <= choice <= len(gcs_backups):
                    blob = gcs_backups[choice - 1]
                    backup_path = f"/tmp/{blob.name.split('/')[-1]}"
                    if not download_from_gcs(blob, backup_path):
                        sys.exit(1)
                else:
                    print("Invalid selection")
                    sys.exit(1)
            except ValueError:
                print("Invalid input")
                sys.exit(1)
    
    # Perform restoration
    success = restore_backup(backup_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()