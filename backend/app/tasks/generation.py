"""
Celery tasks for file generation.
Handles the background processing of website crawling and file generation.
"""
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.generation import Generation
from app.models.website import Website
from app.models.user import User
from app.services.email import send_generation_complete_email, send_generation_failed_email, increment_generation_usage
from app.core.config import settings

logger = logging.getLogger(__name__)


def run_mdream_crawler(
    origin: str,
    out_dir: str,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    use_playwright: bool = False,
    max_pages: int = 500,
    timeout: int = 300
) -> tuple[bool, float, str]:
    """
    Run the Mdream crawler via Docker or npx fallback.
    Returns: (success, duration, error_message)
    """
    # Check if Docker is available
    docker_available = False
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            timeout=10
        )
        docker_available = (result.returncode == 0)
    except Exception:
        pass
    
    start_time = time.time()
    
    try:
        if docker_available:
            # Use Docker with ARM64 support for Apple Silicon
            cmd = [
                'docker', 'run',
                '--platform', 'linux/amd64',  # Force x86_64 emulation on ARM64 (Apple Silicon)
                '--rm',
                '-v', f'{os.path.abspath(out_dir)}:/app/output',  # Mount to mdream's default output
                'harlanzw/mdream',
                '--url', origin  # Direct URL parameter
            ]
            
            if include:
                cmd.extend(['--include', include])
            if exclude:
                cmd.extend(['--exclude', exclude])
            if use_playwright:
                cmd.append('--playwright')
            if max_pages:
                cmd.extend(['--max-pages', str(max_pages)])
            if timeout:
                cmd.extend(['--timeout', str(timeout)])
            
            logger.info(f"Running Docker command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line_stripped = line.strip()
                    if line_stripped:
                        logger.info(f"Mdream: {line_stripped}")
                        output_lines.append(line_stripped)
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout + 120:
                    logger.warning(f"Timeout reached ({elapsed:.1f}s), terminating process")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return False, elapsed, f"Process timeout after {elapsed:.1f}s"
            
            return_code = process.wait()
            duration = time.time() - start_time
            
            if return_code != 0:
                error_msg = f"Docker command failed with exit code {return_code}"
                if output_lines:
                    error_msg += f"\nLast output: {output_lines[-5:]}"
                logger.error(error_msg)
                return False, duration, error_msg
            
            logger.info(f"Docker command completed successfully in {duration:.1f}s")
            return True, duration, ""
            
        else:
            # Fallback to npx
            cmd = [
                'npx', '--yes', '@mdream/crawl',
                '--url', origin,
                '--output', out_dir
            ]
            
            if max_pages:
                cmd.extend(['--max-pages', str(max_pages)])
            if use_playwright:
                cmd.extend(['--driver', 'playwright'])
            else:
                cmd.extend(['--driver', 'http'])
            
            logger.info(f"Running npx command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line_stripped = line.strip()
                    if line_stripped:
                        logger.info(f"Mdream: {line_stripped}")
                        output_lines.append(line_stripped)
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout + 120:
                    logger.warning(f"Timeout reached ({elapsed:.1f}s), terminating process")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return False, elapsed, f"Process timeout after {elapsed:.1f}s"
            
            return_code = process.wait()
            duration = time.time() - start_time
            
            if return_code != 0:
                error_msg = f"npx command failed with exit code {return_code}"
                if output_lines:
                    error_msg += f"\nLast output: {output_lines[-5:]}"
                logger.error(error_msg)
                return False, duration, error_msg
            
            logger.info(f"npx command completed successfully in {duration:.1f}s")
            return True, duration, ""
            
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Exception during crawl: {str(e)}"
        logger.exception(error_msg)
        return False, duration, error_msg


def create_zip_archive(source_dir: str, zip_path: str) -> tuple[bool, int, str]:
    """
    Create a ZIP archive from a directory.
    Returns: (success, file_size, error_message)
    """
    try:
        source_path = Path(source_dir)
        zip_path_obj = Path(zip_path)
        
        if not source_path.exists():
            return False, 0, f"Source directory {source_dir} does not exist"
        
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_path)
                    zipf.write(file_path, arcname)
        
        # Get file size
        file_size = zip_path_obj.stat().st_size
        logger.info(f"Created ZIP archive: {zip_path} ({file_size} bytes)")
        
        return True, file_size, ""
        
    except Exception as e:
        error_msg = f"Failed to create ZIP archive: {str(e)}"
        logger.exception(error_msg)
        return False, 0, error_msg


def count_files_in_directory(directory: str) -> int:
    """Count total files in a directory recursively."""
    try:
        return sum(1 for _, _, files in os.walk(directory) for _ in files)
    except Exception as e:
        logger.error(f"Failed to count files: {e}")
        return 0


@celery_app.task(bind=True, max_retries=2)
def generate_llm_content(self, generation_id: str):
    """
    Main generation task - crawls website and creates LLM-ready files.
    
    Args:
        generation_id: UUID of the Generation record
    """
    db = SessionLocal()
    generation = None
    temp_dir = None
    
    try:
        # Get generation record
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"Generation {generation_id} not found")
            return
        
        # Get website and user
        website = db.query(Website).filter(Website.id == generation.website_id).first()
        user = db.query(User).filter(User.id == generation.user_id).first()
        
        if not website or not user:
            logger.error(f"Website or User not found for generation {generation_id}")
            generation.status = 'failed'
            generation.error_message = "Website or User not found"
            db.commit()
            return
        
        logger.info(f"Starting generation {generation_id} for website {website.url}")
        
        # Update status to processing
        generation.status = 'processing'
        generation.started_at = datetime.utcnow()
        generation.celery_task_id = self.request.id
        db.commit()
        
        # Create temporary directory for output
        temp_dir = f"/tmp/llmready_gen_{generation_id}"
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Run crawler
        success, duration, error_msg = run_mdream_crawler(
            origin=website.url,
            out_dir=temp_dir,
            include=website.include_patterns,
            exclude=website.exclude_patterns,
            use_playwright=website.use_playwright_bool,
            max_pages=website.max_pages,
            timeout=website.timeout
        )
        
        if not success:
            raise Exception(f"Crawler failed: {error_msg}")
        
        # Validate output files
        llms_txt = Path(temp_dir) / 'llms.txt'
        md_dir = Path(temp_dir) / 'md'
        
        if not llms_txt.exists() and not any(Path(temp_dir).glob('*.md')):
            raise Exception("No output files generated by crawler")
        
        # Count total files
        total_files = count_files_in_directory(temp_dir)
        logger.info(f"Generated {total_files} files")
        
        # Create ZIP archive
        storage_path = Path(settings.FILE_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        zip_filename = f"{generation_id}.zip"
        zip_path = storage_path / zip_filename
        
        zip_success, file_size, zip_error = create_zip_archive(temp_dir, str(zip_path))
        
        if not zip_success:
            raise Exception(f"Failed to create ZIP: {zip_error}")
        
        # Update generation record
        generation.status = 'completed'
        generation.completed_at = datetime.utcnow()
        generation.duration_seconds = duration
        generation.file_path = str(zip_path)
        generation.file_size = file_size
        generation.total_files = total_files
        generation.progress_percentage = 100
        
        # Update website metadata
        website.last_generated_at = datetime.utcnow()
        website.generation_count += 1
        
        db.commit()
        
        logger.info(f"Generation {generation_id} completed successfully")
        
        # Increment usage quota
        try:
            increment_generation_usage(db, user.id)
            logger.info(f"Incremented usage for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to increment usage: {e}")
        
        # Send success email
        try:
            send_generation_complete_email(
                user.email,
                user.full_name or user.email,
                website.name or website.url,
                generation_id
            )
            logger.info(f"Sent completion email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
        
    except Exception as e:
        logger.exception(f"Generation {generation_id} failed: {str(e)}")
        
        if generation:
            generation.status = 'failed'
            generation.error_message = str(e)[:1000]  # Limit error message length
            generation.retry_count += 1
            db.commit()
            
            # Send failure email
            try:
                user = db.query(User).filter(User.id == generation.user_id).first()
                if user:
                    send_generation_failed_email(
                        user.email,
                        user.full_name or user.email,
                        str(e)
                    )
            except Exception as email_error:
                logger.error(f"Failed to send failure email: {email_error}")
        
        # Retry if not max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying generation {generation_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory: {e}")
        
        db.close()