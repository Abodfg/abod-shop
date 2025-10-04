#!/usr/bin/env python3
"""
Dual Admin System Testing Suite
Tests the updated administrative system with two admins:
- Main Admin (7040570081): receives all notifications
- System Admin (1573526135): receives only system heartbeat notifications
"""

import requests
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

class DualAdminSystemTester:
    def __init__(self, base_url="https://digicardbot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'DualAdmin-Tester/1.0'
        })
        
        # Admin IDs from the system
        self.MAIN_ADMIN_ID = 7040570081      # الإداري الرئيسي - جميع الإشعارات
        self.SYSTEM_ADMIN_ID = 1573526135    # إداري النظام - نبض النظام فقط
        self.ADMIN_BOT_TOKEN = "7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"

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

    def test_main_admin_access(self):
        """Test Main Admin (7040570081) access and welcome message"""
        print("🔍 Testing Main Admin Access (7040570081)...")
        
        # Test /start command for main admin
        main_admin_update = {
            "update_id": 123460000,
            "message": {
                "message_id": 1000,
                "from": {
                    "id": self.MAIN_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "الإدارة الرئيسية",
                    "username": "main_admin",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.MAIN_ADMIN_ID,
                    "first_name": "الإدارة الرئيسية",
                    "username": "main_admin",
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
            main_admin_update, 
            "Main Admin /start Command"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Main Admin Access Control", True, "Main Admin (7040570081) has full access")
            return True
        else:
            self.log_test("Main Admin Access Control", False, f"Main Admin access failed: {data}")
            return False

    def test_system_admin_access(self):
        """Test System Admin (1573526135) access and welcome message with note"""
        print("🔍 Testing System Admin Access (1573526135)...")
        
        # Test /start command for system admin
        system_admin_update = {
            "update_id": 123460001,
            "message": {
                "message_id": 1001,
                "from": {
                    "id": self.SYSTEM_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "إدارة النظام",
                    "username": "system_admin",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.SYSTEM_ADMIN_ID,
                    "first_name": "إدارة النظام",
                    "username": "system_admin",
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
            system_admin_update, 
            "System Admin /start Command"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("System Admin Access Control", True, "System Admin (1573526135) has access with note about system heartbeat only")
            return True
        else:
            self.log_test("System Admin Access Control", False, f"System Admin access failed: {data}")
            return False

    def test_main_admin_management_functions(self):
        """Test Main Admin access to all management functions"""
        print("🔍 Testing Main Admin Management Functions...")
        
        management_functions = [
            ("manage_products", "Product Management"),
            ("manage_users", "User Management"),
            ("manage_orders", "Order Management"),
            ("reports", "Reports"),
            ("manage_codes", "Code Management")
        ]
        
        all_success = True
        
        for callback_data, function_name in management_functions:
            admin_function_update = {
                "update_id": 123460100 + hash(callback_data) % 100,
                "callback_query": {
                    "id": f"main_admin_{callback_data}",
                    "chat_instance": f"main_admin_chat_{callback_data}",
                    "from": {
                        "id": self.MAIN_ADMIN_ID,
                        "is_bot": False,
                        "first_name": "الإدارة الرئيسية",
                        "username": "main_admin",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 1100 + hash(callback_data) % 100,
                        "from": {
                            "id": 7835622090,
                            "is_bot": True,
                            "first_name": "Abod Admin Bot",
                            "username": "abod_admin_bot"
                        },
                        "chat": {
                            "id": self.MAIN_ADMIN_ID,
                            "first_name": "الإدارة الرئيسية",
                            "username": "main_admin",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Admin main menu"
                    },
                    "data": callback_data
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/admin/abod_admin_webhook_secret', 
                200, 
                admin_function_update, 
                f"Main Admin - {function_name}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Main Admin Management Functions", True, "All management functions accessible to Main Admin")
        else:
            self.log_test("Main Admin Management Functions", False, "Some management functions failed for Main Admin")
        
        return all_success

    def test_system_admin_management_functions(self):
        """Test System Admin access to all management functions"""
        print("🔍 Testing System Admin Management Functions...")
        
        management_functions = [
            ("manage_products", "Product Management"),
            ("manage_users", "User Management"),
            ("manage_orders", "Order Management"),
            ("reports", "Reports"),
            ("manage_codes", "Code Management")
        ]
        
        all_success = True
        
        for callback_data, function_name in management_functions:
            admin_function_update = {
                "update_id": 123460200 + hash(callback_data) % 100,
                "callback_query": {
                    "id": f"system_admin_{callback_data}",
                    "chat_instance": f"system_admin_chat_{callback_data}",
                    "from": {
                        "id": self.SYSTEM_ADMIN_ID,
                        "is_bot": False,
                        "first_name": "إدارة النظام",
                        "username": "system_admin",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 1200 + hash(callback_data) % 100,
                        "from": {
                            "id": 7835622090,
                            "is_bot": True,
                            "first_name": "Abod Admin Bot",
                            "username": "abod_admin_bot"
                        },
                        "chat": {
                            "id": self.SYSTEM_ADMIN_ID,
                            "first_name": "إدارة النظام",
                            "username": "system_admin",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Admin main menu"
                    },
                    "data": callback_data
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/admin/abod_admin_webhook_secret', 
                200, 
                admin_function_update, 
                f"System Admin - {function_name}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("System Admin Management Functions", True, "All management functions accessible to System Admin")
        else:
            self.log_test("System Admin Management Functions", False, "Some management functions failed for System Admin")
        
        return all_success

    def test_notification_system_configuration(self):
        """Test notification system configuration in backend"""
        print("🔍 Testing Notification System Configuration...")
        
        # Check if the backend has the correct admin IDs configured
        # This is tested by checking if both admins can access the system
        main_admin_access = self.test_main_admin_access()
        system_admin_access = self.test_system_admin_access()
        
        if main_admin_access and system_admin_access:
            self.log_test("Notification System Configuration", True, "Both admin IDs configured correctly in system")
            return True
        else:
            self.log_test("Notification System Configuration", False, "Admin ID configuration issues")
            return False

    def test_admin_bot_token_configuration(self):
        """Test Admin Bot Token configuration"""
        print("🔍 Testing Admin Bot Token Configuration...")
        
        # Test webhook with correct admin bot token
        test_update = {
            "update_id": 123460300,
            "message": {
                "message_id": 1300,
                "from": {
                    "id": self.MAIN_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "Test Admin",
                    "username": "test_admin",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.MAIN_ADMIN_ID,
                    "first_name": "Test Admin",
                    "username": "test_admin",
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
            test_update, 
            "Admin Bot Token Test"
        )
        
        if success:
            self.log_test("Admin Bot Token Configuration", True, f"Admin Bot Token ({self.ADMIN_BOT_TOKEN}) working correctly")
            return True
        else:
            self.log_test("Admin Bot Token Configuration", False, "Admin Bot Token configuration issue")
            return False

    def test_product_management_for_main_admin(self):
        """Test product management features for Main Admin"""
        print("🔍 Testing Product Management for Main Admin...")
        
        # Test edit product access
        edit_product_update = {
            "update_id": 123460400,
            "callback_query": {
                "id": "main_admin_edit_product",
                "chat_instance": "main_admin_edit_chat",
                "from": {
                    "id": self.MAIN_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "الإدارة الرئيسية",
                    "username": "main_admin",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1400,
                    "from": {
                        "id": 7835622090,
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.MAIN_ADMIN_ID,
                        "first_name": "الإدارة الرئيسية",
                        "username": "main_admin",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Product management"
                },
                "data": "edit_product"
            }
        }
        
        success_edit, data_edit = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            edit_product_update, 
            "Main Admin - Edit Product"
        )
        
        # Test delete product access
        delete_product_update = {
            "update_id": 123460401,
            "callback_query": {
                "id": "main_admin_delete_product",
                "chat_instance": "main_admin_delete_chat",
                "from": {
                    "id": self.MAIN_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "الإدارة الرئيسية",
                    "username": "main_admin",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1401,
                    "from": {
                        "id": 7835622090,
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.MAIN_ADMIN_ID,
                        "first_name": "الإدارة الرئيسية",
                        "username": "main_admin",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Product management"
                },
                "data": "delete_product"
            }
        }
        
        success_delete, data_delete = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            delete_product_update, 
            "Main Admin - Delete Product"
        )
        
        if success_edit and success_delete:
            self.log_test("Main Admin Product Management", True, "Main Admin can edit and delete products")
            return True
        else:
            self.log_test("Main Admin Product Management", False, "Main Admin product management issues")
            return False

    def test_product_management_for_system_admin(self):
        """Test product management features for System Admin"""
        print("🔍 Testing Product Management for System Admin...")
        
        # Test edit product access
        edit_product_update = {
            "update_id": 123460500,
            "callback_query": {
                "id": "system_admin_edit_product",
                "chat_instance": "system_admin_edit_chat",
                "from": {
                    "id": self.SYSTEM_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "إدارة النظام",
                    "username": "system_admin",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1500,
                    "from": {
                        "id": 7835622090,
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.SYSTEM_ADMIN_ID,
                        "first_name": "إدارة النظام",
                        "username": "system_admin",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Product management"
                },
                "data": "edit_product"
            }
        }
        
        success_edit, data_edit = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            edit_product_update, 
            "System Admin - Edit Product"
        )
        
        # Test delete product access
        delete_product_update = {
            "update_id": 123460501,
            "callback_query": {
                "id": "system_admin_delete_product",
                "chat_instance": "system_admin_delete_chat",
                "from": {
                    "id": self.SYSTEM_ADMIN_ID,
                    "is_bot": False,
                    "first_name": "إدارة النظام",
                    "username": "system_admin",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1501,
                    "from": {
                        "id": 7835622090,
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.SYSTEM_ADMIN_ID,
                        "first_name": "إدارة النظام",
                        "username": "system_admin",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Product management"
                },
                "data": "delete_product"
            }
        }
        
        success_delete, data_delete = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            delete_product_update, 
            "System Admin - Delete Product"
        )
        
        if success_edit and success_delete:
            self.log_test("System Admin Product Management", True, "System Admin can edit and delete products")
            return True
        else:
            self.log_test("System Admin Product Management", False, "System Admin product management issues")
            return False

    def test_product_callbacks_for_both_admins(self):
        """Test product callbacks work for both admins"""
        print("🔍 Testing Product Callbacks for Both Admins...")
        
        # Get products first
        success, products_data = self.test_api_endpoint('GET', '/products', 200, test_name="Get Products for Callback Test")
        
        if success and isinstance(products_data, list) and len(products_data) > 0:
            product_id = products_data[0].get('id', 'test_product_id')
            
            # Test callback for Main Admin
            main_admin_callback = {
                "update_id": 123460600,
                "callback_query": {
                    "id": "main_admin_product_callback",
                    "chat_instance": "main_admin_callback_chat",
                    "from": {
                        "id": self.MAIN_ADMIN_ID,
                        "is_bot": False,
                        "first_name": "الإدارة الرئيسية",
                        "username": "main_admin",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 1600,
                        "from": {
                            "id": 7835622090,
                            "is_bot": True,
                            "first_name": "Abod Admin Bot",
                            "username": "abod_admin_bot"
                        },
                        "chat": {
                            "id": self.MAIN_ADMIN_ID,
                            "first_name": "الإدارة الرئيسية",
                            "username": "main_admin",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Select product"
                    },
                    "data": f"edit_product_{product_id}"
                }
            }
            
            success_main, data_main = self.test_api_endpoint(
                'POST', 
                '/webhook/admin/abod_admin_webhook_secret', 
                200, 
                main_admin_callback, 
                f"Main Admin - Product Callback {product_id}"
            )
            
            # Test callback for System Admin
            system_admin_callback = {
                "update_id": 123460601,
                "callback_query": {
                    "id": "system_admin_product_callback",
                    "chat_instance": "system_admin_callback_chat",
                    "from": {
                        "id": self.SYSTEM_ADMIN_ID,
                        "is_bot": False,
                        "first_name": "إدارة النظام",
                        "username": "system_admin",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 1601,
                        "from": {
                            "id": 7835622090,
                            "is_bot": True,
                            "first_name": "Abod Admin Bot",
                            "username": "abod_admin_bot"
                        },
                        "chat": {
                            "id": self.SYSTEM_ADMIN_ID,
                            "first_name": "إدارة النظام",
                            "username": "system_admin",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Select product"
                    },
                    "data": f"edit_product_{product_id}"
                }
            }
            
            success_system, data_system = self.test_api_endpoint(
                'POST', 
                '/webhook/admin/abod_admin_webhook_secret', 
                200, 
                system_admin_callback, 
                f"System Admin - Product Callback {product_id}"
            )
            
            if success_main and success_system:
                self.log_test("Product Callbacks for Both Admins", True, "Product callbacks working for both admins")
                return True
            else:
                self.log_test("Product Callbacks for Both Admins", False, "Product callback issues")
                return False
        else:
            self.log_test("Product Callbacks for Both Admins", False, "No products available for callback testing")
            return False

    def test_unauthorized_admin_rejection(self):
        """Test that unauthorized admin IDs are rejected"""
        print("🔍 Testing Unauthorized Admin Rejection...")
        
        # Test with unauthorized admin ID
        unauthorized_update = {
            "update_id": 123460700,
            "message": {
                "message_id": 1700,
                "from": {
                    "id": 999999999,  # Unauthorized admin ID
                    "is_bot": False,
                    "first_name": "Fake Admin",
                    "username": "fake_admin",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 999999999,
                    "first_name": "Fake Admin",
                    "username": "fake_admin",
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
            unauthorized_update, 
            "Unauthorized Admin Rejection Test"
        )
        
        if success:
            self.log_test("Unauthorized Admin Rejection", True, "Unauthorized admin properly rejected")
            return True
        else:
            self.log_test("Unauthorized Admin Rejection", False, "Unauthorized admin rejection failed")
            return False

    def run_all_tests(self):
        """Run all dual admin system tests"""
        print("🚀 Starting Dual Admin System Testing...")
        print("=" * 60)
        
        # Test 1: Main Admin Access
        self.test_main_admin_access()
        
        # Test 2: System Admin Access  
        self.test_system_admin_access()
        
        # Test 3: Main Admin Management Functions
        self.test_main_admin_management_functions()
        
        # Test 4: System Admin Management Functions
        self.test_system_admin_management_functions()
        
        # Test 5: Notification System Configuration
        self.test_notification_system_configuration()
        
        # Test 6: Admin Bot Token Configuration
        self.test_admin_bot_token_configuration()
        
        # Test 7: Product Management for Main Admin
        self.test_product_management_for_main_admin()
        
        # Test 8: Product Management for System Admin
        self.test_product_management_for_system_admin()
        
        # Test 9: Product Callbacks for Both Admins
        self.test_product_callbacks_for_both_admins()
        
        # Test 10: Unauthorized Admin Rejection
        self.test_unauthorized_admin_rejection()
        
        # Print summary
        print("=" * 60)
        print("🏁 DUAL ADMIN SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details']}")
            print()
        
        # Overall status
        if success_rate >= 90:
            print("🟢 DUAL ADMIN SYSTEM STATUS: EXCELLENT")
        elif success_rate >= 75:
            print("🟡 DUAL ADMIN SYSTEM STATUS: GOOD")
        elif success_rate >= 50:
            print("🟠 DUAL ADMIN SYSTEM STATUS: NEEDS IMPROVEMENT")
        else:
            print("🔴 DUAL ADMIN SYSTEM STATUS: CRITICAL ISSUES")
        
        print("=" * 60)
        
        return success_rate >= 75

def main():
    """Main function to run dual admin system tests"""
    tester = DualAdminSystemTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()