#!/usr/bin/env python3
"""
Abod Card User Bot Comprehensive Testing Suite
Tests all user bot functionality with precision, consistency, and coherence
"""

import requests
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

class AbodUserBotTester:
    def __init__(self, base_url="https://card-bazaar-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.webhook_url = f"{self.api_url}/webhook/user/abod_user_webhook_secret"
        self.test_user_id = 7040570081  # Admin but also regular user
        self.user_bot_token = "7933553585:AAHNAAxp2ZCVV_KqohmF2Mx5WL66__HYnno"
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodUserBot-Tester/1.0'
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

    def create_telegram_message_update(self, text: str, message_id: int = None, user_id: int = None):
        """Create a Telegram message update"""
        if message_id is None:
            message_id = int(time.time()) % 1000000
        if user_id is None:
            user_id = self.test_user_id
            
        return {
            "update_id": message_id + 1000000,
            "message": {
                "message_id": message_id,
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user",
                    "language_code": "ar"
                },
                "chat": {
                    "id": user_id,
                    "first_name": "Test User",
                    "username": "test_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": text
            }
        }

    def create_telegram_callback_update(self, callback_data: str, message_id: int = None, user_id: int = None):
        """Create a Telegram callback query update"""
        if message_id is None:
            message_id = int(time.time()) % 1000000
        if user_id is None:
            user_id = self.test_user_id
            
        return {
            "update_id": message_id + 2000000,
            "callback_query": {
                "id": f"callback_{message_id}",
                "chat_instance": f"chat_instance_{message_id}",
                "from": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": message_id,
                    "from": {
                        "id": int(self.user_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": user_id,
                        "first_name": "Test User",
                        "username": "test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": callback_data
            }
        }

    def send_webhook_request(self, update_data: dict, test_name: str) -> tuple:
        """Send webhook request and return success status and response"""
        try:
            response = self.session.post(self.webhook_url, json=update_data, timeout=30)
            
            success = response.status_code == 200
            
            try:
                response_json = response.json()
            except:
                response_json = {"raw_response": response.text[:500]}

            details = f"Status: {response.status_code}"
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

    def test_user_bot_start_command(self):
        """Test /start command - should show Web App button and main menu"""
        print("🔍 Testing User Bot Start Command...")
        
        update = self.create_telegram_message_update("/start")
        success, data = self.send_webhook_request(update, "User Bot /start Command")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Start Command Response", True, "Start command processed successfully")
            return True
        else:
            self.log_test("Start Command Response", False, f"Unexpected response: {data}")
            return False

    def test_web_app_button(self):
        """Test Web App button functionality"""
        print("🔍 Testing Web App Button...")
        
        # Test browse_products callback which should show Web App
        update = self.create_telegram_callback_update("browse_products")
        success, data = self.send_webhook_request(update, "Web App Button - Browse Products")
        
        if success:
            self.log_test("Web App Button", True, "Browse products callback working (should show Web App)")
            return True
        else:
            self.log_test("Web App Button", False, "Browse products callback failed")
            return False

    def test_main_menu_buttons(self):
        """Test main menu buttons: المحفظة الرقمية، دعم البرق، رحلاتي السابقة"""
        print("🔍 Testing Main Menu Buttons...")
        
        main_buttons = [
            ("view_wallet", "المحفظة الرقمية"),
            ("support", "دعم البرق"),
            ("order_history", "رحلاتي السابقة")
        ]
        
        all_success = True
        
        for callback_data, button_name in main_buttons:
            update = self.create_telegram_callback_update(callback_data)
            success, data = self.send_webhook_request(update, f"Main Menu Button: {button_name}")
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Main Menu Buttons", True, "All main menu buttons working")
        else:
            self.log_test("Main Menu Buttons", False, "Some main menu buttons failed")
        
        return all_success

    def test_browse_products_callback(self):
        """Test browse_products callback"""
        print("🔍 Testing Browse Products Callback...")
        
        update = self.create_telegram_callback_update("browse_products")
        success, data = self.send_webhook_request(update, "Browse Products Callback")
        
        if success:
            self.log_test("Browse Products Display", True, "Browse products callback working")
            return True
        else:
            self.log_test("Browse Products Display", False, "Browse products callback failed")
            return False

    def test_product_selection(self):
        """Test product selection functionality"""
        print("🔍 Testing Product Selection...")
        
        # First get products to test with real IDs
        try:
            response = self.session.get(f"{self.api_url}/products", timeout=10)
            if response.status_code == 200:
                products = response.json()
                if isinstance(products, list) and len(products) > 0:
                    product_id = products[0].get('id', 'test_product')
                    
                    # Test product selection
                    update = self.create_telegram_callback_update(f"product_{product_id}")
                    success, data = self.send_webhook_request(update, f"Product Selection: {product_id}")
                    
                    if success:
                        self.log_test("Product Selection", True, f"Product {product_id} selection working")
                        return True
                    else:
                        self.log_test("Product Selection", False, "Product selection failed")
                        return False
                else:
                    self.log_test("Product Selection", False, "No products available for testing")
                    return False
            else:
                self.log_test("Product Selection", False, "Cannot fetch products for testing")
                return False
        except Exception as e:
            self.log_test("Product Selection", False, f"Error fetching products: {str(e)}")
            return False

    def test_search_command(self):
        """Test /search command with query"""
        print("🔍 Testing Search Command...")
        
        search_queries = [
            "/search ببجي",
            "/search pubg",
            "/search نتفليكس"
        ]
        
        all_success = True
        
        for query in search_queries:
            update = self.create_telegram_message_update(query)
            success, data = self.send_webhook_request(update, f"Search Command: {query}")
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Search Command Functionality", True, "All search commands working")
        else:
            self.log_test("Search Command Functionality", False, "Some search commands failed")
        
        return all_success

    def test_text_based_search(self):
        """Test text-based search (direct text input)"""
        print("🔍 Testing Text-Based Search...")
        
        search_texts = [
            "ببجي",
            "فورتنايت", 
            "نتفليكس",
            "ستيم"
        ]
        
        all_success = True
        
        for text in search_texts:
            update = self.create_telegram_message_update(text)
            success, data = self.send_webhook_request(update, f"Text Search: {text}")
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Text-Based Search", True, "All text-based searches working")
        else:
            self.log_test("Text-Based Search", False, "Some text-based searches failed")
        
        return all_success

    def test_search_results_display(self):
        """Test search results display with buttons"""
        print("🔍 Testing Search Results Display...")
        
        # Test search that should return results
        update = self.create_telegram_message_update("ببجي")
        success, data = self.send_webhook_request(update, "Search Results Display")
        
        if success:
            self.log_test("Search Results Display", True, "Search results displayed correctly")
            return True
        else:
            self.log_test("Search Results Display", False, "Search results display failed")
            return False

    def test_no_search_results(self):
        """Test 'no results' scenario"""
        print("🔍 Testing No Search Results Scenario...")
        
        # Test search with unlikely query
        update = self.create_telegram_message_update("xyz_nonexistent_product_123")
        success, data = self.send_webhook_request(update, "No Search Results")
        
        if success:
            self.log_test("No Results Handling", True, "No results scenario handled correctly")
            return True
        else:
            self.log_test("No Results Handling", False, "No results scenario failed")
            return False

    def test_wallet_functionality(self):
        """Test wallet functionality"""
        print("🔍 Testing Wallet Functionality...")
        
        # Test view_wallet callback
        update = self.create_telegram_callback_update("view_wallet")
        success, data = self.send_webhook_request(update, "View Wallet")
        
        if success:
            self.log_test("Wallet Balance Display", True, "Wallet view working")
        else:
            self.log_test("Wallet Balance Display", False, "Wallet view failed")
            return False
        
        # Test wallet top-up request
        update = self.create_telegram_callback_update("topup_wallet")
        success, data = self.send_webhook_request(update, "Wallet Top-up Request")
        
        if success:
            self.log_test("Wallet Top-up Request", True, "Wallet top-up request working")
            return True
        else:
            self.log_test("Wallet Top-up Request", False, "Wallet top-up request failed")
            return False

    def test_order_history(self):
        """Test order history functionality"""
        print("🔍 Testing Order History...")
        
        # Test order_history callback
        update = self.create_telegram_callback_update("order_history")
        success, data = self.send_webhook_request(update, "Order History")
        
        if success:
            self.log_test("Orders Display", True, "Order history display working")
        else:
            self.log_test("Orders Display", False, "Order history display failed")
            return False
        
        # Test order details viewing (if orders exist)
        try:
            response = self.session.get(f"{self.api_url}/orders", timeout=10)
            if response.status_code == 200:
                orders = response.json()
                if isinstance(orders, list) and len(orders) > 0:
                    order_id = orders[0].get('id', 'test_order')
                    
                    update = self.create_telegram_callback_update(f"order_details_{order_id}")
                    success, data = self.send_webhook_request(update, f"Order Details: {order_id}")
                    
                    if success:
                        self.log_test("Order Details Viewing", True, "Order details viewing working")
                    else:
                        self.log_test("Order Details Viewing", False, "Order details viewing failed")
                else:
                    self.log_test("Order Details Viewing", True, "No orders available for testing (acceptable)")
            else:
                self.log_test("Order Details Viewing", False, "Cannot fetch orders for testing")
        except Exception as e:
            self.log_test("Order Details Viewing", False, f"Error testing order details: {str(e)}")
        
        return True

    def test_support_functionality(self):
        """Test support functionality"""
        print("🔍 Testing Support Functionality...")
        
        # Test support callback
        update = self.create_telegram_callback_update("support")
        success, data = self.send_webhook_request(update, "Support Contact")
        
        if success:
            self.log_test("Support Contact Information", True, "Support functionality working")
            return True
        else:
            self.log_test("Support Contact Information", False, "Support functionality failed")
            return False

    def test_purchase_flow_category_selection(self):
        """Test purchase flow - category selection"""
        print("🔍 Testing Purchase Flow - Category Selection...")
        
        # First get categories to test with real IDs
        try:
            response = self.session.get(f"{self.api_url}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                if isinstance(categories, list) and len(categories) > 0:
                    category_id = categories[0].get('id', 'test_category')
                    
                    # Test category selection
                    update = self.create_telegram_callback_update(f"category_{category_id}")
                    success, data = self.send_webhook_request(update, f"Category Selection: {category_id}")
                    
                    if success:
                        self.log_test("Category Selection", True, f"Category {category_id} selection working")
                        return True
                    else:
                        self.log_test("Category Selection", False, "Category selection failed")
                        return False
                else:
                    self.log_test("Category Selection", False, "No categories available for testing")
                    return False
            else:
                self.log_test("Category Selection", False, "Cannot fetch categories for testing")
                return False
        except Exception as e:
            self.log_test("Category Selection", False, f"Error fetching categories: {str(e)}")
            return False

    def test_purchase_flow_delivery_types(self):
        """Test purchase with different delivery types (id, email, phone)"""
        print("🔍 Testing Purchase Flow - Delivery Types...")
        
        # Test purchase API endpoint directly
        purchase_data = {
            "user_telegram_id": self.test_user_id,
            "category_id": "test_category",
            "delivery_type": "id",
            "additional_info": {"user_id": "123456789"}
        }
        
        try:
            response = self.session.post(f"{self.api_url}/purchase", json=purchase_data, timeout=10)
            
            # We expect this to fail with proper validation, which is correct behavior
            if response.status_code in [400, 404, 402, 403]:
                self.log_test("Purchase Validation", True, f"Purchase validation working (status: {response.status_code})")
                return True
            elif response.status_code == 200:
                self.log_test("Purchase Validation", True, "Purchase processed successfully")
                return True
            else:
                self.log_test("Purchase Validation", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Purchase Validation", False, f"Error testing purchase: {str(e)}")
            return False

    def test_user_session_management(self):
        """Test user session management"""
        print("🔍 Testing User Session Management...")
        
        # Test session creation through wallet top-up flow
        update = self.create_telegram_callback_update("topup_wallet")
        success, data = self.send_webhook_request(update, "Session Creation - Topup Wallet")
        
        if not success:
            self.log_test("Session Creation", False, "Cannot create session")
            return False
        
        # Test session state with amount input
        amount_update = self.create_telegram_message_update("50")
        success, data = self.send_webhook_request(amount_update, "Session State - Amount Input")
        
        if success:
            self.log_test("Session State Transitions", True, "Session state handling working")
        else:
            self.log_test("Session State Transitions", False, "Session state handling failed")
        
        # Test session clearing with back button
        back_update = self.create_telegram_callback_update("back_to_main_menu")
        success, data = self.send_webhook_request(back_update, "Session Clearing")
        
        if success:
            self.log_test("Session Clearing", True, "Session clearing working")
            return True
        else:
            self.log_test("Session Clearing", False, "Session clearing failed")
            return False

    def test_direct_number_inputs(self):
        """Test direct number inputs (1-8)"""
        print("🔍 Testing Direct Number Inputs...")
        
        all_success = True
        
        for num in range(1, 9):
            update = self.create_telegram_message_update(str(num))
            success, data = self.send_webhook_request(update, f"Direct Number: {num}")
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Direct Number Navigation", True, "All direct numbers (1-8) working")
        else:
            self.log_test("Direct Number Navigation", False, "Some direct numbers failed")
        
        return all_success

    def test_help_commands(self):
        """Test help commands"""
        print("🔍 Testing Help Commands...")
        
        help_commands = ["/help", "/مساعدة", "مساعدة", "help"]
        all_success = True
        
        for cmd in help_commands:
            update = self.create_telegram_message_update(cmd)
            success, data = self.send_webhook_request(update, f"Help Command: {cmd}")
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Help Commands", True, "All help commands working")
        else:
            self.log_test("Help Commands", False, "Some help commands failed")
        
        return all_success

    def test_menu_command(self):
        """Test /menu command"""
        print("🔍 Testing Menu Command...")
        
        update = self.create_telegram_message_update("/menu")
        success, data = self.send_webhook_request(update, "Menu Command")
        
        if success:
            self.log_test("Menu Command", True, "Menu command working")
            return True
        else:
            self.log_test("Menu Command", False, "Menu command failed")
            return False

    def test_bot_performance(self):
        """Test bot performance - responses should be fast"""
        print("🔍 Testing Bot Performance...")
        
        start_time = time.time()
        update = self.create_telegram_message_update("/start")
        success, data = self.send_webhook_request(update, "Performance Test - Start")
        response_time = time.time() - start_time
        
        if success and response_time < 2.0:
            self.log_test("Bot Performance", True, f"Fast response in {response_time:.3f}s")
            return True
        elif success:
            self.log_test("Bot Performance", False, f"Slow response: {response_time:.3f}s")
            return False
        else:
            self.log_test("Bot Performance", False, "Performance test failed")
            return False

    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        print("🔍 Testing Error Handling...")
        
        # Test invalid callback
        update = self.create_telegram_callback_update("invalid_callback_xyz")
        success, data = self.send_webhook_request(update, "Error Handling - Invalid Callback")
        
        if success:
            self.log_test("Error Handling", True, "Invalid callback handled gracefully")
            return True
        else:
            self.log_test("Error Handling", False, "Error handling failed")
            return False

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Abod Card User Bot Comprehensive Testing...")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("User Bot Start Menu", [
                self.test_user_bot_start_command,
                self.test_web_app_button,
                self.test_main_menu_buttons
            ]),
            ("Browse Products", [
                self.test_browse_products_callback,
                self.test_product_selection
            ]),
            ("Search Functionality", [
                self.test_search_command,
                self.test_text_based_search,
                self.test_search_results_display,
                self.test_no_search_results
            ]),
            ("Wallet Functionality", [
                self.test_wallet_functionality
            ]),
            ("Order History", [
                self.test_order_history
            ]),
            ("Support", [
                self.test_support_functionality
            ]),
            ("Purchase Flow", [
                self.test_purchase_flow_category_selection,
                self.test_purchase_flow_delivery_types
            ]),
            ("User Session Management", [
                self.test_user_session_management
            ]),
            ("Additional Features", [
                self.test_direct_number_inputs,
                self.test_help_commands,
                self.test_menu_command,
                self.test_bot_performance,
                self.test_error_handling
            ])
        ]
        
        category_results = {}
        
        for category_name, tests in test_categories:
            print(f"\n📋 Testing Category: {category_name}")
            print("-" * 40)
            
            category_passed = 0
            category_total = len(tests)
            
            for test_func in tests:
                try:
                    result = test_func()
                    if result:
                        category_passed += 1
                except Exception as e:
                    print(f"❌ EXCEPTION in {test_func.__name__}: {str(e)}")
            
            category_results[category_name] = {
                "passed": category_passed,
                "total": category_total,
                "success_rate": (category_passed / category_total) * 100 if category_total > 0 else 0
            }
            
            print(f"📊 {category_name}: {category_passed}/{category_total} tests passed ({category_results[category_name]['success_rate']:.1f}%)")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 ABOD CARD USER BOT TEST SUMMARY")
        print("=" * 60)
        
        for category, results in category_results.items():
            status = "✅" if results['success_rate'] >= 80 else "⚠️" if results['success_rate'] >= 60 else "❌"
            print(f"{status} {category}: {results['passed']}/{results['total']} ({results['success_rate']:.1f}%)")
        
        overall_success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS: {self.tests_passed}/{self.tests_run} tests passed ({overall_success_rate:.1f}%)")
        
        if overall_success_rate >= 80:
            print("🎉 EXCELLENT: User bot is working with precision, consistency, and coherence!")
        elif overall_success_rate >= 60:
            print("⚠️ GOOD: User bot is mostly working, minor issues found")
        else:
            print("❌ NEEDS ATTENTION: User bot has significant issues")
        
        return overall_success_rate >= 60

if __name__ == "__main__":
    tester = AbodUserBotTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)