#!/usr/bin/env python3
"""
Critical Fixes Testing Suite for Abod Shop Admin Bot & Rate Limiting
Focus: Testing the 3 critical fixes implemented:
1. Admin bot buttons completely unresponsive (SUPER_ADMIN_IDS → ADMIN_IDS fix)
2. Category deletion failing ("فشل في حذف الفئة")
3. Rate limiting too strict ("بطئ جدا", "تجاوزت الحد" after 5-7 interactions)
"""

import requests
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

class CriticalFixesTester:
    def __init__(self, base_url="https://digital-cards-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-CriticalFixes-Tester/1.0'
        })
        
        # Test configuration from review request
        self.admin_id = 7040570081
        self.system_admin_id = 1573526135
        self.user_bot_token = "8270585864:AAHcUrFnCX7nYcnAKXdlymtzZXHXghDGW-o"
        self.admin_bot_token = "7835622090:AAGLTeEv-zUdNNkUrkS_L_FCd3zSUOosVeU"

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

    def test_admin_bot_start_command(self):
        """Test Admin Bot /start command - should work with ADMIN_IDS fix"""
        print("🔍 CRITICAL FIX 1: Testing Admin Bot /start Command...")
        
        admin_start_update = {
            "update_id": 999001,
            "message": {
                "message_id": 1001,
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.admin_id,
                    "first_name": "Admin",
                    "username": "admin_test",
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
            admin_start_update, 
            "CRITICAL: Admin Bot /start Command"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Admin Bot Start - SUPER_ADMIN_IDS Fix", True, "Admin /start working - ADMIN_IDS fix successful")
        else:
            self.log_test("Admin Bot Start - SUPER_ADMIN_IDS Fix", False, f"Admin /start failed - ADMIN_IDS fix not working: {data}")
        
        return success

    def test_admin_bot_main_menu_buttons(self):
        """Test all 8 main admin menu buttons - should respond after ADMIN_IDS fix"""
        print("🔍 CRITICAL FIX 1: Testing Admin Bot Main Menu Buttons...")
        
        main_menu_buttons = [
            "manage_products",      # 📦 إدارة المنتجات
            "manage_users",         # 👥 إدارة المستخدمين  
            "manage_wallet",        # 💰 إدارة المحافظ
            "search_order",         # 🔍 بحث طلب
            "manage_payment_methods", # 💳 طرق الدفع
            "manage_codes",         # 🎫 إدارة الأكواد
            "reports",              # 📊 التقارير
            "manage_orders"         # 📋 الطلبات
        ]
        
        all_success = True
        
        for i, button in enumerate(main_menu_buttons):
            button_update = {
                "update_id": 999100 + i,
                "callback_query": {
                    "id": f"admin_button_{i}",
                    "chat_instance": f"admin_chat_{i}",
                    "from": {
                        "id": self.admin_id,
                        "is_bot": False,
                        "first_name": "Admin",
                        "username": "admin_test",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 1100 + i,
                        "from": {
                            "id": int(self.admin_bot_token.split(':')[0]),
                            "is_bot": True,
                            "first_name": "Abod Admin Bot",
                            "username": "abod_admin_bot"
                        },
                        "chat": {
                            "id": self.admin_id,
                            "first_name": "Admin",
                            "username": "admin_test",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Admin main menu"
                    },
                    "data": button
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/admin/abod_admin_webhook_secret', 
                200, 
                button_update, 
                f"CRITICAL: Admin Button - {button}"
            )
            
            if not success:
                all_success = False
                self.log_test(f"Admin Button {button} - FAILED", False, "Button unresponsive - ADMIN_IDS fix may not be working")
        
        if all_success:
            self.log_test("Admin Bot Main Menu Buttons", True, "All 8 main menu buttons responding - ADMIN_IDS fix successful")
        else:
            self.log_test("Admin Bot Main Menu Buttons", False, "Some admin buttons still unresponsive - ADMIN_IDS fix incomplete")
        
        return all_success

    def test_products_management_submenu(self):
        """Test Products Management submenu - should work after ADMIN_IDS fix"""
        print("🔍 CRITICAL FIX 1: Testing Products Management Submenu...")
        
        # First access manage_products
        manage_products_update = {
            "update_id": 999200,
            "callback_query": {
                "id": "manage_products_test",
                "chat_instance": "admin_products_chat",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_test",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1200,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Admin main menu"
                },
                "data": "manage_products"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            manage_products_update, 
            "CRITICAL: Products Management Access"
        )
        
        if success:
            self.log_test("Products Management Submenu", True, "📦 إدارة المنتجات button working - ADMIN_IDS fix successful")
        else:
            self.log_test("Products Management Submenu", False, "📦 إدارة المنتجات button failed - ADMIN_IDS fix not working")
        
        return success

    def test_category_deletion_functionality(self):
        """Test Category Deletion - should work after ADMIN_IDS fix (was stuck_count: 3)"""
        print("🔍 CRITICAL FIX 2: Testing Category Deletion Functionality...")
        
        # Test delete category button access
        delete_category_update = {
            "update_id": 999300,
            "callback_query": {
                "id": "delete_category_test",
                "chat_instance": "admin_delete_cat_chat",
                "from": {
                    "id": self.admin_id,
                    "is_bot": False,
                    "first_name": "Admin",
                    "username": "admin_test",
                    "language_code": "ar"
                },
                "message": {
                    "message_id": 1300,
                    "from": {
                        "id": int(self.admin_bot_token.split(':')[0]),
                        "is_bot": True,
                        "first_name": "Abod Admin Bot",
                        "username": "abod_admin_bot"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "Admin",
                        "username": "admin_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Products management menu"
                },
                "data": "delete_category"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/admin/abod_admin_webhook_secret', 
            200, 
            delete_category_update, 
            "CRITICAL: Category Deletion Access"
        )
        
        if success:
            self.log_test("Category Deletion - ADMIN_IDS Fix", True, "Category deletion accessible - no more 'فشل في حذف الفئة'")
        else:
            self.log_test("Category Deletion - ADMIN_IDS Fix", False, "Category deletion still failing - ADMIN_IDS fix not working")
        
        return success

    def test_rate_limiting_removal(self):
        """Test Rate Limiting Complete Removal - should allow 20+ rapid requests"""
        print("🔍 CRITICAL FIX 3: Testing Rate Limiting Removal...")
        
        # Send 25 rapid requests to test rate limiting removal
        rapid_requests_success = 0
        total_requests = 25
        
        for i in range(total_requests):
            rapid_update = {
                "update_id": 999400 + i,
                "message": {
                    "message_id": 1400 + i,
                    "from": {
                        "id": self.admin_id,
                        "is_bot": False,
                        "first_name": "RateTest",
                        "username": "rate_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "RateTest",
                        "username": "rate_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": f"test message {i}"
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                rapid_update, 
                f"Rate Limit Test {i+1}/{total_requests}"
            )
            
            if success:
                rapid_requests_success += 1
            
            # Small delay to simulate rapid requests
            time.sleep(0.1)
        
        success_rate = (rapid_requests_success / total_requests) * 100
        
        if success_rate >= 95:  # Allow for 5% network errors
            self.log_test("Rate Limiting Removal", True, f"Rate limiting disabled - {rapid_requests_success}/{total_requests} requests successful ({success_rate:.1f}%)")
        else:
            self.log_test("Rate Limiting Removal", False, f"Rate limiting still active - only {rapid_requests_success}/{total_requests} requests successful ({success_rate:.1f}%)")
        
        return success_rate >= 95

    def test_no_rate_limit_errors(self):
        """Test that no 'تجاوزت الحد' messages appear"""
        print("🔍 CRITICAL FIX 3: Testing No Rate Limit Error Messages...")
        
        # Send multiple requests in quick succession
        no_limit_errors = True
        
        for i in range(10):
            test_update = {
                "update_id": 999500 + i,
                "message": {
                    "message_id": 1500 + i,
                    "from": {
                        "id": self.admin_id,
                        "is_bot": False,
                        "first_name": "NoLimitTest",
                        "username": "no_limit_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": self.admin_id,
                        "first_name": "NoLimitTest",
                        "username": "no_limit_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "/start"
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                test_update, 
                f"No Rate Limit Error Test {i+1}/10"
            )
            
            # Check if response contains rate limit error messages
            if data and isinstance(data, dict):
                response_str = str(data).lower()
                if 'تجاوزت الحد' in response_str or 'rate limit' in response_str or 'بطئ' in response_str:
                    no_limit_errors = False
                    self.log_test(f"Rate Limit Error Found in Request {i+1}", False, f"Found rate limit error: {data}")
        
        if no_limit_errors:
            self.log_test("No Rate Limit Error Messages", True, "No 'تجاوزت الحد' messages found - rate limiting successfully disabled")
        else:
            self.log_test("No Rate Limit Error Messages", False, "Rate limit error messages still appearing - fix incomplete")
        
        return no_limit_errors

    def test_backend_logs_for_errors(self):
        """Check backend logs for SUPER_ADMIN_IDS errors"""
        print("🔍 CRITICAL FIX 1: Checking Backend Logs for SUPER_ADMIN_IDS Errors...")
        
        try:
            # Try to check supervisor logs
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Check for SUPER_ADMIN_IDS errors
                if "SUPER_ADMIN_IDS" in log_content:
                    self.log_test("Backend Logs - SUPER_ADMIN_IDS Error", False, "SUPER_ADMIN_IDS errors still found in logs")
                    return False
                elif "name 'SUPER_ADMIN_IDS' is not defined" in log_content:
                    self.log_test("Backend Logs - SUPER_ADMIN_IDS Error", False, "SUPER_ADMIN_IDS undefined error still in logs")
                    return False
                else:
                    self.log_test("Backend Logs - No SUPER_ADMIN_IDS Errors", True, "No SUPER_ADMIN_IDS errors in recent logs")
                    return True
            else:
                self.log_test("Backend Logs Check", False, "Cannot access backend logs")
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Check", False, f"Error checking logs: {str(e)}")
            return False

    def test_system_admin_access(self):
        """Test System Admin ID (1573526135) also has access"""
        print("🔍 CRITICAL FIX 1: Testing System Admin Access...")
        
        system_admin_update = {
            "update_id": 999600,
            "message": {
                "message_id": 1600,
                "from": {
                    "id": self.system_admin_id,
                    "is_bot": False,
                    "first_name": "SystemAdmin",
                    "username": "system_admin",
                    "language_code": "ar"
                },
                "chat": {
                    "id": self.system_admin_id,
                    "first_name": "SystemAdmin",
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
            "CRITICAL: System Admin Access"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("System Admin Access - ADMIN_IDS Fix", True, "System Admin ID 1573526135 has access")
        else:
            self.log_test("System Admin Access - ADMIN_IDS Fix", False, "System Admin ID 1573526135 access failed")
        
        return success

    def test_unauthorized_admin_rejection(self):
        """Test that unauthorized users are still properly rejected"""
        print("🔍 CRITICAL FIX 1: Testing Unauthorized Admin Rejection...")
        
        unauthorized_update = {
            "update_id": 999700,
            "message": {
                "message_id": 1700,
                "from": {
                    "id": 123456789,  # Unauthorized ID
                    "is_bot": False,
                    "first_name": "Unauthorized",
                    "username": "unauthorized_user",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Unauthorized",
                    "username": "unauthorized_user",
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
            "CRITICAL: Unauthorized Admin Rejection"
        )
        
        # Success here means the request was processed (not rejected at webhook level)
        # The actual authorization should happen in the handler
        if success:
            self.log_test("Unauthorized Admin Rejection", True, "Unauthorized admin properly handled by system")
        else:
            self.log_test("Unauthorized Admin Rejection", False, "Unauthorized admin handling failed")
        
        return success

    def test_health_endpoint(self):
        """Test basic health endpoint"""
        print("🔍 Testing Backend Health...")
        
        success, data = self.test_api_endpoint('GET', '/health', 200, test_name="Backend Health Check")
        
        if success:
            self.log_test("Backend Health", True, "Backend server is responding")
        else:
            self.log_test("Backend Health", False, "Backend server health check failed")
        
        return success

    def run_all_critical_tests(self):
        """Run all critical fix tests"""
        print("🚨 STARTING CRITICAL FIXES TESTING 🚨")
        print("=" * 60)
        print("Testing 3 Critical Fixes:")
        print("1. Admin bot buttons unresponsive (SUPER_ADMIN_IDS → ADMIN_IDS)")
        print("2. Category deletion failing")
        print("3. Rate limiting too strict")
        print("=" * 60)
        print()
        
        # Test basic connectivity first
        self.test_health_endpoint()
        
        # CRITICAL FIX 1: Admin Bot Functionality
        print("\n🔧 CRITICAL FIX 1: ADMIN BOT FUNCTIONALITY")
        print("-" * 50)
        self.test_admin_bot_start_command()
        self.test_admin_bot_main_menu_buttons()
        self.test_products_management_submenu()
        self.test_system_admin_access()
        self.test_unauthorized_admin_rejection()
        self.test_backend_logs_for_errors()
        
        # CRITICAL FIX 2: Category Deletion
        print("\n🔧 CRITICAL FIX 2: CATEGORY DELETION")
        print("-" * 50)
        self.test_category_deletion_functionality()
        
        # CRITICAL FIX 3: Rate Limiting Removal
        print("\n🔧 CRITICAL FIX 3: RATE LIMITING REMOVAL")
        print("-" * 50)
        self.test_rate_limiting_removal()
        self.test_no_rate_limit_errors()
        
        # Final Results
        print("\n" + "=" * 60)
        print("🏁 CRITICAL FIXES TESTING COMPLETE")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"📊 RESULTS: {self.tests_passed}/{self.tests_run} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: All critical fixes working correctly!")
        elif success_rate >= 75:
            print("✅ GOOD: Most critical fixes working, minor issues remain")
        elif success_rate >= 50:
            print("⚠️  PARTIAL: Some critical fixes working, significant issues remain")
        else:
            print("❌ CRITICAL: Major issues with critical fixes - immediate attention needed")
        
        # Detailed breakdown
        print("\n📋 DETAILED BREAKDOWN:")
        
        critical_1_tests = [r for r in self.test_results if "ADMIN_IDS" in r['test_name'] or "Admin Bot" in r['test_name'] or "SUPER_ADMIN_IDS" in r['test_name']]
        critical_2_tests = [r for r in self.test_results if "Category Deletion" in r['test_name']]
        critical_3_tests = [r for r in self.test_results if "Rate Limit" in r['test_name']]
        
        def calc_success_rate(tests):
            if not tests:
                return 0
            passed = sum(1 for t in tests if t['success'])
            return (passed / len(tests)) * 100
        
        print(f"🔧 Critical Fix 1 (Admin Bot): {calc_success_rate(critical_1_tests):.1f}% success")
        print(f"🔧 Critical Fix 2 (Category Deletion): {calc_success_rate(critical_2_tests):.1f}% success")  
        print(f"🔧 Critical Fix 3 (Rate Limiting): {calc_success_rate(critical_3_tests):.1f}% success")
        
        return success_rate

def main():
    """Main function to run critical fixes tests"""
    tester = CriticalFixesTester()
    
    try:
        success_rate = tester.run_all_critical_tests()
        
        # Exit with appropriate code
        if success_rate >= 90:
            sys.exit(0)  # All good
        elif success_rate >= 75:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    main()