#!/usr/bin/env python3
"""
Advanced Scenario Testing for Telegram Bot Features
Testing complex user flows and edge cases:
1. Complete user purchase flow with session management
2. Admin order processing with code input
3. Back button functionality during different states
4. Error handling and recovery
5. Multi-step flows with session persistence
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import pymongo
from pymongo import MongoClient

class AdvancedScenarioTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []
        
        # Database connection
        self.mongo_client = MongoClient("mongodb://localhost:27017")
        self.db = self.mongo_client["test_database"]
        
        # Test data
        self.test_user_id = 555666777
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
            "update_id": int(time.time() * 1000),  # Unique update ID
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
                "id": str(int(time.time() * 1000)),
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
                "chat_instance": data.get("chat_instance", f"test_chat_{int(time.time())}")
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

    def setup_test_user(self):
        """Setup test user with balance"""
        try:
            # Remove existing test user
            self.db.users.delete_many({"telegram_id": self.test_user_id})
            self.db.user_sessions.delete_many({"telegram_id": self.test_user_id})
            
            # Create test user with sufficient balance
            test_user = {
                "id": f"test_user_advanced_{int(time.time())}",
                "telegram_id": self.test_user_id,
                "username": "advancedtestuser",
                "first_name": "Advanced Test User",
                "balance": 50.0,  # Sufficient balance for testing
                "join_date": datetime.now(timezone.utc),
                "orders_count": 0
            }
            self.db.users.insert_one(test_user)
            
            self.log_test("Test User Setup", True, f"Created user with balance: ${test_user['balance']}")
            return True
            
        except Exception as e:
            self.log_test("Test User Setup", False, f"Error: {e}")
            return False

    def test_complete_user_purchase_flow(self):
        """Test complete user purchase flow from start to finish"""
        try:
            success_steps = []
            
            # Step 1: User starts bot
            update = self.create_telegram_update("message", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "text": "/start",
                "first_name": "AdvancedTest",
                "username": "advancedtest"
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code == 200:
                success_steps.append("User start")
            
            time.sleep(0.5)  # Small delay between requests
            
            # Step 2: Browse products
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "browse_products"
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code == 200:
                success_steps.append("Browse products")
            
            time.sleep(0.5)
            
            # Step 3: Check wallet
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "view_wallet"
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code == 200:
                success_steps.append("View wallet")
            
            time.sleep(0.5)
            
            # Step 4: Test back button functionality
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "back_to_main_menu"
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code == 200:
                success_steps.append("Back to main menu")
            
            # Verify session was cleared
            session = self.db.user_sessions.find_one({"telegram_id": self.test_user_id})
            if session is None:
                success_steps.append("Session cleared")
            
            success = len(success_steps) >= 4
            self.log_test("Complete User Purchase Flow", success, 
                         f"Completed steps: {', '.join(success_steps)}")
            return success
            
        except Exception as e:
            self.log_test("Complete User Purchase Flow", False, f"Error: {e}")
            return False

    def test_admin_order_management_flow(self):
        """Test admin order management flow"""
        try:
            success_steps = []
            
            # Step 1: Admin starts bot
            update = self.create_telegram_update("message", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "text": "/start",
                "first_name": "Admin",
                "username": "admin"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Admin start")
            
            time.sleep(0.5)
            
            # Step 2: Access order management
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "manage_orders"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Manage orders")
            
            time.sleep(0.5)
            
            # Step 3: View all pending orders
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "view_all_pending"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("View pending orders")
            
            time.sleep(0.5)
            
            # Step 4: View order reports
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "orders_report"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Order reports")
            
            time.sleep(0.5)
            
            # Step 5: Test admin back button
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "admin_back_to_main"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Admin back button")
            
            # Verify admin session was cleared
            session = self.db.admin_sessions.find_one({"telegram_id": self.test_admin_id})
            if session is None:
                success_steps.append("Admin session cleared")
            
            success = len(success_steps) >= 5
            self.log_test("Admin Order Management Flow", success, 
                         f"Completed steps: {', '.join(success_steps)}")
            return success
            
        except Exception as e:
            self.log_test("Admin Order Management Flow", False, f"Error: {e}")
            return False

    def test_session_persistence_and_interruption(self):
        """Test session persistence and interruption with back button"""
        try:
            # Step 1: Start a multi-step process (wallet topup)
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "topup_wallet"
            })
            
            response = self.send_webhook_request("user", update)
            session_created = response and response.status_code == 200
            
            # Verify session was created
            session = self.db.user_sessions.find_one({"telegram_id": self.test_user_id})
            session_exists = session is not None and session.get("state") == "wallet_topup_amount"
            
            time.sleep(0.5)
            
            # Step 2: Interrupt with back button
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "back_to_main_menu"
            })
            
            response = self.send_webhook_request("user", update)
            session_interrupted = response and response.status_code == 200
            
            # Verify session was cleared
            session_after = self.db.user_sessions.find_one({"telegram_id": self.test_user_id})
            session_cleared = session_after is None
            
            success = session_created and session_exists and session_interrupted and session_cleared
            self.log_test("Session Persistence and Interruption", success, 
                         f"Created: {session_created}, Exists: {session_exists}, Interrupted: {session_interrupted}, Cleared: {session_cleared}")
            return success
            
        except Exception as e:
            self.log_test("Session Persistence and Interruption", False, f"Error: {e}")
            return False

    def test_admin_code_management_flow(self):
        """Test admin code management functionality"""
        try:
            success_steps = []
            
            # Step 1: Access code management
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "manage_codes"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Access code management")
            
            time.sleep(0.5)
            
            # Step 2: Check low stock alerts
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "low_stock_alerts"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Low stock alerts")
            
            time.sleep(0.5)
            
            # Step 3: View codes
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "view_codes"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("View codes")
            
            time.sleep(0.5)
            
            # Step 4: Add codes
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "add_codes"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code == 200:
                success_steps.append("Add codes")
            
            success = len(success_steps) >= 3
            self.log_test("Admin Code Management Flow", success, 
                         f"Completed steps: {', '.join(success_steps)}")
            return success
            
        except Exception as e:
            self.log_test("Admin Code Management Flow", False, f"Error: {e}")
            return False

    def test_error_recovery_scenarios(self):
        """Test error recovery scenarios"""
        try:
            success_scenarios = []
            
            # Scenario 1: Invalid callback data
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "callback_data": "invalid_callback_data_12345"
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code in [200, 400, 422]:  # Should handle gracefully
                success_scenarios.append("Invalid callback handled")
            
            time.sleep(0.5)
            
            # Scenario 2: Callback for non-existent order
            update = self.create_telegram_update("callback_query", {
                "chat_id": self.test_admin_id,
                "user_id": self.test_admin_id,
                "callback_data": "process_order_nonexistent_order_id_12345"
            })
            
            response = self.send_webhook_request("admin", update)
            if response and response.status_code in [200, 400, 422]:  # Should handle gracefully
                success_scenarios.append("Non-existent order handled")
            
            time.sleep(0.5)
            
            # Scenario 3: Empty message
            update = self.create_telegram_update("message", {
                "chat_id": self.test_user_id,
                "user_id": self.test_user_id,
                "text": ""
            })
            
            response = self.send_webhook_request("user", update)
            if response and response.status_code in [200, 400, 422]:  # Should handle gracefully
                success_scenarios.append("Empty message handled")
            
            success = len(success_scenarios) >= 2
            self.log_test("Error Recovery Scenarios", success, 
                         f"Handled scenarios: {', '.join(success_scenarios)}")
            return success
            
        except Exception as e:
            self.log_test("Error Recovery Scenarios", False, f"Error: {e}")
            return False

    def test_concurrent_user_sessions(self):
        """Test handling of multiple user sessions"""
        try:
            # Create sessions for multiple users
            user_ids = [self.test_user_id, self.test_user_id + 1, self.test_user_id + 2]
            success_count = 0
            
            for i, user_id in enumerate(user_ids):
                # Start different flows for each user
                callback_data = ["topup_wallet", "browse_products", "view_wallet"][i]
                
                update = self.create_telegram_update("callback_query", {
                    "chat_id": user_id,
                    "user_id": user_id,
                    "callback_data": callback_data
                })
                
                response = self.send_webhook_request("user", update)
                if response and response.status_code == 200:
                    success_count += 1
                
                time.sleep(0.3)
            
            # Verify sessions exist for all users
            sessions_created = 0
            for user_id in user_ids:
                session = self.db.user_sessions.find_one({"telegram_id": user_id})
                if session:
                    sessions_created += 1
            
            # Clean up sessions
            for user_id in user_ids:
                self.db.user_sessions.delete_one({"telegram_id": user_id})
            
            success = success_count >= 2 and sessions_created >= 2
            self.log_test("Concurrent User Sessions", success, 
                         f"Successful requests: {success_count}/3, Sessions created: {sessions_created}/3")
            return success
            
        except Exception as e:
            self.log_test("Concurrent User Sessions", False, f"Error: {e}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Remove test users and sessions
            self.db.users.delete_many({"telegram_id": {"$in": [
                self.test_user_id, 
                self.test_user_id + 1, 
                self.test_user_id + 2
            ]}})
            self.db.user_sessions.delete_many({"telegram_id": {"$in": [
                self.test_user_id, 
                self.test_user_id + 1, 
                self.test_user_id + 2
            ]}})
            self.db.admin_sessions.delete_many({"telegram_id": self.test_admin_id})
            
            self.log_test("Advanced Test Cleanup", True, "Removed test data")
            return True
            
        except Exception as e:
            self.log_test("Advanced Test Cleanup", False, f"Error: {e}")
            return False

    def run_all_tests(self):
        """Run all advanced scenario tests"""
        print("🚀 Starting Advanced Scenario Tests for Telegram Bot")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Stopping tests.")
            return False
        
        try:
            # Advanced scenario tests
            print("\n🛒 Testing Complete User Flows:")
            self.test_complete_user_purchase_flow()
            
            print("\n🔧 Testing Admin Management Flows:")
            self.test_admin_order_management_flow()
            self.test_admin_code_management_flow()
            
            print("\n🔄 Testing Session Management:")
            self.test_session_persistence_and_interruption()
            self.test_concurrent_user_sessions()
            
            print("\n⚠️ Testing Error Handling:")
            self.test_error_recovery_scenarios()
            
        finally:
            # Cleanup
            print("\n🧹 Cleanup:")
            self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Advanced Scenario Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ Errors Found ({len(self.errors)}):")
            for error in self.errors[:5]:
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   • ... and {len(self.errors) - 5} more errors")
        
        return self.tests_passed == self.tests_run

def main():
    tester = AdvancedScenarioTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())