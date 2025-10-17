#!/usr/bin/env python3
"""
Production Database Backup Script
Backs up PostgreSQL database to Google Cloud Storage and local storage
Runs hourly via cron/systemd timer
"""
import os
import sys
import subprocess
import datetime
import logging
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account

# Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "postgres"  # Will be read from .env or environment
DB_NAME = "llmready_prod"

# Backup settings
LOCAL_BACKUP_DIR = "/opt/llmready/backups/database"
GCS_BUCKET_NAME = os.getenv("GCS_BACKUP_BUCKET", "")  # Set in .env
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH", "/opt/llmready/gcs-credentials.json")

# Retention settings (how many backups to keep)
LOCAL_RETENTION_DAYS = 7  # Keep 7 days locally
GCS_RETENTION_DAYS = 30   # Keep 30 days in cloud

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/llmready-backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_db_config():
    """Load database configuration from .env file"""
    env_file = "/opt/llmready/backend/.env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    # Parse: postgresql://user:pass@host:port/dbname
                    db_url = line.split('=', 1)[1].strip()
                    return {
                        'url': db_url,
                        'dbname': db_url.split('/')[-1]
                    }
    return None


def create_backup():
    """Create PostgreSQL backup using pg_dump"""
    logger.info("Starting database backup...")
    
    # Load config from .env
    db_config = load_db_config()
    if db_config:
        db_name = db_config['dbname']
    else:
        db_name = DB_NAME
        logger.warning("Could not load DATABASE_URL from .env, using default")
    
    # Create backup directory
    Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"llmready_{db_name}_{timestamp}.sql.gz"
    local_backup_path = os.path.join(LOCAL_BACKUP_DIR, backup_filename)
    
    logger.info(f"Creating backup: {backup_filename}")
    
    try:
        # Use Docker to run pg_dump
        docker_cmd = [
            'docker', 'exec', '-i',
            subprocess.check_output(
                ['docker', 'ps', '-qf', 'name=postgres'],
                text=True
            ).strip(),
            'pg_dump',
            '-U', DB_USER,
            '-d', db_name,
            '--format=custom',  # Custom format (compressed and restorable)
        ]
        
        # Run pg_dump and save to file
        with open(local_backup_path + '.tmp', 'wb') as f:
            result = subprocess.run(
                docker_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        # Rename to final name
        os.rename(local_backup_path + '.tmp', local_backup_path)
        
        # Get file size
        file_size = os.path.getsize(local_backup_path)
        logger.info(f"✅ Backup created: {backup_filename} ({file_size / 1024 / 1024:.2f} MB)")
        
        return local_backup_path, backup_filename
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Backup failed: {e.stderr.decode() if e.stderr else str(e)}")
        # Clean up temp file
        if os.path.exists(local_backup_path + '.tmp'):
            os.remove(local_backup_path + '.tmp')
        return None, None
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return None, None


def upload_to_gcs(local_path, filename):
    """Upload backup to Google Cloud Storage"""
    if not GCS_BUCKET_NAME:
        logger.warning("⚠️  GCS_BACKUP_BUCKET not configured, skipping cloud upload")
        return False
    
    if not os.path.exists(GCS_CREDENTIALS_PATH):
        logger.warning(f"⚠️  GCS credentials not found at {GCS_CREDENTIALS_PATH}, skipping cloud upload")
        return False
    
    try:
        logger.info(f"Uploading to Google Cloud Storage: {GCS_BUCKET_NAME}")
        
        # Initialize GCS client
        credentials = service_account.Credentials.from_service_account_file(
            GCS_CREDENTIALS_PATH
        )
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Upload with timestamp prefix for organization
        gcs_path = f"database-backups/{filename}"
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        
        logger.info(f"✅ Uploaded to GCS: gs://{GCS_BUCKET_NAME}/{gcs_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ GCS upload failed: {e}")
        return False


def cleanup_old_backups():
    """Remove backups older than retention period"""
    logger.info("Cleaning up old backups...")
    
    # Cleanup local backups
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=LOCAL_RETENTION_DAYS)
        
        for backup_file in Path(LOCAL_BACKUP_DIR).glob("llmready_*.sql.gz"):
            # Extract date from filename (format: llmready_dbname_YYYYMMDD_HHMMSS.sql.gz)
            try:
                parts = backup_file.stem.split('_')
                date_str = parts[-2]  # YYYYMMDD
                file_date = datetime.datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old local backup: {backup_file.name}")
            except (ValueError, IndexError):
                # Skip files that don't match expected format
                continue
                
    except Exception as e:
        logger.error(f"Local cleanup error: {e}")
    
    # Cleanup GCS backups
    if GCS_BUCKET_NAME and os.path.exists(GCS_CREDENTIALS_PATH):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                GCS_CREDENTIALS_PATH
            )
            client = storage.Client(credentials=credentials, project=credentials.project_id)
            bucket = client.bucket(GCS_BUCKET_NAME)
            
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=GCS_RETENTION_DAYS)
            
            blobs = bucket.list_blobs(prefix="database-backups/")
            for blob in blobs:
                if blob.time_created.replace(tzinfo=None) < cutoff_date:
                    blob.delete()
                    logger.info(f"Deleted old GCS backup: {blob.name}")
                    
        except Exception as e:
            logger.error(f"GCS cleanup error: {e}")


def main():
    """Main backup process"""
    logger.info("="*60)
    logger.info("🗄️  LLMReady Database Backup")
    logger.info("="*60)
    
    # Create backup
    local_path, filename = create_backup()
    
    if not local_path:
        logger.error("❌ Backup creation failed")
        sys.exit(1)
    
    # Upload to GCS
    gcs_success = upload_to_gcs(local_path, filename)
    
    # Cleanup old backups
    cleanup_old_backups()
    
    # Summary
    logger.info("="*60)
    logger.info("📊 Backup Summary")
    logger.info("="*60)
    logger.info(f"Local backup: {local_path}")
    logger.info(f"GCS backup: {'✅ SUCCESS' if gcs_success else '⚠️  SKIPPED/FAILED'}")
    logger.info(f"Retention: {LOCAL_RETENTION_DAYS} days local, {GCS_RETENTION_DAYS} days cloud")
    logger.info("="*60)
    
    sys.exit(0 if gcs_success or not GCS_BUCKET_NAME else 1)


if __name__ == "__main__":
    main()