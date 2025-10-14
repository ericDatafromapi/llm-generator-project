#!/usr/bin/env python3
"""
Complete End-to-End Testing Script for LLMReady
Tests the entire user journey from registration to generation download.
"""
import requests
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Test user credentials
TEST_EMAIL = f"test_user_{int(time.time())}@yopmail.com"
TEST_PASSWORD = "SecureTestPass123!"
TEST_NAME = "Test User"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(step_num, message):
    """Print a test step with formatting."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}STEP {step_num}: {message}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}❌ {message}{RESET}")


def print_info(message):
    """Print info message."""
    print(f"{YELLOW}ℹ️  {message}{RESET}")


def print_json(data, title="Response"):
    """Print JSON data with formatting."""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))


def wait_for_user(message="Press Enter to continue..."):
    """Pause for user input."""
    input(f"\n{YELLOW}⏸️  {message}{RESET}")


def check_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("API is healthy and running")
            print_json(response.json(), "Health Check")
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is FastAPI running?")
        print_info("Start FastAPI with: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def check_stripe_cli():
    """Check if Stripe CLI is installed and available."""
    print_info("Checking for Stripe CLI...")
    try:
        result = os.popen("stripe --version").read()
        if result:
            print_success(f"Stripe CLI found: {result.strip()}")
            return True
        else:
            print_error("Stripe CLI not found")
            return False
    except Exception as e:
        print_error(f"Error checking Stripe CLI: {e}")
        return False


def check_webhook_listener():
    """Check if Stripe webhook listener might be running."""
    print_info("Checking for webhook listener...")
    try:
        # Check if stripe listen process is running
        result = os.popen("ps aux | grep 'stripe listen' | grep -v grep").read()
        if result:
            print_success("Stripe webhook listener appears to be running")
            print_info("Process: " + result.strip()[:100] + "...")
            return True
        else:
            print_error("Stripe webhook listener not detected")
            return False
    except Exception as e:
        print_error(f"Error checking webhook listener: {e}")
        return False


def check_celery_worker():
    """Check if Celery worker is running."""
    print_info("Checking for Celery worker...")
    try:
        # Check if celery worker process is running
        result = os.popen("ps aux | grep 'celery' | grep 'worker' | grep -v grep").read()
        if result:
            print_success("Celery worker appears to be running")
            print_info("Process: " + result.strip()[:100] + "...")
            return True
        else:
            print_error("Celery worker not detected")
            return False
    except Exception as e:
        print_error(f"Error checking Celery worker: {e}")
        return False


def check_redis_connection():
    """Check if Redis is accessible."""
    print_info("Checking Redis connection...")
    try:
        # Try docker exec first (for Docker Redis)
        result = os.popen("docker exec llmready_redis redis-cli ping 2>/dev/null").read().strip()
        if result == "PONG":
            print_success("Redis is running and accessible (Docker)")
            return True
        
        # Fallback to direct redis-cli (for local Redis)
        result = os.popen("redis-cli ping 2>/dev/null").read().strip()
        if result == "PONG":
            print_success("Redis is running and accessible (Local)")
            return True
        
        print_error("Redis is not responding")
        return False
    except Exception as e:
        print_error(f"Error checking Redis: {e}")
        return False


def test_registration():
    """Test user registration."""
    print_step(1, "USER REGISTRATION")
    
    print_info(f"Registering user: {TEST_EMAIL}")
    
    response = requests.post(
        f"{API_V1}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
    )
    
    if response.status_code == 201:
        print_success(f"User registered successfully!")
        data = response.json()
        print_json(data, "Registration Response")
        return data  # API returns user directly, not wrapped in "user" key
    else:
        print_error(f"Registration failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def test_login():
    """Test user login."""
    print_step(2, "USER LOGIN")
    
    print_info("Logging in...")
    
    response = requests.post(
        f"{API_V1}/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        print_success("Login successful!")
        data = response.json()
        print_json(data, "Login Response")
        return data.get("access_token")
    else:
        print_error(f"Login failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def test_subscription_checkout(token):
    """Test subscription checkout session creation."""
    print_step(3, "CREATE SUBSCRIPTION CHECKOUT")
    
    print_info("Creating checkout session for Standard plan (€29/month)...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_V1}/subscriptions/checkout",
        headers=headers,
        json={
            "plan_type": "standard",
            "success_url": "http://localhost:3000/dashboard?success=true",
            "cancel_url": "http://localhost:3000/pricing?canceled=true"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        checkout_url = data.get("checkout_url")
        print_success("Checkout session created!")
        print_json(data, "Checkout Response")
        
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}CHECKOUT URL:{RESET}")
        print(f"{BLUE}{checkout_url}{RESET}")
        print(f"{GREEN}{'='*80}{RESET}")
        
        print(f"\n{YELLOW}📝 MANUAL STEP REQUIRED:{RESET}")
        print("1. Copy the checkout URL above")
        print("2. Open it in your browser")
        print("3. Use test card: 4242 4242 4242 4242")
        print("4. Any future expiry date, any CVC, any ZIP")
        print("5. Complete the checkout")
        
        wait_for_user("After completing checkout, press Enter to continue")
        return True
    else:
        print_error(f"Checkout creation failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return False


def verify_subscription(token):
    """Verify subscription was activated."""
    print_step(4, "VERIFY SUBSCRIPTION")
    
    print_info("Checking subscription status...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_V1}/subscriptions/current",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Subscription retrieved successfully!")
        print_json(data, "Subscription Info")
        
        # Check if webhook was processed
        if data.get("stripe_subscription_id") is None:
            print_error("⚠️  WEBHOOK NOT PROCESSED!")
            print_error("The checkout completed but the webhook wasn't received.")
            print("\n" + "="*80)
            print(f"{YELLOW}WEBHOOK TROUBLESHOOTING:{RESET}")
            print("1. Is Stripe CLI running?")
            print("   Run: stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe")
            print("\n2. Check terminal for webhook logs")
            print("\n3. Or manually trigger the webhook:")
            print(f"   stripe trigger checkout.session.completed")
            print("="*80 + "\n")
            
            choice = input(f"{YELLOW}After fixing webhooks, press Enter to retry (or 'skip' to continue anyway): {RESET}").strip().lower()
            if choice != 'skip':
                # Retry verification
                return verify_subscription(token)
            else:
                print_info("Continuing with free plan for testing...")
                return data
        
        # Verify it's the standard plan
        if data.get("plan_type") == "standard":
            print_success("✅ Plan type is correct: Standard")
        else:
            print_error(f"Expected 'standard' plan, got '{data.get('plan_type')}'")
        
        if data.get("status") == "active":
            print_success("✅ Status is active")
        else:
            print_error(f"Expected 'active' status, got '{data.get('status')}'")
        
        if data.get("generations_limit") == 10:
            print_success("✅ Generation limit is correct: 10")
        else:
            print_error(f"Expected 10 generations, got {data.get('generations_limit')}")
        
        return data
    else:
        print_error(f"Subscription verification failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def create_test_website(token):
    """Create a test website for generation."""
    print_step(5, "CREATE TEST WEBSITE")
    
    print_info("Creating a test website...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First check if we need a website endpoint - we might need to create this
    # For now, let's directly insert via database or ask user
    print_info("Note: Website CRUD endpoints will be implemented in Week 7")
    print_info("For this test, we'll use a manual approach")
    
    print(f"\n{YELLOW}📝 MANUAL STEP:{RESET}")
    print("We need to create a test website in the database.")
    print("You can either:")
    print("1. Create a website record manually in the database")
    print("2. Or we can skip website creation and test with an existing website_id")
    
    choice = input(f"\n{YELLOW}Do you have a website_id to test with? (yes/no): {RESET}").strip().lower()
    
    if choice == 'yes':
        website_id = input(f"{YELLOW}Enter the website_id (UUID): {RESET}").strip()
        print_success(f"Using website_id: {website_id}")
        return website_id
    else:
        print_info("Let's create a website via database directly...")
        print("""
