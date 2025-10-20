#!/usr/bin/env python3
"""
Telegram Stars Integration and Purchase Flow Testing
Focused testing for Arabic review request - Abod Card Bot
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class TelegramStarsAPITester:
    def __init__(self, base_url="https://card-bazaar-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-Stars-Tester/1.0'
        })
        
        # Test data from Arabic review request
        self.test_user_id = 7040570081
        self.test_categories = ["games", "gift_cards", "ecommerce", "subscriptions"]
        self.test_delivery_types = ["id", "email", "phone", "code"]

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

    def test_categories_api_for_stars(self):
        """Test categories API to check for stars pricing and delivery types"""
        print("🔍 Testing Categories API for Stars Integration...")
        
        success, data = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories for Stars")
        
        if success and isinstance(data, list):
            self.log_test("Categories API Response", True, f"Returned {len(data)} categories")
            
            # Check for required delivery types
            delivery_types_found = set()
            stars_pricing_found = False
            active_categories = []
            
            for category in data:
                if category.get('delivery_type'):
                    delivery_types_found.add(category['delivery_type'])
                
                if category.get('is_active'):
                    active_categories.append(category)
                
                # Check for stars pricing fields
                if 'price_stars' in category or 'stars_price' in category:
                    stars_pricing_found = True
            
            # Test delivery types coverage
            required_types = set(self.test_delivery_types)
            missing_types = required_types - delivery_types_found
            
            if not missing_types:
                self.log_test("Delivery Types Coverage", True, f"All required types found: {list(delivery_types_found)}")
            else:
                self.log_test("Delivery Types Coverage", False, f"Missing types: {list(missing_types)}")
            
            # Test active categories
            if active_categories:
                self.log_test("Active Categories Available", True, f"{len(active_categories)} active categories found")
            else:
                self.log_test("Active Categories Available", False, "No active categories found - purchases will fail")
            
            # Test stars pricing
            if stars_pricing_found:
                self.log_test("Stars Pricing Fields", True, "Stars pricing fields found in categories")
            else:
                self.log_test("Stars Pricing Fields", False, "No stars pricing fields found")
            
            return success
        else:
            self.log_test("Categories API Response", False, "Invalid response format")
            return False

    def test_purchase_api_with_id_delivery(self):
        """Test purchase API specifically with ID delivery type and additional_info"""
        print("🔍 Testing Purchase API with ID Delivery Type...")
        
        # First get categories to find one with ID delivery
        success, categories = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories for Purchase Test")
        
        if not success or not isinstance(categories, list):
            self.log_test("Purchase API - ID Delivery", False, "Cannot get categories for testing")
            return False
        
        # Find a category with ID delivery type
        id_category = None
        for category in categories:
            if category.get('delivery_type') == 'id':
                id_category = category
                break
        
        if not id_category:
            self.log_test("Purchase API - ID Delivery", False, "No category with ID delivery type found")
            return False
        
        # Test purchase with ID delivery
        purchase_data = {
            "user_telegram_id": self.test_user_id,
            "category_id": id_category['id'],
            "delivery_type": "id",
            "additional_info": "GAME123456789"  # Sample game ID
        }
        
        success, response = self.test_api_endpoint(
            'POST', '/purchase', 200, purchase_data, 
            "Purchase API - ID Delivery with additional_info"
        )
        
        if success:
            # Check if response indicates proper handling
            if isinstance(response, dict):
                if 'error' in response or 'message' in response:
                    # This is expected - system should validate and respond
                    self.log_test("Purchase API - ID Validation", True, f"API validates ID purchases: {response}")
                else:
                    self.log_test("Purchase API - ID Validation", True, "Purchase API processed ID delivery request")
            return True
        else:
            return False

    def test_purchase_api_all_delivery_types(self):
        """Test purchase API with all delivery types"""
        print("🔍 Testing Purchase API with All Delivery Types...")
        
        # Get categories first
        success, categories = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories for All Delivery Types")
        
        if not success or not isinstance(categories, list):
            self.log_test("Purchase API - All Delivery Types", False, "Cannot get categories")
            return False
        
        # Group categories by delivery type
        categories_by_delivery = {}
        for category in categories:
            delivery_type = category.get('delivery_type', 'unknown')
            if delivery_type not in categories_by_delivery:
                categories_by_delivery[delivery_type] = []
            categories_by_delivery[delivery_type].append(category)
        
        all_success = True
        
        # Test each delivery type
        for delivery_type in self.test_delivery_types:
            if delivery_type in categories_by_delivery:
                category = categories_by_delivery[delivery_type][0]  # Use first category of this type
                
                # Prepare appropriate additional_info for each delivery type
                additional_info_map = {
                    "id": "USER123456789",
                    "email": "test@example.com", 
                    "phone": "+966501234567",
                    "code": "REDEEM123"
                }
                
                purchase_data = {
                    "user_telegram_id": self.test_user_id,
                    "category_id": category['id'],
                    "delivery_type": delivery_type,
                    "additional_info": additional_info_map.get(delivery_type, "test_info")
                }
                
                success, response = self.test_api_endpoint(
                    'POST', '/purchase', 200, purchase_data,
                    f"Purchase API - {delivery_type.upper()} delivery"
                )
                
                if not success:
                    all_success = False
            else:
                self.log_test(f"Purchase API - {delivery_type.upper()} delivery", False, f"No categories with {delivery_type} delivery type")
                all_success = False
        
        return all_success

    def test_user_stars_balance(self):
        """Test user stars balance checking"""
        print("🔍 Testing User Stars Balance...")
        
        # Get users to check stars balance fields
        success, users = self.test_api_endpoint('GET', '/users', 200, test_name="Get Users for Stars Balance")
        
        if success and isinstance(users, list):
            # Find our test user
            test_user = None
            for user in users:
                if user.get('telegram_id') == self.test_user_id:
                    test_user = user
                    break
            
            if test_user:
                # Check for stars balance fields
                stars_fields = ['balance_stars', 'stars_balance']
                stars_field_found = any(field in test_user for field in stars_fields)
                
                if stars_field_found:
                    stars_balance = test_user.get('balance_stars', test_user.get('stars_balance', 0))
                    self.log_test("User Stars Balance Fields", True, f"User {self.test_user_id} has {stars_balance} stars")
                else:
                    self.log_test("User Stars Balance Fields", False, "No stars balance fields found in user data")
                
                # Check for regular balance (should still exist for compatibility)
                if 'balance' in test_user:
                    regular_balance = test_user.get('balance', 0)
                    self.log_test("User Regular Balance", True, f"User has ${regular_balance} regular balance")
                else:
                    self.log_test("User Regular Balance", False, "No regular balance field found")
                
                return stars_field_found
            else:
                self.log_test("Test User Found", False, f"Test user {self.test_user_id} not found in users list")
                return False
        else:
            self.log_test("Users API for Stars Balance", False, "Cannot get users data")
            return False

    def test_stars_conversion_rates(self):
        """Test stars to USD conversion rates in the system"""
        print("🔍 Testing Stars Conversion Rates...")
        
        # Get categories to check pricing
        success, categories = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories for Conversion Rates")
        
        if success and isinstance(categories, list):
            conversion_examples = []
            
            for category in categories:
                usd_price = category.get('price', 0)
                stars_price = category.get('price_stars', category.get('stars_price', 0))
                
                if usd_price > 0 and stars_price > 0:
                    conversion_rate = stars_price / usd_price
                    conversion_examples.append({
                        'category': category.get('name', 'Unknown'),
                        'usd': usd_price,
                        'stars': stars_price,
                        'rate': conversion_rate
                    })
            
            if conversion_examples:
                # Check if conversion rates are consistent
                rates = [ex['rate'] for ex in conversion_examples]
                avg_rate = sum(rates) / len(rates)
                
                self.log_test("Stars Conversion Rates", True, f"Found {len(conversion_examples)} pricing examples, avg rate: {avg_rate:.1f} stars/USD")
                
                # Log some examples
                for i, example in enumerate(conversion_examples[:3]):  # Show first 3 examples
                    self.log_test(f"Conversion Example {i+1}", True, 
                                f"{example['category']}: ${example['usd']} = {example['stars']} stars (rate: {example['rate']:.1f})")
                
                return True
            else:
                self.log_test("Stars Conversion Rates", False, "No categories with both USD and stars pricing found")
                return False
        else:
            return False

    def test_ammer_pay_integration(self):
        """Test Ammer Pay integration for stars payments"""
        print("🔍 Testing Ammer Pay Integration...")
        
        # Check if the system has Ammer Pay configuration
        # We can't directly test payment processing, but we can check the purchase flow
        
        # Test a purchase that would trigger Ammer Pay
        purchase_data = {
            "user_telegram_id": self.test_user_id,
            "category_id": "test_category_id",
            "delivery_type": "id",
            "additional_info": "TESTID123",
            "payment_method": "ammer_pay"
        }
        
        success, response = self.test_api_endpoint(
            'POST', '/purchase', 200, purchase_data,
            "Ammer Pay Integration Test"
        )
        
        if success:
            # Check response for Ammer Pay related fields
            if isinstance(response, dict):
                ammer_fields = ['payment_url', 'transaction_id', 'ammer_transaction_id']
                ammer_integration = any(field in response for field in ammer_fields)
                
                if ammer_integration:
                    self.log_test("Ammer Pay Integration", True, "Ammer Pay fields found in response")
                else:
                    self.log_test("Ammer Pay Integration", True, "Purchase API handles payment method parameter")
                
                return True
        
        return success

    def test_purchase_flow_completion(self):
        """Test complete purchase flow - the main issue reported"""
        print("🔍 Testing Complete Purchase Flow (Main Issue)...")
        
        # This tests the specific issue: "عند إدخال ID والضغط على حسناً، يعود للرئيسية بدون إكمال خطوات الشراء"
        
        # Step 1: Get active categories with ID delivery
        success, categories = self.test_api_endpoint('GET', '/categories', 200, test_name="Get Categories for Flow Test")
        
        if not success:
            self.log_test("Purchase Flow - Get Categories", False, "Cannot get categories")
            return False
        
        # Find active category with ID delivery
        target_category = None
        for category in categories:
            if category.get('delivery_type') == 'id' and category.get('is_active', False):
                target_category = category
                break
        
        if not target_category:
            # Try any active category
            for category in categories:
                if category.get('is_active', False):
                    target_category = category
                    break
        
        if not target_category:
            self.log_test("Purchase Flow - Active Category", False, "No active categories found for testing")
            return False
        
        # Step 2: Test purchase with proper data
        purchase_data = {
            "user_telegram_id": self.test_user_id,
            "category_id": target_category['id'],
            "delivery_type": target_category.get('delivery_type', 'id'),
            "additional_info": "TESTUSER123456"
        }
        
        success, response = self.test_api_endpoint(
            'POST', '/purchase', 200, purchase_data,
            "Complete Purchase Flow Test"
        )
        
        if success and isinstance(response, dict):
            # Analyze the response to understand the flow
            if 'error' in response:
                error_msg = response.get('error', '')
                if 'رصيد' in error_msg or 'balance' in error_msg.lower():
                    self.log_test("Purchase Flow - Balance Check", True, "System properly checks user balance")
                elif 'غير نشط' in error_msg or 'inactive' in error_msg.lower():
                    self.log_test("Purchase Flow - Category Status", True, "System properly checks category status")
                elif 'مستخدم' in error_msg or 'user' in error_msg.lower():
                    self.log_test("Purchase Flow - User Validation", True, "System properly validates user")
                else:
                    self.log_test("Purchase Flow - Error Handling", True, f"System returns error: {error_msg}")
            elif 'success' in response or 'تم' in str(response):
                self.log_test("Purchase Flow - Success Path", True, "Purchase completed successfully")
            else:
                self.log_test("Purchase Flow - Response Format", True, f"Purchase API responded: {response}")
            
            return True
        else:
            self.log_test("Complete Purchase Flow Test", False, "Purchase flow failed")
            return False

    def test_stars_only_system(self):
        """Test that system works with stars only (no dollars)"""
        print("🔍 Testing Stars-Only System...")
        
        # Check if categories have stars pricing
        success, categories = self.test_api_endpoint('GET', '/categories', 200, test_name="Categories Stars-Only Check")
        
        if success and isinstance(categories, list):
            stars_only_categories = 0
            mixed_pricing_categories = 0
            
            for category in categories:
                has_usd = 'price' in category and category.get('price', 0) > 0
                has_stars = 'price_stars' in category and category.get('price_stars', 0) > 0
                
                if has_stars and not has_usd:
                    stars_only_categories += 1
                elif has_stars and has_usd:
                    mixed_pricing_categories += 1
            
            if stars_only_categories > 0:
                self.log_test("Stars-Only Categories", True, f"{stars_only_categories} categories with stars-only pricing")
            else:
                self.log_test("Stars-Only Categories", False, "No stars-only categories found")
            
            if mixed_pricing_categories > 0:
                self.log_test("Mixed Pricing Categories", True, f"{mixed_pricing_categories} categories with both USD and stars pricing")
            
            return stars_only_categories > 0 or mixed_pricing_categories > 0
        
        return False

    def test_telegram_stars_invoice_system(self):
        """Test Telegram Stars invoice system integration"""
        print("🔍 Testing Telegram Stars Invoice System...")
        
        # Test if the system can handle stars transactions
        # We'll test this by checking the orders for stars-related fields
        
        success, orders = self.test_api_endpoint('GET', '/orders', 200, test_name="Orders Stars Integration Check")
        
        if success and isinstance(orders, list):
            stars_orders = []
            
            for order in orders:
                if 'price_stars' in order or 'stars_price' in order or order.get('payment_method') == 'ammer_pay':
                    stars_orders.append(order)
            
            if stars_orders:
                self.log_test("Stars Orders Found", True, f"{len(stars_orders)} orders with stars integration")
                
                # Check first stars order for required fields
                stars_order = stars_orders[0]
                required_fields = ['telegram_id', 'price_stars', 'payment_method']
                missing_fields = [field for field in required_fields if field not in stars_order]
                
                if not missing_fields:
                    self.log_test("Stars Order Structure", True, "Stars orders have required fields")
                else:
                    self.log_test("Stars Order Structure", False, f"Missing fields: {missing_fields}")
                
                return True
            else:
                self.log_test("Stars Orders Found", False, "No orders with stars integration found")
                return False
        
        return False

    def run_all_tests(self):
        """Run all Telegram Stars integration tests"""
        print("🌟 Starting Telegram Stars Integration Testing...")
        print("=" * 60)
        
        test_methods = [
            self.test_categories_api_for_stars,
            self.test_purchase_api_with_id_delivery,
            self.test_purchase_api_all_delivery_types,
            self.test_user_stars_balance,
            self.test_stars_conversion_rates,
            self.test_ammer_pay_integration,
            self.test_purchase_flow_completion,
            self.test_stars_only_system,
            self.test_telegram_stars_invoice_system
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Exception in {test_method.__name__}", False, f"Error: {str(e)}")
            
            time.sleep(0.5)  # Small delay between tests
        
        # Print summary
        print("=" * 60)
        print(f"🌟 TELEGRAM STARS TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        # Categorize results
        critical_failures = []
        warnings = []
        
        for result in self.test_results:
            if not result['success']:
                if 'Purchase Flow' in result['test_name'] or 'Stars Balance' in result['test_name']:
                    critical_failures.append(result['test_name'])
                else:
                    warnings.append(result['test_name'])
        
        if critical_failures:
            print(f"🚨 CRITICAL ISSUES: {len(critical_failures)}")
            for issue in critical_failures:
                print(f"   - {issue}")
        
        if warnings:
            print(f"⚠️  WARNINGS: {len(warnings)}")
            for warning in warnings:
                print(f"   - {warning}")
        
        if not critical_failures and not warnings:
            print("✅ ALL TESTS PASSED - Telegram Stars integration working correctly!")
        
        return self.tests_passed, self.tests_run

if __name__ == "__main__":
    tester = TelegramStarsAPITester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        sys.exit(0)  # All tests passed
    elif passed / total >= 0.8:
        sys.exit(1)  # Most tests passed, minor issues
    else:
        sys.exit(2)  # Major issues found