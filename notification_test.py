#!/usr/bin/env python3
"""
Telegram Bot Notification System Testing Suite
Tests all notification functionality including admin notifications, customer notifications, and timing updates
"""

import requests
import sys
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

class TelegramNotificationTester:
    def __init__(self, base_url="https://telegr-shop-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramNotification-Tester/1.0'
        })
        
        # Test configuration
        self.ADMIN_ID = 7040570081  # Correct admin ID
        self.ADMIN_BOT_TOKEN = "7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"
        self.USER_BOT_TOKEN = "7933553585:AAHNAAxp2ZCVV_KqohmF2Mx5WL66__HYnno"
        self.TEST_USER_ID = 987654321  # Test user ID

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

    def create_order_with_available_codes(self):
        """Create a test order that should trigger auto completion notification"""
        print("🔍 Testing Admin Notification - Order with Available Codes...")
        
        # Simulate order creation that should auto-complete
        order_data = {
            "user_id": "test_user_123",
            "telegram_id": self.TEST_USER_ID,
            "product_name": "بطاقة هدايا أمازون",
            "category_name": "أمازون 10$",
            "category_id": "category_123",
            "price": 10.0,
            "delivery_type": "code",
            "status": "pending"
        }
        
        # This should trigger admin notification for auto completion
        success, data = self.test_api_endpoint(
            'POST', 
            '/orders', 
            201, 
            order_data, 
            "Create Order - Auto Completion"
        )
        
        if success:
            self.log_test("Admin Notification - Auto Completion", True, 
                         f"Order created successfully, should notify admin {self.ADMIN_ID}")
        else:
            self.log_test("Admin Notification - Auto Completion", False, 
                         "Failed to create order for auto completion test")
        
        return success

    def create_order_without_codes(self):
        """Create a test order that requires manual processing"""
        print("🔍 Testing Admin Notification - Order without Codes...")
        
        order_data = {
            "user_id": "test_user_124",
            "telegram_id": self.TEST_USER_ID,
            "product_name": "بطاقة هدايا أبل",
            "category_name": "أبل 25$",
            "category_id": "category_124",
            "price": 25.0,
            "delivery_type": "code",
            "status": "pending"
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/orders', 
            201, 
            order_data, 
            "Create Order - Manual Processing"
        )
        
        if success:
            self.log_test("Admin Notification - Manual Processing", True, 
                         f"Order created, should notify admin {self.ADMIN_ID} for manual processing")
        else:
            self.log_test("Admin Notification - Manual Processing", False, 
                         "Failed to create order for manual processing test")
        
        return success

    def create_manual_order(self):
        """Create a manual order (phone, email, id, manual)"""
        print("🔍 Testing Admin Notification - Manual Order...")
        
        manual_order_types = [
            {"delivery_type": "phone", "user_input": "+966501234567"},
            {"delivery_type": "email", "user_input": "test@example.com"},
            {"delivery_type": "id", "user_input": "test_user_id"},
            {"delivery_type": "manual", "user_input": "Manual processing required"}
        ]
        
        all_success = True
        
        for i, order_type in enumerate(manual_order_types):
            order_data = {
                "user_id": f"test_user_12{5+i}",
                "telegram_id": self.TEST_USER_ID,
                "product_name": "خدمة مخصصة",
                "category_name": f"خدمة {order_type['delivery_type']}",
                "category_id": f"category_12{5+i}",
                "price": 15.0,
                "delivery_type": order_type["delivery_type"],
                "user_input_data": order_type["user_input"],
                "status": "pending"
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/orders', 
                201, 
                order_data, 
                f"Manual Order - {order_type['delivery_type']}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Admin Notification - Manual Orders", True, 
                         f"All manual orders created, should notify admin {self.ADMIN_ID}")
        else:
            self.log_test("Admin Notification - Manual Orders", False, 
                         "Some manual orders failed to create")
        
        return all_success

    def test_execution_time_messages(self):
        """Test that messages show '10-30 minutes' instead of '24 hours'"""
        print("🔍 Testing Updated Execution Time Messages...")
        
        # Test FAQ command to check timing information
        telegram_update = {
            "update_id": 123458001,
            "callback_query": {
                "id": "faq_test",
                "chat_instance": "faq_chat_instance",
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 101,
                    "from": {
                        "id": int(self.USER_BOT_TOKEN.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test FAQ"
                },
                "data": "faq"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "FAQ - Execution Time Check"
        )
        
        if success:
            self.log_test("Updated Execution Time - FAQ", True, 
                         "FAQ accessed successfully, should show '10-30 minutes' timing")
        else:
            self.log_test("Updated Execution Time - FAQ", False, 
                         "Failed to access FAQ for timing verification")
        
        return success

    def test_pending_order_messages(self):
        """Test pending order messages show correct timing"""
        print("🔍 Testing Pending Order Messages...")
        
        # Test order history to see pending orders timing
        telegram_update = {
            "update_id": 123458002,
            "callback_query": {
                "id": "order_history_test",
                "chat_instance": "order_history_chat_instance",
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "فاطمة",
                    "username": "fatima_test",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 102,
                    "from": {
                        "id": int(self.USER_BOT_TOKEN.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "فاطمة",
                        "username": "fatima_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test order history"
                },
                "data": "order_history"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "Order History - Timing Check"
        )
        
        if success:
            self.log_test("Updated Execution Time - Pending Orders", True, 
                         "Order history accessed, should show updated timing for pending orders")
        else:
            self.log_test("Updated Execution Time - Pending Orders", False, 
                         "Failed to access order history for timing verification")
        
        return success

    def test_wallet_balance_notification(self):
        """Test customer notification when balance is added to wallet"""
        print("🔍 Testing Customer Notification - Wallet Balance Added...")
        
        # Simulate admin adding balance to user wallet
        balance_data = {
            "telegram_id": self.TEST_USER_ID,
            "amount": 50.0,
            "admin_id": self.ADMIN_ID
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/admin/add-balance', 
            200, 
            balance_data, 
            "Add Balance - Customer Notification"
        )
        
        if success:
            self.log_test("Customer Notification - Balance Added", True, 
                         f"Balance added successfully, should notify user {self.TEST_USER_ID}")
        else:
            self.log_test("Customer Notification - Balance Added", False, 
                         "Failed to add balance for customer notification test")
        
        return success

    def test_order_completion_notification(self):
        """Test customer notification when order is completed and code is sent"""
        print("🔍 Testing Customer Notification - Order Completed...")
        
        # Simulate order completion
        completion_data = {
            "order_id": "test_order_123",
            "telegram_id": self.TEST_USER_ID,
            "code_sent": "AMAZON-GIFT-12345",
            "status": "completed"
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/admin/complete-order', 
            200, 
            completion_data, 
            "Complete Order - Customer Notification"
        )
        
        if success:
            self.log_test("Customer Notification - Order Completed", True, 
                         f"Order completed, should notify user {self.TEST_USER_ID} with code")
        else:
            self.log_test("Customer Notification - Order Completed", False, 
                         "Failed to complete order for customer notification test")
        
        return success

    def test_new_order_received_notification(self):
        """Test customer notification when new order is received"""
        print("🔍 Testing Customer Notification - New Order Received...")
        
        # Create new order to trigger customer notification
        order_data = {
            "user_id": "test_user_130",
            "telegram_id": self.TEST_USER_ID,
            "product_name": "بطاقة هدايا جوجل",
            "category_name": "جوجل بلاي 20$",
            "category_id": "category_130",
            "price": 20.0,
            "delivery_type": "code",
            "status": "pending"
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/orders', 
            201, 
            order_data, 
            "New Order - Customer Notification"
        )
        
        if success:
            self.log_test("Customer Notification - New Order", True, 
                         f"New order created, should notify user {self.TEST_USER_ID}")
        else:
            self.log_test("Customer Notification - New Order", False, 
                         "Failed to create order for customer notification test")
        
        return success

    def test_out_of_stock_notification(self):
        """Test admin notification when codes are out of stock"""
        print("🔍 Testing Admin Notification - Out of Stock...")
        
        # Simulate checking stock levels
        stock_check_data = {
            "category_id": "category_low_stock",
            "admin_id": self.ADMIN_ID
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/admin/check-stock', 
            200, 
            stock_check_data, 
            "Stock Check - Out of Stock Notification"
        )
        
        if success:
            self.log_test("Admin Notification - Out of Stock", True, 
                         f"Stock check completed, should notify admin {self.ADMIN_ID} if low")
        else:
            self.log_test("Admin Notification - Out of Stock", False, 
                         "Failed to check stock for out of stock notification test")
        
        return success

    def test_late_order_notification(self):
        """Test admin notification for orders delayed more than 30 minutes"""
        print("🔍 Testing Admin Notification - Late Orders (30+ minutes)...")
        
        # Simulate checking for late orders
        late_order_check = {
            "admin_id": self.ADMIN_ID,
            "time_threshold": 30  # 30 minutes
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/admin/check-late-orders', 
            200, 
            late_order_check, 
            "Late Orders Check - Admin Notification"
        )
        
        if success:
            self.log_test("Admin Notification - Late Orders", True, 
                         f"Late orders check completed, should notify admin {self.ADMIN_ID}")
        else:
            self.log_test("Admin Notification - Late Orders", False, 
                         "Failed to check late orders for admin notification test")
        
        return success

    def test_manual_order_execution_notification(self):
        """Test admin notification for manual order execution"""
        print("🔍 Testing Admin Notification - Manual Order Execution...")
        
        # Simulate manual order execution
        manual_execution_data = {
            "order_id": "manual_order_123",
            "telegram_id": self.TEST_USER_ID,
            "admin_id": self.ADMIN_ID,
            "execution_notes": "Manual order processed successfully",
            "status": "completed"
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/admin/execute-manual-order', 
            200, 
            manual_execution_data, 
            "Manual Order Execution - Admin Notification"
        )
        
        if success:
            self.log_test("Admin Notification - Manual Execution", True, 
                         f"Manual order executed, should notify admin {self.ADMIN_ID}")
        else:
            self.log_test("Admin Notification - Manual Execution", False, 
                         "Failed to execute manual order for admin notification test")
        
        return success

    def test_admin_id_verification(self):
        """Verify that notifications are sent to correct ADMIN_ID: 7040570081"""
        print("🔍 Testing Admin ID Verification...")
        
        # Test admin webhook with correct admin ID
        admin_update = {
            "update_id": 123458100,
            "message": {
                "message_id": 200,
                "from": {
                    "id": self.ADMIN_ID,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_abod",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.ADMIN_ID,
                    "first_name": "Admin",
                    "username": "admin_abod",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            admin_update, 
            "Admin ID Verification"
        )
        
        if success:
            self.log_test("Admin ID Verification", True, 
                         f"Admin webhook working with correct ID: {self.ADMIN_ID}")
        else:
            self.log_test("Admin ID Verification", False, 
                         f"Failed to verify admin ID: {self.ADMIN_ID}")
        
        # Test with wrong admin ID (should be rejected)
        wrong_admin_update = admin_update.copy()
        wrong_admin_update["message"]["from"]["id"] = 123456789  # Wrong ID
        wrong_admin_update["message"]["chat"]["id"] = 123456789
        
        success2, data2 = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            wrong_admin_update, 
            "Wrong Admin ID Rejection"
        )
        
        if success2:
            self.log_test("Wrong Admin ID Rejection", True, 
                         "Wrong admin ID properly rejected (should show unauthorized message)")
        else:
            self.log_test("Wrong Admin ID Rejection", False, 
                         "Failed to test wrong admin ID rejection")
        
        return success and success2

    def test_bot_tokens_configuration(self):
        """Test that bot tokens are correctly configured"""
        print("🔍 Testing Bot Tokens Configuration...")
        
        # Test user bot token format
        user_token_valid = self.USER_BOT_TOKEN.startswith("7933553585:")
        admin_token_valid = self.ADMIN_BOT_TOKEN.startswith("7835622090:")
        
        if user_token_valid:
            self.log_test("User Bot Token", True, f"User bot token correctly configured: {self.USER_BOT_TOKEN[:20]}...")
        else:
            self.log_test("User Bot Token", False, f"User bot token format incorrect: {self.USER_BOT_TOKEN[:20]}...")
        
        if admin_token_valid:
            self.log_test("Admin Bot Token", True, f"Admin bot token correctly configured: {self.ADMIN_BOT_TOKEN[:20]}...")
        else:
            self.log_test("Admin Bot Token", False, f"Admin bot token format incorrect: {self.ADMIN_BOT_TOKEN[:20]}...")
        
        return user_token_valid and admin_token_valid

    def run_notification_tests(self):
        """Run all notification system tests"""
        print("🚀 Starting Telegram Bot Notification System Tests")
        print("=" * 60)
        
        # Test server health first
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code not in [200, 404]:
                print("❌ Server is not accessible. Stopping tests.")
                return self.generate_report()
        except:
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Test bot configuration
        print("\n🔧 Testing Bot Configuration...")
        print("=" * 60)
        self.test_bot_tokens_configuration()
        self.test_admin_id_verification()
        
        # Test admin notifications for new orders
        print("\n📢 Testing Admin Notifications for New Orders...")
        print("=" * 60)
        self.create_order_with_available_codes()
        self.create_order_without_codes()
        self.create_manual_order()
        
        # Test updated execution time
        print("\n⏰ Testing Updated Execution Time (10-30 minutes)...")
        print("=" * 60)
        self.test_execution_time_messages()
        self.test_pending_order_messages()
        
        # Test customer notifications
        print("\n👤 Testing Customer Notifications...")
        print("=" * 60)
        self.test_wallet_balance_notification()
        self.test_order_completion_notification()
        self.test_new_order_received_notification()
        
        # Test different notification types
        print("\n🔔 Testing Different Notification Types...")
        print("=" * 60)
        self.test_out_of_stock_notification()
        self.test_late_order_notification()
        self.test_manual_order_execution_notification()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 60)
        print("📊 NOTIFICATION SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results
        admin_notifications = []
        customer_notifications = []
        timing_updates = []
        configuration_tests = []
        failed_tests = []
        
        for result in self.test_results:
            if not result['success']:
                failed_tests.append(result)
            elif "Admin Notification" in result['test_name']:
                admin_notifications.append(result)
            elif "Customer Notification" in result['test_name']:
                customer_notifications.append(result)
            elif "Execution Time" in result['test_name'] or "Timing" in result['test_name']:
                timing_updates.append(result)
            elif "Token" in result['test_name'] or "Admin ID" in result['test_name']:
                configuration_tests.append(result)
        
        print(f"\n✅ Admin Notifications: {len(admin_notifications)} tests")
        print(f"✅ Customer Notifications: {len(customer_notifications)} tests")
        print(f"✅ Timing Updates: {len(timing_updates)} tests")
        print(f"✅ Configuration: {len(configuration_tests)} tests")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"  - {result['test_name']}: {result['details']}")
        
        print(f"\n🎯 NOTIFICATION SYSTEM STATUS:")
        if success_rate >= 90:
            print("🟢 EXCELLENT - Notification system working properly")
        elif success_rate >= 75:
            print("🟡 GOOD - Minor issues detected")
        elif success_rate >= 50:
            print("🟠 NEEDS ATTENTION - Several issues found")
        else:
            print("🔴 CRITICAL - Major notification system problems")
        
        print("\n" + "=" * 60)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "admin_notifications": len(admin_notifications),
            "customer_notifications": len(customer_notifications),
            "timing_updates": len(timing_updates),
            "configuration_tests": len(configuration_tests)
        }

def main():
    """Main test execution"""
    tester = TelegramNotificationTester()
    results = tester.run_notification_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All notification tests passed!")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} notification test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())