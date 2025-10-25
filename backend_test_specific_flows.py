#!/usr/bin/env python3
"""
Specific Flow Testing for Abod Card Telegram Bot System
Tests specific user scenarios mentioned in the review request:
1. Complete admin code addition flow with different code types
2. Complete user product browsing and purchase flow
3. Session management during multi-step processes
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SpecificFlowTester:
    def __init__(self, base_url="https://digital-shop-bot-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AbodCard-SpecificFlowTester/1.0'
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

    def simulate_admin_code_addition_flow(self):
        """Simulate the complete admin code addition flow"""
        print("🔧 Testing Admin Code Addition Flow...")
        
        admin_id = 123456789
        
        # Step 1: Admin starts with /start
        try:
            start_update = {
                "update_id": 200001,
                "message": {
                    "message_id": 1,
                    "date": int(datetime.now().timestamp()),
                    "chat": {"id": admin_id, "type": "private"},
                    "from": {"id": admin_id, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                    "text": "/start"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=start_update)
            success = response.status_code == 200
            self.log_test(
                "Admin Flow - Start Command",
                success,
                f"Admin bot responded to /start with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Admin Flow - Start Command", False, f"Error: {str(e)}")

        # Step 2: Admin clicks "إدارة الأكواد" (manage_codes)
        try:
            manage_codes_callback = {
                "update_id": 200002,
                "callback_query": {
                    "id": "callback_200002",
                    "from": {"id": admin_id, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                    "message": {
                        "message_id": 2,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": admin_id, "type": "private"},
                        "from": {"id": 7835622090, "is_bot": True, "first_name": "AbodCard Admin Bot"}
                    },
                    "chat_instance": "admin_chat_instance_200002",
                    "data": "manage_codes"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=manage_codes_callback)
            success = response.status_code == 200
            self.log_test(
                "Admin Flow - Manage Codes Selection",
                success,
                f"Manage codes callback handled with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Admin Flow - Manage Codes Selection", False, f"Error: {str(e)}")

        # Step 3: Admin clicks "إضافة أكواد" (add_codes)
        try:
            add_codes_callback = {
                "update_id": 200003,
                "callback_query": {
                    "id": "callback_200003",
                    "from": {"id": admin_id, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                    "message": {
                        "message_id": 3,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": admin_id, "type": "private"},
                        "from": {"id": 7835622090, "is_bot": True, "first_name": "AbodCard Admin Bot"}
                    },
                    "chat_instance": "admin_chat_instance_200003",
                    "data": "add_codes"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=add_codes_callback)
            success = response.status_code == 200
            self.log_test(
                "Admin Flow - Add Codes Selection",
                success,
                f"Add codes callback handled with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("Admin Flow - Add Codes Selection", False, f"Error: {str(e)}")

        # Step 4: Get available categories and test selecting one
        try:
            categories_response = self.session.get(f"{self.api_url}/categories")
            if categories_response.status_code == 200:
                categories = categories_response.json()
                code_categories = [c for c in categories if c.get('delivery_type') == 'code']
                
                if code_categories:
                    category_id = code_categories[0]['id']
                    
                    # Admin selects a category to add codes to
                    select_category_callback = {
                        "update_id": 200004,
                        "callback_query": {
                            "id": "callback_200004",
                            "from": {"id": admin_id, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                            "message": {
                                "message_id": 4,
                                "date": int(datetime.now().timestamp()),
                                "chat": {"id": admin_id, "type": "private"},
                                "from": {"id": 7835622090, "is_bot": True, "first_name": "AbodCard Admin Bot"}
                            },
                            "chat_instance": "admin_chat_instance_200004",
                            "data": f"add_codes_to_category_{category_id}"
                        }
                    }
                    
                    response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=select_category_callback)
                    success = response.status_code == 200
                    self.log_test(
                        "Admin Flow - Category Selection for Codes",
                        success,
                        f"Category selection handled with status {response.status_code}",
                        response.json() if success else response.text
                    )
                else:
                    self.log_test("Admin Flow - Category Selection for Codes", False, "No code categories available")
            else:
                self.log_test("Admin Flow - Category Selection for Codes", False, "Failed to fetch categories")
        except Exception as e:
            self.log_test("Admin Flow - Category Selection for Codes", False, f"Error: {str(e)}")

        # Step 5: Test code type selection (text type)
        try:
            if code_categories:
                category_id = code_categories[0]['id']
                
                code_type_callback = {
                    "update_id": 200005,
                    "callback_query": {
                        "id": "callback_200005",
                        "from": {"id": admin_id, "is_bot": False, "first_name": "Admin", "username": "adminuser"},
                        "message": {
                            "message_id": 5,
                            "date": int(datetime.now().timestamp()),
                            "chat": {"id": admin_id, "type": "private"},
                            "from": {"id": 7835622090, "is_bot": True, "first_name": "AbodCard Admin Bot"}
                        },
                        "chat_instance": "admin_chat_instance_200005",
                        "data": f"code_type_text_{category_id}"
                    }
                }
                
                response = self.session.post(f"{self.api_url}/webhook/admin/abod_admin_webhook_secret", json=code_type_callback)
                success = response.status_code == 200
                self.log_test(
                    "Admin Flow - Code Type Selection (Text)",
                    success,
                    f"Code type selection handled with status {response.status_code}",
                    response.json() if success else response.text
                )
        except Exception as e:
            self.log_test("Admin Flow - Code Type Selection (Text)", False, f"Error: {str(e)}")

    def simulate_user_product_browsing_flow(self):
        """Simulate the complete user product browsing and purchase flow"""
        print("🛒 Testing User Product Browsing Flow...")
        
        user_id = 987654321
        
        # Step 1: User starts with /start
        try:
            start_update = {
                "update_id": 300001,
                "message": {
                    "message_id": 1,
                    "date": int(datetime.now().timestamp()),
                    "chat": {"id": user_id, "type": "private"},
                    "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                    "text": "/start"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=start_update)
            success = response.status_code == 200
            self.log_test(
                "User Flow - Start Command",
                success,
                f"User bot responded to /start with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("User Flow - Start Command", False, f"Error: {str(e)}")

        # Step 2: User clicks "الشراء" (browse_products)
        try:
            browse_callback = {
                "update_id": 300002,
                "callback_query": {
                    "id": "callback_300002",
                    "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                    "message": {
                        "message_id": 2,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": user_id, "type": "private"},
                        "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                    },
                    "chat_instance": "user_chat_instance_300002",
                    "data": "browse_products"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=browse_callback)
            success = response.status_code == 200
            self.log_test(
                "User Flow - Browse Products Selection",
                success,
                f"Browse products callback handled with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("User Flow - Browse Products Selection", False, f"Error: {str(e)}")

        # Step 3: User selects a product
        try:
            products_response = self.session.get(f"{self.api_url}/products")
            if products_response.status_code == 200:
                products = products_response.json()
                
                if products:
                    product_id = products[0]['id']
                    
                    product_callback = {
                        "update_id": 300003,
                        "callback_query": {
                            "id": "callback_300003",
                            "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                            "message": {
                                "message_id": 3,
                                "date": int(datetime.now().timestamp()),
                                "chat": {"id": user_id, "type": "private"},
                                "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                            },
                            "chat_instance": "user_chat_instance_300003",
                            "data": f"product_{product_id}"
                        }
                    }
                    
                    response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=product_callback)
                    success = response.status_code == 200
                    self.log_test(
                        "User Flow - Product Selection",
                        success,
                        f"Product selection handled with status {response.status_code}",
                        response.json() if success else response.text
                    )
                else:
                    self.log_test("User Flow - Product Selection", False, "No products available")
            else:
                self.log_test("User Flow - Product Selection", False, "Failed to fetch products")
        except Exception as e:
            self.log_test("User Flow - Product Selection", False, f"Error: {str(e)}")

        # Step 4: User selects a category
        try:
            categories_response = self.session.get(f"{self.api_url}/categories")
            if categories_response.status_code == 200:
                categories = categories_response.json()
                
                if categories:
                    category_id = categories[0]['id']
                    
                    category_callback = {
                        "update_id": 300004,
                        "callback_query": {
                            "id": "callback_300004",
                            "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                            "message": {
                                "message_id": 4,
                                "date": int(datetime.now().timestamp()),
                                "chat": {"id": user_id, "type": "private"},
                                "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                            },
                            "chat_instance": "user_chat_instance_300004",
                            "data": f"category_{category_id}"
                        }
                    }
                    
                    response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=category_callback)
                    success = response.status_code == 200
                    self.log_test(
                        "User Flow - Category Selection",
                        success,
                        f"Category selection handled with status {response.status_code}",
                        response.json() if success else response.text
                    )
                else:
                    self.log_test("User Flow - Category Selection", False, "No categories available")
            else:
                self.log_test("User Flow - Category Selection", False, "Failed to fetch categories")
        except Exception as e:
            self.log_test("User Flow - Category Selection", False, f"Error: {str(e)}")

        # Step 5: Test wallet viewing
        try:
            wallet_callback = {
                "update_id": 300005,
                "callback_query": {
                    "id": "callback_300005",
                    "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                    "message": {
                        "message_id": 5,
                        "date": int(datetime.now().timestamp()),
                        "chat": {"id": user_id, "type": "private"},
                        "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                    },
                    "chat_instance": "user_chat_instance_300005",
                    "data": "view_wallet"
                }
            }
            
            response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=wallet_callback)
            success = response.status_code == 200
            self.log_test(
                "User Flow - View Wallet",
                success,
                f"View wallet callback handled with status {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test("User Flow - View Wallet", False, f"Error: {str(e)}")

    def test_session_management(self):
        """Test session management during multi-step processes"""
        print("🔄 Testing Session Management...")
        
        # Test that sessions are properly created and managed
        # This is implicit in the callback handling, but we can test some edge cases
        
        # Test rapid successive callbacks (session consistency)
        user_id = 987654321
        
        try:
            # Send multiple callbacks in quick succession
            for i in range(3):
                callback = {
                    "update_id": 400000 + i,
                    "callback_query": {
                        "id": f"callback_400{i:03d}",
                        "from": {"id": user_id, "is_bot": False, "first_name": "TestUser", "username": "testuser"},
                        "message": {
                            "message_id": 10 + i,
                            "date": int(datetime.now().timestamp()),
                            "chat": {"id": user_id, "type": "private"},
                            "from": {"id": 7933553585, "is_bot": True, "first_name": "AbodCard User Bot"}
                        },
                        "chat_instance": f"user_chat_instance_400{i:03d}",
                        "data": "main_menu"
                    }
                }
                
                response = self.session.post(f"{self.api_url}/webhook/user/abod_user_webhook_secret", json=callback)
                if response.status_code != 200:
                    self.log_test("Session Management - Rapid Callbacks", False, f"Failed on callback {i+1}")
                    return
                
                time.sleep(0.1)  # Small delay between requests
            
            self.log_test(
                "Session Management - Rapid Callbacks",
                True,
                "Successfully handled 3 rapid successive callbacks"
            )
        except Exception as e:
            self.log_test("Session Management - Rapid Callbacks", False, f"Error: {str(e)}")

    def test_data_validation_and_integrity(self):
        """Test data validation and integrity"""
        print("🔍 Testing Data Validation and Integrity...")
        
        # Test that products have valid categories
        try:
            products_response = self.session.get(f"{self.api_url}/products")
            categories_response = self.session.get(f"{self.api_url}/categories")
            
            if products_response.status_code == 200 and categories_response.status_code == 200:
                products = products_response.json()
                categories = categories_response.json()
                
                # Check that all categories reference valid products
                product_ids = {p['id'] for p in products}
                invalid_categories = [c for c in categories if c.get('product_id') not in product_ids]
                
                success = len(invalid_categories) == 0
                self.log_test(
                    "Data Integrity - Product-Category References",
                    success,
                    f"All {len(categories)} categories reference valid products" if success else f"{len(invalid_categories)} categories have invalid product references",
                    {"invalid_categories": len(invalid_categories)} if not success else None
                )
                
                # Check that categories have required fields for user bot functionality
                required_fields = ['id', 'name', 'description', 'price', 'delivery_type', 'product_id']
                incomplete_categories = []
                for cat in categories:
                    missing_fields = [field for field in required_fields if field not in cat or cat[field] is None]
                    if missing_fields:
                        incomplete_categories.append({"category": cat.get('name', 'Unknown'), "missing": missing_fields})
                
                success = len(incomplete_categories) == 0
                self.log_test(
                    "Data Integrity - Category Field Completeness",
                    success,
                    f"All {len(categories)} categories have required fields" if success else f"{len(incomplete_categories)} categories missing required fields",
                    {"incomplete_categories": incomplete_categories[:3]} if not success else None
                )
            else:
                self.log_test("Data Integrity - Product-Category References", False, "Failed to fetch data")
        except Exception as e:
            self.log_test("Data Integrity - Product-Category References", False, f"Error: {str(e)}")

    def run_specific_flow_tests(self):
        """Run all specific flow tests"""
        print("🚀 Starting Specific Flow Testing for Abod Card Telegram Bot System")
        print("=" * 80)
        
        # Test admin code addition flow
        self.simulate_admin_code_addition_flow()
        
        # Test user product browsing flow
        self.simulate_user_product_browsing_flow()
        
        # Test session management
        self.test_session_management()
        
        # Test data validation
        self.test_data_validation_and_integrity()
        
        return True

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 80)
        print("📊 SPECIFIC FLOW TEST REPORT")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 Test Results Summary:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}")
            if result["details"]:
                print(f"    {result['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "results": self.test_results
        }

def main():
    """Main test execution"""
    tester = SpecificFlowTester()
    
    try:
        success = tester.run_specific_flow_tests()
        report = tester.generate_report()
        
        if success:
            print(f"\n🎉 Specific flow testing completed!")
            print(f"Overall success rate: {report['success_rate']:.1f}%")
        else:
            print(f"\n⚠️ Specific flow testing completed with issues.")
            print(f"Overall success rate: {report['success_rate']:.1f}%")
        
        return 0 if report['success_rate'] >= 80 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())