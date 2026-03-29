#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class KelikaAPITester:
    def __init__(self, base_url="https://tenant-cloud-builder.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test data
        self.admin_credentials = {
            "email": "admin@kelika.com",
            "password": "admin123"
        }
        
        # Test counters
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Store created resources for cleanup
        self.created_tenant_id = None
        self.created_venue_id = None
        self.created_court_id = None
        self.created_booking_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"name": name, "details": details})

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, auth_required: bool = True) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if not success:
                response_data["status_code"] = response.status_code
                response_data["expected_status"] = expected_status
            
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e)}

    def test_auth_login(self):
        """Test super admin login"""
        print("\n🔐 Testing Authentication...")
        
        success, response = self.make_request(
            "POST", "auth/login", 
            self.admin_credentials, 
            expected_status=200,
            auth_required=False
        )
        
        if success and "id" in response:
            self.log_test("Super Admin Login", True, f"Logged in as {response.get('email')}")
            return True
        else:
            self.log_test("Super Admin Login", False, f"Response: {response}")
            return False

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.make_request("GET", "auth/me")
        
        if success and response.get("role") == "super_admin":
            self.log_test("Get Current User", True, f"Role: {response.get('role')}")
            return True
        else:
            self.log_test("Get Current User", False, f"Response: {response}")
            return False

    def test_create_tenant(self):
        """Test tenant creation"""
        print("\n🏢 Testing Tenant Management...")
        
        tenant_data = {
            "business_name": f"Test Sports Center {datetime.now().strftime('%H%M%S')}",
            "admin_email": f"admin{datetime.now().strftime('%H%M%S')}@testsports.com",
            "admin_password": "TestPass123!",
            "admin_name": "Test Admin",
            "subdomain": f"testsports{datetime.now().strftime('%H%M%S')}",
            "timezone": "UTC",
            "currency": "USD"
        }
        
        success, response = self.make_request(
            "POST", "tenants", 
            tenant_data, 
            expected_status=200
        )
        
        if success and "id" in response:
            self.created_tenant_id = response["id"]
            self.log_test("Create Tenant", True, f"Created tenant: {response.get('business_name')}")
            return True
        else:
            self.log_test("Create Tenant", False, f"Response: {response}")
            return False

    def test_get_tenants(self):
        """Test get tenants list"""
        success, response = self.make_request("GET", "tenants")
        
        if success and isinstance(response, list):
            self.log_test("Get Tenants List", True, f"Found {len(response)} tenants")
            return True
        else:
            self.log_test("Get Tenants List", False, f"Response: {response}")
            return False

    def test_create_venue(self):
        """Test venue creation"""
        print("\n🏟️ Testing Venue Management...")
        
        if not self.created_tenant_id:
            self.log_test("Create Venue", False, "No tenant ID available")
            return False
        
        venue_data = {
            "name": f"Test Arena {datetime.now().strftime('%H%M%S')}",
            "description": "A test sports arena for automated testing",
            "address": "123 Test Street, Test City, TC 12345",
            "image_url": "https://images.unsplash.com/photo-1765124540460-b884e248ac2b"
        }
        
        success, response = self.make_request(
            "POST", "venues", 
            venue_data, 
            expected_status=200
        )
        
        if success and "id" in response:
            self.created_venue_id = response["id"]
            self.log_test("Create Venue", True, f"Created venue: {response.get('name')}")
            return True
        else:
            self.log_test("Create Venue", False, f"Response: {response}")
            return False

    def test_get_venues(self):
        """Test get venues list"""
        success, response = self.make_request("GET", "venues")
        
        if success and isinstance(response, list):
            self.log_test("Get Venues List", True, f"Found {len(response)} venues")
            return True
        else:
            self.log_test("Get Venues List", False, f"Response: {response}")
            return False

    def test_create_court(self):
        """Test court creation"""
        print("\n🎾 Testing Court Management...")
        
        if not self.created_venue_id:
            self.log_test("Create Court", False, "No venue ID available")
            return False
        
        court_data = {
            "venue_id": self.created_venue_id,
            "name": f"Test Court {datetime.now().strftime('%H%M%S')}",
            "sport_type": "Tennis",
            "capacity": 4,
            "indoor": True
        }
        
        success, response = self.make_request(
            "POST", "courts", 
            court_data, 
            expected_status=200
        )
        
        if success and "id" in response:
            self.created_court_id = response["id"]
            self.log_test("Create Court", True, f"Created court: {response.get('name')}")
            return True
        else:
            self.log_test("Create Court", False, f"Response: {response}")
            return False

    def test_get_courts(self):
        """Test get courts list"""
        success, response = self.make_request("GET", "courts")
        
        if success and isinstance(response, list):
            self.log_test("Get Courts List", True, f"Found {len(response)} courts")
            return True
        else:
            self.log_test("Get Courts List", False, f"Response: {response}")
            return False

    def test_create_pricing_rule(self):
        """Test pricing rule creation"""
        print("\n💰 Testing Pricing Management...")
        
        if not self.created_court_id:
            self.log_test("Create Pricing Rule", False, "No court ID available")
            return False
        
        pricing_data = {
            "court_id": self.created_court_id,
            "rule_type": "hourly",
            "price": 50.0,
            "start_time": "09:00",
            "end_time": "17:00",
            "days_of_week": [1, 2, 3, 4, 5]  # Monday to Friday
        }
        
        success, response = self.make_request(
            "POST", "pricing", 
            pricing_data, 
            expected_status=200
        )
        
        if success and "id" in response:
            self.log_test("Create Pricing Rule", True, f"Created pricing rule: ${response.get('price')}/hour")
            return True
        else:
            self.log_test("Create Pricing Rule", False, f"Response: {response}")
            return False

    def test_get_pricing_rules(self):
        """Test get pricing rules"""
        success, response = self.make_request("GET", "pricing")
        
        if success and isinstance(response, list):
            self.log_test("Get Pricing Rules", True, f"Found {len(response)} pricing rules")
            return True
        else:
            self.log_test("Get Pricing Rules", False, f"Response: {response}")
            return False

    def test_create_booking(self):
        """Test booking creation"""
        print("\n📅 Testing Booking Management...")
        
        if not self.created_court_id:
            self.log_test("Create Booking", False, "No court ID available")
            return False
        
        booking_data = {
            "court_id": self.created_court_id,
            "customer_email": "testcustomer@example.com",
            "customer_name": "Test Customer",
            "customer_phone": "+1234567890",
            "date": "2026-02-15",
            "start_time": "10:00",
            "end_time": "11:00",
            "total_price": 50.0
        }
        
        success, response = self.make_request(
            "POST", "bookings", 
            booking_data, 
            expected_status=200,
            auth_required=False  # Booking endpoint doesn't require auth
        )
        
        if success and "id" in response:
            self.created_booking_id = response["id"]
            self.log_test("Create Booking", True, f"Created booking for {response.get('customer_name')}")
            return True
        else:
            self.log_test("Create Booking", False, f"Response: {response}")
            return False

    def test_get_bookings(self):
        """Test get bookings list"""
        success, response = self.make_request("GET", "bookings")
        
        if success and isinstance(response, list):
            self.log_test("Get Bookings List", True, f"Found {len(response)} bookings")
            return True
        else:
            self.log_test("Get Bookings List", False, f"Response: {response}")
            return False

    def test_create_customer(self):
        """Test customer creation"""
        print("\n👥 Testing Customer Management...")
        
        if not self.created_tenant_id:
            self.log_test("Create Customer", False, "No tenant ID available")
            return False
        
        customer_data = {
            "tenant_id": self.created_tenant_id,
            "email": f"customer{datetime.now().strftime('%H%M%S')}@example.com",
            "name": "Test Customer",
            "phone": "+1234567890"
        }
        
        success, response = self.make_request(
            "POST", "customers", 
            customer_data, 
            expected_status=200
        )
        
        if success and "id" in response:
            self.log_test("Create Customer", True, f"Created customer: {response.get('name')}")
            return True
        else:
            self.log_test("Create Customer", False, f"Response: {response}")
            return False

    def test_get_customers(self):
        """Test get customers list"""
        success, response = self.make_request("GET", "customers")
        
        if success and isinstance(response, list):
            self.log_test("Get Customers List", True, f"Found {len(response)} customers")
            return True
        else:
            self.log_test("Get Customers List", False, f"Response: {response}")
            return False

    def test_analytics_dashboard(self):
        """Test analytics dashboard"""
        print("\n📊 Testing Analytics...")
        
        success, response = self.make_request("GET", "analytics/dashboard")
        
        expected_keys = ["total_bookings", "total_venues", "total_customers", "total_revenue"]
        if success and all(key in response for key in expected_keys):
            self.log_test("Analytics Dashboard", True, 
                         f"Revenue: ${response.get('total_revenue', 0)}, "
                         f"Bookings: {response.get('total_bookings', 0)}")
            return True
        else:
            self.log_test("Analytics Dashboard", False, f"Response: {response}")
            return False

    def test_qr_code_generation(self):
        """Test QR code generation"""
        print("\n📱 Testing QR Code Generation...")
        
        if not self.created_venue_id:
            self.log_test("QR Code Generation", False, "No venue ID available")
            return False
        
        success, response = self.make_request("GET", f"qr-code/{self.created_venue_id}")
        
        if success and "qr_code" in response and "booking_url" in response:
            self.log_test("QR Code Generation", True, f"Generated QR for venue")
            return True
        else:
            self.log_test("QR Code Generation", False, f"Response: {response}")
            return False

    def test_payment_checkout(self):
        """Test payment checkout session creation"""
        print("\n💳 Testing Payment Integration...")
        
        if not self.created_booking_id:
            self.log_test("Payment Checkout", False, "No booking ID available")
            return False
        
        checkout_data = {
            "booking_id": self.created_booking_id,
            "origin_url": self.base_url
        }
        
        success, response = self.make_request(
            "POST", "payments/checkout", 
            checkout_data, 
            expected_status=200
        )
        
        if success and "url" in response and "session_id" in response:
            self.log_test("Payment Checkout", True, f"Created checkout session")
            return True
        else:
            self.log_test("Payment Checkout", False, f"Response: {response}")
            return False

    def test_auth_logout(self):
        """Test logout"""
        print("\n🚪 Testing Logout...")
        
        success, response = self.make_request(
            "POST", "auth/logout", 
            expected_status=200
        )
        
        if success:
            self.log_test("Logout", True, "Successfully logged out")
            return True
        else:
            self.log_test("Logout", False, f"Response: {response}")
            return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Kelika API Test Suite")
        print("=" * 50)
        
        # Authentication tests
        if not self.test_auth_login():
            print("❌ Authentication failed - stopping tests")
            return False
        
        self.test_auth_me()
        
        # Core functionality tests
        self.test_create_tenant()
        self.test_get_tenants()
        
        self.test_create_venue()
        self.test_get_venues()
        
        self.test_create_court()
        self.test_get_courts()
        
        self.test_create_pricing_rule()
        self.test_get_pricing_rules()
        
        self.test_create_booking()
        self.test_get_bookings()
        
        self.test_create_customer()
        self.test_get_customers()
        
        # Analytics and additional features
        self.test_analytics_dashboard()
        self.test_qr_code_generation()
        self.test_payment_checkout()
        
        # Cleanup
        self.test_auth_logout()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = KelikaAPITester()
    
    try:
        tester.run_all_tests()
        success = tester.print_summary()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())