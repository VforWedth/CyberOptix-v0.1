#!/usr/bin/env python3
"""
Test script to verify dynamic address selection implementation
"""

import os

def test_dynamic_implementation():
    """Test that dynamic selection is properly implemented"""
    print("Testing dynamic address selection implementation...")

    template_file = 'templates/flame/checkout.html'

    if not os.path.exists(template_file):
        print(f"FAIL: {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test for dynamic features
        dynamic_features = {
            'API-first approach': 'Always try API first for dynamic, real-time data' in content,
            'Immediate dropdown enabling': 'citySelect.disabled = false;' in content and 'townshipSelect.disabled = false;' in content,
            'Loading state management': 'Loading cities...' in content and 'Loading townships...' in content,
            'Helper functions': 'populateCityDropdown' in content and 'populateTownshipDropdown' in content,
            'Enhanced error handling': 'API failed, trying offline data' in content,
            'Offline fallback only': 'fallback only' in content,
            'Cache dependency removed': 'cacheAddressData' not in content,
            'Simplified enabling': 'dropdowns ready for dynamic loading' in content
        }

        all_passed = True
        for feature_name, condition in dynamic_features.items():
            if condition:
                print(f"PASS: {feature_name}")
            else:
                print(f"FAIL: {feature_name}")
                all_passed = False

        # Check debugging statements
        debug_count = content.count('console.log')
        if debug_count >= 10:
            print(f"PASS: Debugging statements ({debug_count} found)")
        else:
            print(f"FAIL: Insufficient debugging statements ({debug_count} found)")
            all_passed = False

        # Check code cleanliness
        if 'offline data first if available' not in content:
            print("PASS: Removed offline-first priority logic")
        else:
            print("FAIL: Still contains offline-first priority logic")
            all_passed = False

        return all_passed

    except Exception as e:
        print(f"FAIL: Error reading template: {e}")
        return False

def test_function_structure():
    """Test that functions are properly structured"""
    print("\nTesting function structure...")

    template_file = 'templates/flame/checkout.html'

    if not os.path.exists(template_file):
        print(f"FAIL: {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test function structure
        functions = {
            'loadCities with API-first': 'loadCities: function(stateId, selectedCityId = null)' in content,
            'loadTownships with API-first': 'loadTownships: function(cityId, selectedTownshipId = null)' in content,
            'populateCityDropdown helper': 'populateCityDropdown: function(cities, selectedCityId = null)' in content,
            'populateTownshipDropdown helper': 'populateTownshipDropdown: function(townships, selectedTownshipId = null)' in content,
            'Simplified enableAddressDropdowns': 'enableAddressDropdowns: function()' in content
        }

        all_passed = True
        for func_name, condition in functions.items():
            if condition:
                print(f"PASS: {func_name}")
            else:
                print(f"FAIL: {func_name}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"FAIL: Error reading template: {e}")
        return False

def test_expected_behavior():
    """Test expected behavior patterns"""
    print("\nTesting expected behavior patterns...")

    template_file = 'templates/flame/checkout.html'

    if not os.path.exists(template_file):
        print(f"FAIL: {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test behavior patterns
        behaviors = {
            'Immediate enabling on load': 'citySelect.disabled = false;' in content,
            'Loading state feedback': 'Loading cities...' in content,
            'Error handling with fallback': '.catch(error => {' in content,
            'Graceful offline degradation': 'trying offline data' in content,
            'Clean function separation': 'populateCityDropdown' in content,
            'Consistent logging': 'API success: Loaded' in content
        }

        all_passed = True
        for behavior_name, condition in behaviors.items():
            if condition:
                print(f"PASS: {behavior_name}")
            else:
                print(f"FAIL: {behavior_name}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"FAIL: Error reading template: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("DYNAMIC ADDRESS SELECTION TEST")
    print("=" * 60)

    tests = [
        ('Dynamic Implementation', test_dynamic_implementation),
        ('Function Structure', test_function_structure),
        ('Expected Behavior', test_expected_behavior)
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
    print("DYNAMIC SELECTION TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nSUCCESS: Dynamic address selection is properly implemented!")
        print("\nKEY IMPROVEMENTS:")
        print("✅ API-first approach - immediate dropdown enabling")
        print("✅ Clean offline fallback - only when API fails")
        print("✅ Helper functions - cleaner code organization")
        print("✅ Enhanced debugging - better troubleshooting")
        print("✅ Simplified logic - removed cache dependencies")
        print("\nEXPECTED BEHAVIOR:")
        print("1. Select state → Cities load immediately (enabled)")
        print("2. Select city → Townships load immediately (enabled)")
        print("3. If offline → Graceful fallback to JSON data")
        print("4. Console shows clear success/error messages")
    else:
        print(f"\nFAILED: {len(results) - passed} test(s) failed")

    return passed == len(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)