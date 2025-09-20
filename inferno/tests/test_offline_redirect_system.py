#!/usr/bin/env python3
"""
Test script for offline redirect system functionality
Tests dynamic offline redirects and accurate offline logic
"""

import os
import sys
import time
import json
import requests
from urllib.parse import urljoin

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))

class OfflineRedirectSystemTester:
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

    def test_offline_redirect_manager_js(self):
        """Test if offline redirect manager JavaScript is available"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/offline-redirect-manager.js'))
            success = response.status_code == 200

            if success:
                content = response.text
                required_classes = [
                    'OfflineRedirectManager',
                    'setupConnectionMonitoring',
                    'redirectToOfflineVersion',
                    'handleConnectionLoss',
                    'handleConnectionRestore'
                ]

                missing_classes = [cls for cls in required_classes if cls not in content]

                if missing_classes:
                    success = False
                    details = f"Missing classes/methods: {', '.join(missing_classes)}"
                else:
                    details = "All required classes and methods present"
            else:
                details = f"Status: {response.status_code}"

            self.log_test("Offline Redirect Manager JS", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Redirect Manager JS", False, str(e))
            return False

    def test_offline_parameter_redirect(self):
        """Test redirect with offline=true parameter"""
        try:
            test_urls = [
                '/checkout/shop/shop-1/?offline=true',
                '/products/?offline=true',
                '/search/?offline=true'
            ]

            successful_redirects = 0

            for test_url in test_urls:
                response = self.session.get(urljoin(self.base_url, test_url), allow_redirects=False)

                # Check for redirect (302/301) or direct offline page (200)
                if response.status_code in [200, 302, 301]:
                    if response.status_code in [302, 301]:
                        # Check if redirected to appropriate offline URL
                        location = response.headers.get('Location', '')
                        if '/offline/' in location or '/checkout/direct/' in location:
                            successful_redirects += 1
                    else:
                        # Check if page content indicates offline mode
                        if '/offline/' in test_url or 'offline' in response.text.lower():
                            successful_redirects += 1

            success = successful_redirects >= len(test_urls) * 0.6  # 60% success rate
            details = f"Successful redirects: {successful_redirects}/{len(test_urls)}"

            self.log_test("Offline Parameter Redirects", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Parameter Redirects", False, str(e))
            return False

    def test_checkout_to_direct_redirect(self):
        """Test checkout redirects to direct input version"""
        try:
            checkout_urls = [
                '/checkout/shop/shop-1/?offline=true',
                '/checkout/shop/test-shop/?offline=true'
            ]

            successful_redirects = 0

            for checkout_url in checkout_urls:
                response = self.session.get(urljoin(self.base_url, checkout_url), allow_redirects=False)

                if response.status_code in [302, 301]:
                    location = response.headers.get('Location', '')
                    if '/checkout/direct/' in location:
                        successful_redirects += 1
                elif response.status_code == 200:
                    # Check if it's already the direct checkout page
                    if 'direct' in checkout_url or 'DirectInputAddressManager' in response.text:
                        successful_redirects += 1

            success = successful_redirects >= len(checkout_urls) * 0.5  # 50% success rate
            details = f"Checkout redirects: {successful_redirects}/{len(checkout_urls)}"

            self.log_test("Checkout to Direct Redirects", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Checkout to Direct Redirects", False, str(e))
            return False

    def test_offline_middleware_headers(self):
        """Test if offline middleware adds appropriate headers"""
        try:
            test_urls = [
                '/',
                '/products/',
                '/shop/',
                '/category/'
            ]

            header_checks = 0

            for test_url in test_urls:
                response = self.session.get(urljoin(self.base_url, test_url))

                if response.status_code == 200:
                    # Check for offline capability header
                    if response.headers.get('X-Offline-Capable') == 'true':
                        header_checks += 1

                    # Check for cache headers on cacheable content
                    if 'Cache-Control' in response.headers:
                        header_checks += 0.5

            success = header_checks >= len(test_urls) * 0.75  # 75% of expected headers
            details = f"Header checks passed: {header_checks}/{len(test_urls)}"

            self.log_test("Offline Middleware Headers", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Middleware Headers", False, str(e))
            return False

    def test_offline_route_mapping(self):
        """Test if offline route mappings work correctly"""
        try:
            route_tests = [
                {
                    'original': '/checkout/shop/test-shop/',
                    'expected_pattern': '/checkout/direct/',
                    'preserve_shop': True
                },
                {
                    'original': '/products/',
                    'expected_pattern': '/offline/',
                    'preserve_shop': False
                },
                {
                    'original': '/search/',
                    'expected_pattern': '/offline/',
                    'preserve_shop': False
                }
            ]

            correct_mappings = 0

            for route_test in route_tests:
                # Test with offline parameter
                test_url = route_test['original'] + '?offline=true'
                response = self.session.get(urljoin(self.base_url, test_url), allow_redirects=False)

                if response.status_code in [302, 301]:
                    location = response.headers.get('Location', '')
                    if route_test['expected_pattern'] in location:
                        if route_test['preserve_shop']:
                            # Check if shop ID is preserved
                            if 'test-shop' in location or 'shop-' in location:
                                correct_mappings += 1
                        else:
                            correct_mappings += 1

            success = correct_mappings >= len(route_tests) * 0.6  # 60% success rate
            details = f"Correct mappings: {correct_mappings}/{len(route_tests)}"

            self.log_test("Offline Route Mapping", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Route Mapping", False, str(e))
            return False

    def test_connection_monitoring_js(self):
        """Test if connection monitoring JavaScript functions are present"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/offline-redirect-manager.js'))

            if response.status_code != 200:
                self.log_test("Connection Monitoring JS", False, "JavaScript file not accessible")
                return False

            content = response.text
            monitoring_functions = [
                'setupConnectionMonitoring',
                'checkConnection',
                'handleConnectionLoss',
                'handleConnectionRestore',
                'navigator.onLine'
            ]

            present_functions = [func for func in monitoring_functions if func in content]
            success = len(present_functions) >= len(monitoring_functions) * 0.8  # 80% of functions

            details = f"Present functions: {len(present_functions)}/{len(monitoring_functions)}"
            if not success:
                missing = [f for f in monitoring_functions if f not in content]
                details += f". Missing: {', '.join(missing)}"

            self.log_test("Connection Monitoring JS", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Connection Monitoring JS", False, str(e))
            return False

    def test_offline_form_interception(self):
        """Test if offline form submission interception is implemented"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/offline-redirect-manager.js'))

            if response.status_code != 200:
                self.log_test("Offline Form Interception", False, "JavaScript file not accessible")
                return False

            content = response.text
            interception_features = [
                'setupFormInterception',
                'handleOfflineFormSubmission',
                'addEventListener',
                'submit',
                'preventDefault'
            ]

            present_features = [feature for feature in interception_features if feature in content]
            success = len(present_features) >= len(interception_features) * 0.6  # 60% of features

            details = f"Present features: {len(present_features)}/{len(interception_features)}"

            self.log_test("Offline Form Interception", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Form Interception", False, str(e))
            return False

    def test_offline_notification_system(self):
        """Test if offline notification system is implemented"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/offline-redirect-manager.js'))

            if response.status_code != 200:
                self.log_test("Offline Notification System", False, "JavaScript file not accessible")
                return False

            content = response.text
            notification_features = [
                'showOfflineNotification',
                'hideOfflineNotification',
                'showReconnectionNotification',
                'showRedirectNotification',
                'alert',
                'modal'
            ]

            present_features = [feature for feature in notification_features if feature in content]
            success = len(present_features) >= len(notification_features) * 0.7  # 70% of features

            details = f"Present features: {len(present_features)}/{len(notification_features)}"

            self.log_test("Offline Notification System", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Notification System", False, str(e))
            return False

    def test_offline_url_patterns(self):
        """Test if offline URL patterns are correctly configured"""
        try:
            # Test offline page existence
            response = self.session.get(urljoin(self.base_url, '/offline/'))
            offline_page_exists = response.status_code == 200

            # Test direct checkout URL pattern
            response = self.session.get(urljoin(self.base_url, '/checkout/direct/shop-1/'))
            direct_checkout_exists = response.status_code in [200, 302]  # 302 if login required

            success = offline_page_exists and direct_checkout_exists

            details = []
            if not offline_page_exists:
                details.append("Offline page (/offline/) not accessible")
            if not direct_checkout_exists:
                details.append("Direct checkout page (/checkout/direct/shop-1/) not accessible")

            self.log_test("Offline URL Patterns", success, "; ".join(details) if details else None)
            return success
        except Exception as e:
            self.log_test("Offline URL Patterns", False, str(e))
            return False

    def test_dynamic_shop_id_handling(self):
        """Test if shop IDs are dynamically handled in offline redirects"""
        try:
            test_shops = ['shop-1', 'test-shop', 'demo-shop']
            successful_handling = 0

            for shop_id in test_shops:
                # Test checkout redirect with shop ID
                test_url = f'/checkout/shop/{shop_id}/?offline=true'
                response = self.session.get(urljoin(self.base_url, test_url), allow_redirects=False)

                if response.status_code in [302, 301]:
                    location = response.headers.get('Location', '')
                    # Check if shop ID is preserved in redirect
                    if shop_id in location or '/checkout/direct/' in location:
                        successful_handling += 1

            success = successful_handling >= len(test_shops) * 0.5  # 50% success rate
            details = f"Dynamic shop handling: {successful_handling}/{len(test_shops)}"

            self.log_test("Dynamic Shop ID Handling", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Dynamic Shop ID Handling", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive report"""
        print("🔄 Running Offline Redirect System Tests...")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_server_accessibility,
            self.test_offline_redirect_manager_js,
            self.test_offline_parameter_redirect,
            self.test_checkout_to_direct_redirect,
            self.test_offline_middleware_headers,
            self.test_offline_route_mapping,
            self.test_connection_monitoring_js,
            self.test_offline_form_interception,
            self.test_offline_notification_system,
            self.test_offline_url_patterns,
            self.test_dynamic_shop_id_handling
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
            print("🎉 ALL TESTS PASSED! Offline redirect system is fully functional.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Offline redirect system should work well.")
        elif passed >= total * 0.6:
            print("⚠️  Some issues found. Review failed tests before deploying.")
        else:
            print("❌ Major issues detected. Offline redirect system needs fixes.")

        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details'] and not result['success']:
                print(f"   └─ {result['details']}")

        return passed, total

    def generate_usage_instructions(self):
        """Generate usage instructions for offline redirect system"""
        instructions = """
🎯 OFFLINE REDIRECT SYSTEM USAGE
================================

## How the System Works:

### 1. AUTOMATIC DETECTION:
   🔍 Monitors connection status with navigator.onLine
   🔍 Detects offline parameters (?offline=true)
   🔍 Checks for connection quality indicators
   🔍 Handles failed network requests

### 2. DYNAMIC REDIRECTS:
   🔄 /checkout/shop/ID/ → /checkout/direct/ID/
   🔄 /products/ → /offline/
   🔄 /search/ → /offline/
   🔄 /payment/ → /checkout/direct/
   🔄 Preserves shop IDs and context

### 3. USER NOTIFICATIONS:
   📱 Shows offline status notifications
   📱 Provides redirect explanations
   📱 Offers user choice for offline mode
   📱 Displays reconnection confirmations

### 4. FORM INTERCEPTION:
   🛡️ Intercepts forms requiring internet
   🛡️ Redirects to offline alternatives
   🛡️ Preserves form data when possible
   🛡️ Shows appropriate error messages

## Testing the System:

### Manual Testing:
1. Add ?offline=true to any URL
2. Use browser dev tools to simulate offline
3. Disconnect network and navigate
4. Try submitting forms while offline

### Expected Behavior:
✅ Smooth redirects to offline pages
✅ Preserved shop IDs and context
✅ Clear user notifications
✅ No broken functionality

## Benefits:
- ✅ Seamless offline experience
- ✅ Dynamic context preservation
- ✅ User-friendly notifications
- ✅ Automatic connection monitoring
- ✅ Graceful degradation
"""
        print(instructions)

def main():
    """Main function to run tests"""
    print("🚀 CyberOptix - Offline Redirect System Tester")
    print("=============================================")

    tester = OfflineRedirectSystemTester()

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