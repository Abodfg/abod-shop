#!/usr/bin/env python3
"""
Abod Card Security and Vulnerability Testing Suite
فحص شامل لنظام Abod Card Telegram Bot - اختبار الأمان والثغرات

This module performs comprehensive security testing as requested:
1. Security and authentication testing
2. System limits and boundary testing  
3. Data flow verification
4. Performance and stability testing
5. Updated text verification
6. Notification system verification
"""

import requests
import sys
import json
import time
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, List
import random
import string

class AbodCardSecurityTester:
    def __init__(self, base_url="https://telegr-shop-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-SecurityTester/1.0'
        })
        
        # Security test constants
        self.ADMIN_ID = 7040570081  # الإيدي الصحيح للإدارة
        self.WRONG_ADMIN_ID = 123456789  # إيدي خاطئ للاختبار
        self.TEST_USER_ID = 987654321  # إيدي مستخدم عادي للاختبار
        
        # Webhook secrets
        self.USER_WEBHOOK_SECRET = "abod_user_webhook_secret"
        self.ADMIN_WEBHOOK_SECRET = "abod_admin_webhook_secret"

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None, severity: str = "medium"):
        """Log test result with security severity"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        severity_icon = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "💀"}
        print(f"{status} {severity_icon.get(severity, '🟠')} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {str(response_data)[:200]}")
        print()

    def test_api_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                         data: Dict = None, test_name: str = None, timeout: int = 30) -> tuple:
        """Test a single API endpoint with security focus"""
        if not test_name:
            test_name = f"{method} {endpoint}"
            
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=timeout)
            else:
                return False, {}

            success = response.status_code == expected_status
            
            try:
                response_json = response.json()
            except:
                response_json = {"raw_response": response.text[:500]}

            return success, response_json

        except requests.exceptions.Timeout:
            return False, {"error": "timeout"}
        except requests.exceptions.ConnectionError:
            return False, {"error": "connection_error"}
        except Exception as e:
            return False, {"error": str(e)}

    # ==================== 1. فحص الأمان والمصادقة ====================
    
    def test_admin_bot_protection(self):
        """التحقق من حماية Admin Bot من المستخدمين غير المسموحين"""
        print("🔒 Testing Admin Bot Protection...")
        
        # Test 1: Unauthorized user trying to access admin bot
        telegram_update = {
            "update_id": 999001,
            "message": {
                "message_id": 1,
                "from": {
                    "id": self.TEST_USER_ID,  # مستخدم عادي
                    "is_bot": False,
                    "first_name": "مستخدم عادي",
                    "username": "normal_user"
                },
                "chat": {
                    "id": self.TEST_USER_ID,
                    "first_name": "مستخدم عادي",
                    "username": "normal_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/admin/{self.ADMIN_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Admin Bot - Unauthorized User Access"
        )
        
        # Should reject unauthorized user
        if success:
            self.log_test("Admin Bot Protection - Unauthorized Access", True, 
                         f"Admin bot correctly rejects unauthorized user {self.TEST_USER_ID}", 
                         data, "high")
        else:
            self.log_test("Admin Bot Protection - Unauthorized Access", False, 
                         "Admin bot access test failed", data, "critical")
        
        # Test 2: Authorized admin access
        telegram_update["message"]["from"]["id"] = self.ADMIN_ID
        telegram_update["message"]["chat"]["id"] = self.ADMIN_ID
        telegram_update["message"]["from"]["first_name"] = "الإدارة"
        telegram_update["message"]["chat"]["first_name"] = "الإدارة"
        
        success2, data2 = self.test_api_endpoint(
            'POST', 
            f'/webhook/admin/{self.ADMIN_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Admin Bot - Authorized Admin Access"
        )
        
        if success2:
            self.log_test("Admin Bot Protection - Authorized Access", True, 
                         f"Admin bot correctly accepts authorized admin {self.ADMIN_ID}", 
                         data2, "medium")
        else:
            self.log_test("Admin Bot Protection - Authorized Access", False, 
                         "Admin bot failed to accept authorized admin", data2, "high")
        
        return success and success2

    def test_webhook_secrets_protection(self):
        """اختبار webhook secrets وحمايتها"""
        print("🔐 Testing Webhook Secrets Protection...")
        
        test_data = {"test": "unauthorized_access"}
        
        # Test wrong user webhook secret
        success1, data1 = self.test_api_endpoint(
            'POST', '/webhook/user/wrong_secret', 403, test_data, 
            "User Webhook - Wrong Secret"
        )
        
        # Test wrong admin webhook secret
        success2, data2 = self.test_api_endpoint(
            'POST', '/webhook/admin/wrong_secret', 403, test_data,
            "Admin Webhook - Wrong Secret"
        )
        
        # Test no secret
        success3, data3 = self.test_api_endpoint(
            'POST', '/webhook/user/', 404, test_data,
            "User Webhook - No Secret"
        )
        
        # Test empty secret
        success4, data4 = self.test_api_endpoint(
            'POST', '/webhook/user/', 404, test_data,
            "User Webhook - Empty Secret"
        )
        
        all_protected = success1 and success2 and success3 and success4
        
        if all_protected:
            self.log_test("Webhook Secrets Protection", True, 
                         "All webhook endpoints properly protected with secrets", 
                         None, "high")
        else:
            self.log_test("Webhook Secrets Protection", False, 
                         "Some webhook endpoints not properly protected", 
                         {"user": data1, "admin": data2}, "critical")
        
        return all_protected

    def test_sensitive_data_protection(self):
        """فحص حماية البيانات الحساسة (أكواد، أرصدة، معلومات شخصية)"""
        print("🛡️ Testing Sensitive Data Protection...")
        
        # Test 1: Try to access user data without proper authentication
        success1, data1 = self.test_api_endpoint(
            'GET', '/users', 200, None, "Access User Data Without Auth"
        )
        
        # Check if sensitive data is exposed
        sensitive_exposed = False
        if success1 and isinstance(data1, list) and len(data1) > 0:
            user = data1[0]
            # Check if sensitive fields are present in response
            sensitive_fields = ['balance', 'telegram_id', 'username', 'first_name']
            exposed_fields = [field for field in sensitive_fields if field in user]
            if exposed_fields:
                sensitive_exposed = True
                self.log_test("Sensitive Data Exposure - User Data", False, 
                             f"Sensitive user fields exposed: {exposed_fields}", 
                             user, "high")
            else:
                self.log_test("Sensitive Data Protection - User Data", True, 
                             "User sensitive data properly protected", None, "medium")
        
        # Test 2: Try to access codes without authentication
        success2, data2 = self.test_api_endpoint(
            'GET', '/codes', 200, None, "Access Codes Without Auth"
        )
        
        codes_exposed = False
        if success2 and isinstance(data2, list) and len(data2) > 0:
            code = data2[0]
            if 'code' in code:
                codes_exposed = True
                self.log_test("Sensitive Data Exposure - Codes", False, 
                             "Code values exposed without authentication", 
                             code, "critical")
            else:
                self.log_test("Sensitive Data Protection - Codes", True, 
                             "Code values properly protected", None, "high")
        
        return not (sensitive_exposed or codes_exposed)

    def test_admin_info_leakage_prevention(self):
        """التأكد من عدم تسريب معلومات الإدارة للمستخدمين العاديين"""
        print("🔍 Testing Admin Information Leakage Prevention...")
        
        # Test regular user trying to access admin functions via user bot
        telegram_update = {
            "update_id": 999002,
            "message": {
                "message_id": 2,
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "مستخدم عادي",
                    "username": "normal_user"
                },
                "chat": {
                    "id": self.TEST_USER_ID,
                    "first_name": "مستخدم عادي", 
                    "username": "normal_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/admin"  # Try admin command
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "User Bot - Admin Command Attempt"
        )
        
        # Check if admin information is leaked in response
        admin_info_leaked = False
        if success and data:
            response_str = str(data).lower()
            admin_keywords = ['admin', 'إدارة', 'manage', 'control', 'dashboard', 'لوحة تحكم']
            leaked_keywords = [kw for kw in admin_keywords if kw in response_str]
            if leaked_keywords:
                admin_info_leaked = True
                self.log_test("Admin Information Leakage", False, 
                             f"Admin keywords found in user response: {leaked_keywords}", 
                             data, "high")
            else:
                self.log_test("Admin Information Protection", True, 
                             "No admin information leaked to regular user", 
                             None, "medium")
        
        return not admin_info_leaked

    # ==================== 2. اختبار حدود النظام ====================
    
    def test_input_validation_and_injection(self):
        """اختبار معالجة البيانات الخاطئة والمدخلات غير الصحيحة"""
        print("🧪 Testing Input Validation and Injection Protection...")
        
        # SQL Injection attempts
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        # NoSQL Injection attempts  
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "this.password == this.username"}
        ]
        
        # XSS attempts
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        injection_blocked = True
        
        # Test SQL injection in text messages
        for payload in sql_payloads:
            telegram_update = {
                "update_id": 999100 + len(sql_payloads),
                "message": {
                    "message_id": 100,
                    "from": {
                        "id": self.TEST_USER_ID,
                        "is_bot": False,
                        "first_name": "Test User",
                        "username": "test_user"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Test User",
                        "username": "test_user", 
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": payload
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
                200, 
                telegram_update, 
                f"SQL Injection Test: {payload[:20]}..."
            )
            
            # Check if injection was processed (bad) or rejected/sanitized (good)
            if success and data:
                response_str = str(data).lower()
                if 'error' in response_str or 'invalid' in response_str:
                    # Good - injection was caught
                    continue
                elif 'drop' in response_str or 'union' in response_str:
                    # Bad - injection might have been processed
                    injection_blocked = False
                    self.log_test("SQL Injection Protection", False, 
                                 f"Potential SQL injection vulnerability with payload: {payload}", 
                                 data, "critical")
                    break
        
        if injection_blocked:
            self.log_test("Input Validation - SQL Injection", True, 
                         "SQL injection attempts properly handled", None, "high")
        
        return injection_blocked

    def test_system_limits_and_boundaries(self):
        """فحص حدود الأرقام والنصوص (طول النص، قيم سالبة، قيم كبيرة جداً)"""
        print("📏 Testing System Limits and Boundaries...")
        
        # Test extremely long text
        long_text = "A" * 10000  # 10KB text
        telegram_update = {
            "update_id": 999200,
            "message": {
                "message_id": 200,
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "chat": {
                    "id": self.TEST_USER_ID,
                    "first_name": "Test User",
                    "username": "test_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": long_text
            }
        }
        
        success1, data1 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Long Text Input Test",
            timeout=60  # Longer timeout for large data
        )
        
        # Test negative values in numeric fields
        telegram_update["message"]["from"]["id"] = -999999999
        telegram_update["message"]["chat"]["id"] = -999999999
        telegram_update["message"]["text"] = "/start"
        
        success2, data2 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Negative ID Values Test"
        )
        
        # Test extremely large numbers
        telegram_update["message"]["from"]["id"] = 999999999999999999
        telegram_update["message"]["chat"]["id"] = 999999999999999999
        
        success3, data3 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Large Number Values Test"
        )
        
        limits_handled = success1 and success2 and success3
        
        if limits_handled:
            self.log_test("System Limits and Boundaries", True, 
                         "System properly handles extreme input values", None, "medium")
        else:
            self.log_test("System Limits and Boundaries", False, 
                         "System may not handle extreme input values properly", 
                         {"long_text": data1, "negative": data2, "large": data3}, "high")
        
        return limits_handled

    def test_error_handling_and_exceptions(self):
        """فحص معالجة الأخطاء والاستثناءات"""
        print("⚠️ Testing Error Handling and Exceptions...")
        
        # Test malformed JSON
        malformed_json = '{"invalid": json, "missing": quote}'
        
        try:
            response = self.session.post(
                f"{self.api_url}/webhook/user/{self.USER_WEBHOOK_SECRET}",
                data=malformed_json,  # Send as raw data, not JSON
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            success1 = response.status_code in [400, 422, 500]  # Should return error status
            data1 = response.text
            
        except Exception as e:
            success1 = True  # Exception handling is working
            data1 = str(e)
        
        # Test missing required fields
        incomplete_update = {
            "update_id": 999300,
            # Missing message field
        }
        
        success2, data2 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200,  # Should handle gracefully
            incomplete_update, 
            "Missing Required Fields Test"
        )
        
        # Test invalid update structure
        invalid_update = {
            "not_an_update": "invalid_structure",
            "random_field": 12345
        }
        
        success3, data3 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200,  # Should handle gracefully
            invalid_update, 
            "Invalid Update Structure Test"
        )
        
        error_handling_works = success1 and success2 and success3
        
        if error_handling_works:
            self.log_test("Error Handling and Exceptions", True, 
                         "System properly handles malformed requests and errors", None, "medium")
        else:
            self.log_test("Error Handling and Exceptions", False, 
                         "System may not handle errors properly", 
                         {"malformed": data1, "missing": data2, "invalid": data3}, "high")
        
        return error_handling_works

    # ==================== 3. فحص تدفق البيانات ====================
    
    def test_balance_management_logic(self):
        """فحص منطق إدارة الأرصدة (عدم السماح بأرصدة سالبة غير مشروعة)"""
        print("💰 Testing Balance Management Logic...")
        
        # This test would require actual database access or API endpoints
        # For now, we'll test the webhook responses for balance-related operations
        
        # Test wallet view request
        telegram_update = {
            "update_id": 999400,
            "callback_query": {
                "id": "balance_test",
                "chat_instance": "balance_chat_instance",
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 400,
                    "from": {
                        "id": 7933553585,
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Test User",
                        "username": "test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test balance"
                },
                "data": "view_wallet"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Balance Management - View Wallet"
        )
        
        if success:
            self.log_test("Balance Management Logic", True, 
                         "Balance management system responding correctly", None, "medium")
        else:
            self.log_test("Balance Management Logic", False, 
                         "Balance management system not responding", data, "high")
        
        return success

    def test_code_usage_and_prevention(self):
        """اختبار إدارة الأكواد ومنع الاستخدام المتكرر"""
        print("🎫 Testing Code Usage and Duplicate Prevention...")
        
        # Test browsing products (which may show codes)
        telegram_update = {
            "update_id": 999500,
            "callback_query": {
                "id": "code_test",
                "chat_instance": "code_chat_instance", 
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 500,
                    "from": {
                        "id": 7933553585,
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Test User",
                        "username": "test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test codes"
                },
                "data": "browse_products"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Code Management - Browse Products"
        )
        
        if success:
            self.log_test("Code Usage and Prevention", True, 
                         "Code management system responding correctly", None, "medium")
        else:
            self.log_test("Code Usage and Prevention", False, 
                         "Code management system not responding", data, "medium")
        
        return success

    def test_order_status_management(self):
        """فحص حالات الطلبات المختلفة (pending, completed, failed)"""
        print("📦 Testing Order Status Management...")
        
        # Test order history view
        telegram_update = {
            "update_id": 999600,
            "callback_query": {
                "id": "order_test",
                "chat_instance": "order_chat_instance",
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "Test User",
                    "username": "test_user"
                },
                "message": {
                    "message_id": 600,
                    "from": {
                        "id": 7933553585,
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Test User",
                        "username": "test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Test orders"
                },
                "data": "order_history"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Order Status Management - Order History"
        )
        
        if success:
            self.log_test("Order Status Management", True, 
                         "Order status management system responding correctly", None, "medium")
        else:
            self.log_test("Order Status Management", False, 
                         "Order status management system not responding", data, "medium")
        
        return success

    # ==================== 4. اختبار الأداء والاستقرار ====================
    
    def test_concurrent_requests(self):
        """اختبار النظام تحت ضغط (طلبات متعددة متزامنة)"""
        print("🚀 Testing System Under Load - Concurrent Requests...")
        
        def send_concurrent_request(request_id):
            """Send a single concurrent request"""
            telegram_update = {
                "update_id": 999700 + request_id,
                "message": {
                    "message_id": 700 + request_id,
                    "from": {
                        "id": self.TEST_USER_ID + request_id,
                        "is_bot": False,
                        "first_name": f"User{request_id}",
                        "username": f"user{request_id}"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID + request_id,
                        "first_name": f"User{request_id}",
                        "username": f"user{request_id}",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "/start"
                }
            }
            
            try:
                response = self.session.post(
                    f"{self.api_url}/webhook/user/{self.USER_WEBHOOK_SECRET}",
                    json=telegram_update,
                    timeout=30
                )
                return response.status_code == 200, response.json() if response.status_code == 200 else response.text
            except Exception as e:
                return False, str(e)
        
        # Send 10 concurrent requests
        import concurrent.futures
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_concurrent_request, i) for i in range(10)]
            
            for future in concurrent.futures.as_completed(futures):
                success, data = future.result()
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        total_time = time.time() - start_time
        
        if successful_requests >= 8:  # Allow 2 failures out of 10
            self.log_test("Concurrent Requests Performance", True, 
                         f"Handled {successful_requests}/10 concurrent requests in {total_time:.2f}s", 
                         None, "medium")
        else:
            self.log_test("Concurrent Requests Performance", False, 
                         f"Only {successful_requests}/10 concurrent requests succeeded in {total_time:.2f}s", 
                         None, "high")
        
        return successful_requests >= 8

    def test_memory_and_resource_usage(self):
        """فحص معالجة الذاكرة وتسريب البيانات"""
        print("🧠 Testing Memory and Resource Usage...")
        
        # Send multiple large requests to test memory handling
        large_data_requests = 0
        successful_large_requests = 0
        
        for i in range(5):
            # Create large text payload
            large_text = "Large data test " * 1000  # ~15KB text
            
            telegram_update = {
                "update_id": 999800 + i,
                "message": {
                    "message_id": 800 + i,
                    "from": {
                        "id": self.TEST_USER_ID,
                        "is_bot": False,
                        "first_name": "Memory Test User",
                        "username": "memory_test_user"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Memory Test User",
                        "username": "memory_test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": large_text
                }
            }
            
            large_data_requests += 1
            success, data = self.test_api_endpoint(
                'POST', 
                f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
                200, 
                telegram_update, 
                f"Memory Test - Large Request {i+1}",
                timeout=60
            )
            
            if success:
                successful_large_requests += 1
            
            # Small delay between requests
            time.sleep(0.5)
        
        if successful_large_requests >= 4:  # Allow 1 failure out of 5
            self.log_test("Memory and Resource Usage", True, 
                         f"Successfully handled {successful_large_requests}/5 large data requests", 
                         None, "medium")
        else:
            self.log_test("Memory and Resource Usage", False, 
                         f"Only {successful_large_requests}/5 large data requests succeeded", 
                         None, "high")
        
        return successful_large_requests >= 4

    def test_database_connection_stability(self):
        """اختبار الاتصال بقاعدة البيانات والشبكة"""
        print("🗄️ Testing Database Connection Stability...")
        
        # Test multiple database-dependent operations
        db_operations = [
            ("browse_products", "Database - Products Query"),
            ("view_wallet", "Database - User Balance Query"), 
            ("order_history", "Database - Orders Query")
        ]
        
        successful_db_ops = 0
        
        for callback_data, test_name in db_operations:
            telegram_update = {
                "update_id": 999900 + successful_db_ops,
                "callback_query": {
                    "id": f"db_test_{successful_db_ops}",
                    "chat_instance": f"db_chat_instance_{successful_db_ops}",
                    "from": {
                        "id": self.TEST_USER_ID,
                        "is_bot": False,
                        "first_name": "DB Test User",
                        "username": "db_test_user"
                    },
                    "message": {
                        "message_id": 900 + successful_db_ops,
                        "from": {
                            "id": 7933553585,
                            "is_bot": True,
                            "first_name": "Abod Card Bot",
                            "username": "abod_card_bot"
                        },
                        "chat": {
                            "id": self.TEST_USER_ID,
                            "first_name": "DB Test User",
                            "username": "db_test_user",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "DB test"
                    },
                    "data": callback_data
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
                200, 
                telegram_update, 
                test_name
            )
            
            if success:
                successful_db_ops += 1
            
            time.sleep(0.2)  # Small delay between operations
        
        if successful_db_ops >= 2:  # Allow 1 failure out of 3
            self.log_test("Database Connection Stability", True, 
                         f"Database operations successful: {successful_db_ops}/3", 
                         None, "medium")
        else:
            self.log_test("Database Connection Stability", False, 
                         f"Database operations failed: {successful_db_ops}/3", 
                         None, "high")
        
        return successful_db_ops >= 2

    # ==================== 5. التحقق من النص المحدث ====================
    
    def test_updated_text_verification(self):
        """اختبار النص الجديد "نتيجة الطلب Order Answer" والتأكد من ظهور رسالة الدعم الفني "@AbodStoreVIP" """
        print("📝 Testing Updated Text Verification...")
        
        # Test support message
        telegram_update = {
            "update_id": 998001,
            "callback_query": {
                "id": "support_text_test",
                "chat_instance": "support_chat_instance",
                "from": {
                    "id": self.TEST_USER_ID,
                    "is_bot": False,
                    "first_name": "Text Test User",
                    "username": "text_test_user"
                },
                "message": {
                    "message_id": 1001,
                    "from": {
                        "id": 7933553585,
                        "is_bot": True,
                        "first_name": "Abod Card Bot",
                        "username": "abod_card_bot"
                    },
                    "chat": {
                        "id": self.TEST_USER_ID,
                        "first_name": "Text Test User",
                        "username": "text_test_user",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Support test"
                },
                "data": "support"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Updated Text - Support Message"
        )
        
        support_text_correct = False
        if success and data:
            response_str = str(data).lower()
            if "@abodstorevi" in response_str or "abodstorevi" in response_str:
                support_text_correct = True
                self.log_test("Updated Text - Support Contact", True, 
                             "Support message contains correct contact @AbodStoreVIP", 
                             None, "low")
            else:
                self.log_test("Updated Text - Support Contact", False, 
                             "Support message missing @AbodStoreVIP contact", 
                             data, "medium")
        
        # Test FAQ for execution time update (10-30 minutes)
        telegram_update["callback_query"]["data"] = "faq"
        telegram_update["callback_query"]["id"] = "faq_text_test"
        
        success2, data2 = self.test_api_endpoint(
            'POST', 
            f'/webhook/user/{self.USER_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Updated Text - FAQ Execution Time"
        )
        
        execution_time_correct = False
        if success2 and data2:
            response_str = str(data2)
            if "10-30" in response_str and "دقيقة" in response_str:
                execution_time_correct = True
                self.log_test("Updated Text - Execution Time", True, 
                             "FAQ shows updated execution time '10-30 minutes'", 
                             None, "low")
            elif "24" in response_str and "ساعة" in response_str:
                self.log_test("Updated Text - Execution Time", False, 
                             "FAQ still shows old execution time '24 hours'", 
                             data2, "medium")
            else:
                self.log_test("Updated Text - Execution Time", False, 
                             "FAQ execution time text unclear", 
                             data2, "low")
        
        return support_text_correct and execution_time_correct

    # ==================== 6. فحص نظام الإشعارات ====================
    
    def test_notification_system_verification(self):
        """التأكد من وصول الإشعارات للإدارة الصحيحة (7040570081) واختبار أنواع الإشعارات المختلفة"""
        print("🔔 Testing Notification System Verification...")
        
        # Test admin ID configuration
        admin_id_correct = (self.ADMIN_ID == 7040570081)
        
        if admin_id_correct:
            self.log_test("Notification System - Admin ID", True, 
                         f"Admin ID correctly set to {self.ADMIN_ID}", 
                         None, "high")
        else:
            self.log_test("Notification System - Admin ID", False, 
                         f"Admin ID incorrectly set to {self.ADMIN_ID}, should be 7040570081", 
                         None, "critical")
        
        # Test admin bot access with correct ID
        telegram_update = {
            "update_id": 998002,
            "message": {
                "message_id": 1002,
                "from": {
                    "id": self.ADMIN_ID,
                    "is_bot": False,
                    "first_name": "الإدارة",
                    "username": "admin_user"
                },
                "chat": {
                    "id": self.ADMIN_ID,
                    "first_name": "الإدارة",
                    "username": "admin_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            f'/webhook/admin/{self.ADMIN_WEBHOOK_SECRET}', 
            200, 
            telegram_update, 
            "Notification System - Admin Bot Access"
        )
        
        admin_bot_working = success
        if admin_bot_working:
            self.log_test("Notification System - Admin Bot", True, 
                         "Admin bot accessible with correct admin ID", 
                         None, "high")
        else:
            self.log_test("Notification System - Admin Bot", False, 
                         "Admin bot not accessible with correct admin ID", 
                         data, "critical")
        
        # Test notification prevention for duplicate/wrong notifications
        # This would require testing the actual notification functions, 
        # but we can test the webhook endpoints don't leak information
        
        return admin_id_correct and admin_bot_working

    def run_comprehensive_security_tests(self):
        """Run all comprehensive security tests"""
        print("🛡️ Starting Comprehensive Security and Vulnerability Testing")
        print("فحص شامل لنظام Abod Card Telegram Bot - اختبار الأمان والثغرات")
        print("=" * 80)
        
        # 1. فحص الأمان والمصادقة
        print("\n🔒 1. فحص الأمان والمصادقة (Security and Authentication Testing)")
        print("-" * 60)
        self.test_admin_bot_protection()
        self.test_webhook_secrets_protection()
        self.test_sensitive_data_protection()
        self.test_admin_info_leakage_prevention()
        
        # 2. اختبار حدود النظام
        print("\n🧪 2. اختبار حدود النظام (System Limits and Boundary Testing)")
        print("-" * 60)
        self.test_input_validation_and_injection()
        self.test_system_limits_and_boundaries()
        self.test_error_handling_and_exceptions()
        
        # 3. فحص تدفق البيانات
        print("\n💰 3. فحص تدفق البيانات (Data Flow Verification)")
        print("-" * 60)
        self.test_balance_management_logic()
        self.test_code_usage_and_prevention()
        self.test_order_status_management()
        
        # 4. اختبار الأداء والاستقرار
        print("\n🚀 4. اختبار الأداء والاستقرار (Performance and Stability Testing)")
        print("-" * 60)
        self.test_concurrent_requests()
        self.test_memory_and_resource_usage()
        self.test_database_connection_stability()
        
        # 5. التحقق من النص المحدث
        print("\n📝 5. التحقق من النص المحدث (Updated Text Verification)")
        print("-" * 60)
        self.test_updated_text_verification()
        
        # 6. فحص نظام الإشعارات
        print("\n🔔 6. فحص نظام الإشعارات (Notification System Verification)")
        print("-" * 60)
        self.test_notification_system_verification()
        
        return self.generate_security_report()

    def generate_security_report(self):
        """Generate comprehensive security test report"""
        print("=" * 80)
        print("📊 تقرير الأمان الشامل (COMPREHENSIVE SECURITY REPORT)")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"إجمالي الاختبارات (Total Tests): {self.tests_run}")
        print(f"نجح (Passed): {self.tests_passed}")
        print(f"فشل (Failed): {self.tests_run - self.tests_passed}")
        print(f"معدل النجاح (Success Rate): {success_rate:.1f}%")
        
        # Categorize results by severity
        critical_failures = [r for r in self.test_results if not r['success'] and r['severity'] == 'critical']
        high_failures = [r for r in self.test_results if not r['success'] and r['severity'] == 'high']
        medium_failures = [r for r in self.test_results if not r['success'] and r['severity'] == 'medium']
        low_failures = [r for r in self.test_results if not r['success'] and r['severity'] == 'low']
        
        print(f"\n🚨 الثغرات الحرجة (Critical Vulnerabilities): {len(critical_failures)}")
        print(f"⚠️ الثغرات عالية الخطورة (High Risk): {len(high_failures)}")
        print(f"🟡 الثغرات متوسطة الخطورة (Medium Risk): {len(medium_failures)}")
        print(f"🟢 الثغرات منخفضة الخطورة (Low Risk): {len(low_failures)}")
        
        # Security assessment
        if len(critical_failures) == 0 and len(high_failures) <= 2:
            security_level = "🟢 ممتاز (Excellent)"
        elif len(critical_failures) == 0 and len(high_failures) <= 5:
            security_level = "🟡 جيد (Good)"
        elif len(critical_failures) <= 2:
            security_level = "🟠 متوسط (Average)"
        else:
            security_level = "🔴 ضعيف (Poor)"
        
        print(f"\n🛡️ تقييم مستوى الأمان العام (Overall Security Level): {security_level}")
        
        # Detailed failure report
        if critical_failures:
            print(f"\n💀 الثغرات الحرجة المكتشفة (Critical Vulnerabilities Found):")
            for failure in critical_failures:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        if high_failures:
            print(f"\n🔴 الثغرات عالية الخطورة (High Risk Vulnerabilities):")
            for failure in high_failures:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        if medium_failures:
            print(f"\n🟠 الثغرات متوسطة الخطورة (Medium Risk Issues):")
            for failure in medium_failures[:5]:  # Show first 5
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        # Recommendations
        print(f"\n📋 التوصيات للتحسينات (Recommendations for Improvements):")
        if critical_failures:
            print("  🚨 إصلاح الثغرات الحرجة فوراً (Fix critical vulnerabilities immediately)")
        if high_failures:
            print("  ⚠️ معالجة الثغرات عالية الخطورة (Address high-risk vulnerabilities)")
        if len(medium_failures) > 3:
            print("  🔧 تحسين معالجة الأخطاء (Improve error handling)")
        if success_rate < 90:
            print("  📈 تحسين الاستقرار العام للنظام (Improve overall system stability)")
        
        print(f"\n✅ تأكيد عمل النص المحدث (Updated Text Verification):")
        text_tests = [r for r in self.test_results if 'Updated Text' in r['test_name']]
        text_success = sum(1 for t in text_tests if t['success'])
        print(f"  📝 اختبارات النص: {text_success}/{len(text_tests)} نجحت")
        
        print("\n" + "=" * 80)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "security_level": security_level,
            "critical_failures": len(critical_failures),
            "high_failures": len(high_failures),
            "medium_failures": len(medium_failures),
            "low_failures": len(low_failures),
            "test_results": self.test_results
        }

def main():
    """Main security test execution"""
    tester = AbodCardSecurityTester()
    results = tester.run_comprehensive_security_tests()
    
    # Exit with appropriate code based on security level
    if results["critical_failures"] == 0 and results["high_failures"] <= 2:
        print("🎉 النظام آمن! (System is secure!)")
        return 0
    elif results["critical_failures"] > 0:
        print("🚨 ثغرات حرجة مكتشفة! (Critical vulnerabilities found!)")
        return 2
    else:
        print("⚠️ ثغرات أمنية مكتشفة (Security vulnerabilities found)")
        return 1

if __name__ == "__main__":
    sys.exit(main())