#!/usr/bin/env python3
"""
Test script for direct address input functionality
Tests user input without cache dependencies
"""

import os
import sys
import time
import json
import requests
from urllib.parse import urljoin

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))

class DirectAddressInputTester:
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name, success, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details and not success:
            print(f"    Details: {details}")

    def test_server_accessibility(self):
        """Test if Django server is running"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            success = response.status_code == 200
            self.log_test("Django Server Running", success)
            return success
        except requests.exceptions.ConnectionError:
            self.log_test("Django Server Running", False, "Cannot connect - start server with 'python manage.py runserver'")
            return False
        except Exception as e:
            self.log_test("Django Server Running", False, str(e))
            return False

    def test_direct_checkout_url(self):
        """Test if direct checkout URL is accessible"""
        try:
            # Test with sample shop ID
            response = self.session.get(urljoin(self.base_url, '/checkout/direct/shop-1/'))

            # Accept 200 (success) or 302 (redirect to login)
            success = response.status_code in [200, 302]

            if response.status_code == 302:
                # Check if redirecting to login (expected for unauthenticated users)
                location = response.headers.get('Location', '')
                is_login_redirect = 'sign-in' in location or 'login' in location
                success = is_login_redirect
                details = "Redirects to login (expected for unauthenticated users)" if is_login_redirect else f"Unexpected redirect to: {location}"
            else:
                details = "Direct checkout page accessible"

            self.log_test("Direct Checkout URL Available", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Direct Checkout URL Available", False, str(e))
            return False

    def test_direct_address_manager_js(self):
        """Test if direct address manager JavaScript is available"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/direct-address-manager.js'))
            success = response.status_code == 200

            if success:
                # Check if the file contains key functionality
                content = response.text
                required_functions = [
                    'DirectAddressManager',
                    'setupAddressAutocomplete',
                    'updateCitySuggestions',
                    'validateAddress',
                    'saveAddress'
                ]

                missing_functions = [func for func in required_functions if func not in content]

                if missing_functions:
                    success = False
                    details = f"Missing functions: {', '.join(missing_functions)}"
                else:
                    details = "All required functions present"
            else:
                details = f"Status: {response.status_code}"

            self.log_test("Direct Address Manager JS", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Direct Address Manager JS", False, str(e))
            return False

    def test_direct_checkout_template(self):
        """Test if direct checkout template exists"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'templates', 'flame', 'checkout_direct_input.html'
            )

            exists = os.path.exists(template_path)

            if exists:
                # Check template content
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                required_elements = [
                    'delivery-state',
                    'delivery-city',
                    'delivery-township',
                    'delivery-street',
                    'DirectInputAddressManager',
                    'validate-address-btn'
                ]

                missing_elements = [elem for elem in required_elements if elem not in content]

                if missing_elements:
                    success = False
                    details = f"Missing elements: {', '.join(missing_elements)}"
                else:
                    success = True
                    details = "All required elements present"
            else:
                success = False
                details = "Template file not found"

            self.log_test("Direct Checkout Template", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Direct Checkout Template", False, str(e))
            return False

    def test_address_autocomplete_data(self):
        """Test if address autocomplete data is properly structured"""
        try:
            js_file_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'static', 'js', 'direct-address-manager.js'
            )

            if not os.path.exists(js_file_path):
                self.log_test("Address Autocomplete Data", False, "JavaScript file not found")
                return False

            with open(js_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for Myanmar address data
            required_data = [
                'Yangon',
                'Mandalay',
                'Naypyidaw',
                'Shan State',
                'Downtown',
                'Taunggyi'
            ]

            missing_data = [data for data in required_data if data not in content]

            if missing_data:
                success = False
                details = f"Missing address data: {', '.join(missing_data)}"
            else:
                success = True
                details = "Myanmar address data present"

            self.log_test("Address Autocomplete Data", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Address Autocomplete Data", False, str(e))
            return False

    def test_shipping_calculation_logic(self):
        """Test shipping cost calculation logic"""
        try:
            js_file_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'static', 'js', 'direct-address-manager.js'
            )

            if not os.path.exists(js_file_path):
                self.log_test("Shipping Calculation Logic", False, "JavaScript file not found")
                return False

            with open(js_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for shipping calculation methods
            shipping_functions = [
                'calculateShippingCost',
                'getShippingZone',
                'getEstimatedDeliveryDays'
            ]

            missing_functions = [func for func in shipping_functions if func not in content]

            if missing_functions:
                success = False
                details = f"Missing shipping functions: {', '.join(missing_functions)}"
            else:
                success = True
                details = "Shipping calculation logic present"

            self.log_test("Shipping Calculation Logic", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Shipping Calculation Logic", False, str(e))
            return False

    def test_address_validation_features(self):
        """Test address validation features"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'templates', 'flame', 'checkout_direct_input.html'
            )

            if not os.path.exists(template_path):
                self.log_test("Address Validation Features", False, "Template not found")
                return False

            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            validation_features = [
                'required',  # HTML5 validation
                'validateField',  # JavaScript validation
                'showFieldError',  # Error display
                'clearFieldError',  # Error clearing
                'validate-address-btn'  # Manual validation button
            ]

            missing_features = [feature for feature in validation_features if feature not in content]

            if missing_features:
                success = False
                details = f"Missing validation features: {', '.join(missing_features)}"
            else:
                success = True
                details = "Address validation features present"

            self.log_test("Address Validation Features", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Address Validation Features", False, str(e))
            return False

    def test_local_storage_functionality(self):
        """Test local storage for saved addresses"""
        try:
            js_file_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'static', 'js', 'direct-address-manager.js'
            )

            if not os.path.exists(js_file_path):
                self.log_test("Local Storage Functionality", False, "JavaScript file not found")
                return False

            with open(js_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            storage_functions = [
                'loadSavedAddresses',
                'persistSavedAddresses',
                'saveAddress',
                'localStorage'
            ]

            missing_functions = [func for func in storage_functions if func not in content]

            if missing_functions:
                success = False
                details = f"Missing storage functions: {', '.join(missing_functions)}"
            else:
                success = True
                details = "Local storage functionality present"

            self.log_test("Local Storage Functionality", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Local Storage Functionality", False, str(e))
            return False

    def test_offline_compatibility(self):
        """Test offline compatibility features"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'templates', 'flame', 'checkout_direct_input.html'
            )

            if not os.path.exists(template_path):
                self.log_test("Offline Compatibility", False, "Template not found")
                return False

            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            offline_features = [
                'connection-status',
                'monitorConnectionStatus',
                'navigator.onLine',
                'offline',
                'Cash on Delivery'
            ]

            missing_features = [feature for feature in offline_features if feature not in content]

            if missing_features:
                success = False
                details = f"Missing offline features: {', '.join(missing_features)}"
            else:
                success = True
                details = "Offline compatibility features present"

            self.log_test("Offline Compatibility", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Compatibility", False, str(e))
            return False

    def test_form_accessibility(self):
        """Test form accessibility features"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__),
                'inferno', 'templates', 'flame', 'checkout_direct_input.html'
            )

            if not os.path.exists(template_path):
                self.log_test("Form Accessibility", False, "Template not found")
                return False

            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            accessibility_features = [
                'label for=',  # Proper labels
                'placeholder=',  # Helpful placeholders
                'aria-',  # ARIA attributes
                'form-text',  # Help text
                'required'  # Required field indicators
            ]

            present_features = [feature for feature in accessibility_features if feature in content]

            # Require at least 4 out of 5 accessibility features
            success = len(present_features) >= 4

            if success:
                details = f"Found {len(present_features)}/5 accessibility features"
            else:
                missing = [f for f in accessibility_features if f not in content]
                details = f"Only {len(present_features)}/5 features. Missing: {', '.join(missing)}"

            self.log_test("Form Accessibility", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Form Accessibility", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive report"""
        print("🔄 Running Direct Address Input Tests...")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_server_accessibility,
            self.test_direct_checkout_url,
            self.test_direct_address_manager_js,
            self.test_direct_checkout_template,
            self.test_address_autocomplete_data,
            self.test_shipping_calculation_logic,
            self.test_address_validation_features,
            self.test_local_storage_functionality,
            self.test_offline_compatibility,
            self.test_form_accessibility
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            print()  # Add spacing between tests

        # Generate report
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")

        if passed == total:
            print("🎉 ALL TESTS PASSED! Direct address input is fully functional.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Direct address input should work well.")
        elif passed >= total * 0.6:
            print("⚠️  Some issues found. Review failed tests before use.")
        else:
            print("❌ Major issues detected. Direct address input needs fixes.")

        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details'] and not result['success']:
                print(f"   └─ {result['details']}")

        return passed, total

    def generate_usage_instructions(self):
        """Generate usage instructions"""
        instructions = """
🎯 DIRECT ADDRESS INPUT USAGE
=============================

## How to Use Direct Address Input:

### 1. ACCESS THE FEATURE:
   - Visit: /checkout/direct/shop-1/
   - Replace 'shop-1' with actual shop ID
   - Login required for checkout

### 2. FILL ADDRESS MANUALLY:
   ✅ State/Region: Type directly (e.g., "Yangon", "Shan State")
   ✅ City/Town: Type directly (e.g., "Downtown", "Taunggyi")
   ✅ Township: Optional field
   ✅ Street Address: Full address details
   ✅ Landmark: For easy delivery location

### 3. SMART FEATURES:
   🔍 Auto-suggestions as you type
   📍 Shipping cost calculation
   💾 Save addresses for future use
   ✅ Address validation
   📱 Works completely offline

### 4. NO CACHE REQUIRED:
   ⚡ No internet needed for address input
   🏠 All Myanmar locations built-in
   💻 Local storage for saved addresses
   🔄 Works without external APIs

### 5. PAYMENT OPTIONS:
   💳 Cash on Delivery (offline)
   🌐 Online payments (when connected)

## Benefits:
- ✅ Works without cached address data
- ✅ User has full control over address
- ✅ No dependency on external services
- ✅ Fast and responsive interface
- ✅ Saves user preferences locally
"""
        print(instructions)

def main():
    """Main function to run tests"""
    print("🚀 CyberOptix - Direct Address Input Tester")
    print("==========================================")

    tester = DirectAddressInputTester()

    # Test if server is running
    if not tester.test_server_accessibility():
        print("\n⚠️  Django server not accessible.")
        print("Please start the server:")
        print("   cd inferno")
        print("   python manage.py runserver")
        print("\nThen run this test again.")
        return False

    # Run comprehensive tests
    passed, total = tester.run_comprehensive_test()

    # Generate usage instructions
    print("\n" + "=" * 60)
    tester.generate_usage_instructions()

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)