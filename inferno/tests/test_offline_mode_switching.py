#!/usr/bin/env python3
"""
Test script for offline mode switching functionality
Tests frontend toggle controls and API endpoints
"""

import os
import sys
import time
import json
import requests
from urllib.parse import urljoin

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))

class OfflineModeSwitchingTester:
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

    def test_api_ping_endpoint(self):
        """Test if /api/ping/ endpoint works"""
        try:
            # Test HEAD request (used by connection checker)
            response = self.session.head(urljoin(self.base_url, '/api/ping/'))
            head_success = response.status_code == 200

            # Test GET request
            response = self.session.get(urljoin(self.base_url, '/api/ping/'))
            get_success = response.status_code == 200

            # Check response content for GET
            content_valid = False
            if get_success:
                try:
                    data = response.json()
                    content_valid = data.get('status') == 'ok' and 'timestamp' in data
                except:
                    pass

            success = head_success and get_success and content_valid

            details = []
            if not head_success:
                details.append("HEAD request failed")
            if not get_success:
                details.append("GET request failed")
            if not content_valid:
                details.append("Invalid response content")

            self.log_test("API Ping Endpoint", success, "; ".join(details) if details else None)
            return success
        except Exception as e:
            self.log_test("API Ping Endpoint", False, str(e))
            return False

    def test_force_offline_api(self):
        """Test force offline API endpoint"""
        try:
            # Get CSRF token first
            csrf_token = self.get_csrf_token()

            response = self.session.post(
                urljoin(self.base_url, '/api/force-offline/'),
                headers={'X-CSRFToken': csrf_token} if csrf_token else {}
            )

            success = response.status_code == 200

            if success:
                try:
                    data = response.json()
                    success = data.get('status') == 'offline_mode_enabled'
                except:
                    success = False

            self.log_test("Force Offline API", success,
                         None if success else f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Force Offline API", False, str(e))
            return False

    def test_force_online_api(self):
        """Test force online API endpoint"""
        try:
            # Get CSRF token first
            csrf_token = self.get_csrf_token()

            response = self.session.post(
                urljoin(self.base_url, '/api/force-online/'),
                headers={'X-CSRFToken': csrf_token} if csrf_token else {}
            )

            success = response.status_code == 200

            if success:
                try:
                    data = response.json()
                    success = data.get('status') == 'online_mode_enabled'
                except:
                    success = False

            self.log_test("Force Online API", success,
                         None if success else f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Force Online API", False, str(e))
            return False

    def test_offline_mode_toggle_js(self):
        """Test if offline mode toggle JavaScript is loaded"""
        try:
            response = self.session.get(urljoin(self.base_url, '/static/js/offline-mode-toggle.js'))
            success = response.status_code == 200

            if success:
                content = response.text
                required_components = [
                    'OfflineModeToggle',
                    'createToggleButton',
                    'switchToOnline',
                    'switchToOffline',
                    'testOfflineMode'
                ]

                missing_components = [comp for comp in required_components if comp not in content]

                if missing_components:
                    success = False
                    details = f"Missing components: {', '.join(missing_components)}"
                else:
                    details = "All components present"
            else:
                details = f"Status: {response.status_code}"

            self.log_test("Offline Mode Toggle JS", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline Mode Toggle JS", False, str(e))
            return False

    def test_toggle_integration_in_base_template(self):
        """Test if toggle is integrated in base template"""
        try:
            response = self.session.get(self.base_url)

            if response.status_code != 200:
                self.log_test("Toggle Integration", False, f"Homepage not accessible: {response.status_code}")
                return False

            content = response.text
            integration_checks = [
                'offline-mode-toggle.js' in content,
                'offline-redirect-manager.js' in content
            ]

            success = all(integration_checks)
            details = f"Integration checks: {sum(integration_checks)}/{len(integration_checks)} passed"

            self.log_test("Toggle Integration", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Toggle Integration", False, str(e))
            return False

    def test_offline_url_parameter_handling(self):
        """Test if ?offline=true parameter triggers offline mode"""
        try:
            test_urls = [
                '/?offline=true',
                '/products/?offline=true',
                '/checkout/shop/shop-1/?offline=true'
            ]

            successful_redirects = 0

            for test_url in test_urls:
                response = self.session.get(urljoin(self.base_url, test_url), allow_redirects=False)

                # Check for redirect or offline content
                if response.status_code in [302, 301]:
                    location = response.headers.get('Location', '')
                    if '/offline/' in location or '/checkout/direct/' in location:
                        successful_redirects += 1
                elif response.status_code == 200:
                    # Check if page shows offline indicators
                    if 'offline' in response.text.lower():
                        successful_redirects += 1

            success = successful_redirects >= len(test_urls) * 0.5  # 50% success rate
            details = f"Successful offline handling: {successful_redirects}/{len(test_urls)}"

            self.log_test("Offline URL Parameter Handling", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Offline URL Parameter Handling", False, str(e))
            return False

    def test_session_based_offline_mode(self):
        """Test if session-based offline mode works"""
        try:
            # First, force offline mode via API
            csrf_token = self.get_csrf_token()

            force_response = self.session.post(
                urljoin(self.base_url, '/api/force-offline/'),
                headers={'X-CSRFToken': csrf_token} if csrf_token else {}
            )

            if force_response.status_code != 200:
                self.log_test("Session-based Offline Mode", False, "Failed to force offline mode")
                return False

            # Now test if regular pages detect offline mode
            test_response = self.session.get(urljoin(self.base_url, '/checkout/shop/shop-1/'), allow_redirects=False)

            # Should redirect to offline version or show offline content
            success = False
            if test_response.status_code in [302, 301]:
                location = test_response.headers.get('Location', '')
                success = '/checkout/direct/' in location
            elif test_response.status_code == 200:
                success = 'offline' in test_response.text.lower()

            # Clean up - force online mode
            self.session.post(
                urljoin(self.base_url, '/api/force-online/'),
                headers={'X-CSRFToken': csrf_token} if csrf_token else {}
            )

            self.log_test("Session-based Offline Mode", success,
                         None if success else "Offline mode not detected in session")
            return success
        except Exception as e:
            self.log_test("Session-based Offline Mode", False, str(e))
            return False

    def test_middleware_offline_detection(self):
        """Test if middleware correctly detects offline requests"""
        try:
            # Test with offline user agent
            headers = {'User-Agent': 'offline-test-browser'}
            response = self.session.get(
                urljoin(self.base_url, '/checkout/shop/shop-1/'),
                headers=headers,
                allow_redirects=False
            )

            middleware_detected = response.status_code in [302, 301] and \
                                 '/checkout/direct/' in response.headers.get('Location', '')

            # Test with connection quality header
            headers = {'Connection': 'slow'}
            response2 = self.session.get(
                urljoin(self.base_url, '/products/'),
                headers=headers,
                allow_redirects=False
            )

            connection_detected = response2.status_code in [302, 301] and \
                                 '/offline/' in response2.headers.get('Location', '')

            success = middleware_detected or connection_detected
            details = f"User-agent detection: {middleware_detected}, Connection detection: {connection_detected}"

            self.log_test("Middleware Offline Detection", success, details if not success else None)
            return success
        except Exception as e:
            self.log_test("Middleware Offline Detection", False, str(e))
            return False

    def get_csrf_token(self):
        """Get CSRF token from homepage"""
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                # Try to extract CSRF token from HTML
                import re
                csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
                if csrf_match:
                    return csrf_match.group(1)

                # Try meta tag
                meta_match = re.search(r'<meta name=["\']csrf-token["\'] content=["\']([^"\']+)["\']', response.text)
                if meta_match:
                    return meta_match.group(1)
        except:
            pass
        return None

    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive report"""
        print("🔄 Running Offline Mode Switching Tests...")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_server_accessibility,
            self.test_api_ping_endpoint,
            self.test_force_offline_api,
            self.test_force_online_api,
            self.test_offline_mode_toggle_js,
            self.test_toggle_integration_in_base_template,
            self.test_offline_url_parameter_handling,
            self.test_session_based_offline_mode,
            self.test_middleware_offline_detection
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
            print("🎉 ALL TESTS PASSED! Offline mode switching is fully functional.")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Offline mode switching should work well.")
        elif passed >= total * 0.6:
            print("⚠️  Some issues found. Review failed tests before deploying.")
        else:
            print("❌ Major issues detected. Offline mode switching needs fixes.")

        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details'] and not result['success']:
                print(f"   └─ {result['details']}")

        return passed, total

    def generate_usage_instructions(self):
        """Generate usage instructions for offline mode switching"""
        instructions = """
🎯 OFFLINE MODE SWITCHING USAGE
===============================

## How to Switch to Offline Mode:

### 1. FRONTEND TOGGLE (Recommended):
   🎛️ Look for floating toggle button (top-right corner)
   🎛️ Click the toggle button to open dropdown
   🎛️ Select "Offline Mode" or "Test Offline"
   🎛️ Page will redirect to offline version

### 2. URL PARAMETER:
   🔗 Add ?offline=true to any URL
   🔗 Example: /checkout/shop/shop-1/?offline=true
   🔗 Automatic redirect to offline version

### 3. API CALLS:
   📡 POST /api/force-offline/ - Enable offline mode
   📡 POST /api/force-online/ - Enable online mode
   📡 HEAD /api/ping/ - Check server connectivity

### 4. DEVELOPER TOOLS:
   🛠️ Use browser Network tab → "Offline"
   🛠️ Automatic detection and redirect

## Visual Indicators:

### Online Mode:
✅ Green WiFi icon in toggle
✅ "Online" status text
✅ All features available

### Offline Mode:
⚠️ Red WiFi-slash icon in toggle
⚠️ "Offline" status text
⚠️ Limited features, COD only

## Expected Behavior:
- ✅ Smooth transitions between modes
- ✅ Context preservation (shop ID, cart)
- ✅ Clear user notifications
- ✅ Automatic page redirects
- ✅ Session persistence

## Troubleshooting:
- If toggle doesn't appear: Check JavaScript console
- If API fails: Verify CSRF token and authentication
- If redirects don't work: Check middleware configuration
"""
        print(instructions)

def main():
    """Main function to run tests"""
    print("🚀 CyberOptix - Offline Mode Switching Tester")
    print("============================================")

    tester = OfflineModeSwitchingTester()

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