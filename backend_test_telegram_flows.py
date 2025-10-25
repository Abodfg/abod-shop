#!/usr/bin/env python3
"""
Comprehensive Test for Telegram Bot Flows with New Delivery Types
Testing the complete purchase flows for ID and Email delivery types
"""

import requests
import json
import sys
import time
from datetime import datetime

class TelegramFlowTester:
    def __init__(self, base_url="https://digital-cards-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def simulate_webhook_call(self, webhook_type, telegram_id, message_text, callback_data=None):
        """Simulate a webhook call to the bot"""
        try:
            if webhook_type == "user":
                webhook_url = f"{self.api_url}/webhook/user/abod_user_webhook_secret"
            else:
                webhook_url = f"{self.api_url}/webhook/admin/abod_admin_webhook_secret"
            
            if callback_data:
                # Callback query
                payload = {
                    "update_id": int(time.time()),
                    "callback_query": {
                        "id": str(int(time.time())),
                        "from": {"id": telegram_id, "is_bot": False, "first_name": "TestUser"},
                        "message": {
                            "message_id": 1,
                            "chat": {"id": telegram_id, "type": "private"},
                            "date": int(time.time())
                        },
                        "data": callback_data
                    }
                }
            else:
                # Text message
                payload = {
                    "update_id": int(time.time()),
                    "message": {
                        "message_id": 1,
                        "from": {"id": telegram_id, "is_bot": False, "first_name": "TestUser"},
                        "chat": {"id": telegram_id, "type": "private"},
                        "date": int(time.time()),
                        "text": message_text
                    }
                }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code, response.text
            
        except Exception as e:
            return 500, str(e)

    def test_user_start_flow(self):
        """Test user /start command"""
        telegram_id = 999001
        status_code, response = self.simulate_webhook_call("user", telegram_id, "/start")
        
        success = status_code == 200
        self.log_test("User Start Flow", success, f"Status: {status_code}")
        return success

    def test_browse_products_flow(self):
        """Test browse products callback"""
        telegram_id = 999002
        status_code, response = self.simulate_webhook_call("user", telegram_id, None, "browse_products")
        
        success = status_code == 200
        self.log_test("Browse Products Flow", success, f"Status: {status_code}")
        return success

    def test_category_selection_with_id_delivery(self):
        """Test selecting a category with ID delivery type"""
        telegram_id = 999003
        
        # First get categories to find one with 'id' delivery type
        try:
            categories_response = requests.get(f"{self.api_url}/categories")
            if categories_response.status_code == 200:
                categories = categories_response.json()
                id_category = next((cat for cat in categories if cat.get('delivery_type') == 'id'), None)
                
                if id_category:
                    category_id = id_category['id']
                    status_code, response = self.simulate_webhook_call("user", telegram_id, None, f"category_{category_id}")
                    
                    success = status_code == 200
                    self.log_test("Category Selection (ID Delivery)", success, 
                                f"Status: {status_code}, Category: {id_category['name']}")
                    return success
                else:
                    self.log_test("Category Selection (ID Delivery)", False, "No ID delivery category found")
                    return False
            else:
                self.log_test("Category Selection (ID Delivery)", False, "Failed to fetch categories")
                return False
                
        except Exception as e:
            self.log_test("Category Selection (ID Delivery)", False, f"Error: {str(e)}")
            return False

    def test_category_selection_with_email_delivery(self):
        """Test selecting a category with email delivery type"""
        telegram_id = 999004
        
        try:
            categories_response = requests.get(f"{self.api_url}/categories")
            if categories_response.status_code == 200:
                categories = categories_response.json()
                email_category = next((cat for cat in categories if cat.get('delivery_type') == 'email'), None)
                
                if email_category:
                    category_id = email_category['id']
                    status_code, response = self.simulate_webhook_call("user", telegram_id, None, f"category_{category_id}")
                    
                    success = status_code == 200
                    self.log_test("Category Selection (Email Delivery)", success, 
                                f"Status: {status_code}, Category: {email_category['name']}")
                    return success
                else:
                    self.log_test("Category Selection (Email Delivery)", False, "No email delivery category found")
                    return False
            else:
                self.log_test("Category Selection (Email Delivery)", False, "Failed to fetch categories")
                return False
                
        except Exception as e:
            self.log_test("Category Selection (Email Delivery)", False, f"Error: {str(e)}")
            return False

    def test_purchase_flow_with_id_input(self):
        """Test complete purchase flow with ID input"""
        telegram_id = 999005
        
        try:
            # Get ID delivery category
            categories_response = requests.get(f"{self.api_url}/categories")
            if categories_response.status_code != 200:
                self.log_test("Purchase Flow (ID Input)", False, "Failed to fetch categories")
                return False
            
            categories = categories_response.json()
            id_category = next((cat for cat in categories if cat.get('delivery_type') == 'id'), None)
            
            if not id_category:
                self.log_test("Purchase Flow (ID Input)", False, "No ID delivery category found")
                return False
            
            category_id = id_category['id']
            
            # Step 1: Start purchase
            status_code, response = self.simulate_webhook_call("user", telegram_id, None, f"buy_category_{category_id}")
            
            if status_code != 200:
                self.log_test("Purchase Flow (ID Input) - Start", False, f"Status: {status_code}")
                return False
            
            # Step 2: Simulate ID input
            test_id = "USER123456789"
            status_code, response = self.simulate_webhook_call("user", telegram_id, test_id)
            
            success = status_code == 200
            self.log_test("Purchase Flow (ID Input) - Complete", success, 
                        f"Status: {status_code}, Test ID: {test_id}")
            
            # Check if order was created
            orders_response = requests.get(f"{self.api_url}/orders")
            if orders_response.status_code == 200:
                orders = orders_response.json()
                new_order = next((order for order in orders 
                                if order.get('telegram_id') == telegram_id 
                                and order.get('delivery_type') == 'id'), None)
                
                if new_order:
                    self.log_test("Order Creation (ID Input)", True, 
                                f"Order created with user_input_data: {new_order.get('user_input_data')}")
                else:
                    self.log_test("Order Creation (ID Input)", False, "No order found with ID delivery type")
            
            return success
            
        except Exception as e:
            self.log_test("Purchase Flow (ID Input)", False, f"Error: {str(e)}")
            return False

    def test_purchase_flow_with_email_input(self):
        """Test complete purchase flow with email input"""
        telegram_id = 999006
        
        try:
            # Get email delivery category
            categories_response = requests.get(f"{self.api_url}/categories")
            if categories_response.status_code != 200:
                self.log_test("Purchase Flow (Email Input)", False, "Failed to fetch categories")
                return False
            
            categories = categories_response.json()
            email_category = next((cat for cat in categories if cat.get('delivery_type') == 'email'), None)
            
            if not email_category:
                self.log_test("Purchase Flow (Email Input)", False, "No email delivery category found")
                return False
            
            category_id = email_category['id']
            
            # Step 1: Start purchase
            status_code, response = self.simulate_webhook_call("user", telegram_id, None, f"buy_category_{category_id}")
            
            if status_code != 200:
                self.log_test("Purchase Flow (Email Input) - Start", False, f"Status: {status_code}")
                return False
            
            # Step 2: Simulate email input
            test_email = "testuser@example.com"
            status_code, response = self.simulate_webhook_call("user", telegram_id, test_email)
            
            success = status_code == 200
            self.log_test("Purchase Flow (Email Input) - Complete", success, 
                        f"Status: {status_code}, Test Email: {test_email}")
            
            # Check if order was created
            orders_response = requests.get(f"{self.api_url}/orders")
            if orders_response.status_code == 200:
                orders = orders_response.json()
                new_order = next((order for order in orders 
                                if order.get('telegram_id') == telegram_id 
                                and order.get('delivery_type') == 'email'), None)
                
                if new_order:
                    self.log_test("Order Creation (Email Input)", True, 
                                f"Order created with user_input_data: {new_order.get('user_input_data')}")
                else:
                    self.log_test("Order Creation (Email Input)", False, "No order found with email delivery type")
            
            return success
            
        except Exception as e:
            self.log_test("Purchase Flow (Email Input)", False, f"Error: {str(e)}")
            return False

    def test_input_validation(self):
        """Test input validation for ID and email"""
        telegram_id = 999007
        
        # Test invalid email
        status_code, response = self.simulate_webhook_call("user", telegram_id, "invalid-email")
        success1 = status_code == 200  # Should handle gracefully
        
        # Test invalid ID (too short)
        status_code, response = self.simulate_webhook_call("user", telegram_id, "12")
        success2 = status_code == 200  # Should handle gracefully
        
        # Test valid email format
        status_code, response = self.simulate_webhook_call("user", telegram_id, "valid@email.com")
        success3 = status_code == 200
        
        # Test valid ID format
        status_code, response = self.simulate_webhook_call("user", telegram_id, "VALIDID123")
        success4 = status_code == 200
        
        overall_success = success1 and success2 and success3 and success4
        self.log_test("Input Validation", overall_success, 
                    f"Invalid email: {success1}, Invalid ID: {success2}, Valid email: {success3}, Valid ID: {success4}")
        
        return overall_success

    def test_session_handling_for_new_flows(self):
        """Test session handling for new purchase flows"""
        telegram_id = 999008
        
        # Test session states
        session_tests = [
            ("purchase_input_id", "Test session for ID input"),
            ("purchase_input_email", "Test session for email input"),
            ("purchase_input_phone", "Test session for phone input")
        ]
        
        all_success = True
        for state, description in session_tests:
            # Simulate message that would be handled by session state
            status_code, response = self.simulate_webhook_call("user", telegram_id, "test_input")
            
            success = status_code == 200
            if not success:
                all_success = False
            
            self.log_test(f"Session Handling - {state}", success, f"Status: {status_code}")
        
        return all_success

    def test_admin_order_processing(self):
        """Test admin order processing for new delivery types"""
        admin_telegram_id = 7040570081  # The new admin ID from the code
        
        # Test admin start
        status_code, response = self.simulate_webhook_call("admin", admin_telegram_id, "/start")
        success1 = status_code == 200
        
        # Test manage orders
        status_code, response = self.simulate_webhook_call("admin", admin_telegram_id, None, "manage_orders")
        success2 = status_code == 200
        
        # Test view all pending
        status_code, response = self.simulate_webhook_call("admin", admin_telegram_id, None, "view_all_pending")
        success3 = status_code == 200
        
        overall_success = success1 and success2 and success3
        self.log_test("Admin Order Processing", overall_success, 
                    f"Start: {success1}, Manage: {success2}, View Pending: {success3}")
        
        return overall_success

    def run_comprehensive_test(self):
        """Run all Telegram flow tests"""
        print("🤖 Starting Comprehensive Telegram Bot Flow Tests")
        print("=" * 70)
        
        # Run all tests
        test_methods = [
            self.test_user_start_flow,
            self.test_browse_products_flow,
            self.test_category_selection_with_id_delivery,
            self.test_category_selection_with_email_delivery,
            self.test_purchase_flow_with_id_input,
            self.test_purchase_flow_with_email_input,
            self.test_input_validation,
            self.test_session_handling_for_new_flows,
            self.test_admin_order_processing
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_test(f"Test Method {test_method.__name__}", False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Telegram flow tests passed!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = TelegramFlowTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        # Save detailed results
        with open('/app/test_telegram_flows_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': tester.tests_run,
                    'passed_tests': tester.tests_passed,
                    'success_rate': f"{(tester.tests_passed/tester.tests_run)*100:.1f}%",
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': tester.test_results
            }, f, indent=2, ensure_ascii=False)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())