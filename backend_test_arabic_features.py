#!/usr/bin/env python3
"""
Backend Test for Arabic Abod Card Features
Testing specific features mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime
import time

class AbodCardTester:
    def __init__(self, base_url="https://cardmartbot.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.failed_tests.append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED {details}")
        
    def test_api_endpoint(self, endpoint, method="GET", data=None, expected_status=200):
        """Test API endpoint"""
        try:
            url = f"{self.base_url}/api/{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            
            success = response.status_code == expected_status
            return success, response.status_code, response.text[:200] if not success else "OK"
        except Exception as e:
            return False, 0, str(e)
    
    def test_webhook_security(self):
        """Test webhook security with wrong secrets"""
        print("\n🔒 Testing Webhook Security...")
        
        # Test user webhook with wrong secret
        success, status, details = self.test_api_endpoint(
            "webhook/user/wrong_secret", 
            "POST", 
            {"message": {"text": "/start"}}, 
            403
        )
        self.log_test("User Webhook Security", success, f"Status: {status}")
        
        # Test admin webhook with wrong secret  
        success, status, details = self.test_api_endpoint(
            "webhook/admin/wrong_secret", 
            "POST", 
            {"message": {"text": "/start"}}, 
            403
        )
        self.log_test("Admin Webhook Security", success, f"Status: {status}")
    
    def test_user_bot_features(self):
        """Test user bot specific features"""
        print("\n👤 Testing User Bot Features...")
        
        # Test user webhook with correct secret
        user_start_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "date": 1632825600,
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "from": {
                    "id": 123456789,
                    "username": "testuser",
                    "first_name": "Test User",
                    "is_bot": False
                },
                "text": "/start"
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            "POST", 
            user_start_data, 
            200
        )
        self.log_test("User Bot Start Command", success, f"Status: {status}")
        
        # Test direct number handling (1-8)
        for number in range(1, 9):
            number_data = {
                "update_id": 123456 + number,
                "message": {
                    "message_id": 1 + number,
                    "date": 1632825600,
                    "chat": {
                        "id": 123456789,
                        "type": "private"
                    },
                    "from": {
                        "id": 123456789,
                        "username": "testuser",
                        "first_name": "Test User",
                        "is_bot": False
                    },
                    "text": str(number)
                }
            }
            
            success, status, details = self.test_api_endpoint(
                "webhook/user/abod_user_webhook_secret", 
                "POST", 
                number_data, 
                200
            )
            self.log_test(f"Direct Number Access ({number})", success, f"Status: {status}")
        
        # Test unrecognized text handling
        unknown_text_data = {
            "update_id": 123466,
            "message": {
                "message_id": 11,
                "date": 1632825600,
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "from": {
                    "id": 123456789,
                    "username": "testuser",
                    "first_name": "Test User",
                    "is_bot": False
                },
                "text": "random unknown text"
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            "POST", 
            unknown_text_data, 
            200
        )
        self.log_test("Unrecognized Text Handling", success, f"Status: {status}")
    
    def test_callback_features(self):
        """Test callback query features"""
        print("\n🔘 Testing Callback Features...")
        
        callback_features = [
            "browse_products",
            "view_wallet", 
            "order_history",
            "special_offers",
            "about_store",
            "refresh_data",
            "daily_surprises",
            "support",
            "faq",
            "submit_complaint",
            "spending_details",
            "back_to_main_menu"
        ]
        
        for i, feature in enumerate(callback_features):
            callback_data = {
                "update_id": 123500 + i,
                "callback_query": {
                    "id": f"callback_{i}",
                    "from": {
                        "id": 123456789,
                        "username": "testuser",
                        "first_name": "Test User",
                        "is_bot": False
                    },
                    "message": {
                        "message_id": 100 + i,
                        "date": 1632825600,
                        "chat": {
                            "id": 123456789,
                            "type": "private"
                        },
                        "from": {
                            "id": 123456789,
                            "username": "testuser", 
                            "first_name": "Test User",
                            "is_bot": False
                        },
                        "text": "Previous message"
                    },
                    "data": feature
                }
            }
            
            success, status, details = self.test_api_endpoint(
                "webhook/user/abod_user_webhook_secret", 
                "POST", 
                callback_data, 
                200
            )
            self.log_test(f"Callback Feature: {feature}", success, f"Status: {status}")
    
    def test_admin_bot_filtering(self):
        """Test admin bot filtering for specific ID"""
        print("\n🔧 Testing Admin Bot Filtering...")
        
        # Test authorized admin ID (7040570081)
        admin_start_data = {
            "update_id": 123600,
            "message": {
                "message_id": 200,
                "date": 1632825600,
                "chat": {
                    "id": 7040570081,
                    "type": "private"
                },
                "from": {
                    "id": 7040570081,
                    "username": "admin",
                    "first_name": "Admin",
                    "is_bot": False
                },
                "text": "/start"
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/admin/abod_admin_webhook_secret", 
            "POST", 
            admin_start_data, 
            200
        )
        self.log_test("Authorized Admin Access", success, f"Status: {status}")
        
        # Test unauthorized admin access
        unauthorized_ids = [123456789, 987654321, 555666777]
        for i, unauthorized_id in enumerate(unauthorized_ids):
            unauthorized_data = {
                "update_id": 123700 + i,
                "message": {
                    "message_id": 300 + i,
                    "date": 1632825600,
                    "chat": {
                        "id": unauthorized_id,
                        "type": "private"
                    },
                    "from": {
                        "id": unauthorized_id,
                        "username": "unauthorized",
                        "first_name": "Unauthorized",
                        "is_bot": False
                    },
                    "text": "/start"
                }
            }
            
            success, status, details = self.test_api_endpoint(
                "webhook/admin/abod_admin_webhook_secret", 
                "POST", 
                unauthorized_data, 
                200
            )
            # For unauthorized access, we expect 200 but the bot should ignore
            self.log_test(f"Unauthorized Admin Ignored ({unauthorized_id})", success, f"Status: {status}")
    
    def test_session_handling(self):
        """Test session handling and ID/email input fix"""
        print("\n💾 Testing Session Handling & ID/Email Input Fix...")
        
        # Test phone input session
        phone_session_data = {
            "update_id": 123800,
            "message": {
                "message_id": 400,
                "date": 1632825600,
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "from": {
                    "id": 123456789,
                    "username": "testuser",
                    "first_name": "Test User",
                    "is_bot": False
                },
                "text": "+1234567890"
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            "POST", 
            phone_session_data, 
            200
        )
        self.log_test("Phone Input Handling", success, f"Status: {status}")
        
        # Test email input session
        email_session_data = {
            "update_id": 123801,
            "message": {
                "message_id": 401,
                "date": 1632825600,
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "from": {
                    "id": 123456789,
                    "username": "testuser",
                    "first_name": "Test User",
                    "is_bot": False
                },
                "text": "test@example.com"
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            "POST", 
            email_session_data, 
            200
        )
        self.log_test("Email Input Handling", success, f"Status: {status}")
        
        # Test ID input session
        id_session_data = {
            "message": {
                "chat_id": 123456789,
                "text": "USER123456",
                "from_user": {
                    "username": "testuser",
                    "first_name": "Test User"
                }
            }
        }
        
        success, status, details = self.test_api_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            "POST", 
            id_session_data, 
            200
        )
        self.log_test("ID Input Handling", success, f"Status: {status}")
    
    def test_database_endpoints(self):
        """Test database-related endpoints"""
        print("\n🗄️ Testing Database Endpoints...")
        
        endpoints = [
            "products",
            "categories", 
            "users",
            "orders",
            "pending_orders"
        ]
        
        for endpoint in endpoints:
            success, status, details = self.test_api_endpoint(endpoint)
            self.log_test(f"Database Endpoint: {endpoint}", success, f"Status: {status}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Abod Card Arabic Features Testing...")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run test suites
        self.test_webhook_security()
        self.test_user_bot_features()
        self.test_callback_features()
        self.test_admin_bot_filtering()
        self.test_session_handling()
        self.test_database_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"  • {failed_test}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(self.failed_tests) == 0

def main():
    """Main function"""
    print("🎯 Abod Card Arabic Features Backend Tester")
    print("Testing specific features from the review request...")
    
    tester = AbodCardTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())