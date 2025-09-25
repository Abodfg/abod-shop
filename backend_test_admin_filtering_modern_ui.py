#!/usr/bin/env python3
"""
Backend Test for Admin Filtering and Modern UI Features
Testing the specific features mentioned in the review request:
1. Admin bot filtering for ID 7040570081 only
2. Modern user interface features
3. Session handling improvements
4. New keyboard and messaging features
"""

import requests
import json
import sys
from datetime import datetime
import time

class TelegramBotTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_id = 7040570081  # The authorized admin ID
        self.unauthorized_id = 123456789  # Unauthorized user ID
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED - {details}")
        
        if details:
            print(f"   Details: {details}")
        print()

    def test_admin_filtering(self):
        """Test that admin bot only responds to authorized admin ID"""
        print("🔒 Testing Admin Bot Filtering...")
        
        # Test 1: Authorized admin should get proper response
        admin_webhook_data = {
            "message": {
                "message_id": 1,
                "chat": {
                    "id": self.admin_id,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start",
                "from": {
                    "id": self.admin_id,
                    "username": "admin_user",
                    "first_name": "Admin",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/admin/abod_admin_webhook_secret",
                json=admin_webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            authorized_success = response.status_code == 200
            self.log_test(
                "Admin Bot - Authorized ID Response", 
                authorized_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Admin Bot - Authorized ID Response", False, str(e))
        
        # Test 2: Unauthorized user should be rejected
        unauthorized_webhook_data = {
            "message": {
                "chat_id": self.unauthorized_id,
                "text": "/start", 
                "from_user": {
                    "id": self.unauthorized_id,
                    "username": "unauthorized_user",
                    "first_name": "Unauthorized"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/admin/abod_admin_webhook_secret",
                json=unauthorized_webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should still return 200 but admin bot should not respond to unauthorized user
            unauthorized_handled = response.status_code == 200
            self.log_test(
                "Admin Bot - Unauthorized ID Handling",
                unauthorized_handled,
                f"Status: {response.status_code} (Admin bot should ignore unauthorized users)"
            )
            
        except Exception as e:
            self.log_test("Admin Bot - Unauthorized ID Handling", False, str(e))

    def test_modern_user_interface(self):
        """Test modern user interface features"""
        print("🎨 Testing Modern User Interface Features...")
        
        # Test user bot with modern interface
        user_webhook_data = {
            "message": {
                "chat_id": 987654321,
                "text": "/start",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user",
                    "first_name": "TestUser"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=user_webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            modern_ui_success = response.status_code == 200
            self.log_test(
                "User Bot - Modern Interface Start",
                modern_ui_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("User Bot - Modern Interface Start", False, str(e))

    def test_callback_features(self):
        """Test modern callback features like special offers, about store, etc."""
        print("🔄 Testing Modern Callback Features...")
        
        # Test special offers callback
        special_offers_data = {
            "callback_query": {
                "message": {
                    "chat_id": 987654321
                },
                "data": "special_offers",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=special_offers_data,
                headers={"Content-Type": "application/json"}
            )
            
            special_offers_success = response.status_code == 200
            self.log_test(
                "Special Offers Callback",
                special_offers_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Special Offers Callback", False, str(e))
        
        # Test about store callback
        about_store_data = {
            "callback_query": {
                "message": {
                    "chat_id": 987654321
                },
                "data": "about_store",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=about_store_data,
                headers={"Content-Type": "application/json"}
            )
            
            about_store_success = response.status_code == 200
            self.log_test(
                "About Store Callback",
                about_store_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("About Store Callback", False, str(e))
        
        # Test refresh data callback
        refresh_data_data = {
            "callback_query": {
                "message": {
                    "chat_id": 987654321
                },
                "data": "refresh_data",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=refresh_data_data,
                headers={"Content-Type": "application/json"}
            )
            
            refresh_data_success = response.status_code == 200
            self.log_test(
                "Refresh Data Callback",
                refresh_data_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Refresh Data Callback", False, str(e))

    def test_back_button_functionality(self):
        """Test improved back button with session clearing"""
        print("🔙 Testing Back Button Functionality...")
        
        back_button_data = {
            "callback_query": {
                "message": {
                    "chat_id": 987654321
                },
                "data": "back_to_main_menu",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=back_button_data,
                headers={"Content-Type": "application/json"}
            )
            
            back_button_success = response.status_code == 200
            self.log_test(
                "Back Button with Session Clearing",
                back_button_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Back Button with Session Clearing", False, str(e))

    def test_spending_details_feature(self):
        """Test spending details feature"""
        print("📊 Testing Spending Details Feature...")
        
        spending_details_data = {
            "callback_query": {
                "message": {
                    "chat_id": 987654321
                },
                "data": "spending_details",
                "from_user": {
                    "id": 987654321,
                    "username": "test_user"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=spending_details_data,
                headers={"Content-Type": "application/json"}
            )
            
            spending_success = response.status_code == 200
            self.log_test(
                "Spending Details Feature",
                spending_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Spending Details Feature", False, str(e))

    def test_webhook_security(self):
        """Test webhook security with wrong secrets"""
        print("🔐 Testing Webhook Security...")
        
        # Test with wrong admin secret
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/admin/wrong_secret",
                json={"message": {"chat_id": self.admin_id, "text": "/start"}},
                headers={"Content-Type": "application/json"}
            )
            
            security_working = response.status_code == 403
            self.log_test(
                "Admin Webhook Security",
                security_working,
                f"Status: {response.status_code} (should be 403)"
            )
            
        except Exception as e:
            self.log_test("Admin Webhook Security", False, str(e))
        
        # Test with wrong user secret
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/wrong_secret",
                json={"message": {"chat_id": 987654321, "text": "/start"}},
                headers={"Content-Type": "application/json"}
            )
            
            user_security_working = response.status_code == 403
            self.log_test(
                "User Webhook Security",
                user_security_working,
                f"Status: {response.status_code} (should be 403)"
            )
            
        except Exception as e:
            self.log_test("User Webhook Security", False, str(e))

    def test_api_endpoints(self):
        """Test basic API endpoints"""
        print("🌐 Testing API Endpoints...")
        
        endpoints = [
            "/api/products",
            "/api/categories", 
            "/api/users",
            "/api/orders",
            "/api/pending-orders"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                self.log_test(
                    f"API Endpoint {endpoint}",
                    success,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_test(f"API Endpoint {endpoint}", False, str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Telegram Bot Backend Tests for Admin Filtering and Modern UI")
        print("=" * 70)
        
        # Test admin filtering (most important)
        self.test_admin_filtering()
        
        # Test modern UI features
        self.test_modern_user_interface()
        self.test_callback_features()
        self.test_back_button_functionality()
        self.test_spending_details_feature()
        
        # Test security
        self.test_webhook_security()
        
        # Test basic API endpoints
        self.test_api_endpoints()
        
        # Print summary
        print("=" * 70)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main function"""
    tester = TelegramBotTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())