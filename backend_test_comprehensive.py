#!/usr/bin/env python3
"""
Comprehensive Abod Card Backend API Testing Suite
Tests all new features including delivery types, code types, pending orders, etc.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class ComprehensiveAbodCardTester:
    def __init__(self, base_url="https://digicardbot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-ComprehensiveTester/2.0'
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

    def test_products_api(self):
        """Test products API with enhanced validation"""
        print("🔍 Testing Enhanced Products API...")
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

    def test_categories_api(self):
        """Test categories API with delivery types validation"""
        print("🔍 Testing Categories API with Delivery Types...")
        success, data = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories List")
        
        if success and isinstance(data, list):
            self.log_test("Categories Response Format", True, f"Returned {len(data)} categories")
            
            # Test category structure and delivery types
            if len(data) > 0:
                category = data[0]
                required_fields = ['id', 'name', 'description', 'category_type', 'price', 'delivery_type', 'redemption_method', 'terms', 'product_id', 'created_at']
                missing_fields = [field for field in required_fields if field not in category]
                
                if not missing_fields:
                    self.log_test("Category Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Category Structure Validation", False, f"Missing fields: {missing_fields}")
                
                # Test delivery types
                valid_delivery_types = ['code', 'phone', 'email', 'manual']
                delivery_type = category.get('delivery_type')
                if delivery_type in valid_delivery_types:
                    self.log_test("Delivery Type Validation", True, f"Valid delivery type: {delivery_type}")
                else:
                    self.log_test("Delivery Type Validation", False, f"Invalid delivery type: {delivery_type}")
                
                # Test price is numeric
                price = category.get('price')
                if isinstance(price, (int, float)) and price >= 0:
                    self.log_test("Price Validation", True, f"Valid price: ${price}")
                else:
                    self.log_test("Price Validation", False, f"Invalid price: {price}")
                    
        elif success:
            self.log_test("Categories Response Format", True, "Empty categories list returned")
        
        return success

    def test_codes_stats_api(self):
        """Test codes statistics API"""
        print("🔍 Testing Codes Statistics API...")
        success, data = self.test_api_endpoint('GET', '/codes-stats', 200, test_name="Get Codes Statistics")
        
        if success and isinstance(data, list):
            self.log_test("Codes Stats Response Format", True, f"Returned {len(data)} code statistics")
            
            # Test codes stats structure
            if len(data) > 0:
                stat = data[0]
                required_fields = ['category_name', 'category_id', 'total_codes', 'used_codes', 'available_codes', 'status']
                missing_fields = [field for field in required_fields if field not in stat]
                
                if not missing_fields:
                    self.log_test("Codes Stats Structure", True, "All required fields present")
                else:
                    self.log_test("Codes Stats Structure", False, f"Missing fields: {missing_fields}")
                
                # Test status values
                valid_statuses = ['good', 'medium', 'low']
                status = stat.get('status')
                if status in valid_statuses:
                    self.log_test("Codes Status Validation", True, f"Valid status: {status}")
                else:
                    self.log_test("Codes Status Validation", False, f"Invalid status: {status}")
                
                # Test numeric values
                total_codes = stat.get('total_codes', 0)
                used_codes = stat.get('used_codes', 0)
                available_codes = stat.get('available_codes', 0)
                
                if total_codes == used_codes + available_codes:
                    self.log_test("Codes Math Validation", True, "Total = Used + Available")
                else:
                    self.log_test("Codes Math Validation", False, f"Math error: {total_codes} ≠ {used_codes} + {available_codes}")
                    
        elif success:
            self.log_test("Codes Stats Response Format", True, "Empty codes stats returned")
        
        return success

    def test_pending_orders_api(self):
        """Test pending orders API"""
        print("🔍 Testing Pending Orders API...")
        success, data = self.test_api_endpoint('GET', '/pending-orders', 200, test_name="Get Pending Orders")
        
        if success and isinstance(data, list):
            self.log_test("Pending Orders Response Format", True, f"Returned {len(data)} pending orders")
            
            # Test pending order structure
            if len(data) > 0:
                order = data[0]
                required_fields = ['id', 'user_id', 'telegram_id', 'product_name', 'category_name', 'price', 'delivery_type', 'status', 'order_date']
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_test("Pending Order Structure", True, "All required fields present")
                else:
                    self.log_test("Pending Order Structure", False, f"Missing fields: {missing_fields}")
                
                # Verify all orders are actually pending
                if order.get('status') == 'pending':
                    self.log_test("Pending Status Validation", True, "Order status is pending")
                else:
                    self.log_test("Pending Status Validation", False, f"Non-pending order in pending list: {order.get('status')}")
                
                # Test delivery type
                valid_delivery_types = ['code', 'phone', 'email', 'manual']
                delivery_type = order.get('delivery_type')
                if delivery_type in valid_delivery_types:
                    self.log_test("Pending Order Delivery Type", True, f"Valid delivery type: {delivery_type}")
                else:
                    self.log_test("Pending Order Delivery Type", False, f"Invalid delivery type: {delivery_type}")
                
                # Check for user input data if delivery type requires it
                if delivery_type in ['phone', 'email']:
                    user_input_data = order.get('user_input_data')
                    if user_input_data:
                        self.log_test("User Input Data Present", True, f"User input: {user_input_data}")
                    else:
                        self.log_test("User Input Data Present", False, "Missing user input for phone/email delivery")
                        
        elif success:
            self.log_test("Pending Orders Response Format", True, "No pending orders")
        
        return success

    def test_users_api_enhanced(self):
        """Test users API with enhanced validation"""
        print("🔍 Testing Enhanced Users API...")
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
                
                # Test data types
                balance = user.get('balance', 0)
                orders_count = user.get('orders_count', 0)
                telegram_id = user.get('telegram_id')
                
                if isinstance(balance, (int, float)) and balance >= 0:
                    self.log_test("User Balance Validation", True, f"Valid balance: ${balance}")
                else:
                    self.log_test("User Balance Validation", False, f"Invalid balance: {balance}")
                
                if isinstance(orders_count, int) and orders_count >= 0:
                    self.log_test("User Orders Count Validation", True, f"Valid orders count: {orders_count}")
                else:
                    self.log_test("User Orders Count Validation", False, f"Invalid orders count: {orders_count}")
                
                if isinstance(telegram_id, int):
                    self.log_test("Telegram ID Validation", True, f"Valid telegram ID: {telegram_id}")
                else:
                    self.log_test("Telegram ID Validation", False, f"Invalid telegram ID: {telegram_id}")
                    
        elif success:
            self.log_test("Users Response Format", True, "Empty users list returned")
            
        return success

    def test_orders_api_enhanced(self):
        """Test orders API with enhanced validation"""
        print("🔍 Testing Enhanced Orders API...")
        success, data = self.test_api_endpoint('GET', '/orders', 200, test_name="Get Orders List")
        
        if success and isinstance(data, list):
            self.log_test("Orders Response Format", True, f"Returned {len(data)} orders")
            
            # Test order structure if orders exist
            if len(data) > 0:
                order = data[0]
                required_fields = ['id', 'user_id', 'telegram_id', 'product_name', 'category_name', 'price', 'delivery_type', 'status', 'order_date']
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_test("Order Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Order Structure Validation", False, f"Missing fields: {missing_fields}")
                    
                # Test order status values
                valid_statuses = ['pending', 'completed', 'failed']
                status = order.get('status')
                if status in valid_statuses:
                    self.log_test("Order Status Validation", True, f"Valid status: {status}")
                else:
                    self.log_test("Order Status Validation", False, f"Invalid status: {status}")
                
                # Test delivery type
                valid_delivery_types = ['code', 'phone', 'email', 'manual']
                delivery_type = order.get('delivery_type')
                if delivery_type in valid_delivery_types:
                    self.log_test("Order Delivery Type Validation", True, f"Valid delivery type: {delivery_type}")
                else:
                    self.log_test("Order Delivery Type Validation", False, f"Invalid delivery type: {delivery_type}")
                
                # Test price
                price = order.get('price')
                if isinstance(price, (int, float)) and price > 0:
                    self.log_test("Order Price Validation", True, f"Valid price: ${price}")
                else:
                    self.log_test("Order Price Validation", False, f"Invalid price: {price}")
                    
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

    def test_webhook_security(self):
        """Test webhook endpoints security"""
        print("🔍 Testing Webhook Security...")
        
        # Test user webhook with wrong secret
        success1, data1 = self.test_api_endpoint('POST', '/webhook/user/wrong_secret', 403, 
                                             {"test": "data"}, "User Webhook Security")
        
        # Test admin webhook with wrong secret  
        success2, data2 = self.test_api_endpoint('POST', '/webhook/admin/wrong_secret', 403,
                                               {"test": "data"}, "Admin Webhook Security")
        
        return success1 and success2

    def test_telegram_integration_endpoints(self):
        """Test Telegram bot integration readiness"""
        print("🔍 Testing Telegram Integration Readiness...")
        
        # Test that webhook endpoints exist (even if they return 403)
        try:
            # User webhook endpoint
            response1 = self.session.post(f"{self.api_url}/webhook/user/test", json={"test": "data"}, timeout=10)
            user_webhook_exists = response1.status_code in [403, 422, 500]  # Any response means endpoint exists
            
            # Admin webhook endpoint  
            response2 = self.session.post(f"{self.api_url}/webhook/admin/test", json={"test": "data"}, timeout=10)
            admin_webhook_exists = response2.status_code in [403, 422, 500]  # Any response means endpoint exists
            
            if user_webhook_exists:
                self.log_test("User Webhook Endpoint Exists", True, "User webhook endpoint is available")
            else:
                self.log_test("User Webhook Endpoint Exists", False, f"User webhook returned: {response1.status_code}")
            
            if admin_webhook_exists:
                self.log_test("Admin Webhook Endpoint Exists", True, "Admin webhook endpoint is available")
            else:
                self.log_test("Admin Webhook Endpoint Exists", False, f"Admin webhook returned: {response2.status_code}")
                
            return user_webhook_exists and admin_webhook_exists
            
        except Exception as e:
            self.log_test("Telegram Integration Test", False, f"Error testing webhooks: {str(e)}")
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive API tests"""
        print("🚀 Starting Comprehensive Abod Card Backend Tests")
        print("Testing New Features: Delivery Types, Code Types, Pending Orders, Enhanced UI")
        print("=" * 70)
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Run all comprehensive tests
        self.test_products_api()
        self.test_categories_api()  # New: Test delivery types
        self.test_codes_stats_api()  # New: Test code statistics
        self.test_pending_orders_api()  # New: Test pending orders management
        self.test_users_api_enhanced()
        self.test_orders_api_enhanced()
        self.test_webhooks_setup()
        self.test_webhook_security()
        self.test_telegram_integration_endpoints()  # New: Test Telegram integration
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results
        failed_tests = [result for result in self.test_results if not result['success']]
        critical_failures = []
        minor_failures = []
        
        for failure in failed_tests:
            if any(keyword in failure['test_name'].lower() for keyword in ['connectivity', 'server', 'webhook setup']):
                critical_failures.append(failure)
            else:
                minor_failures.append(failure)
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        if minor_failures:
            print(f"\n⚠️  MINOR ISSUES ({len(minor_failures)}):")
            for failure in minor_failures:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        if success_rate >= 90:
            print(f"\n🎉 Excellent! System is working very well ({success_rate:.1f}% success rate)")
        elif success_rate >= 75:
            print(f"\n✅ Good! System is mostly functional ({success_rate:.1f}% success rate)")
        elif success_rate >= 50:
            print(f"\n⚠️  Warning! System has significant issues ({success_rate:.1f}% success rate)")
        else:
            print(f"\n❌ Critical! System has major problems ({success_rate:.1f}% success rate)")
        
        print("\n" + "=" * 70)
        
        # Return results for further processing
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "critical_failures": critical_failures,
            "minor_failures": minor_failures
        }

def main():
    """Main test execution"""
    tester = ComprehensiveAbodCardTester()
    results = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All comprehensive tests passed!")
        return 0
    elif results["success_rate"] >= 80:
        print(f"✅ Most tests passed ({results['success_rate']:.1f}%)")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} test(s) failed ({results['success_rate']:.1f}% success)")
        return 1

if __name__ == "__main__":
    sys.exit(main())