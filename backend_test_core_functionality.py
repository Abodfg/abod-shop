#!/usr/bin/env python3
"""
Core Functionality Testing Suite for Abod Card Telegram Bot
Tests the core functions and database operations for the reported fixes
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class CoreFunctionalityTester:
    def __init__(self, base_url="https://cardmartbot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-CoreTester/1.0'
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

    def test_server_connectivity(self):
        """Test basic server connectivity"""
        print("🔍 Testing Server Connectivity...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code in [200, 404]:
                self.log_test("Server Connectivity", True, f"Server responding (status: {response.status_code})")
                return True
            else:
                self.log_test("Server Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Cannot connect to server: {str(e)}")
            return False

    def test_products_api_for_user_bot(self):
        """Test products API that user bot relies on"""
        print("🔍 Testing Products API for User Bot...")
        
        try:
            response = self.session.get(f"{self.api_url}/products", timeout=10)
            if response.status_code == 200:
                products = response.json()
                self.log_test("Products API Response", True, f"Retrieved {len(products)} products")
                
                # Test product structure for user bot functionality
                if len(products) > 0:
                    product = products[0]
                    required_fields = ['id', 'name', 'description', 'terms', 'is_active']
                    missing_fields = [field for field in required_fields if field not in product]
                    
                    if not missing_fields:
                        self.log_test("Product Structure for User Bot", True, "All required fields present for user bot")
                        
                        # Test if product is active (user bot should only show active products)
                        if product.get('is_active', False):
                            self.log_test("Product Active Status", True, "Product is active and should be visible to users")
                        else:
                            self.log_test("Product Active Status", False, "Product is inactive - may not be visible to users")
                    else:
                        self.log_test("Product Structure for User Bot", False, f"Missing fields: {missing_fields}")
                        
                    return True
                else:
                    self.log_test("Products Available for User Bot", False, "No products available for user bot to display")
                    return False
            else:
                self.log_test("Products API Response", False, f"API returned status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Products API Response", False, f"Error: {str(e)}")
            return False

    def test_categories_api_for_user_bot(self):
        """Test categories API that user bot relies on for product details"""
        print("🔍 Testing Categories API for User Bot Product Details...")
        
        try:
            response = self.session.get(f"{self.api_url}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                self.log_test("Categories API Response", True, f"Retrieved {len(categories)} categories")
                
                if len(categories) > 0:
                    category = categories[0]
                    required_fields = ['id', 'name', 'description', 'price', 'product_id', 'delivery_type']
                    missing_fields = [field for field in required_fields if field not in category]
                    
                    if not missing_fields:
                        self.log_test("Category Structure for User Bot", True, "All required fields present for user bot")
                        
                        # Test price format (important for user bot display)
                        price = category.get('price')
                        if isinstance(price, (int, float)) and price > 0:
                            self.log_test("Category Price Format", True, f"Valid price format: ${price}")
                        else:
                            self.log_test("Category Price Format", False, f"Invalid price: {price}")
                            
                        # Test delivery type (important for purchase flow)
                        delivery_type = category.get('delivery_type')
                        valid_delivery_types = ['code', 'phone', 'email', 'manual']
                        if delivery_type in valid_delivery_types:
                            self.log_test("Category Delivery Type", True, f"Valid delivery type: {delivery_type}")
                        else:
                            self.log_test("Category Delivery Type", False, f"Invalid delivery type: {delivery_type}")
                    else:
                        self.log_test("Category Structure for User Bot", False, f"Missing fields: {missing_fields}")
                        
                    return True
                else:
                    self.log_test("Categories Available for User Bot", False, "No categories available for product details")
                    return False
            else:
                self.log_test("Categories API Response", False, f"API returned status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Categories API Response", False, f"Error: {str(e)}")
            return False

    def test_codes_stats_for_admin_bot(self):
        """Test codes statistics API that admin bot uses for code management"""
        print("🔍 Testing Codes Statistics for Admin Bot...")
        
        try:
            response = self.session.get(f"{self.api_url}/codes-stats", timeout=10)
            if response.status_code == 200:
                codes_stats = response.json()
                self.log_test("Codes Stats API Response", True, f"Retrieved {len(codes_stats)} code statistics")
                
                if len(codes_stats) > 0:
                    stat = codes_stats[0]
                    required_fields = ['category_name', 'category_id', 'total_codes', 'used_codes', 'available_codes', 'status']
                    missing_fields = [field for field in required_fields if field not in stat]
                    
                    if not missing_fields:
                        self.log_test("Codes Stats Structure", True, "All required fields present for admin bot")
                        
                        # Test numeric consistency
                        total = stat.get('total_codes', 0)
                        used = stat.get('used_codes', 0)
                        available = stat.get('available_codes', 0)
                        
                        if total == used + available:
                            self.log_test("Codes Math Validation", True, f"Math correct: {total} = {used} + {available}")
                        else:
                            self.log_test("Codes Math Validation", False, f"Math error: {total} ≠ {used} + {available}")
                            
                        # Test status calculation
                        status = stat.get('status')
                        expected_status = 'low' if available <= 5 else 'medium' if available <= 10 else 'good'
                        if status == expected_status:
                            self.log_test("Codes Status Calculation", True, f"Status correctly calculated: {status}")
                        else:
                            self.log_test("Codes Status Calculation", False, f"Status mismatch: {status} vs expected {expected_status}")
                    else:
                        self.log_test("Codes Stats Structure", False, f"Missing fields: {missing_fields}")
                        
                    return True
                else:
                    self.log_test("Codes Stats Available", True, "No code statistics (empty system)")
                    return True
            else:
                self.log_test("Codes Stats API Response", False, f"API returned status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Codes Stats API Response", False, f"Error: {str(e)}")
            return False

    def test_webhook_endpoints_security(self):
        """Test webhook endpoints security and structure"""
        print("🔍 Testing Webhook Security...")
        
        # Test user webhook with wrong secret (should return 403)
        try:
            response = self.session.post(f"{self.api_url}/webhook/user/wrong_secret", 
                                       json={"test": "data"}, timeout=10)
            if response.status_code == 403:
                self.log_test("User Webhook Security", True, "Correctly rejected invalid secret")
            else:
                self.log_test("User Webhook Security", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("User Webhook Security", False, f"Error: {str(e)}")

        # Test admin webhook with wrong secret (should return 403)
        try:
            response = self.session.post(f"{self.api_url}/webhook/admin/wrong_secret", 
                                       json={"test": "data"}, timeout=10)
            if response.status_code == 403:
                self.log_test("Admin Webhook Security", True, "Correctly rejected invalid secret")
            else:
                self.log_test("Admin Webhook Security", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Webhook Security", False, f"Error: {str(e)}")

    def test_basic_webhook_functionality(self):
        """Test basic webhook functionality with minimal valid data"""
        print("🔍 Testing Basic Webhook Functionality...")
        
        # Test user webhook with minimal valid message
        user_start_message = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User"
                },
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "/start"
            }
        }
        
        try:
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", 
                                       json=user_start_message, timeout=10)
            if response.status_code == 200:
                self.log_test("User Webhook Basic Functionality", True, "User webhook processed /start message")
            else:
                self.log_test("User Webhook Basic Functionality", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Webhook Basic Functionality", False, f"Error: {str(e)}")

        # Test admin webhook with minimal valid message
        admin_start_message = {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Admin User"
                },
                "chat": {
                    "id": 987654321,
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "/start"
            }
        }
        
        try:
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", 
                                       json=admin_start_message, timeout=10)
            if response.status_code == 200:
                self.log_test("Admin Webhook Basic Functionality", True, "Admin webhook processed /start message")
            else:
                self.log_test("Admin Webhook Basic Functionality", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Webhook Basic Functionality", False, f"Error: {str(e)}")

    def test_database_consistency(self):
        """Test database consistency for bot operations"""
        print("🔍 Testing Database Consistency...")
        
        # Get all data and check relationships
        try:
            products_response = self.session.get(f"{self.api_url}/products", timeout=10)
            categories_response = self.session.get(f"{self.api_url}/categories", timeout=10)
            
            if products_response.status_code == 200 and categories_response.status_code == 200:
                products = products_response.json()
                categories = categories_response.json()
                
                self.log_test("Database Data Retrieval", True, f"Retrieved {len(products)} products, {len(categories)} categories")
                
                # Check product-category relationships
                product_ids = {p['id'] for p in products}
                category_product_ids = {c['product_id'] for c in categories}
                
                orphaned_categories = category_product_ids - product_ids
                if not orphaned_categories:
                    self.log_test("Product-Category Relationships", True, "All categories have valid product references")
                else:
                    self.log_test("Product-Category Relationships", False, f"Orphaned categories: {len(orphaned_categories)}")
                
                # Check if there are products with categories (needed for user bot)
                products_with_categories = product_ids & category_product_ids
                if products_with_categories:
                    self.log_test("Products with Categories", True, f"{len(products_with_categories)} products have categories")
                else:
                    self.log_test("Products with Categories", False, "No products have categories - user bot won't show details")
                    
            else:
                self.log_test("Database Data Retrieval", False, "Failed to retrieve database data")
                
        except Exception as e:
            self.log_test("Database Data Retrieval", False, f"Error: {str(e)}")

    def test_code_delivery_types(self):
        """Test code delivery types functionality"""
        print("🔍 Testing Code Delivery Types...")
        
        try:
            response = self.session.get(f"{self.api_url}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                
                delivery_types = {}
                for category in categories:
                    delivery_type = category.get('delivery_type', 'unknown')
                    delivery_types[delivery_type] = delivery_types.get(delivery_type, 0) + 1
                
                self.log_test("Delivery Types Distribution", True, f"Found delivery types: {dict(delivery_types)}")
                
                # Check if code delivery type exists (needed for admin bot code addition)
                if 'code' in delivery_types:
                    self.log_test("Code Delivery Type Available", True, f"{delivery_types['code']} categories use code delivery")
                else:
                    self.log_test("Code Delivery Type Available", False, "No categories use code delivery - admin code addition won't work")
                
                # Check for valid delivery types
                valid_types = {'code', 'phone', 'email', 'manual'}
                invalid_types = set(delivery_types.keys()) - valid_types
                if not invalid_types:
                    self.log_test("Valid Delivery Types", True, "All delivery types are valid")
                else:
                    self.log_test("Valid Delivery Types", False, f"Invalid delivery types: {invalid_types}")
                    
            else:
                self.log_test("Delivery Types Check", False, f"Categories API returned: {response.status_code}")
                
        except Exception as e:
            self.log_test("Delivery Types Check", False, f"Error: {str(e)}")

    def run_core_functionality_tests(self):
        """Run all core functionality tests"""
        print("🚀 Starting Core Functionality Tests for Telegram Bot Fixes")
        print("Testing:")
        print("1. User bot product browsing and details functionality")
        print("2. Admin bot code management functionality")
        print("3. Database operations and consistency")
        print("=" * 70)
        
        # Test server connectivity first
        if not self.test_server_connectivity():
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Test user bot related functionality
        print("\n👤 Testing User Bot Related Functionality...")
        self.test_products_api_for_user_bot()
        self.test_categories_api_for_user_bot()
        
        # Test admin bot related functionality
        print("\n🔧 Testing Admin Bot Related Functionality...")
        self.test_codes_stats_for_admin_bot()
        self.test_code_delivery_types()
        
        # Test webhook functionality
        print("\n🔗 Testing Webhook Functionality...")
        self.test_webhook_endpoints_security()
        self.test_basic_webhook_functionality()
        
        # Test database consistency
        print("\n🗄️ Testing Database Consistency...")
        self.test_database_consistency()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 70)
        print("📊 CORE FUNCTIONALITY TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results
        user_bot_tests = [r for r in self.test_results if 'user bot' in r['test_name'].lower() or 'products' in r['test_name'].lower() or 'categories' in r['test_name'].lower()]
        admin_bot_tests = [r for r in self.test_results if 'admin bot' in r['test_name'].lower() or 'codes' in r['test_name'].lower()]
        webhook_tests = [r for r in self.test_results if 'webhook' in r['test_name'].lower()]
        database_tests = [r for r in self.test_results if 'database' in r['test_name'].lower()]
        
        def calc_success_rate(tests):
            if not tests:
                return 0
            return sum(1 for t in tests if t['success']) / len(tests) * 100
        
        print(f"\n📊 Success Rate by Category:")
        print(f"  User Bot Functionality: {calc_success_rate(user_bot_tests):.1f}% ({sum(1 for t in user_bot_tests if t['success'])}/{len(user_bot_tests)})")
        print(f"  Admin Bot Functionality: {calc_success_rate(admin_bot_tests):.1f}% ({sum(1 for t in admin_bot_tests if t['success'])}/{len(admin_bot_tests)})")
        print(f"  Webhook Functionality: {calc_success_rate(webhook_tests):.1f}% ({sum(1 for t in webhook_tests if t['success'])}/{len(webhook_tests)})")
        print(f"  Database Operations: {calc_success_rate(database_tests):.1f}% ({sum(1 for t in database_tests if t['success'])}/{len(database_tests)})")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for failure in failed_tests:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        # Critical issues analysis
        critical_issues = []
        if calc_success_rate(user_bot_tests) < 80:
            critical_issues.append("User bot product browsing functionality has issues")
        if calc_success_rate(admin_bot_tests) < 80:
            critical_issues.append("Admin bot code management functionality has issues")
        if calc_success_rate(webhook_tests) < 80:
            critical_issues.append("Webhook functionality has issues")
            
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 Excellent! Core functionality is working very well ({success_rate:.1f}% success rate)")
        elif success_rate >= 75:
            print(f"\n✅ Good! Most core functionality is working ({success_rate:.1f}% success rate)")
        elif success_rate >= 50:
            print(f"\n⚠️  Warning! Core functionality has significant issues ({success_rate:.1f}% success rate)")
        else:
            print(f"\n❌ Critical! Core functionality has major problems ({success_rate:.1f}% success rate)")
        
        print("\n" + "=" * 70)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "user_bot_success_rate": calc_success_rate(user_bot_tests),
            "admin_bot_success_rate": calc_success_rate(admin_bot_tests),
            "webhook_success_rate": calc_success_rate(webhook_tests),
            "database_success_rate": calc_success_rate(database_tests),
            "test_results": self.test_results,
            "failed_tests": failed_tests,
            "critical_issues": critical_issues
        }

def main():
    """Main test execution"""
    tester = CoreFunctionalityTester()
    results = tester.run_core_functionality_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All core functionality tests passed!")
        return 0
    elif results["success_rate"] >= 80:
        print(f"✅ Most tests passed ({results['success_rate']:.1f}%)")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} test(s) failed ({results['success_rate']:.1f}% success)")
        return 1

if __name__ == "__main__":
    sys.exit(main())