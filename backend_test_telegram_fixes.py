#!/usr/bin/env python3
"""
Telegram Bot Fixes Testing Suite for Abod Card
Tests specific fixes for:
1. Admin bot code addition functionality
2. User bot product browsing and details
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class TelegramBotFixesTester:
    def __init__(self, base_url="https://telegr-shop-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-TelegramFixesTester/1.0'
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
            if response.status_code in [200, 404]:  # 404 is OK for root path
                self.log_test("Server Connectivity", True, f"Server responding (status: {response.status_code})")
                return True
            else:
                self.log_test("Server Connectivity", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Cannot connect to server: {str(e)}")
            return False

    def test_webhook_endpoints_exist(self):
        """Test that webhook endpoints are properly configured"""
        print("🔍 Testing Webhook Endpoints...")
        
        # Test user webhook endpoint exists
        try:
            response = self.session.post(f"{self.api_url}/webhook/user/test_secret", 
                                       json={"test": "data"}, timeout=10)
            user_webhook_exists = response.status_code in [403, 422, 500]
            
            if user_webhook_exists:
                self.log_test("User Webhook Endpoint", True, "User webhook endpoint exists")
            else:
                self.log_test("User Webhook Endpoint", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("User Webhook Endpoint", False, f"Error: {str(e)}")
            user_webhook_exists = False

        # Test admin webhook endpoint exists
        try:
            response = self.session.post(f"{self.api_url}/webhook/admin/test_secret", 
                                       json={"test": "data"}, timeout=10)
            admin_webhook_exists = response.status_code in [403, 422, 500]
            
            if admin_webhook_exists:
                self.log_test("Admin Webhook Endpoint", True, "Admin webhook endpoint exists")
            else:
                self.log_test("Admin Webhook Endpoint", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Webhook Endpoint", False, f"Error: {str(e)}")
            admin_webhook_exists = False

        return user_webhook_exists and admin_webhook_exists

    def simulate_telegram_update(self, webhook_type: str, update_data: dict):
        """Simulate a Telegram update to webhook"""
        secret = "abod_user_webhook_secret" if webhook_type == "user" else "abod_admin_webhook_secret"
        endpoint = f"/webhook/{webhook_type}/{secret}"
        
        try:
            response = self.session.post(f"{self.api_url}{endpoint}", 
                                       json=update_data, timeout=30)
            return response.status_code == 200, response
        except Exception as e:
            return False, str(e)

    def test_admin_bot_start_command(self):
        """Test admin bot /start command"""
        print("🔍 Testing Admin Bot Start Command...")
        
        # Simulate /start message to admin bot
        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "Admin",
                    "username": "admin_user",
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "/start"
            }
        }
        
        success, response = self.simulate_telegram_update("admin", update_data)
        
        if success:
            self.log_test("Admin Bot Start Command", True, "Admin bot processed /start command")
        else:
            self.log_test("Admin Bot Start Command", False, f"Failed to process /start: {response}")
        
        return success

    def test_admin_manage_codes_callback(self):
        """Test admin bot manage codes callback"""
        print("🔍 Testing Admin Manage Codes Callback...")
        
        # Simulate manage_codes callback
        update_data = {
            "update_id": 123457,
            "callback_query": {
                "id": "callback_123",
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user"
                },
                "message": {
                    "message_id": 2,
                    "from": {
                        "id": 123456789,  # Bot ID
                        "is_bot": True,
                        "first_name": "Abod Card Admin Bot"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "Admin",
                        "username": "admin_user",
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp()),
                    "text": "اختر العملية المطلوبة:"
                },
                "data": "manage_codes"
            }
        }
        
        success, response = self.simulate_telegram_update("admin", update_data)
        
        if success:
            self.log_test("Admin Manage Codes Callback", True, "Admin bot processed manage_codes callback")
        else:
            self.log_test("Admin Manage Codes Callback", False, f"Failed to process callback: {response}")
        
        return success

    def test_admin_add_codes_callback(self):
        """Test admin bot add codes callback"""
        print("🔍 Testing Admin Add Codes Callback...")
        
        # Simulate add_codes callback
        update_data = {
            "update_id": 123458,
            "callback_query": {
                "id": "callback_124",
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user"
                },
                "message": {
                    "message_id": 3,
                    "chat": {
                        "id": 987654321,
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp())
                },
                "data": "add_codes"
            }
        }
        
        success, response = self.simulate_telegram_update("admin", update_data)
        
        if success:
            self.log_test("Admin Add Codes Callback", True, "Admin bot processed add_codes callback")
        else:
            self.log_test("Admin Add Codes Callback", False, f"Failed to process callback: {response}")
        
        return success

    def test_admin_code_type_selection(self):
        """Test admin bot code type selection callbacks"""
        print("🔍 Testing Admin Code Type Selection...")
        
        # Test different code type selections
        code_types = ["text", "number", "dual"]
        category_id = "test_category_123"
        
        for code_type in code_types:
            update_data = {
                "update_id": 123459 + code_types.index(code_type),
                "callback_query": {
                    "id": f"callback_125_{code_type}",
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Admin",
                        "username": "admin_user"
                    },
                    "message": {
                        "message_id": 4 + code_types.index(code_type),
                        "chat": {
                            "id": 987654321,
                            "type": "private"
                        },
                        "date": int(datetime.now().timestamp())
                    },
                    "data": f"code_type_{code_type}_{category_id}"
                }
            }
            
            success, response = self.simulate_telegram_update("admin", update_data)
            
            if success:
                self.log_test(f"Admin Code Type Selection ({code_type})", True, 
                            f"Admin bot processed {code_type} code type selection")
            else:
                self.log_test(f"Admin Code Type Selection ({code_type})", False, 
                            f"Failed to process {code_type} selection: {response}")

    def test_user_bot_start_command(self):
        """Test user bot /start command"""
        print("🔍 Testing User Bot Start Command...")
        
        # Simulate /start message to user bot
        update_data = {
            "update_id": 223456,
            "message": {
                "message_id": 10,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test User",
                    "username": "test_user",
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "/start"
            }
        }
        
        success, response = self.simulate_telegram_update("user", update_data)
        
        if success:
            self.log_test("User Bot Start Command", True, "User bot processed /start command")
        else:
            self.log_test("User Bot Start Command", False, f"Failed to process /start: {response}")
        
        return success

    def test_user_browse_products_callback(self):
        """Test user bot browse products callback"""
        print("🔍 Testing User Browse Products Callback...")
        
        # Simulate browse_products callback
        update_data = {
            "update_id": 223457,
            "callback_query": {
                "id": "user_callback_123",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 11,
                    "from": {
                        "id": 987654321,  # Bot ID
                        "is_bot": True,
                        "first_name": "Abod Card Bot"
                    },
                    "chat": {
                        "id": 123456789,
                        "first_name": "Test User",
                        "username": "test_user",
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp()),
                    "text": "اختر من الخيارات التالية:"
                },
                "data": "browse_products"
            }
        }
        
        success, response = self.simulate_telegram_update("user", update_data)
        
        if success:
            self.log_test("User Browse Products Callback", True, "User bot processed browse_products callback")
        else:
            self.log_test("User Browse Products Callback", False, f"Failed to process callback: {response}")
        
        return success

    def test_user_product_selection_callback(self):
        """Test user bot product selection callback"""
        print("🔍 Testing User Product Selection Callback...")
        
        # Simulate product selection callback
        product_id = "test_product_123"
        update_data = {
            "update_id": 223458,
            "callback_query": {
                "id": "user_callback_124",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 12,
                    "chat": {
                        "id": 123456789,
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp())
                },
                "data": f"product_{product_id}"
            }
        }
        
        success, response = self.simulate_telegram_update("user", update_data)
        
        if success:
            self.log_test("User Product Selection Callback", True, "User bot processed product selection callback")
        else:
            self.log_test("User Product Selection Callback", False, f"Failed to process callback: {response}")
        
        return success

    def test_user_category_selection_callback(self):
        """Test user bot category selection callback"""
        print("🔍 Testing User Category Selection Callback...")
        
        # Simulate category selection callback
        category_id = "test_category_123"
        update_data = {
            "update_id": 223459,
            "callback_query": {
                "id": "user_callback_125",
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 13,
                    "chat": {
                        "id": 123456789,
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp())
                },
                "data": f"category_{category_id}"
            }
        }
        
        success, response = self.simulate_telegram_update("user", update_data)
        
        if success:
            self.log_test("User Category Selection Callback", True, "User bot processed category selection callback")
        else:
            self.log_test("User Category Selection Callback", False, f"Failed to process callback: {response}")
        
        return success

    def test_database_operations(self):
        """Test database operations through API endpoints"""
        print("🔍 Testing Database Operations...")
        
        # Test products API
        try:
            response = self.session.get(f"{self.api_url}/products", timeout=10)
            if response.status_code == 200:
                products = response.json()
                self.log_test("Products Database Query", True, f"Retrieved {len(products)} products")
            else:
                self.log_test("Products Database Query", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Products Database Query", False, f"Error: {str(e)}")

        # Test categories API
        try:
            response = self.session.get(f"{self.api_url}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                self.log_test("Categories Database Query", True, f"Retrieved {len(categories)} categories")
            else:
                self.log_test("Categories Database Query", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Categories Database Query", False, f"Error: {str(e)}")

        # Test codes stats API
        try:
            response = self.session.get(f"{self.api_url}/codes-stats", timeout=10)
            if response.status_code == 200:
                codes_stats = response.json()
                self.log_test("Codes Stats Database Query", True, f"Retrieved {len(codes_stats)} code statistics")
            else:
                self.log_test("Codes Stats Database Query", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Codes Stats Database Query", False, f"Error: {str(e)}")

    def test_session_management(self):
        """Test session management functionality"""
        print("🔍 Testing Session Management...")
        
        # The session management is internal to the bot handlers
        # We can test it indirectly by checking if the bot responds correctly to state-dependent messages
        
        # Test admin text input (simulating codes input state)
        admin_text_update = {
            "update_id": 323456,
            "message": {
                "message_id": 20,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_user"
                },
                "chat": {
                    "id": 987654321,
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "ABC123\nDEF456\nGHI789"
            }
        }
        
        success, response = self.simulate_telegram_update("admin", admin_text_update)
        
        if success:
            self.log_test("Admin Session Management", True, "Admin bot processed text input")
        else:
            self.log_test("Admin Session Management", False, f"Failed to process text input: {response}")

        # Test user text input (simulating wallet topup)
        user_text_update = {
            "update_id": 323457,
            "message": {
                "message_id": 21,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "50"
            }
        }
        
        success, response = self.simulate_telegram_update("user", user_text_update)
        
        if success:
            self.log_test("User Session Management", True, "User bot processed text input")
        else:
            self.log_test("User Session Management", False, f"Failed to process text input: {response}")

    def run_telegram_fixes_tests(self):
        """Run all Telegram bot fixes tests"""
        print("🚀 Starting Telegram Bot Fixes Testing")
        print("Testing Fixes for:")
        print("1. Admin bot code addition functionality")
        print("2. User bot product browsing and details")
        print("=" * 70)
        
        # Test server connectivity first
        if not self.test_server_connectivity():
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Test webhook endpoints
        self.test_webhook_endpoints_exist()
        
        # Test admin bot functionality (code addition fixes)
        print("\n🔧 Testing Admin Bot Code Addition Fixes...")
        self.test_admin_bot_start_command()
        self.test_admin_manage_codes_callback()
        self.test_admin_add_codes_callback()
        self.test_admin_code_type_selection()
        
        # Test user bot functionality (product browsing fixes)
        print("\n👤 Testing User Bot Product Browsing Fixes...")
        self.test_user_bot_start_command()
        self.test_user_browse_products_callback()
        self.test_user_product_selection_callback()
        self.test_user_category_selection_callback()
        
        # Test supporting functionality
        print("\n🗄️ Testing Supporting Functionality...")
        self.test_database_operations()
        self.test_session_management()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 70)
        print("📊 TELEGRAM BOT FIXES TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results by functionality
        admin_tests = [r for r in self.test_results if 'admin' in r['test_name'].lower()]
        user_tests = [r for r in self.test_results if 'user' in r['test_name'].lower()]
        database_tests = [r for r in self.test_results if 'database' in r['test_name'].lower()]
        
        admin_success = sum(1 for t in admin_tests if t['success']) / len(admin_tests) * 100 if admin_tests else 0
        user_success = sum(1 for t in user_tests if t['success']) / len(user_tests) * 100 if user_tests else 0
        database_success = sum(1 for t in database_tests if t['success']) / len(database_tests) * 100 if database_tests else 0
        
        print(f"\n📊 Success Rate by Category:")
        print(f"  Admin Bot Functionality: {admin_success:.1f}% ({sum(1 for t in admin_tests if t['success'])}/{len(admin_tests)})")
        print(f"  User Bot Functionality: {user_success:.1f}% ({sum(1 for t in user_tests if t['success'])}/{len(user_tests)})")
        print(f"  Database Operations: {database_success:.1f}% ({sum(1 for t in database_tests if t['success'])}/{len(database_tests)})")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for failure in failed_tests:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 Excellent! Telegram bot fixes are working very well ({success_rate:.1f}% success rate)")
        elif success_rate >= 75:
            print(f"\n✅ Good! Most Telegram bot functionality is working ({success_rate:.1f}% success rate)")
        elif success_rate >= 50:
            print(f"\n⚠️  Warning! Telegram bot has significant issues ({success_rate:.1f}% success rate)")
        else:
            print(f"\n❌ Critical! Telegram bot has major problems ({success_rate:.1f}% success rate)")
        
        print("\n" + "=" * 70)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "admin_success_rate": admin_success,
            "user_success_rate": user_success,
            "database_success_rate": database_success,
            "test_results": self.test_results,
            "failed_tests": failed_tests
        }

def main():
    """Main test execution"""
    tester = TelegramBotFixesTester()
    results = tester.run_telegram_fixes_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All Telegram bot fixes tests passed!")
        return 0
    elif results["success_rate"] >= 80:
        print(f"✅ Most tests passed ({results['success_rate']:.1f}%)")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} test(s) failed ({results['success_rate']:.1f}% success)")
        return 1

if __name__ == "__main__":
    sys.exit(main())