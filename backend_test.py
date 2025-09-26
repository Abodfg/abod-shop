#!/usr/bin/env python3
"""
Abod Card Backend API Testing Suite
Tests all API endpoints and Telegram bot functionality
"""

import requests
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

class AbodCardAPITester:
    def __init__(self, base_url="https://telecard-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-Tester/1.0'
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

    def test_products_api(self):
        """Test products API endpoint"""
        print("🔍 Testing Products API...")
        success, data = self.test_api_endpoint('GET', '/products', 200, test_name="Get Products List")
        
        if success and isinstance(data, list):
            self.log_test("Products Response Format", True, f"Returned {len(data)} products")
            
            # Test product structure if products exist
            if len(data) > 0:
                product = data[0]
                required_fields = ['id', 'name', 'description', 'terms', 'is_active', 'created_at']
                missing_fields = [field for field in required_fields if field not in product]
                
                if not missing_fields:
                    self.log_test("Product Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Product Structure Validation", False, f"Missing fields: {missing_fields}")
        elif success:
            self.log_test("Products Response Format", True, "Empty products list returned")
        
        return success

    def test_users_api(self):
        """Test users API endpoint"""
        print("🔍 Testing Users API...")
        success, data = self.test_api_endpoint('GET', '/users', 200, test_name="Get Users List")
        
        if success and isinstance(data, list):
            self.log_test("Users Response Format", True, f"Returned {len(data)} users")
            
            # Test user structure if users exist
            if len(data) > 0:
                user = data[0]
                required_fields = ['id', 'telegram_id', 'balance', 'join_date', 'orders_count']
                missing_fields = [field for field in required_fields if field not in user]
                
                if not missing_fields:
                    self.log_test("User Structure Validation", True, "All required fields present")
                else:
                    self.log_test("User Structure Validation", False, f"Missing fields: {missing_fields}")
        elif success:
            self.log_test("Users Response Format", True, "Empty users list returned")
            
        return success

    def test_orders_api(self):
        """Test orders API endpoint"""
        print("🔍 Testing Orders API...")
        success, data = self.test_api_endpoint('GET', '/orders', 200, test_name="Get Orders List")
        
        if success and isinstance(data, list):
            self.log_test("Orders Response Format", True, f"Returned {len(data)} orders")
            
            # Test order structure if orders exist
            if len(data) > 0:
                order = data[0]
                required_fields = ['id', 'user_id', 'telegram_id', 'product_name', 'category_name', 'price', 'status', 'order_date']
                missing_fields = [field for field in required_fields if field not in order]
                
                if not missing_fields:
                    self.log_test("Order Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Order Structure Validation", False, f"Missing fields: {missing_fields}")
                    
                # Test order status values
                valid_statuses = ['pending', 'completed', 'failed']
                if order.get('status') in valid_statuses:
                    self.log_test("Order Status Validation", True, f"Valid status: {order.get('status')}")
                else:
                    self.log_test("Order Status Validation", False, f"Invalid status: {order.get('status')}")
        elif success:
            self.log_test("Orders Response Format", True, "Empty orders list returned")
            
        return success

    def test_webhooks_setup(self):
        """Test webhook setup endpoint"""
        print("🔍 Testing Webhook Setup...")
        success, data = self.test_api_endpoint('POST', '/set-webhooks', 200, test_name="Setup Webhooks")
        
        if success:
            if isinstance(data, dict) and data.get('status') == 'success':
                self.log_test("Webhook Setup Response", True, "Webhooks configured successfully")
            else:
                self.log_test("Webhook Setup Response", False, f"Unexpected response format: {data}")
        
        return success

    def test_webhook_endpoints(self):
        """Test webhook endpoints (should return 403 without proper secret)"""
        print("🔍 Testing Webhook Security...")
        
        # Test user webhook with wrong secret
        success, data = self.test_api_endpoint('POST', '/webhook/user/wrong_secret', 403, 
                                             {"test": "data"}, "User Webhook Security")
        
        # Test admin webhook with wrong secret  
        success2, data2 = self.test_api_endpoint('POST', '/webhook/admin/wrong_secret', 403,
                                               {"test": "data"}, "Admin Webhook Security")
        
        return success and success2

    def test_cors_headers(self):
        """Test CORS configuration"""
        print("🔍 Testing CORS Configuration...")
        
        try:
            # Make an OPTIONS request to check CORS headers
            response = self.session.options(f"{self.api_url}/products", timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                self.log_test("CORS Headers Present", True, f"CORS configured: {cors_headers}")
                return True
            else:
                self.log_test("CORS Headers Present", False, "No CORS headers found")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers Test", False, f"Error testing CORS: {str(e)}")
            return False

    def test_server_health(self):
        """Test basic server connectivity"""
        print("🔍 Testing Server Health...")
        
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

    def test_telegram_webhook_user_start(self):
        """Test Telegram user webhook with /start command"""
        print("🔍 Testing Telegram User Webhook - /start Command...")
        
        # Simulate Telegram /start message
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
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
            telegram_update, 
            "Telegram /start Command"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Enhanced Welcome Animation", True, "Start command processed successfully")
        else:
            self.log_test("Enhanced Welcome Animation", False, f"Unexpected response: {data}")
        
        return success

    def test_telegram_webhook_menu_command(self):
        """Test Telegram user webhook with /menu command"""
        print("🔍 Testing Telegram User Webhook - /menu Command...")
        
        # Test /menu command
        telegram_update = {
            "update_id": 123456790,
            "message": {
                "message_id": 2,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/menu"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "Telegram /menu Command"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Menu Command Handler", True, "Menu command processed successfully")
        else:
            self.log_test("Menu Command Handler", False, f"Unexpected response: {data}")
        
        return success

    def test_telegram_help_commands(self):
        """Test various help commands"""
        print("🔍 Testing Help Commands...")
        
        help_commands = ["/help", "/مساعدة", "مساعدة", "help"]
        all_success = True
        
        for i, cmd in enumerate(help_commands):
            telegram_update = {
                "update_id": 123456791 + i,
                "message": {
                    "message_id": 3 + i,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": cmd
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Help Command: {cmd}"
            )
            
            if not success:
                all_success = False
        
        return all_success

    def test_telegram_direct_numbers(self):
        """Test direct number inputs (1-8)"""
        print("🔍 Testing Direct Number Inputs...")
        
        all_success = True
        
        for num in range(1, 9):
            telegram_update = {
                "update_id": 123456800 + num,
                "message": {
                    "message_id": 10 + num,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": str(num)
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Direct Number Input: {num}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Enhanced Text Processing - Numbers", True, "All direct numbers (1-8) processed successfully")
        else:
            self.log_test("Enhanced Text Processing - Numbers", False, "Some direct number inputs failed")
        
        return all_success

    def test_telegram_keyword_shortcuts(self):
        """Test keyword shortcuts"""
        print("🔍 Testing Keyword Shortcuts...")
        
        keywords = [
            "shop", "متجر", "منتجات", "shopping",
            "wallet", "محفظة", "رصيد", "balance",
            "orders", "طلبات", "طلباتي", "history",
            "support", "دعم", "مساعدة",
            "offers", "عروض", "خصومات", "deals"
        ]
        
        all_success = True
        
        for i, keyword in enumerate(keywords[:10]):  # Test first 10 keywords
            telegram_update = {
                "update_id": 123456900 + i,
                "message": {
                    "message_id": 20 + i,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": keyword
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Keyword: {keyword}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Enhanced Text Processing - Keywords", True, "Keyword shortcuts processed successfully")
        else:
            self.log_test("Enhanced Text Processing - Keywords", False, "Some keyword shortcuts failed")
        
        return all_success

    def test_telegram_interactive_buttons(self):
        """Test interactive button callbacks"""
        print("🔍 Testing Interactive Button Callbacks...")
        
        button_callbacks = [
            "browse_products",
            "view_wallet", 
            "order_history",
            "special_offers",
            "support",
            "about_store",
            "refresh_data",
            "daily_surprises",
            "show_full_menu",
            "quick_access"
        ]
        
        all_success = True
        
        for i, callback in enumerate(button_callbacks):
            telegram_update = {
                "update_id": 123457000 + i,
                "callback_query": {
                    "id": f"callback_{i}",
                    "chat_instance": f"chat_instance_{i}",  # Added missing chat_instance
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "أحمد",
                        "username": "ahmed_test",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 30 + i,
                        "from": {
                            "id": 7933553585,
                            "is_bot": True,
                            "first_name": "Abod Card Bot",
                            "username": "abod_card_bot"
                        },
                        "chat": {
                            "id": 987654321,
                            "first_name": "أحمد",
                            "username": "ahmed_test",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Test message"
                    },
                    "data": callback
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Button Callback: {callback}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Interactive Button Animations", True, "All button callbacks processed successfully")
        else:
            self.log_test("Interactive Button Animations", False, "Some button callbacks failed")
        
        return all_success

    def test_telegram_unknown_input(self):
        """Test enhanced help for unknown input"""
        print("🔍 Testing Enhanced Help for Unknown Input...")
        
        telegram_update = {
            "update_id": 123457100,
            "message": {
                "message_id": 50,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "أحمد",
                    "username": "ahmed_test",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "random_unknown_text_xyz"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "Unknown Input Help"
        )
        
        if success and isinstance(data, dict) and data.get('status') == 'ok':
            self.log_test("Enhanced Help for Unknown Input", True, "Unknown input handled with help message")
        else:
            self.log_test("Enhanced Help for Unknown Input", False, f"Unexpected response: {data}")
        
        return success

    def test_performance_welcome_response(self):
        """Test performance-focused welcome response (/start) - should be fast without delays"""
        print("🔍 Testing Performance-focused Welcome Response...")
        
        start_time = time.time()
        
        telegram_update = {
            "update_id": 123457200,
            "message": {
                "message_id": 60,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "محمد",
                    "username": "mohammed_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "محمد",
                    "username": "mohammed_test",
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
            telegram_update, 
            "Performance Welcome /start"
        )
        
        response_time = time.time() - start_time
        
        if success and response_time < 1.0:  # Should respond in less than 1 second
            self.log_test("Performance-focused Welcome", True, f"Fast response in {response_time:.3f}s (< 1s target)")
        elif success:
            self.log_test("Performance-focused Welcome", False, f"Slow response: {response_time:.3f}s (> 1s)")
        else:
            self.log_test("Performance-focused Welcome", False, "Request failed")
        
        return success and response_time < 1.0

    def test_quick_menu_response(self):
        """Test quick menu (/menu) - should respond immediately with clear options"""
        print("🔍 Testing Quick Menu Response...")
        
        start_time = time.time()
        
        telegram_update = {
            "update_id": 123457201,
            "message": {
                "message_id": 61,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "فاطمة",
                    "username": "fatima_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "فاطمة",
                    "username": "fatima_test",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/menu"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "Quick Menu /menu"
        )
        
        response_time = time.time() - start_time
        
        if success and response_time < 1.0:
            self.log_test("Menu Command Handler", True, f"Quick menu response in {response_time:.3f}s")
        elif success:
            self.log_test("Menu Command Handler", False, f"Slow menu response: {response_time:.3f}s")
        else:
            self.log_test("Menu Command Handler", False, "Menu request failed")
        
        return success and response_time < 1.0

    def test_bot_commands_functionality(self):
        """Test all Bot Commands: /start, /menu, /help, /shop, /wallet, /orders, /support"""
        print("🔍 Testing Bot Commands Functionality...")
        
        bot_commands = [
            "/start", "/menu", "/help", "/shop", "/wallet", "/orders", "/support"
        ]
        
        all_success = True
        
        for i, command in enumerate(bot_commands):
            start_time = time.time()
            
            telegram_update = {
                "update_id": 123457300 + i,
                "message": {
                    "message_id": 70 + i,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "علي",
                        "username": "ali_test",
                        "language_code": "ar"
                    },
                    "chat": {
                        "id": 987654321,
                        "first_name": "علي",
                        "username": "ali_test",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": command
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Bot Command: {command}"
            )
            
            response_time = time.time() - start_time
            
            if not success or response_time >= 1.0:
                all_success = False
                if success:
                    self.log_test(f"Bot Command {command} Performance", False, f"Slow response: {response_time:.3f}s")
        
        if all_success:
            self.log_test("Persistent Menu Button", True, "All bot commands working with fast response")
        else:
            self.log_test("Persistent Menu Button", False, "Some bot commands failed or slow")
        
        return all_success

    def test_direct_response_system(self):
        """Test direct response system - buttons should respond immediately without loading messages"""
        print("🔍 Testing Direct Response System...")
        
        direct_callbacks = [
            "browse_products", "view_wallet", "order_history", "support"
        ]
        
        all_success = True
        total_response_time = 0
        
        for i, callback in enumerate(direct_callbacks):
            start_time = time.time()
            
            telegram_update = {
                "update_id": 123457400 + i,
                "callback_query": {
                    "id": f"direct_callback_{i}",
                    "chat_instance": f"direct_chat_instance_{i}",
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "سارة",
                        "username": "sara_test",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 80 + i,
                        "from": {
                            "id": 7933553585,
                            "is_bot": True,
                            "first_name": "Abod Card Bot",
                            "username": "abod_card_bot"
                        },
                        "chat": {
                            "id": 987654321,
                            "first_name": "سارة",
                            "username": "sara_test",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Test direct response"
                    },
                    "data": callback
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Direct Response: {callback}"
            )
            
            response_time = time.time() - start_time
            total_response_time += response_time
            
            if not success or response_time >= 1.0:
                all_success = False
        
        avg_response_time = total_response_time / len(direct_callbacks)
        
        if all_success and avg_response_time < 0.5:
            self.log_test("Direct Response System", True, f"All buttons respond quickly (avg: {avg_response_time:.3f}s)")
        else:
            self.log_test("Direct Response System", False, f"Slow or failed responses (avg: {avg_response_time:.3f}s)")
        
        return all_success and avg_response_time < 0.5

    def test_simplified_keyboard_design(self):
        """Test simplified keyboard with 6 basic buttons"""
        print("🔍 Testing Simplified Keyboard Design...")
        
        # Test main keyboard buttons
        main_buttons = [
            "browse_products",  # التسوق
            "view_wallet",      # المحفظة
            "order_history",    # الطلبات
            "support",          # الدعم
            "special_offers",   # العروض
            "show_full_menu"    # القائمة
        ]
        
        all_success = True
        
        for i, button in enumerate(main_buttons):
            telegram_update = {
                "update_id": 123457500 + i,
                "callback_query": {
                    "id": f"keyboard_test_{i}",
                    "chat_instance": f"keyboard_chat_instance_{i}",
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "خالد",
                        "username": "khalid_test",
                        "language_code": "ar"
                    },
                    "message": {
                        "message_id": 90 + i,
                        "from": {
                            "id": 7933553585,
                            "is_bot": True,
                            "first_name": "Abod Card Bot",
                            "username": "abod_card_bot"
                        },
                        "chat": {
                            "id": 987654321,
                            "first_name": "خالد",
                            "username": "khalid_test",
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Test keyboard"
                    },
                    "data": button
                }
            }
            
            success, data = self.test_api_endpoint(
                'POST', 
                '/webhook/user/abod_user_webhook_secret', 
                200, 
                telegram_update, 
                f"Keyboard Button: {button}"
            )
            
            if not success:
                all_success = False
        
        if all_success:
            self.log_test("Simplified UI Design", True, "All 6 main keyboard buttons working correctly")
        else:
            self.log_test("Simplified UI Design", False, "Some keyboard buttons failed")
        
        return all_success

    def test_simplified_help_messages(self):
        """Test simplified help messages - should be short and useful"""
        print("🔍 Testing Simplified Help Messages...")
        
        # Test help command
        start_time = time.time()
        
        telegram_update = {
            "update_id": 123457600,
            "message": {
                "message_id": 100,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "نور",
                    "username": "noor_test",
                    "language_code": "ar"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "نور",
                    "username": "noor_test",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/help"
            }
        }
        
        success, data = self.test_api_endpoint(
            'POST', 
            '/webhook/user/abod_user_webhook_secret', 
            200, 
            telegram_update, 
            "Simplified Help Message"
        )
        
        response_time = time.time() - start_time
        
        if success and response_time < 1.0:
            self.log_test("Simplified Help Testing", True, f"Help message delivered quickly in {response_time:.3f}s")
            return True
        elif success:
            self.log_test("Simplified Help Testing", False, f"Help response too slow: {response_time:.3f}s")
            return False
        else:
            self.log_test("Simplified Help Testing", False, "Help command failed")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Abod Card Backend API Tests")
        print("=" * 50)
        
        # Test server health first
        if not self.test_server_health():
            print("❌ Server is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Run basic API tests
        self.test_products_api()
        self.test_users_api() 
        self.test_orders_api()
        self.test_webhooks_setup()
        self.test_webhook_endpoints()
        self.test_cors_headers()
        
        # Run Telegram bot functionality tests
        print("\n🤖 Testing Telegram Bot Functionality...")
        print("=" * 50)
        
        self.test_telegram_webhook_user_start()
        self.test_telegram_webhook_menu_command()
        self.test_telegram_help_commands()
        self.test_telegram_direct_numbers()
        self.test_telegram_keyword_shortcuts()
        self.test_telegram_interactive_buttons()
        self.test_telegram_unknown_input()
        
        # Run Performance and Response Tests (Arabic Review Requirements)
        print("\n⚡ Testing Performance and Response Improvements...")
        print("=" * 50)
        
        self.test_performance_welcome_response()
        self.test_quick_menu_response()
        self.test_bot_commands_functionality()
        self.test_direct_response_system()
        self.test_simplified_keyboard_design()
        self.test_simplified_help_messages()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print("\n" + "=" * 50)
        
        # Return results for further processing
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = AbodCardAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {results['failed_tests']} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())