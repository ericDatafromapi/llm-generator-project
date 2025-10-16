#!/usr/bin/env python3
"""
Production Testing Script - Test workflows in production environment
Tests: Registration, Login, Subscription, and Generation workflows
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional

# Configuration
API_BASE_URL = "https://api.llmready.ai"  # Update with your actual API URL
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"

class ProductionTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def log(self, message: str, status: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "RUNNING": "🔄"
        }
        symbol = symbols.get(status, "•")
        print(f"[{timestamp}] {symbol} {message}")
    
    def test_health_check(self) -> bool:
        """Test API health endpoint"""
        self.log("Testing API health check...", "RUNNING")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log(f"Health check passed: {data}", "SUCCESS")
                return True
            else:
                self.log(f"Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Health check error: {e}", "ERROR")
            return False
    
    def test_registration(self) -> bool:
        """Test user registration"""
        self.log(f"Testing registration with email: {TEST_EMAIL}", "RUNNING")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "full_name": TEST_NAME
                }
            )
            
            self.log(f"Registration response status: {response.status_code}")
            self.log(f"Registration response: {response.text}")
            
            if response.status_code == 201:
                data = response.json()
                
                # Check if tokens are returned
                if 'access_token' in data and 'refresh_token' in data:
                    self.access_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    self.user_id = data.get('user', {}).get('id')
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                    self.log("Registration successful with tokens", "SUCCESS")
                    return True
                else:
                    self.log("Registration succeeded but NO TOKENS returned - BUG FOUND!", "WARNING")
                    self.log(f"Response keys: {data.keys()}", "WARNING")
                    # Try to login instead
                    return self.test_login()
            else:
                self.log(f"Registration failed: {response.json()}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Registration error: {e}", "ERROR")
            return False
    
    def test_login(self) -> bool:
        """Test user login"""
        self.log(f"Testing login with email: {TEST_EMAIL}", "RUNNING")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
                self.user_id = data.get('user', {}).get('id')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.log("Login successful", "SUCCESS")
                return True
            else:
                self.log(f"Login failed: {response.json()}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Login error: {e}", "ERROR")
            return False
    
    def test_get_subscription(self) -> bool:
        """Test getting current subscription"""
        self.log("Testing get current subscription...", "RUNNING")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/subscriptions/current")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Current plan: {data.get('plan_type')}", "SUCCESS")
                self.log(f"Status: {data.get('status')}", "INFO")
                self.log(f"Generations: {data.get('generations_used')}/{data.get('generations_limit')}", "INFO")
                return True
            else:
                self.log(f"Get subscription failed: {response.json()}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Get subscription error: {e}", "ERROR")
            return False
    
    def test_celery_status(self) -> bool:
        """Test if Celery tasks are registered"""
        self.log("Checking Celery task registration...", "RUNNING")
        self.log("Run this command on server:", "INFO")
        self.log("cd /opt/llmready/backend && python -c \"from app.core.celery_app import celery_app; print('Tasks:', [t for t in celery_app.tasks.keys() if 'app.' in t])\"", "INFO")
        return True
    
    def test_create_website(self) -> Optional[str]:
        """Test creating a website"""
        self.log("Testing create website...", "RUNNING")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/websites",
                json={
                    "name": "Test Website",
                    "url": "https://example.com",
                    "description": "Test website for production testing"
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                website_id = data.get('id')
                self.log(f"Website created: {website_id}", "SUCCESS")
                return website_id
            else:
                self.log(f"Create website failed: {response.json()}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Create website error: {e}", "ERROR")
            return None
    
    def test_create_generation(self, website_id: str) -> Optional[str]:
        """Test creating a generation"""
        self.log(f"Testing create generation for website {website_id}...", "RUNNING")
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/generations",
                json={
                    "website_id": website_id
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                generation_id = data.get('id')
                self.log(f"Generation created: {generation_id}", "SUCCESS")
                self.log(f"Status: {data.get('status')}", "INFO")
                return generation_id
            else:
                self.log(f"Create generation failed: {response.json()}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Create generation error: {e}", "ERROR")
            return None
    
    def run_all_tests(self):
        """Run all production tests"""
        self.log("=" * 60)
        self.log("PRODUCTION TESTING SUITE")
        self.log("=" * 60)
        
        results = {
            "health_check": False,
            "registration": False,
            "subscription": False,
            "website_creation": False,
            "generation_creation": False
        }
        
        # 1. Health check
        results["health_check"] = self.test_health_check()
        if not results["health_check"]:
            self.log("Health check failed, aborting tests", "ERROR")
            return results
        
        time.sleep(1)
        
        # 2. Registration
        results["registration"] = self.test_registration()
        if not results["registration"]:
            self.log("Registration failed, aborting tests", "ERROR")
            return results
        
        time.sleep(1)
        
        # 3. Get subscription
        results["subscription"] = self.test_get_subscription()
        
        time.sleep(1)
        
        # 4. Create website
        website_id = self.test_create_website()
        results["website_creation"] = website_id is not None
        
        if website_id:
            time.sleep(1)
            
            # 5. Create generation
            generation_id = self.test_create_generation(website_id)
            results["generation_creation"] = generation_id is not None
        
        # Summary
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        for test_name, passed in results.items():
            status = "SUCCESS" if passed else "ERROR"
            self.log(f"{test_name}: {'PASSED' if passed else 'FAILED'}", status)
        
        return results

def main():
    """Main entry point"""
    import sys
    
    # Allow custom API URL
    api_url = sys.argv[1] if len(sys.argv) > 1 else API_BASE_URL
    
    tester = ProductionTester(api_url)
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()