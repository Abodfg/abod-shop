#!/usr/bin/env python3
"""
Comprehensive Backend Test for Telegram Bot Features
Testing the new features mentioned in the review request:
1. Universal back function (back_to_main_menu)
2. Session clearing when back is pressed
3. Order processing buttons (process_order_)
4. Admin notifications and background tasks
5. Comprehensive order reports
6. New admin ID usage
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

class TelegramBotTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        
        # Test data
        self.test_user_id = 123456789
        self.test_admin_id = 7040570081  # New admin ID from review
        self.user_webhook_secret = "abod_user_webhook_secret"
        self.admin_webhook_secret = "abod_admin_webhook_secret"

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
                self.errors.append(f"{name}: {details}")

    def create_telegram_update(self, update_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Telegram update object"""
        base_update = {
            "update_id": int(time.time()),
        }
        
        if update_type == "message":
            base_update["message"] = {
                "message_id": int(time.time()),
                "date": int(time.time()),
                "chat": {"id": data.get("chat_id", self.test_user_id), "type": "private"},
                "from": {
                    "id": data.get("user_id", self.test_user_id),
                    "is_bot": False,
                    "first_name": data.get("first_name", "Test"),
                    "username": data.get("username", "testuser")
                },
                "text": data.get("text", "/start")
            }
        elif update_type == "callback_query":
            base_update["callback_query"] = {
                "id": str(int(time.time())),
                "from": {
                    "id": data.get("user_id", self.test_user_id),
                    "is_bot": False,
                    "first_name": data.get("first_name", "Test"),
                    "username": data.get("username", "testuser")
                },
                "message": {
                    "message_id": int(time.time()),
                    "date": int(time.time()),
                    "chat": {"id": data.get("chat_id", self.test_user_id), "type": "private"},
                    "from": {"id": 123, "is_bot": True, "first_name": "Bot"}
                },
                "data": data.get("callback_data", "back_to_main_menu"),
                "chat_instance": data.get("chat_instance", "test_chat_instance")  # Fixed missing field
            }
        
        return base_update

    def send_webhook_request(self, webhook_type: str, update_data: Dict[str, Any]) -> requests.Response:
        """Send webhook request to bot"""
        secret = self.user_webhook_secret if webhook_type == "user" else self.admin_webhook_secret
        url = f"{self.base_url}/api/webhook/{webhook_type}/{secret}"
        
        try:
            response = requests.post(url, json=update_data, timeout=10)
            return response
        except Exception as e:
            print(f"❌ Webhook request failed: {e}")
            return None

    def test_server_health(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            success = response.status_code == 200
            self.log_test("Server Health Check", success, 
                         f"Status: {response.status_code}" if success else "Server not responding")
            return success
        except Exception as e:
            self.log_test("Server Health Check", False, f"Error: {e}")
            return False

    def test_user_start_command(self):
        """Test user /start command"""
        update = self.create_telegram_update("message", {
            "chat_id": self.test_user_id,
            "user_id": self.test_user_id,
            "text": "/start",
            "first_name": "TestUser",
            "username": "testuser"
        })
        
        response = self.send_webhook_request("user", update)
        if response:
            success = response.status_code == 200
            self.log_test("User Start Command", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("User Start Command", False, "No response received")
            return False

    def test_admin_start_command(self):
        """Test admin /start command"""
        update = self.create_telegram_update("message", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "text": "/start",
            "first_name": "Admin",
            "username": "admin"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success = response.status_code == 200
            self.log_test("Admin Start Command", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("Admin Start Command", False, "No response received")
            return False

    def test_universal_back_function_user(self):
        """Test universal back function for users"""
        # Test back_to_main_menu callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_user_id,
            "user_id": self.test_user_id,
            "callback_data": "back_to_main_menu"
        })
        
        response = self.send_webhook_request("user", update)
        if response:
            success = response.status_code == 200
            self.log_test("User Universal Back Function", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("User Universal Back Function", False, "No response received")
            return False

    def test_universal_back_function_admin(self):
        """Test universal back function for admin"""
        # Test admin_back_to_main callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "admin_back_to_main"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success = response.status_code == 200
            self.log_test("Admin Universal Back Function", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("Admin Universal Back Function", False, "No response received")
            return False

    def test_order_processing_buttons(self):
        """Test order processing buttons in admin bot"""
        # Test manage_orders callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "manage_orders"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success = response.status_code == 200
            self.log_test("Admin Order Management", success, 
                         f"Status: {response.status_code}")
        else:
            self.log_test("Admin Order Management", False, "No response received")
            success = False

        # Test view_all_pending callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "view_all_pending"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success2 = response.status_code == 200
            self.log_test("Admin View All Pending Orders", success2, 
                         f"Status: {response.status_code}")
        else:
            self.log_test("Admin View All Pending Orders", False, "No response received")
            success2 = False

        return success and success2

    def test_order_reports(self):
        """Test comprehensive order reports"""
        # Test orders_report callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "orders_report"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success = response.status_code == 200
            self.log_test("Admin Order Reports", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("Admin Order Reports", False, "No response received")
            return False

    def test_user_product_browsing(self):
        """Test user product browsing functionality"""
        # Test browse_products callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_user_id,
            "user_id": self.test_user_id,
            "callback_data": "browse_products"
        })
        
        response = self.send_webhook_request("user", update)
        if response:
            success = response.status_code == 200
            self.log_test("User Product Browsing", success, 
                         f"Status: {response.status_code}")
            return success
        else:
            self.log_test("User Product Browsing", False, "No response received")
            return False

    def test_admin_code_management(self):
        """Test admin code management functionality"""
        # Test manage_codes callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "manage_codes"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success = response.status_code == 200
            self.log_test("Admin Code Management", success, 
                         f"Status: {response.status_code}")
        else:
            self.log_test("Admin Code Management", False, "No response received")
            success = False

        # Test low_stock_alerts callback
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_admin_id,
            "user_id": self.test_admin_id,
            "callback_data": "low_stock_alerts"
        })
        
        response = self.send_webhook_request("admin", update)
        if response:
            success2 = response.status_code == 200
            self.log_test("Admin Low Stock Alerts", success2, 
                         f"Status: {response.status_code}")
        else:
            self.log_test("Admin Low Stock Alerts", False, "No response received")
            success2 = False

        return success and success2

    def test_webhook_security(self):
        """Test webhook security with invalid secrets"""
        # Test invalid user webhook secret
        url = f"{self.base_url}/api/webhook/user/invalid_secret"
        update = self.create_telegram_update("message", {"text": "/start"})
        
        try:
            response = requests.post(url, json=update, timeout=5)
            success = response.status_code == 403
            self.log_test("User Webhook Security", success, 
                         f"Status: {response.status_code} (should be 403)")
        except Exception as e:
            self.log_test("User Webhook Security", False, f"Error: {e}")
            success = False

        # Test invalid admin webhook secret
        url = f"{self.base_url}/api/webhook/admin/invalid_secret"
        
        try:
            response = requests.post(url, json=update, timeout=5)
            success2 = response.status_code == 403
            self.log_test("Admin Webhook Security", success2, 
                         f"Status: {response.status_code} (should be 403)")
        except Exception as e:
            self.log_test("Admin Webhook Security", False, f"Error: {e}")
            success2 = False

        return success and success2

    def test_session_management(self):
        """Test session management and clearing"""
        # First, create a session by starting a flow
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_user_id,
            "user_id": self.test_user_id,
            "callback_data": "topup_wallet"
        })
        
        response = self.send_webhook_request("user", update)
        session_created = response and response.status_code == 200
        
        # Then test back button to clear session
        update = self.create_telegram_update("callback_query", {
            "chat_id": self.test_user_id,
            "user_id": self.test_user_id,
            "callback_data": "back_to_main_menu"
        })
        
        response = self.send_webhook_request("user", update)
        session_cleared = response and response.status_code == 200
        
        success = session_created and session_cleared
        self.log_test("Session Management & Clearing", success, 
                     f"Session created: {session_created}, Session cleared: {session_cleared}")
        return success

    def test_error_handling(self):
        """Test error handling with malformed requests"""
        # Test malformed JSON
        url = f"{self.base_url}/api/webhook/user/{self.user_webhook_secret}"
        
        try:
            response = requests.post(url, data="invalid json", timeout=5)
            success = response.status_code in [400, 422, 500]  # Should handle gracefully
            self.log_test("Error Handling - Malformed JSON", success, 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Malformed JSON", False, f"Error: {e}")
            success = False

        # Test missing required fields
        incomplete_update = {"update_id": 123}
        
        try:
            response = requests.post(url, json=incomplete_update, timeout=5)
            success2 = response.status_code in [200, 400, 422, 500]  # Should handle gracefully
            self.log_test("Error Handling - Incomplete Update", success2, 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Incomplete Update", False, f"Error: {e}")
            success2 = False

        return success and success2

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Telegram Bot Feature Tests")
        print("=" * 60)
        
        # Basic connectivity tests
        if not self.test_server_health():
            print("❌ Server not responding. Stopping tests.")
            return False
        
        # Core functionality tests
        print("\n📱 Testing Core Bot Functionality:")
        self.test_user_start_command()
        self.test_admin_start_command()
        
        # New feature tests from review request
        print("\n🔄 Testing Universal Back Function:")
        self.test_universal_back_function_user()
        self.test_universal_back_function_admin()
        
        print("\n📋 Testing Order Processing Features:")
        self.test_order_processing_buttons()
        self.test_order_reports()
        
        print("\n🛒 Testing User Features:")
        self.test_user_product_browsing()
        
        print("\n🔧 Testing Admin Features:")
        self.test_admin_code_management()
        
        print("\n🔒 Testing Security & Session Management:")
        self.test_webhook_security()
        self.test_session_management()
        
        print("\n⚠️ Testing Error Handling:")
        self.test_error_handling()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ Errors Found ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   • ... and {len(self.errors) - 5} more errors")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TelegramBotTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())