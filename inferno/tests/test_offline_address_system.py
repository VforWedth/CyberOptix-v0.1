#!/usr/bin/env python3
"""
Test script for offline address system functionality
Tests dynamic address passing and offline checkout capabilities
"""

import os
import sys
import time
import json
import requests
from urllib.parse import urljoin

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))

class OfflineAddressSystemTester:
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
        """Test if Django server is running and accessible"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            self.log_test("Server Accessibility", response.status_code == 200)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            self.log_test("Server Accessibility", False, "Cannot connect to Django server")
            return False
        except Exception as e:
            self.log_test("Server Accessibility", False, str(e))
            return False

    def test_offline_page_exists(self):
        """Test if offline page is accessible"""
        try:
            response = self.session.get(urljoin(self.base_url, '/offline/'))
            success = response.status_code == 200
            self.log_test("Offline Page Exists", success,
                         None if success else f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Offline Page Exists", False, str(e))
            return False

    def test_checkout_offline_page(self):
        """Test if offline checkout page exists"""
        try:
            # First try to access a shop checkout page
            response = self.session.get(urljoin(self.base_url, '/checkout/shop-1/'))

            # Check if page loads (might redirect or show different content)
            success = response.status_code in [200, 302]
            self.log_test("Checkout Page Accessible", success,
                         None if success else f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Checkout Page Accessible", False, str(e))
            return False

    def test_static_assets_offline_ready(self):
        """Test if static assets are ready for offline use"""
        static_assets = [
            '/static/js/offline-manager.js',
            '/static/assets/css/checkout.css',
            '/static/assets/libs/bootstrap/css/bootstrap.min.css',
            '/static/assets/libs/jquery/jquery.min.js'
        ]

        offline_ready_count = 0
        for asset in static_assets:
            try:
                response = self.session.get(urljoin(self.base_url, asset))
                if response.status_code == 200:
                    offline_ready_count += 1
            except:
                pass

        success = offline_ready_count >= len(static_assets) * 0.8  # 80% threshold
        self.log_test(f"Static Assets Offline Ready ({offline_ready_count}/{len(static_assets)})",
                     success)
        return success

    def test_pwa_manifest(self):
        """Test if PWA manifest is available"""
        try:
            response = self.session.get(urljoin(self.base_url, '/manifest.json'))
            success = response.status_code == 200
            if success:
                try:
                    manifest = response.json()
                    # Check for essential PWA properties
                    required_props = ['name', 'start_url', 'display']
                    has_required = all(prop in manifest for prop in required_props)
                    success = has_required
                    details = "Valid PWA manifest" if has_required else "Missing required properties"
                except:
                    success = False
                    details = "Invalid JSON manifest"
            else:
                details = f"Status: {response.status_code}"

            self.log_test("PWA Manifest Available", success,
                         None if success else details)
            return success
        except Exception as e:
            self.log_test("PWA Manifest Available", False, str(e))
            return False

    def test_service_worker(self):
        """Test if service worker is available"""
        try:
            response = self.session.get(urljoin(self.base_url, '/sw.js'))
            success = response.status_code == 200
            self.log_test("Service Worker Available", success,
                         None if success else f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Service Worker Available", False, str(e))
            return False

    def test_address_api_endpoints(self):
        """Test address-related API endpoints"""
        endpoints = [
            '/api/v1/states/',
            '/api/v1/cities/',
            '/api/v1/townships/'
        ]

        working_endpoints = 0
        for endpoint in endpoints:
            try:
                response = self.session.get(urljoin(self.base_url, endpoint))
                if response.status_code == 200:
                    working_endpoints += 1
                    # Try to parse JSON
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'results' in data:
                            # Paginated response
                            pass
                        elif isinstance(data, list):
                            # Direct list response
                            pass
                    except:
                        working_endpoints -= 1
            except:
                pass

        success = working_endpoints >= len(endpoints) * 0.67  # 67% threshold
        self.log_test(f"Address API Endpoints ({working_endpoints}/{len(endpoints)})", success)
        return success

    def test_dynamic_address_form(self):
        """Test if dynamic address form components exist in checkout"""
        try:
            # Get checkout page content
            response = self.session.get(urljoin(self.base_url, '/checkout/shop-1/'))

            if response.status_code == 200:
                content = response.text

                # Check for address form elements
                address_elements = [
                    'offline-state',
                    'offline-city',
                    'offline-township',
                    'offline-street-address'
                ]

                found_elements = sum(1 for element in address_elements if element in content)
                success = found_elements >= len(address_elements) * 0.75  # 75% threshold

                details = f"Found {found_elements}/{len(address_elements)} address form elements"
                self.log_test("Dynamic Address Form Elements", success,
                             None if success else details)
                return success
            else:
                self.log_test("Dynamic Address Form Elements", False,
                             f"Checkout page not accessible: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Dynamic Address Form Elements", False, str(e))
            return False

    def test_offline_cart_functionality(self):
        """Test offline cart storage capabilities"""
        try:
            # Get a product page to test cart functionality
            response = self.session.get(urljoin(self.base_url, '/'))

            if response.status_code == 200:
                content = response.text

                # Check for offline cart related JavaScript
                offline_features = [
                    'offline-manager',
                    'IndexedDB',
                    'addToOfflineCart',
                    'getOfflineCart'
                ]

                found_features = sum(1 for feature in offline_features if feature in content)
                success = found_features >= 2  # At least 2 offline features should be present

                details = f"Found {found_features}/{len(offline_features)} offline cart features"
                self.log_test("Offline Cart Functionality", success,
                             None if success else details)
                return success
            else:
                self.log_test("Offline Cart Functionality", False,
                             f"Homepage not accessible: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Offline Cart Functionality", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive report"""
        print("🔄 Running Offline Address System Tests...")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_server_accessibility,
            self.test_offline_page_exists,
            self.test_checkout_offline_page,
            self.test_static_assets_offline_ready,
            self.test_pwa_manifest,
            self.test_service_worker,
            self.test_address_api_endpoints,
            self.test_dynamic_address_form,
            self.test_offline_cart_functionality
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
            print("🎉 ALL TESTS PASSED! Your project is ready for offline operation.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor issues may exist but core functionality works.")
        elif passed >= total * 0.6:
            print("⚠️  Some critical issues found. Review failed tests before proceeding.")
        else:
            print("❌ Major issues detected. Significant work needed for offline functionality.")

        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details'] and not result['success']:
                print(f"   └─ {result['details']}")

        return passed, total

    def generate_test_instructions(self):
        """Generate testing instructions for manual testing"""
        instructions = """
🧪 MANUAL TESTING INSTRUCTIONS
===============================

1. BASIC OFFLINE TEST:
   - Visit your site online first
   - Browse some products to cache them
   - Disconnect from internet
   - Navigate to /offline/ to see offline page
   - Try browsing cached products

2. DYNAMIC ADDRESS TEST:
   - With internet disconnected
   - Go to checkout page (/checkout/shop-1/)
   - Fill in address fields manually
   - Verify all required fields work
   - Test state, city, township inputs

3. OFFLINE CHECKOUT TEST:
   - Add items to cart while online
   - Disconnect internet
   - Go to checkout page
   - Fill delivery address dynamically
   - Submit as Cash on Delivery
   - Verify order is saved for later submission

4. RECONNECTION TEST:
   - Reconnect to internet
   - Verify offline orders are submitted
   - Check for sync notifications

🎯 EXPECTED BEHAVIOR:
- Address fields should accept manual input
- Checkout should work with COD payment
- Orders should queue when offline
- Automatic sync when back online
"""
        print(instructions)

def main():
    """Main function to run tests"""
    print("🚀 CyberOptix LaptopMart Myanmar - Offline Address System Tester")
    print("================================================================")

    # Check if Django server should be started
    import subprocess
    import sys

    tester = OfflineAddressSystemTester()

    # Test if server is running
    if not tester.test_server_accessibility():
        print("\n⚠️  Django server not accessible at http://127.0.0.1:8000")
        print("Please start the Django server first:")
        print("   cd inferno")
        print("   python manage.py runserver")
        print("\nThen run this test again.")
        return False

    # Run comprehensive tests
    passed, total = tester.run_comprehensive_test()

    # Generate manual testing instructions
    print("\n" + "=" * 60)
    tester.generate_test_instructions()

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)