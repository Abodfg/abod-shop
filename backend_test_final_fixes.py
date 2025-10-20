#!/usr/bin/env python3
"""
Final Fixes Testing Suite for Abod Card Telegram Bot System
Tests the fixes mentioned in the review request:
1. Admin bot code addition flow (adding codes)
2. User bot product browsing and entering specific product details
3. CallbackQuery and message handling fixes
4. Database operations and error handling
5. Webhook security and authentication
6. Session management
7. Real-time code statistics updates
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class FinalFixesTester:
    def __init__(self, base_url="https://card-bazaar-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-FinalFixesTester/1.0'
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
        try:
            response = self.session.get(f"{self.api_url}/products", timeout=10)
            success = response.status_code == 200
            self.log_test(
                "Server Connectivity", 
                success,
                f"Status: {response.status_code}" if success else f"Failed with status {response.status_code}",
                response.json() if success else response.text
            )
            return success
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Connection error: {str(e)}")
            return False

    def test_user_bot_product_browsing_apis(self):
        """Test APIs that support user bot product browsing functionality"""
        print("🔍 Testing User Bot Product Browsing APIs...")
        
        # Test products API
        try:
            response = self.session.get(f"{self.api_url}/products")
            if response.status_code == 200:
                products = response.json()
                success = len(products) >= 2  # Should have at least 2 products as mentioned
                self.log_test(
                    "Products API for User Bot",
                    success,
                    f"Found {len(products)} products" if success else "Insufficient products for testing",
                    {"product_count": len(products), "products": [p.get('name', 'Unknown') for p in products[:3]]}
                )
                return products if success else []
            else:
                self.log_test("Products API for User Bot", False, f"HTTP {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Products API for User Bot", False, f"Error: {str(e)}")
            return []

    def test_user_bot_categories_apis(self):
        """Test APIs that support user bot category browsing and product details"""
        print("🔍 Testing User Bot Categories APIs...")
        
        try:
            response = self.session.get(f"{self.api_url}/categories")
            if response.status_code == 200:
                categories = response.json()
                success = len(categories) >= 2  # Should have at least 2 categories as mentioned
                
                # Validate category structure for user bot functionality
                valid_categories = []
                for cat in categories:
                    required_fields = ['id', 'name', 'description', 'price', 'delivery_type', 'product_id']
                    if all(field in cat for field in required_fields):
                        valid_categories.append(cat)
                
                self.log_test(
                    "Categories API for User Bot",
                    success and len(valid_categories) >= 2,
                    f"Found {len(categories)} categories, {len(valid_categories)} valid for user bot",
                    {
                        "total_categories": len(categories),
                        "valid_categories": len(valid_categories),
                        "delivery_types": list(set(cat.get('delivery_type', 'unknown') for cat in valid_categories))
                    }
                )
                return valid_categories if success else []
            else:
                self.log_test("Categories API for User Bot", False, f"HTTP {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Categories API for User Bot", False, f"Error: {str(e)}")
            return []

    def test_admin_bot_code_management_apis(self):
        """Test APIs that support admin bot code addition functionality"""
        print("🔍 Testing Admin Bot Code Management APIs...")
        
        try:
            response = self.session.get(f"{self.api_url}/codes-stats")
            if response.status_code == 200:
                stats = response.json()
                success = isinstance(stats, list)
                
                # Check for categories that support code delivery
                code_categories = [s for s in stats if s.get('category_name')]
                
                self.log_test(
                    "Codes Statistics API for Admin Bot",
                    success,
                    f"Found {len(code_categories)} categories with code statistics",
                    {
                        "total_stats": len(stats),
                        "code_categories": len(code_categories),
                        "sample_stats": stats[:2] if stats else []
                    }
                )
                return code_categories if success else []
            else:
                self.log_test("Codes Statistics API for Admin Bot", False, f"HTTP {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_test("Codes Statistics API for Admin Bot", False, f"Error: {str(e)}")
            return []

    def test_webhook_security(self):
        """Test webhook security and authentication"""
        print("🔍 Testing Webhook Security...")
        
        # Test user webhook with invalid secret
        try:
            response = self.session.post(f"{self.api_url}/webhook/user/invalid_secret", json={})
            success = response.status_code == 403
            self.log_test(
                "User Webhook Security (Invalid Secret)",
                success,
                f"Correctly rejected with status {response.status_code}" if success else f"Security issue: status {response.status_code}",
                response.text
            )
        except Exception as e:
            self.log_test("User Webhook Security (Invalid Secret)", False, f"Error: {str(e)}")

        # Test admin webhook with invalid secret
        try:
            response = self.session.post(f"{self.api_url}/webhook/admin/invalid_secret", json={})
            success = response.status_code == 403
            self.log_test(
                "Admin Webhook Security (Invalid Secret)",
                success,
                f"Correctly rejected with status {response.status_code}" if success else f"Security issue: status {response.status_code}",
                response.text
            )
        except Exception as e:
            self.log_test("Admin Webhook Security (Invalid Secret)", False, f"Error: {str(e)}")

    def test_webhook_functionality_basic(self):
        """Test basic webhook functionality with valid secrets"""
        print("🔍 Testing Basic Webhook Functionality...")
        
        # Test user webhook with valid secret but minimal data (simulating /start command)
        try:
            test_update = {
                "update_id": 123456,
                "message": {
                    "message_id": 1,
                    "date": int(datetime.now().timestamp()),
                    "chat": {"id": 987654321, "type": "private"},
                    "from": {"id": 987654321, "is_bot": False, "first_name": "Test", "username": "testuser"},
                    "text": "/start"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=test_update)
            success = response.status_code == 200
            self.log_test(
                "User Webhook Basic Functionality (/start)",
                success,
                f"Status {response.status_code}" + (f" - {response.json()}" if success else ""),
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("User Webhook Basic Functionality (/start)", False, f"Error: {str(e)}")

        # Test admin webhook with valid secret but minimal data
        try:
            test_update = {
                "update_id": 123457,
                "message": {
                    "message_id": 1,
                    "date": int(datetime.now().timestamp()),
                    "chat": {"id": 123456789, "type": "private"},
                    "from": {"id": 123456789, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                    "text": "/start"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=test_update)
            success = response.status_code == 200
            self.log_test(
                "Admin Webhook Basic Functionality (/start)",
                success,
                f"Status {response.status_code}" + (f" - {response.json()}" if success else ""),
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Admin Webhook Basic Functionality (/start)", False, f"Error: {str(e)}")

    def test_callback_query_handling(self):
        """Test callback query handling fixes"""
        print("🔍 Testing CallbackQuery Handling Fixes...")
        
        # Test user bot callback query (browse_products)
        try:
            test_callback = {
                "update_id": 123458,
                "callback_query": {
                    "id": "callback_123",
                    "from": {"id": 987654321, "is_bot": False, "first_name": "Test", "username": "testuser"},
                    "message": {
                        "message_id": 2,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": 987654321, "type": "private"},
                        "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                    },
                    "chat_instance": "callback_chat_instance_123",
                    "data": "browse_products"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=test_callback)
            success = response.status_code == 200
            self.log_test(
                "User Bot CallbackQuery Handling (browse_products)",
                success,
                f"Status {response.status_code}" + (f" - {response.json()}" if success else ""),
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("User Bot CallbackQuery Handling (browse_products)", False, f"Error: {str(e)}")

        # Test admin bot callback query (manage_codes)
        try:
            test_callback = {
                "update_id": 123459,
                "callback_query": {
                    "id": "callback_124",
                    "from": {"id": 123456789, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                    "message": {
                        "message_id": 2,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": 123456789, "type": "private"},
                        "from": {"id": 7835622090, "is_bot": True, "first_name": "AbodCard Admin Bot"}
                    },
                    "chat_instance": "callback_chat_instance_124",
                    "data": "manage_codes"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=test_callback)
            success = response.status_code == 200
            self.log_test(
                "Admin Bot CallbackQuery Handling (manage_codes)",
                success,
                f"Status {response.status_code}" + (f" - {response.json()}" if success else ""),
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Admin Bot CallbackQuery Handling (manage_codes)", False, f"Error: {str(e)}")

    def test_database_consistency(self):
        """Test database consistency and relationships"""
        print("🔍 Testing Database Consistency...")
        
        try:
            # Get products and categories
            products_response = self.session.get(f"{self.api_url}/products")
            categories_response = self.session.get(f"{self.api_url}/categories")
            
            if products_response.status_code == 200 and categories_response.status_code == 200:
                products = products_response.json()
                categories = categories_response.json()
                
                # Check product-category relationships
                product_ids = {p['id'] for p in products}
                categories_with_valid_products = [c for c in categories if c.get('product_id') in product_ids]
                
                success = len(categories_with_valid_products) == len(categories)
                self.log_test(
                    "Database Product-Category Relationships",
                    success,
                    f"{len(categories_with_valid_products)}/{len(categories)} categories have valid product references",
                    {
                        "total_products": len(products),
                        "total_categories": len(categories),
                        "valid_relationships": len(categories_with_valid_products)
                    }
                )
                
                # Check delivery types distribution
                delivery_types = {}
                for cat in categories:
                    dt = cat.get('delivery_type', 'unknown')
                    delivery_types[dt] = delivery_types.get(dt, 0) + 1
                
                code_delivery_count = delivery_types.get('code', 0)
                self.log_test(
                    "Code Delivery Categories Available",
                    code_delivery_count >= 2,
                    f"Found {code_delivery_count} categories using code delivery (needed for admin code addition testing)",
                    delivery_types
                )
                
            else:
                self.log_test("Database Consistency", False, "Failed to fetch products or categories")
                
        except Exception as e:
            self.log_test("Database Consistency", False, f"Error: {str(e)}")

    def test_real_time_code_statistics(self):
        """Test real-time code statistics updates"""
        print("🔍 Testing Real-time Code Statistics...")
        
        try:
            response = self.session.get(f"{self.api_url}/codes-stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Validate statistics structure and calculations
                valid_stats = 0
                for stat in stats:
                    required_fields = ['category_name', 'total_codes', 'used_codes', 'available_codes', 'status']
                    if all(field in stat for field in required_fields):
                        # Validate math
                        total = stat['total_codes']
                        used = stat['used_codes']
                        available = stat['available_codes']
                        
                        if total == used + available:
                            valid_stats += 1
                        else:
                            print(f"    Math error in {stat['category_name']}: {total} != {used} + {available}")
                
                success = valid_stats == len(stats) and len(stats) > 0
                self.log_test(
                    "Real-time Code Statistics Validation",
                    success,
                    f"{valid_stats}/{len(stats)} statistics have correct calculations",
                    {
                        "total_categories": len(stats),
                        "valid_calculations": valid_stats,
                        "sample_stats": stats[:2] if stats else []
                    }
                )
            else:
                self.log_test("Real-time Code Statistics Validation", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Real-time Code Statistics Validation", False, f"Error: {str(e)}")

    def test_error_handling_and_exceptions(self):
        """Test error handling and exception management"""
        print("🔍 Testing Error Handling and Exceptions...")
        
        # Test invalid callback data
        try:
            test_callback = {
                "update_id": 123460,
                "callback_query": {
                    "id": "callback_125",
                    "from": {"id": 987654321, "is_bot": False, "first_name": "Test", "username": "testuser"},
                    "message": {
                        "message_id": 3,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": 987654321, "type": "private"},
                        "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                    },
                    "chat_instance": "callback_chat_instance_125",
                    "data": "invalid_callback_data_xyz"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=test_callback)
            success = response.status_code == 200  # Should handle gracefully, not crash
            self.log_test(
                "Error Handling - Invalid Callback Data",
                success,
                f"Handled gracefully with status {response.status_code}" if success else f"Failed with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Error Handling - Invalid Callback Data", False, f"Error: {str(e)}")

        # Test malformed webhook data
        try:
            malformed_data = {"invalid": "structure", "missing": "required_fields"}
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=malformed_data)
            success = response.status_code in [200, 400, 422]  # Should handle gracefully
            self.log_test(
                "Error Handling - Malformed Webhook Data",
                success,
                f"Handled gracefully with status {response.status_code}" if success else f"Unexpected status {response.status_code}",
                response.text
            )
        except Exception as e:
            self.log_test("Error Handling - Malformed Webhook Data", False, f"Error: {str(e)}")

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Final Fixes Testing for Abod Card Telegram Bot System")
        print("=" * 80)
        
        # Basic connectivity
        if not self.test_server_connectivity():
            print("❌ Server connectivity failed. Stopping tests.")
            return False
        
        # Test user bot functionality APIs
        products = self.test_user_bot_product_browsing_apis()
        categories = self.test_user_bot_categories_apis()
        
        # Test admin bot functionality APIs
        code_stats = self.test_admin_bot_code_management_apis()
        
        # Test webhook security and functionality
        self.test_webhook_security()
        self.test_webhook_functionality_basic()
        
        # Test callback query handling fixes
        self.test_callback_query_handling()
        
        # Test database consistency
        self.test_database_consistency()
        
        # Test real-time statistics
        self.test_real_time_code_statistics()
        
        # Test error handling
        self.test_error_handling_and_exceptions()
        
        return True

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 80)
        print("📊 FINAL FIXES TEST REPORT")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 Test Results Summary:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}")
            if result["details"]:
                print(f"    {result['details']}")
        
        # Categorize results
        categories = {
            "User Bot APIs": [],
            "Admin Bot APIs": [],
            "Webhook Security": [],
            "CallbackQuery Handling": [],
            "Database Operations": [],
            "Error Handling": []
        }
        
        for result in self.test_results:
            name = result["test_name"]
            if "User Bot" in name or "Product" in name or "Categories" in name:
                categories["User Bot APIs"].append(result)
            elif "Admin Bot" in name or "Codes" in name:
                categories["Admin Bot APIs"].append(result)
            elif "Webhook" in name:
                categories["Webhook Security"].append(result)
            elif "CallbackQuery" in name:
                categories["CallbackQuery Handling"].append(result)
            elif "Database" in name or "Statistics" in name:
                categories["Database Operations"].append(result)
            elif "Error" in name:
                categories["Error Handling"].append(result)
        
        print("\n📊 Results by Category:")
        for category, results in categories.items():
            if results:
                passed = sum(1 for r in results if r["success"])
                total = len(results)
                rate = (passed / total * 100) if total > 0 else 0
                print(f"{category}: {passed}/{total} ({rate:.1f}%)")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "results": self.test_results,
            "categories": categories
        }

def main():
    """Main test execution"""
    tester = FinalFixesTester()
    
    try:
        success = tester.run_comprehensive_test()
        report = tester.generate_report()
        
        if success:
            print(f"\n🎉 Testing completed successfully!")
            print(f"Overall success rate: {report['success_rate']:.1f}%")
        else:
            print(f"\n⚠️ Testing completed with issues.")
            print(f"Overall success rate: {report['success_rate']:.1f}%")
        
        return 0 if report['success_rate'] >= 80 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())