Run this SQL in your PostgreSQL database:

INSERT INTO websites (id, user_id, url, name, max_pages, timeout, is_active, use_playwright, generation_count, created_at, updated_at)
SELECT
    gen_random_uuid(),
    id,
    'https://example.com',
    'Example.com Test Site',
    10,
    300,
    1,
    0,
    0,
    NOW(),
    NOW()
FROM users
WHERE email = '{email}'
RETURNING id;
        """.format(email=TEST_EMAIL))
        
        website_id = input(f"\n{YELLOW}Enter the website_id from the query result: {RESET}").strip()
        return website_id


def test_generation_quota_check(token):
    """Check generation quota before starting."""
    print_step(6, "CHECK GENERATION QUOTA")
    
    print_info("Checking available quota...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_V1}/generations/quota/check",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Quota check successful!")
        print_json(data, "Quota Status")
        
        if data.get("can_generate"):
            print_success(f"✅ Can generate! {data.get('remaining_generations')} generations remaining")
        else:
            print_error("❌ Cannot generate - quota exceeded")
        
        return data
    else:
        print_error(f"Quota check failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def test_start_generation(token, website_id, generation_num=1):
    """Start a generation."""
    print_step(f"7.{generation_num}", f"START GENERATION #{generation_num}")
    
    print_info(f"Starting generation for website {website_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_V1}/generations/start",
        headers=headers,
        json={"website_id": website_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        generation_id = data.get("generation_id")
        print_success(f"Generation started! ID: {generation_id}")
        print_json(data, "Generation Start Response")
        return generation_id
    else:
        print_error(f"Generation start failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def test_generation_status(token, generation_id):
    """Check generation status."""
    print_info(f"Checking status of generation {generation_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_V1}/generations/{generation_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        progress = data.get("progress_percentage", 0)
        
        print(f"Status: {status} ({progress}%)")
        return data
    else:
        print_error(f"Status check failed: {response.status_code}")
        return None


def wait_for_generation_completion(token, generation_id, max_wait=600):
    """Poll generation status until complete or timeout."""
    print_step(8, "WAIT FOR GENERATION COMPLETION")
    
    print_info(f"Polling generation status (max {max_wait}s)...")
    print_info("Note: First generation may take longer as Docker pulls the Mdream image")
    
    start_time = time.time()
    last_status = None
    stuck_counter = 0  # Count how long we've been stuck in pending
    
    while (time.time() - start_time) < max_wait:
        data = test_generation_status(token, generation_id)
        
        if not data:
            time.sleep(5)
            continue
        
        status = data.get("status")
        progress = data.get("progress_percentage", 0)
        
        if status != last_status:
            print(f"  Status changed: {last_status} → {status} ({progress}%)")
            last_status = status
            stuck_counter = 0  # Reset stuck counter on status change
        
        if status == "completed":
            duration = data.get("duration_seconds")
            total_files = data.get("total_files", 0)
            print_success(f"Generation completed in {duration:.1f}s!")
            print_success(f"Generated {total_files} files")
            print_json(data, "Final Status")
            return True
        
        elif status == "failed":
            error = data.get("error_message", "Unknown error")
            print_error(f"Generation failed: {error}")
            print_json(data, "Error Details")
            return False
        
        elif status == "pending":
            stuck_counter += 1
            
            # If stuck in pending for 60 seconds (12 iterations * 5s), show warning
            if stuck_counter == 12:
                print(f"\n{YELLOW}⚠️  Task stuck in 'pending' for 60 seconds!{RESET}")
                print(f"\n{YELLOW}This usually means Celery worker is not picking up tasks.{RESET}")
                print(f"\n{YELLOW}TROUBLESHOOTING:{RESET}")
                print("1. Check Celery worker terminal - do you see task logs?")
                print("2. Restart Celery worker:")
                print(f"   {BLUE}pkill -9 celery{RESET}")
                print(f"   {BLUE}cd backend && source .venv/bin/activate{RESET}")
                print(f"   {BLUE}celery -A app.core.celery_app worker --loglevel=info --purge{RESET}")
                print("3. Clear Redis queue:")
                print(f"   {BLUE}redis-cli FLUSHDB{RESET}")
                print(f"\nSee: {BLUE}backend/CELERY_TROUBLESHOOTING.md{RESET} for details\n")
                
                choice = input(f"{YELLOW}Continue waiting? (yes/no): {RESET}").strip().lower()
                if choice != 'yes':
                    print_error("Stopping test - Celery worker issue")
                    return False
                stuck_counter = 0  # Reset counter if user wants to continue
            
            print(f"  {status.capitalize()}... {progress}%", end='\r')
            time.sleep(5)
        
        elif status == "processing":
            print(f"  {status.capitalize()}... {progress}%", end='\r')
            time.sleep(5)
        
        else:
            print_info(f"Unexpected status: {status}")
            time.sleep(5)
    
    print_error(f"Timeout after {max_wait}s")
    print_error("Task never completed - likely Celery worker issue")
    print_info(f"See: backend/CELERY_TROUBLESHOOTING.md for debugging steps")
    return False


def test_file_download(token, generation_id):
    """Test file download and verify contents."""
    print_step(9, "TEST FILE DOWNLOAD")
    
    print_info(f"Downloading generation {generation_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_V1}/generations/{generation_id}/download",
        headers=headers,
        stream=True
    )
    
    if response.status_code == 200:
        # Save to downloads folder
        downloads_dir = Path.home() / "Downloads"
        filename = f"llmready_test_{generation_id}.zip"
        filepath = downloads_dir / filename
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = filepath.stat().st_size
        print_success(f"File downloaded successfully!")
        print_info(f"Location: {filepath}")
        print_info(f"Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Try to list zip contents
        try:
            import zipfile
            with zipfile.ZipFile(filepath, 'r') as zf:
                files = zf.namelist()
                print_success(f"ZIP contains {len(files)} files:")
                for f in files[:10]:  # Show first 10
                    print(f"  - {f}")
                if len(files) > 10:
                    print(f"  ... and {len(files) - 10} more")
        except Exception as e:
            print_error(f"Could not read ZIP contents: {e}")
        
        return filepath
    else:
        print_error(f"Download failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def test_generation_history(token):
    """Test generation history endpoint."""
    print_step(10, "CHECK GENERATION HISTORY")
    
    print_info("Fetching generation history...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_V1}/generations/history?page=1&per_page=10",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        items = data.get("items", [])
        
        print_success(f"Found {total} total generation(s)")
        print_json(data, "History Response")
        
        return items
    else:
        print_error(f"History check failed: {response.status_code}")
        print_json(response.json(), "Error Response")
        return None


def verify_database_data():
    """Verify data in database."""
    print_step(11, "VERIFY DATABASE DATA")
    
    print_info("Checking database directly...")
    
    try:
        # Database query commands
        queries = [
            ("User record", f"SELECT id, email, full_name, is_active, is_verified FROM users WHERE email = '{TEST_EMAIL}';"),
            ("Subscription", f"SELECT plan_type, status, generations_used, generations_limit FROM subscriptions WHERE user_id = (SELECT id FROM users WHERE email = '{TEST_EMAIL}');"),
            ("Websites", f"SELECT id, url, name FROM websites WHERE user_id = (SELECT id FROM users WHERE email = '{TEST_EMAIL}');"),
            ("Generations", f"SELECT id, status, total_files, file_size FROM generations WHERE user_id = (SELECT id FROM users WHERE email = '{TEST_EMAIL}');"),
        ]
        
        print(f"\n{YELLOW}Run these PostgreSQL queries to verify data:{RESET}\n")
        
        for title, query in queries:
            print(f"{BLUE}{title}:{RESET}")
            print(f"docker exec llmready_postgres psql -U postgres -d llmready_dev -c \"{query}\"")
            print()
        
        wait_for_user("After checking the database, press Enter to continue")
        
        return True
        
    except Exception as e:
        print_error(f"Database verification setup failed: {e}")
        return False


def check_file_storage():
    """Check if files are stored correctly."""
    print_step(12, "CHECK FILE STORAGE")
    
    print_info("Checking file storage directory...")
    
    # Use relative path from backend directory
    storage_path = Path("storage/files")
    
    if not storage_path.exists():
        print_error(f"Storage directory does not exist: {storage_path}")
        print_info("Create it with: mkdir -p backend/storage/files")
        return False
    
    # List files
    files = list(storage_path.glob("*.zip"))
    
    print_success(f"Storage directory exists: {storage_path.absolute()}")
    print_info(f"Found {len(files)} ZIP file(s)")
    
    for f in files:
        size = f.stat().st_size
        modified = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"  - {f.name}: {size:,} bytes ({size/1024:.1f} KB), modified {modified}")
    
    return True


def run_complete_test():
    """Run the complete end-to-end test."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🧪 LLMReady Complete End-to-End Test{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"\nTest User: {TEST_EMAIL}")
    print(f"Base URL: {BASE_URL}")
    print(f"Start Time: {datetime.now()}")
    
    # Step 0: Health check
    print_step(0, "API HEALTH CHECK")
    if not check_health():
        print_error("Cannot proceed - API is not running")
        return False
    
    # Step 1: Registration
    user_data = test_registration()
    if not user_data:
        print_error("Cannot proceed - registration failed")
        return False
    
    user_id = user_data.get("id")
    print_info(f"User ID: {user_id}")
    
    # Step 2: Login
    token = test_login()
    if not token:
        print_error("Cannot proceed - login failed")
        return False
    
    print_info(f"Access Token: {token[:20]}...")
    
    # Step 3: Create checkout session
    if not test_subscription_checkout(token):
        print_error("Cannot proceed - checkout creation failed")
        return False
    
    # Step 4: Verify subscription (after manual checkout completion)
    subscription_data = verify_subscription(token)
    if not subscription_data:
        print_error("Cannot proceed - subscription not found")
        print_info("Make sure you completed the Stripe checkout!")
        return False
    
    # Step 5: Create/get test website
    website_id = create_test_website(token)
    if not website_id:
        print_error("Cannot proceed - no website available")
        return False
    
    # Step 6: Check quota before generation
    quota_data = test_generation_quota_check(token)
    if not quota_data or not quota_data.get("can_generate"):
        print_error("Cannot proceed - no quota available")
        return False
    
    # Step 7: Start first generation
    generation_id_1 = test_start_generation(token, website_id, 1)
    if not generation_id_1:
        print_error("First generation start failed")
        return False
    
    # Step 8: Wait for completion
    if not wait_for_generation_completion(token, generation_id_1):
        print_error("First generation did not complete successfully")
        return False
    
    # Step 9: Download file
    downloaded_file = test_file_download(token, generation_id_1)
    if not downloaded_file:
        print_error("File download failed")
        return False
    
    # Check quota after first generation
    print_step("7.2", "CHECK QUOTA AFTER GENERATION")
    quota_data = test_generation_quota_check(token)
    if quota_data:
        if quota_data.get("generations_used") == 1:
            print_success("✅ Usage counter incremented correctly!")
        else:
            print_error(f"Expected 1 generation used, got {quota_data.get('generations_used')}")
    
    # Test second generation (optional)
    print(f"\n{YELLOW}Do you want to test a second generation? (yes/no): {RESET}", end='')
    if input().strip().lower() == 'yes':
        generation_id_2 = test_start_generation(token, website_id, 2)
        if generation_id_2:
            if wait_for_generation_completion(token, generation_id_2):
                test_file_download(token, generation_id_2)
                
                # Check quota again
                print_step("7.3", "CHECK QUOTA AFTER 2ND GENERATION")
                test_generation_quota_check(token)
    
    # Step 10: Check history
    history = test_generation_history(token)
    
    # Step 11: Verify database
    verify_database_data()
    
    # Step 12: Check file storage
    check_file_storage()
    
    # Final summary
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}🎉 TEST COMPLETE!{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"\nTest Summary:")
    print(f"  - User: {TEST_EMAIL}")
    print(f"  - User ID: {user_id}")
    print(f"  - Plan: Standard (€29/month)")
    print(f"  - Generations tested: 1-2")
    print(f"  - Downloaded file: {downloaded_file}")
    print(f"  - End Time: {datetime.now()}")
    
    return True


