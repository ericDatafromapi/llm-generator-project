#!/usr/bin/env python3
"""
Test Generation Workflow Directly on Production Server
This script simulates a complete generation workflow using actual server resources.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/opt/llmready/backend')

from app.core.database import SessionLocal
from app.models.generation import Generation
from app.models.website import Website
from app.models.user import User
from app.tasks.generation import run_mdream_crawler, create_zip_archive
from datetime import datetime

def log(message, status="INFO"):
    """Log with colors"""
    colors = {
        "INFO": "\033[0;36m",  # Cyan
        "SUCCESS": "\033[0;32m",  # Green
        "ERROR": "\033[0;31m",  # Red
        "WARNING": "\033[1;33m",  # Yellow
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status}: {message}{reset}")

def test_docker():
    """Test if Docker is available and working"""
    log("Testing Docker availability...", "INFO")
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Docker installed: {result.stdout.strip()}", "SUCCESS")
            
            # Check if mdream image exists
            result = subprocess.run(['docker', 'images', 'harlanzw/mdream', '--format', '{{.Repository}}:{{.Tag}}'], 
                                  capture_output=True, text=True)
            if 'harlanzw/mdream' in result.stdout:
                log("mdream Docker image found", "SUCCESS")
                return True
            else:
                log("mdream Docker image NOT found", "ERROR")
                log("Run: docker pull harlanzw/mdream", "WARNING")
                return False
        else:
            log("Docker not working properly", "ERROR")
            return False
    except FileNotFoundError:
        log("Docker not installed", "ERROR")
        return False

def test_npx():
    """Test if npx is available"""
    log("Testing npx availability...", "INFO")
    try:
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"npx installed: {result.stdout.strip()}", "SUCCESS")
            return True
        else:
            log("npx not working properly", "WARNING")
            return False
    except FileNotFoundError:
        log("npx not installed", "WARNING")
        return False

def test_crawler_simple():
    """Test the crawler with a simple website"""
    log("\n=== Testing Crawler with Simple Website ===", "INFO")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="llmready_test_")
    log(f"Created temp directory: {temp_dir}", "INFO")
    
    try:
        # Test URL
        test_url = "https://example.com"
        log(f"Testing crawler with: {test_url}", "INFO")
        
        # Run crawler
        success, duration, error_msg = run_mdream_crawler(
            origin=test_url,
            out_dir=temp_dir,
            max_pages=5,
            timeout=60
        )
        
        if success:
            log(f"Crawler succeeded in {duration:.2f}s", "SUCCESS")
            
            # Check output files
            output_files = list(Path(temp_dir).rglob('*'))
            log(f"Generated {len(output_files)} files", "INFO")
            
            # Check for llms.txt
            llms_txt = Path(temp_dir) / 'llms.txt'
            if llms_txt.exists():
                size = llms_txt.stat().st_size
                log(f"llms.txt exists ({size} bytes)", "SUCCESS")
                
                # Show first few lines
                with open(llms_txt, 'r') as f:
                    preview = f.read(500)
                    log(f"Content preview:\n{preview}...", "INFO")
            else:
                log("llms.txt not found", "WARNING")
            
            # Test ZIP creation
            zip_path = temp_dir + ".zip"
            log(f"Testing ZIP creation: {zip_path}", "INFO")
            zip_success, file_size, zip_error = create_zip_archive(temp_dir, zip_path)
            
            if zip_success:
                log(f"ZIP created successfully ({file_size} bytes)", "SUCCESS")
                os.remove(zip_path)
            else:
                log(f"ZIP creation failed: {zip_error}", "ERROR")
            
            return True
        else:
            log(f"Crawler failed: {error_msg}", "ERROR")
            return False
            
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            log(f"Cleaned up temp directory", "INFO")

def test_generation_database():
    """Test database connectivity and generation records"""
    log("\n=== Testing Database Connectivity ===", "INFO")
    
    db = SessionLocal()
    try:
        # Count users
        user_count = db.query(User).count()
        log(f"Total users in database: {user_count}", "INFO")
        
        # Count websites
        website_count = db.query(Website).count()
        log(f"Total websites in database: {website_count}", "INFO")
        
        # Count generations
        generation_count = db.query(Generation).count()
        log(f"Total generations in database: {generation_count}", "INFO")
        
        # Show recent generations
        recent_gens = db.query(Generation).order_by(Generation.created_at.desc()).limit(5).all()
        
        if recent_gens:
            log("\nRecent generations:", "INFO")
            for gen in recent_gens:
                status_color = "SUCCESS" if gen.status == "completed" else "ERROR" if gen.status == "failed" else "WARNING"
                log(f"  ID: {gen.id}", status_color)
                log(f"    Status: {gen.status}", status_color)
                log(f"    Created: {gen.created_at}", status_color)
                if gen.error_message:
                    log(f"    Error: {gen.error_message[:100]}", "ERROR")
        
        return True
        
    except Exception as e:
        log(f"Database error: {e}", "ERROR")
        return False
    finally:
        db.close()

def test_celery_connectivity():
    """Test Celery/Redis connectivity"""
    log("\n=== Testing Celery/Redis Connectivity ===", "INFO")
    
    try:
        from app.core.celery_app import celery_app
        
        # Check registered tasks
        tasks = [t for t in celery_app.tasks.keys() if 'app.' in t]
        log(f"Registered Celery tasks: {len(tasks)}", "SUCCESS" if tasks else "ERROR")
        for task in tasks:
            log(f"  - {task}", "INFO")
        
        # Try to ping Redis
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        if 'PONG' in result.stdout:
            log("Redis is responding", "SUCCESS")
        else:
            log("Redis not responding properly", "WARNING")
        
        # Check queue lengths
        result = subprocess.run(['redis-cli', 'LLEN', 'celery'], capture_output=True, text=True, timeout=5)
        queue_len = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        log(f"Celery queue length: {queue_len}", "INFO")
        
        result = subprocess.run(['redis-cli', 'LLEN', 'generation'], capture_output=True, text=True, timeout=5)
        gen_queue_len = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        log(f"Generation queue length: {gen_queue_len}", "INFO")
        
        return len(tasks) > 0
        
    except Exception as e:
        log(f"Celery/Redis error: {e}", "ERROR")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 LLMReady Generation Workflow Test (Production)")
    print("="*60 + "\n")
    
    results = {
        "docker": test_docker(),
        "npx": test_npx(),
        "database": test_generation_database(),
        "celery": test_celery_connectivity(),
        "crawler": False
    }
    
    # Only test crawler if Docker or npx available
    if results["docker"] or results["npx"]:
        results["crawler"] = test_crawler_simple()
    else:
        log("\nSkipping crawler test (no Docker or npx available)", "WARNING")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Generation should work.")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        
        # Provide recommendations
        print("\n💡 Recommendations:")
        if not results["docker"] and not results["npx"]:
            print("  1. Install Docker: sudo /opt/llmready/scripts/install-docker.sh")
            print("     OR")
            print("  2. Install Node.js: sudo apt-get install -y nodejs npm")
        if not results["celery"]:
            print("  3. Restart Celery worker: sudo systemctl restart llmready-celery-worker")
        if not results["database"]:
            print("  4. Check database connection in /opt/llmready/backend/.env")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())