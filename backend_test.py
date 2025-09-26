#!/usr/bin/env python3
"""
Abod Card Backend API Testing Suite
Tests all API endpoints for the Telegram bot system
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class AbodCardAPITester:
    def __init__(self, base_url="https://telecard-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-Tester/1.0'
        })

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def test_api_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                         data: Dict = None, test_name: str = None) -> tuple:
        """Test a single API endpoint"""
        if not test_name:
            test_name = f"{method} {endpoint}"
            
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=30)
            else:
                self.log_test(test_name, False, f"Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            
            try:
                response_json = response.json()
            except:
                response_json = {"raw_response": response.text[:500]}

            details = f"Status: {response.status_code} (expected {expected_status})"
            if not success:
                details += f", Response: {response.text[:200]}"
                
            self.log_test(test_name, success, details, response_json)
            return success, response_json

        except requests.exceptions.Timeout:
            self.log_test(test_name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(test_name, False, "Connection error - server may be down")
            return False, {}
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False, {}

    def test_products_api(self):
        """Test products API endpoint"""
        print("🔍 Testing Products API...")
        success, data = self.test_api_endpoint('GET', '/products', 200, test_name="Get Products List")
        
        if success and isinstance(data, list):
            self.log_test("Products Response Format", True, f"Returned {len(data)} products")
            
            # Test product structure if products exist
            if len(data) > 0:
                product = data[0]
                required_fields = ['id', 'name', 'description', 'terms', 'is_active', 'created_at']
                missing_fields = [field for field in required_fields if field not in product]
                
                if not missing_fields:
                    self.log_test("Product Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Product Structure Validation", False, f"Missing fields: {missing_fields}")
        elif success:
            self.log_test("Products Response Format", True, "Empty products list returned")
        
        return success

    def test_users_api(self):
        """Test users API endpoint"""
        print("🔍 Testing Users API...")
        success, data = self.test_api_endpoint('GET', '/users', 200, test_name="Get Users List")
        
        if success and isinstance(data, list):
            self.log_test("Users Response Format", True, f"Returned {len(data)} users")
            
            # Test user structure if users exist
            if len(data) > 0:
                user = data[0]
                required_fields = ['id', 'telegram_id', 'balance', 'join_date', 'orders_count']
                missing_fields = [field for field in required_fields if field not in user]
                
                if not missing_fields:
                    self.log_test("User Structure Validation", True, "All required fields present")
                else:
                    self.log_test("User Structure Validation", False, f"Missing fields: {missing_fields}")
        elif success:
            self.log_test("Users Response Format", True, "Empty users list returned")
            
        return success

    def test_orders_api(self):
        """Test orders API endpoint"""
        print("🔍 Testing Orders API...")
        success, data = self.test_api_endpoint('GET', '/orders', 200, test_name="Get Orders List")
        
        if success and isinstance(data, list):
            self.log_test("Orders Response Format", True, f"Returned {len(data)} orders")
            
            # Test order structure if orders exist
            if len(data) > 0:
                order = data[0]
                required_fields = ['id', 'user_id', 'telegram_id', 'product_name', 'category_name', 'price', 'status', 'order_date']
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_test("Order Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Order Structure Validation", False, f"Missing fields: {missing_fields}")
                    
                # Test order status values
                valid_statuses = ['pending', 'completed', 'failed']
                if order.get('status') in valid_statuses:
                    self.log_test("Order Status Validation", True, f"Valid status: {order.get('status')}")
                else:
                    self.log_test("Order Status Validation", False, f"Invalid status: {order.get('status')}")
        elif success:
            self.log_test("Orders Response Format", True, "Empty orders list returned")
            
        return success

    def test_webhooks_setup(self):
        """Test webhook setup endpoint"""
        print("🔍 Testing Webhook Setup...")
        success, data = self.test_api_endpoint('POST', '/set-webhooks', 200, test_name="Setup Webhooks")
        
        if success:
            if isinstance(data, dict) and data.get('status') == 'success':
                self.log_test("Webhook Setup Response", True, "Webhooks configured successfully")
            else:
                self.log_test("Webhook Setup Response", False, f"Unexpected response format: {data}")
        
        return success

    def test_webhook_endpoints(self):
        """Test webhook endpoints (should return 403 without proper secret)"""
        print("🔍 Testing Webhook Security...")
        
        # Test user webhook with wrong secret
        success, data = self.test_api_endpoint('POST', '/webhook/user/wrong_secret', 403, 
                                             {"test": "data"}, "User Webhook Security")
        
        # Test admin webhook with wrong secret  
        success2, data2 = self.test_api_endpoint('POST', '/webhook/admin/wrong_secret', 403,
                                               {"test": "data"}, "Admin Webhook Security")
        
        return success and success2

    def test_cors_headers(self):
        """Test CORS configuration"""
        print("🔍 Testing CORS Configuration...")
        
        try:
            # Make an OPTIONS request to check CORS headers
            response = self.session.options(f"{self.api_url}/products", timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                self.log_test("CORS Headers Present", True, f"CORS configured: {cors_headers}")
                return True
            else:
                self.log_test("CORS Headers Present", False, "No CORS headers found")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers Test", False, f"Error testing CORS: {str(e)}")
            return False

    def test_server_health(self):
        """Test basic server connectivity"""
        print("🔍 Testing Server Health...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code in [200, 404]:  # 404 is OK for root path
                self.log_test("Server Connectivity", True, f"Server responding (status: {response.status_code})")
                return True
            else:
                self.log_test("Server Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Cannot connect to server: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Abod Card Backend API Tests")
        print("=" * 50)
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Run all API tests
        self.test_products_api()
        self.test_users_api() 
        self.test_orders_api()
        self.test_webhooks_setup()
        self.test_webhook_endpoints()
        self.test_cors_headers()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print("\n" + "=" * 50)
        
        # Return results for further processing
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = AbodCardAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())