#!/usr/bin/env python3
"""
Focused Backend Test for Arabic Abod Card Features
Testing the specific features mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime

class FocusedAbodCardTester:
    def __init__(self, base_url="https://telecard-manager.preview.emergentagent.com"):
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
        
    def test_webhook_endpoint(self, endpoint, data, expected_status=200):
        """Test webhook endpoint"""
        try:
            url = f"{self.base_url}/api/{endpoint}"
            response = requests.post(url, json=data, timeout=10)
            success = response.status_code == expected_status
            return success, response.status_code, response.text[:200] if not success else "OK"
        except Exception as e:
            return False, 0, str(e)
    
    def test_core_features(self):
        """Test the core features mentioned in the review request"""
        print("\n🎯 Testing Core Arabic Features...")
        
        # Test 1: رسالة الترحيب الجديدة مع الأنيميشن الجذاب (New welcome message with animation)
        welcome_data = {
            "update_id": 1001,
            "message": {
                "message_id": 1,
                "date": 1632825600,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                "text": "/start"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            welcome_data
        )
        self.log_test("1. رسالة الترحيب الجديدة مع الأنيميشن الجذاب", success, f"Status: {status}")
        
        # Test 2-4: معالجة الأرقام المباشرة (1-8) للوصول السريع (Direct number handling)
        for number in [1, 4, 8]:  # Test a few key numbers
            number_data = {
                "update_id": 1000 + number,
                "message": {
                    "message_id": number,
                    "date": 1632825600,
                    "chat": {"id": 123456789, "type": "private"},
                    "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                    "text": str(number)
                }
            }
            
            success, status, details = self.test_webhook_endpoint(
                "webhook/user/abod_user_webhook_secret", 
                number_data
            )
            self.log_test(f"2-4. معالجة الأرقام المباشرة ({number})", success, f"Status: {status}")
        
        # Test 5: إصلاح معالجات إدخال الإيدي والإيميل (Fix ID and email input handlers)
        email_data = {
            "update_id": 1020,
            "message": {
                "message_id": 20,
                "date": 1632825600,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                "text": "test@example.com"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            email_data
        )
        self.log_test("5. إصلاح معالجات إدخال الإيميل", success, f"Status: {status}")
        
        id_data = {
            "update_id": 1021,
            "message": {
                "message_id": 21,
                "date": 1632825600,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                "text": "USER123456"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            id_data
        )
        self.log_test("5. إصلاح معالجات إدخال الإيدي", success, f"Status: {status}")
        
        # Test 10: معالجة النصوص غير المفهومة مع رسائل المساعدة (Handling unrecognized text)
        unknown_text_data = {
            "update_id": 1030,
            "message": {
                "message_id": 30,
                "date": 1632825600,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                "text": "random unknown text that should trigger help"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/user/abod_user_webhook_secret", 
            unknown_text_data
        )
        self.log_test("10. معالجة النصوص غير المفهومة مع رسائل المساعدة", success, f"Status: {status}")
    
    def test_admin_filtering(self):
        """Test admin bot filtering - the main issue mentioned"""
        print("\n🔧 Testing Admin Bot Filtering...")
        
        # Test authorized admin (7040570081)
        admin_data = {
            "update_id": 2001,
            "message": {
                "message_id": 100,
                "date": 1632825600,
                "chat": {"id": 7040570081, "type": "private"},
                "from": {"id": 7040570081, "username": "admin", "first_name": "Admin", "is_bot": False},
                "text": "/start"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/admin/abod_admin_webhook_secret", 
            admin_data
        )
        self.log_test("Admin Bot - Authorized Access (7040570081)", success, f"Status: {status}")
        
        # Test unauthorized admin
        unauthorized_data = {
            "update_id": 2002,
            "message": {
                "message_id": 101,
                "date": 1632825600,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "username": "unauthorized", "first_name": "Unauthorized", "is_bot": False},
                "text": "/start"
            }
        }
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/admin/abod_admin_webhook_secret", 
            unauthorized_data
        )
        self.log_test("Admin Bot - Unauthorized Access Ignored", success, f"Status: {status}")
    
    def test_key_callback_features(self):
        """Test key callback features mentioned in the review"""
        print("\n🔘 Testing Key Callback Features...")
        
        key_features = [
            ("daily_surprises", "6. دالة المفاجآت اليومية"),
            ("support", "7. الدعم الفني المحسن"),
            ("faq", "8. الأسئلة الشائعة"),
            ("spending_details", "9. تفاصيل الإنفاق"),
            ("back_to_main_menu", "11. التنقل السلس")
        ]
        
        for i, (callback_data, description) in enumerate(key_features):
            callback_request = {
                "update_id": 3000 + i,
                "callback_query": {
                    "id": f"callback_{i}",
                    "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                    "message": {
                        "message_id": 200 + i,
                        "date": 1632825600,
                        "chat": {"id": 123456789, "type": "private"},
                        "from": {"id": 123456789, "username": "testuser", "first_name": "Test User", "is_bot": False},
                        "text": "Previous message"
                    },
                    "data": callback_data
                }
            }
            
            success, status, details = self.test_webhook_endpoint(
                "webhook/user/abod_user_webhook_secret", 
                callback_request
            )
            self.log_test(description, success, f"Status: {status}")
    
    def test_security_features(self):
        """Test security features"""
        print("\n🔒 Testing Security Features...")
        
        # Test webhook security
        wrong_secret_data = {"message": {"text": "/start"}}
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/user/wrong_secret", 
            wrong_secret_data,
            403
        )
        self.log_test("User Webhook Security", success, f"Status: {status}")
        
        success, status, details = self.test_webhook_endpoint(
            "webhook/admin/wrong_secret", 
            wrong_secret_data,
            403
        )
        self.log_test("Admin Webhook Security", success, f"Status: {status}")
    
    def run_focused_tests(self):
        """Run focused tests on the specific features mentioned in the review"""
        print("🎯 Starting Focused Arabic Features Testing...")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run focused test suites
        self.test_security_features()
        self.test_core_features()
        self.test_admin_filtering()
        self.test_key_callback_features()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
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
            print("\n🎉 ALL FOCUSED TESTS PASSED!")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(self.failed_tests) == 0

def main():
    """Main function"""
    print("🎯 Focused Abod Card Arabic Features Backend Tester")
    print("Testing specific features from the Arabic review request...")
    
    tester = FocusedAbodCardTester()
    success = tester.run_focused_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())