if __name__ == "__main__":
    print(f"\n{BLUE}Starting LLMReady End-to-End Test...{RESET}\n")
    
    # Check prerequisites
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}PREREQUISITES CHECK{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    # Check Stripe CLI
    stripe_cli_ok = check_stripe_cli()
    if not stripe_cli_ok:
        print_error("\nStripe CLI is required for webhook testing!")
        print_info("Install: https://stripe.com/docs/stripe-cli")
        choice = input(f"\n{YELLOW}Continue anyway? (yes/no): {RESET}").strip().lower()
        if choice != 'yes':
            print_error("Exiting - Stripe CLI required")
            sys.exit(1)
    
    # Check webhook listener
    webhook_ok = check_webhook_listener()
    if not webhook_ok:
        print(f"\n{YELLOW}⚠️  Stripe webhook listener is NOT running!{RESET}")
        print(f"\n{YELLOW}To start it, run in a separate terminal:{RESET}")
        print(f"{BLUE}stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe{RESET}\n")
        choice = input(f"{YELLOW}Have you started the webhook listener? (yes/no/skip): {RESET}").strip().lower()
        if choice == 'no':
            print_error("Please start the webhook listener first!")
            sys.exit(1)
        elif choice == 'skip':
            print_info("Continuing without webhook listener - subscription tests may fail")
    
    # Check Redis
    redis_ok = check_redis_connection()
    if not redis_ok:
        print_error("\n❌ Redis is required for Celery tasks!")
        print_info("Start Redis with: docker-compose up -d redis")
        sys.exit(1)
    
    # Check Celery worker
    celery_ok = check_celery_worker()
    if not celery_ok:
        print(f"\n{YELLOW}⚠️  Celery worker is NOT running!{RESET}")
        print(f"\n{YELLOW}To start it, run in a separate terminal:{RESET}")
        print(f"{BLUE}cd backend && source .venv/bin/activate && celery -A app.core.celery_app worker --loglevel=info{RESET}\n")
        choice = input(f"{YELLOW}Have you started the Celery worker? (yes/no): {RESET}").strip().lower()
        if choice == 'no':
            print_error("Celery worker is required for generation tasks!")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("Other required services:")
    print("  - FastAPI running? (will check)")
    print("  - PostgreSQL running? (required)")
    print("  - Redis running? (required)")
    print("  - Celery worker running? (required for generation)")
    print("  - Docker running? (required for Mdream)")
    print("="*80 + "\n")
    
    wait_for_user("Make sure all services are running, then press Enter to start")
    
    try:
        success = run_complete_test()
        
        if success:
            print(f"\n{GREEN}✅ All tests passed!{RESET}")
            sys.exit(0)
        else:
            print(f"\n{RED}❌ Some tests failed{RESET}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)