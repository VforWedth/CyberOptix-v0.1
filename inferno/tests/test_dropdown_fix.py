#!/usr/bin/env python3
"""
Test script to verify dropdown enabling fix
"""

import os

def test_checkout_template_fixes():
    """Test that checkout template has the dropdown enabling fixes"""
    print("Testing checkout template dropdown fixes...")

    template_file = 'templates/flame/checkout.html'

    if not os.path.exists(template_file):
        print(f"FAIL: {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test for the specific fixes
        fixes = {
            'Offline data first priority': 'if (this.offlineAddressData) {' in content,
            'Enhanced city loading debugging': 'console.log(\'🔄 Loading cities offline for state:\', stateId);' in content,
            'Enhanced township loading debugging': 'console.log(\'🔄 Loading townships offline for city:\', cityId);' in content,
            'Explicit dropdown enabling': 'citySelect.style.pointerEvents = \'auto\';' in content,
            'Auto-enabling function': 'enableAddressDropdowns: function()' in content,
            'Force enable mechanism': 'this.enableAddressDropdowns();' in content,
            'Online/offline fallback priority': 'Try offline data first if available, regardless of connection status' in content
        }

        all_passed = True
        for fix_name, condition in fixes.items():
            if condition:
                print(f"PASS: {fix_name}")
            else:
                print(f"FAIL: {fix_name}")
                all_passed = False

        # Count debugging statements
        debug_count = content.count('console.log')
        print(f"INFO: Found {debug_count} debug statements in template")

        return all_passed

    except Exception as e:
        print(f"FAIL: Error reading template: {e}")
        return False

def test_json_data_availability():
    """Test that JSON data is available and properly structured"""
    print("\nTesting JSON data availability...")

    json_file = 'static/js/myanmar-addresses.min.json'

    if not os.path.exists(json_file):
        print(f"FAIL: {json_file} not found")
        return False

    try:
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if we have meaningful data
        if data['total_states'] > 0 and data['total_cities'] > 0:
            print(f"PASS: JSON data contains {data['total_states']} states and {data['total_cities']} cities")

            # Check if first state has cities
            if data['states'] and data['states'][0]['cities']:
                first_state = data['states'][0]
                print(f"PASS: First state '{first_state['name']}' has {len(first_state['cities'])} cities")
                return True
            else:
                print("FAIL: First state has no cities")
                return False
        else:
            print("FAIL: JSON data is empty or invalid")
            return False

    except Exception as e:
        print(f"FAIL: Error reading JSON: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("DROPDOWN ENABLING FIX TEST")
    print("=" * 60)

    tests = [
        ('Template Fixes', test_checkout_template_fixes),
        ('JSON Data', test_json_data_availability)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("FIX TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nSUCCESS: All dropdown enabling fixes are in place!")
        print("\nTROUBLESHOOTING STEPS:")
        print("1. Open browser developer tools (F12)")
        print("2. Go to Console tab")
        print("3. Navigate to checkout page")
        print("4. Select a state from the dropdown")
        print("5. Check console for debug messages:")
        print("   - Look for '✅ Loaded offline address data'")
        print("   - Look for '🔄 Loading cities offline for state'")
        print("   - Look for '✅ City dropdown enabled with X options'")
        print("6. If city dropdown is still disabled:")
        print("   - Check if browser blocks local files (try with localhost)")
        print("   - Verify Django server is serving static files correctly")
        print("   - Check network tab for failed requests")
    else:
        print(f"\nFAILED: {len(results) - passed} test(s) failed")

    return passed == len(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)