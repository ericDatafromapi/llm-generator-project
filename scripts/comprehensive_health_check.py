#!/usr/bin/env python3
"""
Comprehensive Health Check for Production/Local
Tests all major endpoints and features without modifying data
"""
import requests
import json
import sys
from typing import Dict, List, Tuple

# Configuration
API_BASE_URL = input("Enter API URL (e.g., http://localhost:8000 or https://api.llmready.ai): ").strip()

class HealthChecker:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[Tuple[str, bool, str]] = []
    
    def log(self, message: str, status: str = "INFO"):
        colors = {
            "INFO": "\033[0;36m",
            "SUCCESS": "\033[0;32m",
            "ERROR": "\033[0;31m",
            "WARNING": "\033[1;33m",
        }
        reset = "\033[0m"
        symbol = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(status, "•")
        print(f"{colors.get(status, '')}{symbol} {message}{reset}")
    
    def test(self, name: str, passed: bool, message: str = ""):
        self.results.append((name, passed, message))
        status = "SUCCESS" if passed else "ERROR"
        self.log(f"{name}: {'PASS' if passed else 'FAIL'} {message}", status)
    
    def check_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        self.log("\n1️⃣ Testing Health Endpoint...", "INFO")
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.test("Health Endpoint", True, f"Status: {data.get('status')}")
                return True
            else:
                self.test("Health Endpoint", False, f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.test("Health Endpoint", False, str(e))
            return False
    
    def check_cors(self) -> bool:
        """Test CORS configuration"""
        self.log("\n2️⃣ Testing CORS...", "INFO")
        try:
            r = requests.options(f"{self.base_url}/api/v1/auth/login", 
                               headers={'Origin': 'http://localhost:3000'},
                               timeout=5)
            has_cors = 'access-control-allow-origin' in r.headers
            self.test("CORS Headers", has_cors, 
                     f"CORS: {r.headers.get('access-control-allow-origin', 'Not set')}")
            return has_cors
        except Exception as e:
            self.test("CORS Headers", False, str(e))
            return False
    
    def check_registration_endpoint(self) -> bool:
        """Test registration endpoint (without actually registering)"""
        self.log("\n3️⃣ Testing Registration Endpoint...", "INFO")
        try:
            # Try with invalid data to test endpoint is reachable
            r = requests.post(f"{self.base_url}/api/v1/auth/register",
                            json={"email": "", "password": ""},
                            timeout=5)
            
            # Should return 422 (validation error) not 404 or 500
            if r.status_code == 422:
                self.test("Registration Endpoint", True, "Validation working (422)")
                return True
            elif r.status_code == 400:
                self.test("Registration Endpoint", True, "Endpoint reachable (400)")
                return True
            else:
                self.test("Registration Endpoint", False, f"Unexpected: {r.status_code}")
                return False
        except Exception as e:
            self.test("Registration Endpoint", False, str(e))
            return False
    
    def check_login_endpoint(self) -> bool:
        """Test login endpoint"""
        self.log("\n4️⃣ Testing Login Endpoint...", "INFO")
        try:
            r = requests.post(f"{self.base_url}/api/v1/auth/login",
                            json={"email": "test@test.com", "password": "test"},
                            timeout=5)
            # Should return 401 (invalid credentials) not 404 or 500
            if r.status_code == 401:
                self.test("Login Endpoint", True, "Auth working (401)")
                return True
            else:
                self.test("Login Endpoint", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.test("Login Endpoint", False, str(e))
            return False
    
    def check_subscription_plans(self) -> bool:
        """Test subscription plans endpoint (public)"""
        self.log("\n5️⃣ Testing Subscription Plans...", "INFO")
        try:
            r = requests.get(f"{self.base_url}/api/v1/subscriptions/plans", timeout=5)
            if r.status_code == 200:
                data = r.json()
                plans = data.get('plans', {})
                self.test("Subscription Plans", len(plans) >= 4, 
                         f"Found {len(plans)} plans")
                return len(plans) >= 4
            else:
                self.test("Subscription Plans", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.test("Subscription Plans", False, str(e))
            return False
    
    def check_webhook_endpoint(self) -> bool:
        """Test webhook endpoint is accessible"""
        self.log("\n6️⃣ Testing Webhook Endpoint...", "INFO")
        try:
            r = requests.post(f"{self.base_url}/api/v1/webhooks/stripe",
                            json={}, timeout=5)
            # Should return 400 (missing signature) not 404 or 500
            if r.status_code == 400:
                self.test("Webhook Endpoint", True, "Accessible (400 - missing signature)")
                return True
            else:
                self.test("Webhook Endpoint", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.test("Webhook Endpoint", False, str(e))
            return False
    
    def check_database_connection(self) -> bool:
        """Test database is connected (via health endpoint)"""
        self.log("\n7️⃣ Testing Database Connection...", "INFO")
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                db_status = data.get('database') == 'connected'
                self.test("Database Connection", db_status,
                         f"Database: {data.get('database')}")
                return db_status
            else:
                self.test("Database Connection", False, "Health check failed")
                return False
        except Exception as e:
            self.test("Database Connection", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 HEALTH CHECK SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, p, _ in self.results if p)
        total = len(self.results)
        
        for name, passed_test, msg in self.results:
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{status} - {name}")
            if msg and not passed_test:
                print(f"      {msg}")
        
        print("\n" + "="*60)
        print(f"Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All systems operational!")
            return 0
        else:
            print("⚠️  Some issues detected - review above")
            return 1

def main():
    print("\n" + "="*60)
    print("🏥 LLMReady Comprehensive Health Check")
    print("="*60)
    print(f"Testing: {API_BASE_URL}")
    print("="*60)
    
    checker = HealthChecker(API_BASE_URL)
    
    # Run all checks
    checker.check_health_endpoint()
    checker.check_cors()
    checker.check_registration_endpoint()
    checker.check_login_endpoint()
    checker.check_subscription_plans()
    checker.check_webhook_endpoint()
    checker.check_database_connection()
    
    # Print summary
    return checker.print_summary()

if __name__ == "__main__":
    sys.exit(main())