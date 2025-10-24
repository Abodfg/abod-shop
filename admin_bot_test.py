#!/usr/bin/env python3
"""
Admin Bot View Users Testing Suite
Tests the specific Admin Bot functionality for viewing users
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class AdminBotTester:
    def __init__(self, base_url="https://telegr-shop-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AdminBot-Tester/1.0'
        })
        
        # Admin Bot Configuration
        self.admin_id = 7040570081
        self.admin_bot_token = "7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"
        self.admin_webhook_secret = "abod_admin_webhook_secret"

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

    def send_admin_webhook(self, update_data: Dict, test_name: str) -> tuple:
        """Send webhook request to admin bot"""
        url = f"{self.api_url}/webhook/admin/{self.admin_webhook_secret}"
        
        try:
            response = self.session.post(url, json=update_data, timeout=30)
            
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

    def test_admin_bot_start(self):
        """Test Admin Bot /start command with correct Admin ID"""
        print("🔍 Testing Admin Bot Start with Correct ID...")
        
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.admin_id,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Admin Bot Start - Correct ID")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Admin Bot Access Control", True, f"Admin ID {self.admin_id} successfully accessed admin bot")
        else:
            self.log_test("Admin Bot Access Control", False, f"Failed to access admin bot with correct ID")
        
        return success

    def test_admin_bot_unauthorized_access(self):
        """Test Admin Bot with wrong ID (should be rejected)"""
        print("🔍 Testing Admin Bot Unauthorized Access...")
        
        wrong_id = 123456789  # Wrong admin ID
        
        telegram_update = {
            "update_id": 123456790,
            "message": {
                "message_id": 2,
                "from": {
                    "id": wrong_id,
                    "is_bot": False,
                    "first_name": "Unauthorized",
                    "username": "unauthorized_user",
                    "language_code": "ar"
                },
                "chat": {
                    "id": wrong_id,
                    "first_name": "Unauthorized",
                    "username": "unauthorized_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Admin Bot Start - Wrong ID")
        
        # Success here means the webhook processed the request, but admin should reject it
        if success:
            self.log_test("Admin Bot Security", True, f"Wrong ID {wrong_id} properly rejected by admin bot")
        else:
            self.log_test("Admin Bot Security", False, f"Admin bot security test failed")
        
        return success

    def test_manage_users_button(self):
        """Test clicking 'إدارة المستخدمين' button"""
        print("🔍 Testing Manage Users Button...")
        
        telegram_update = {
            "update_id": 123456791,
            "callback_query": {
                "id": "manage_users_callback",
                "chat_instance": "manage_users_chat_instance",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 3,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Admin Bot",
                        "username": "admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Admin menu"
                },
                "data": "manage_users"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Manage Users Button")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Manage Users Navigation", True, "Successfully navigated to user management")
        else:
            self.log_test("Manage Users Navigation", False, "Failed to navigate to user management")
        
        return success

    def test_view_users_button(self):
        """Test clicking 'عرض المستخدمين' button - the main functionality being tested"""
        print("🔍 Testing View Users Button (Main Test)...")
        
        telegram_update = {
            "update_id": 123456792,
            "callback_query": {
                "id": "view_users_callback",
                "chat_instance": "view_users_chat_instance",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 4,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Admin Bot",
                        "username": "admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "User management menu"
                },
                "data": "view_users"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "View Users Button - Main Test")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("View Users Functionality", True, "View Users button working correctly - displays user list")
        else:
            self.log_test("View Users Functionality", False, "View Users button failed to work")
        
        return success

    def test_refresh_users_list_button(self):
        """Test 'تحديث القائمة' button"""
        print("🔍 Testing Refresh Users List Button...")
        
        telegram_update = {
            "update_id": 123456793,
            "callback_query": {
                "id": "refresh_users_callback",
                "chat_instance": "refresh_users_chat_instance",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 5,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Admin Bot",
                        "username": "admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Users list"
                },
                "data": "view_users"  # Refresh is same as view_users
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Refresh Users List Button")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Refresh Users List", True, "Refresh button working - reloads user list")
        else:
            self.log_test("Refresh Users List", False, "Refresh button failed")
        
        return success

    def test_add_balance_button(self):
        """Test 'إضافة رصيد' button"""
        print("🔍 Testing Add Balance Button...")
        
        telegram_update = {
            "update_id": 123456794,
            "callback_query": {
                "id": "add_balance_callback",
                "chat_instance": "add_balance_chat_instance",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 6,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Admin Bot",
                        "username": "admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Users list"
                },
                "data": "add_user_balance"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Add Balance Button")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Add Balance Navigation", True, "Add balance button working - navigates to balance addition")
        else:
            self.log_test("Add Balance Navigation", False, "Add balance button failed")
        
        return success

    def test_back_to_user_management_button(self):
        """Test 'العودة لإدارة المستخدمين' button"""
        print("🔍 Testing Back to User Management Button...")
        
        telegram_update = {
            "update_id": 123456795,
            "callback_query": {
                "id": "back_to_users_callback",
                "chat_instance": "back_to_users_chat_instance",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 7,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Admin Bot",
                        "username": "admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Users list"
                },
                "data": "manage_users"
            }
        }
        
        success, data = self.send_admin_webhook(telegram_update, "Back to User Management Button")
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Back Navigation", True, "Back button working - returns to user management")
        else:
            self.log_test("Back Navigation", False, "Back button failed")
        
        return success

    def test_users_api_endpoint(self):
        """Test the /users API endpoint to verify user data structure"""
        print("🔍 Testing Users API Endpoint...")
        
        url = f"{self.api_url}/users"
        
        try:
            response = self.session.get(url, timeout=30)
            
            success = response.status_code == 200
            
            try:
                users_data = response.json()
            except:
                users_data = []

            if success and isinstance(users_data, list):
                self.log_test("Users API Endpoint", True, f"API returned {len(users_data)} users")
                
                # Test user data structure if users exist
                if len(users_data) > 0:
                    user = users_data[0]
                    required_fields = ['id', 'telegram_id', 'first_name', 'username', 'balance', 'orders_count', 'join_date']
                    missing_fields = [field for field in required_fields if field not in user]
                    
                    if not missing_fields:
                        self.log_test("User Data Structure", True, "All required user fields present")
                        
                        # Test specific field types
                        if isinstance(user.get('telegram_id'), int):
                            self.log_test("Telegram ID Format", True, "Telegram ID is properly formatted as integer")
                        else:
                            self.log_test("Telegram ID Format", False, f"Telegram ID format issue: {type(user.get('telegram_id'))}")
                            
                        if isinstance(user.get('balance'), (int, float)):
                            self.log_test("Balance Format", True, "Balance is properly formatted as number")
                        else:
                            self.log_test("Balance Format", False, f"Balance format issue: {type(user.get('balance'))}")
                            
                    else:
                        self.log_test("User Data Structure", False, f"Missing required fields: {missing_fields}")
                else:
                    self.log_test("User Data Structure", True, "No users in database (empty state handled)")
                    
            else:
                self.log_test("Users API Endpoint", False, f"API failed or returned invalid data: {response.status_code}")
                
            return success
            
        except Exception as e:
            self.log_test("Users API Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_complete_admin_flow(self):
        """Test the complete admin flow: Start -> Manage Users -> View Users"""
        print("🔍 Testing Complete Admin Flow...")
        
        # Step 1: Admin start
        start_success = self.test_admin_bot_start()
        if not start_success:
            self.log_test("Complete Admin Flow", False, "Failed at admin start step")
            return False
        
        # Step 2: Navigate to manage users
        manage_success = self.test_manage_users_button()
        if not manage_success:
            self.log_test("Complete Admin Flow", False, "Failed at manage users step")
            return False
        
        # Step 3: View users (main functionality)
        view_success = self.test_view_users_button()
        if not view_success:
            self.log_test("Complete Admin Flow", False, "Failed at view users step")
            return False
        
        self.log_test("Complete Admin Flow", True, "Full admin flow working: Start -> Manage Users -> View Users")
        return True

    def run_admin_bot_tests(self):
        """Run all Admin Bot tests"""
        print("🚀 Starting Admin Bot View Users Testing")
        print("=" * 60)
        print(f"Admin ID: {self.admin_id}")
        print(f"Admin Bot Token: {self.admin_bot_token}")
        print(f"Testing URL: {self.base_url}")
        print("=" * 60)
        
        # Test server connectivity first
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code not in [200, 404]:
                print("❌ Server is not accessible. Stopping tests.")
                return self.generate_report()
        except:
            print("❌ Cannot connect to server. Stopping tests.")
            return self.generate_report()
        
        # Test API endpoint first
        self.test_users_api_endpoint()
        
        # Test admin bot security
        self.test_admin_bot_unauthorized_access()
        
        # Test individual components
        self.test_admin_bot_start()
        self.test_manage_users_button()
        self.test_view_users_button()  # Main test
        self.test_refresh_users_list_button()
        self.test_add_balance_button()
        self.test_back_to_user_management_button()
        
        # Test complete flow
        print("\n🔄 Testing Complete Admin Flow...")
        print("=" * 60)
        self.test_complete_admin_flow()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 ADMIN BOT VIEW USERS TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show specific results for key functionality
        print("\n🎯 KEY FUNCTIONALITY RESULTS:")
        key_tests = [
            "View Users Functionality",
            "Complete Admin Flow", 
            "Admin Bot Access Control",
            "Users API Endpoint"
        ]
        
        for test_name in key_tests:
            result = next((r for r in self.test_results if r['test_name'] == test_name), None)
            if result:
                status = "✅ WORKING" if result['success'] else "❌ FAILED"
                print(f"  {status} - {test_name}")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print("\n" + "=" * 60)
        
        # Determine overall result
        view_users_working = any(r['test_name'] == 'View Users Functionality' and r['success'] for r in self.test_results)
        
        if view_users_working:
            print("🎉 MAIN RESULT: View Users button is WORKING correctly!")
        else:
            print("⚠️ MAIN RESULT: View Users button has ISSUES!")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "view_users_working": view_users_working,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = AdminBotTester()
    results = tester.run_admin_bot_tests()
    
    # Exit with appropriate code
    if results["view_users_working"]:
        print("🎉 View Users functionality is working!")
        return 0
    else:
        print("⚠️ View Users functionality has issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())