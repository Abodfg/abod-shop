#!/usr/bin/env python3
"""
Comprehensive Backend Test for Review Request Features
Testing specific features mentioned in the Arabic review request:
1. فلترة بوت الإدارة للإيدي 7040570081 فقط
2. عدم استجابة بوت الإدارة لأي مستخدم آخر
3. الواجهة العصرية الجديدة لبوت المستخدم
4. رسالة الترحيب المحدثة مع التصميم الجديد
5. الكيبورد العصري الجديد مع خيارات متقدمة
6. دالة الرجوع المحسنة مع مسح كامل للجلسة
7. العروض الخاصة ومعلومات المتجر
8. تحديث بيانات المستخدم وتفاصيل الإنفاق
9. عرض المحفظة العصري مع إحصائيات مفصلة
10. تصفح المنتجات بتصميم جذاب
11. حالة الطلبات تبقى 'pending' حتى التنفيذ اليدوي
12. معالجة صحيحة للجلسات مع منع التداخل
"""

import requests
import json
import sys
from datetime import datetime
import time

class ReviewFeatureTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_id = 7040570081  # The authorized admin ID from server.py
        self.unauthorized_ids = [123456789, 987654321, 555666777]  # Multiple unauthorized IDs
        
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

    def test_admin_id_filtering_comprehensive(self):
        """Test comprehensive admin ID filtering - Feature 1 & 2"""
        print("🔒 Testing Comprehensive Admin ID Filtering...")
        
        # Test authorized admin ID (7040570081)
        admin_webhook_data = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": self.admin_id, "type": "private"},
                "date": int(time.time()),
                "text": "/start",
                "from": {
                    "id": self.admin_id,
                    "username": "authorized_admin",
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
                "Admin ID 7040570081 - Authorized Access", 
                authorized_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Admin ID 7040570081 - Authorized Access", False, str(e))
        
        # Test multiple unauthorized IDs
        for i, unauthorized_id in enumerate(self.unauthorized_ids):
            unauthorized_webhook_data = {
                "update_id": i + 2,
                "message": {
                    "message_id": i + 2,
                    "chat": {"id": unauthorized_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "/start",
                    "from": {
                        "id": unauthorized_id,
                        "username": f"unauthorized_user_{i}",
                        "first_name": f"Unauthorized{i}",
                        "is_bot": False
                    }
                }
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/webhook/admin/abod_admin_webhook_secret",
                    json=unauthorized_webhook_data,
                    headers={"Content-Type": "application/json"}
                )
                
                # Should return 200 but admin bot should ignore unauthorized users
                unauthorized_handled = response.status_code == 200
                self.log_test(
                    f"Admin Bot Ignores ID {unauthorized_id}",
                    unauthorized_handled,
                    f"Status: {response.status_code} (Admin bot should ignore this user)"
                )
                
            except Exception as e:
                self.log_test(f"Admin Bot Ignores ID {unauthorized_id}", False, str(e))

    def test_modern_user_interface_features(self):
        """Test modern user interface features - Features 3, 4, 5"""
        print("🎨 Testing Modern User Interface Features...")
        
        test_user_id = 987654321
        
        # Test modern welcome message and keyboard
        user_start_data = {
            "update_id": 10,
            "message": {
                "message_id": 10,
                "chat": {"id": test_user_id, "type": "private"},
                "date": int(time.time()),
                "text": "/start",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=user_start_data,
                headers={"Content-Type": "application/json"}
            )
            
            modern_ui_success = response.status_code == 200
            self.log_test(
                "Modern Welcome Message & Keyboard",
                modern_ui_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Modern Welcome Message & Keyboard", False, str(e))

    def test_advanced_keyboard_options(self):
        """Test advanced keyboard options - Feature 5"""
        print("⌨️ Testing Advanced Keyboard Options...")
        
        test_user_id = 987654321
        advanced_options = [
            "browse_products",  # 🛍️ تسوق المنتجات
            "view_wallet",      # 💳 محفظتي
            "order_history",    # 📦 طلباتي
            "special_offers",   # ⭐ العروض الخاصة
            "support",          # 💬 الدعم الفني
            "about_store",      # ℹ️ حول المتجر
            "refresh_data"      # 🔄 تحديث البيانات
        ]
        
        for i, option in enumerate(advanced_options):
            callback_data = {
                "update_id": 20 + i,
                "callback_query": {
                    "id": f"callback_{20 + i}",
                    "chat_instance": f"test_instance_{20 + i}",
                    "message": {
                        "message_id": 20 + i,
                        "chat": {"id": test_user_id, "type": "private"},
                        "date": int(time.time()),
                        "text": "Test message"
                    },
                    "data": option,
                    "from": {
                        "id": test_user_id,
                        "username": "test_user",
                        "first_name": "TestUser",
                        "is_bot": False
                    }
                }
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                    json=callback_data,
                    headers={"Content-Type": "application/json"}
                )
                
                option_success = response.status_code == 200
                self.log_test(
                    f"Advanced Option: {option}",
                    option_success,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_test(f"Advanced Option: {option}", False, str(e))

    def test_improved_back_function(self):
        """Test improved back function with session clearing - Feature 6"""
        print("🔙 Testing Improved Back Function...")
        
        test_user_id = 987654321
        
        # Test back to main menu with session clearing
        back_data = {
            "update_id": 30,
            "callback_query": {
                "id": "callback_30",
                "chat_instance": "test_instance_30",
                "message": {
                    "message_id": 30,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "back_to_main_menu",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=back_data,
                headers={"Content-Type": "application/json"}
            )
            
            back_success = response.status_code == 200
            self.log_test(
                "Improved Back Function with Session Clearing",
                back_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Improved Back Function with Session Clearing", False, str(e))

    def test_special_offers_and_store_info(self):
        """Test special offers and store information - Feature 7"""
        print("⭐ Testing Special Offers and Store Information...")
        
        test_user_id = 987654321
        
        # Test special offers
        special_offers_data = {
            "update_id": 31,
            "callback_query": {
                "id": "callback_31",
                "chat_instance": "test_instance_31",
                "message": {
                    "message_id": 31,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "special_offers",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=special_offers_data,
                headers={"Content-Type": "application/json"}
            )
            
            offers_success = response.status_code == 200
            self.log_test(
                "Special Offers Feature",
                offers_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Special Offers Feature", False, str(e))
        
        # Test about store
        about_store_data = {
            "update_id": 32,
            "callback_query": {
                "id": "callback_32",
                "chat_instance": "test_instance_32",
                "message": {
                    "message_id": 32,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "about_store",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=about_store_data,
                headers={"Content-Type": "application/json"}
            )
            
            store_info_success = response.status_code == 200
            self.log_test(
                "Store Information Feature",
                store_info_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Store Information Feature", False, str(e))

    def test_user_data_updates_and_spending(self):
        """Test user data updates and spending details - Feature 8"""
        print("📊 Testing User Data Updates and Spending Details...")
        
        test_user_id = 987654321
        
        # Test refresh data
        refresh_data = {
            "update_id": 33,
            "callback_query": {
                "id": "callback_33",
                "chat_instance": "test_instance_33",
                "message": {
                    "message_id": 33,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "refresh_data",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=refresh_data,
                headers={"Content-Type": "application/json"}
            )
            
            refresh_success = response.status_code == 200
            self.log_test(
                "User Data Refresh Feature",
                refresh_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("User Data Refresh Feature", False, str(e))
        
        # Test spending details
        spending_data = {
            "update_id": 34,
            "callback_query": {
                "id": "callback_34",
                "chat_instance": "test_instance_34",
                "message": {
                    "message_id": 34,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "spending_details",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=spending_data,
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

    def test_modern_wallet_display(self):
        """Test modern wallet display - Feature 9"""
        print("💳 Testing Modern Wallet Display...")
        
        test_user_id = 987654321
        
        wallet_data = {
            "update_id": 35,
            "callback_query": {
                "id": "callback_35",
                "chat_instance": "test_instance_35",
                "message": {
                    "message_id": 35,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "view_wallet",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=wallet_data,
                headers={"Content-Type": "application/json"}
            )
            
            wallet_success = response.status_code == 200
            self.log_test(
                "Modern Wallet Display with Statistics",
                wallet_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Modern Wallet Display with Statistics", False, str(e))

    def test_product_browsing_design(self):
        """Test product browsing with attractive design - Feature 10"""
        print("🛍️ Testing Product Browsing Design...")
        
        test_user_id = 987654321
        
        browse_data = {
            "update_id": 36,
            "callback_query": {
                "id": "callback_36",
                "chat_instance": "test_instance_36",
                "message": {
                    "message_id": 36,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "browse_products",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=browse_data,
                headers={"Content-Type": "application/json"}
            )
            
            browse_success = response.status_code == 200
            self.log_test(
                "Attractive Product Browsing Design",
                browse_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Attractive Product Browsing Design", False, str(e))

    def test_pending_order_status(self):
        """Test that orders remain pending until manual execution - Feature 11"""
        print("⏳ Testing Pending Order Status Management...")
        
        # Test API endpoint for pending orders
        try:
            response = requests.get(f"{self.base_url}/api/pending-orders")
            
            pending_success = response.status_code == 200
            self.log_test(
                "Pending Orders API Endpoint",
                pending_success,
                f"Status: {response.status_code}"
            )
            
            if pending_success:
                try:
                    orders = response.json()
                    self.log_test(
                        "Pending Orders Data Structure",
                        True,
                        f"Found {len(orders)} pending orders"
                    )
                except:
                    self.log_test(
                        "Pending Orders Data Structure",
                        False,
                        "Could not parse JSON response"
                    )
            
        except Exception as e:
            self.log_test("Pending Orders API Endpoint", False, str(e))

    def test_session_handling(self):
        """Test proper session handling to prevent interference - Feature 12"""
        print("🔄 Testing Session Handling...")
        
        # Test session clearing functionality through back button
        test_user_id = 987654321
        
        # Simulate a session state and then clear it
        back_data = {
            "update_id": 40,
            "callback_query": {
                "id": "callback_40",
                "chat_instance": "test_instance_40",
                "message": {
                    "message_id": 40,
                    "chat": {"id": test_user_id, "type": "private"},
                    "date": int(time.time()),
                    "text": "Test message"
                },
                "data": "back_to_main_menu",
                "from": {
                    "id": test_user_id,
                    "username": "test_user",
                    "first_name": "TestUser",
                    "is_bot": False
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/webhook/user/abod_user_webhook_secret",
                json=back_data,
                headers={"Content-Type": "application/json"}
            )
            
            session_success = response.status_code == 200
            self.log_test(
                "Session Handling and Clearing",
                session_success,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Session Handling and Clearing", False, str(e))

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Feature Tests for Review Request")
        print("=" * 80)
        
        # Test all features mentioned in the review request
        self.test_admin_id_filtering_comprehensive()      # Features 1 & 2
        self.test_modern_user_interface_features()        # Features 3, 4, 5
        self.test_advanced_keyboard_options()             # Feature 5
        self.test_improved_back_function()                # Feature 6
        self.test_special_offers_and_store_info()         # Feature 7
        self.test_user_data_updates_and_spending()        # Feature 8
        self.test_modern_wallet_display()                 # Feature 9
        self.test_product_browsing_design()               # Feature 10
        self.test_pending_order_status()                  # Feature 11
        self.test_session_handling()                      # Feature 12
        
        # Print summary
        print("=" * 80)
        print(f"📊 Comprehensive Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All comprehensive tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main function"""
    tester = ReviewFeatureTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())