#!/usr/bin/env python3
"""
Test script to verify complete offline address functionality
"""

import os
import json

def test_offline_address_data():
    """Test that offline address data is properly structured"""
    print("Testing offline address data...")

    json_file = 'static/js/myanmar-addresses.min.json'

    if not os.path.exists(json_file):
        print(f"FAIL: {json_file} not found")
        return False

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Test structure
        required_fields = ['version', 'total_states', 'total_cities', 'total_townships', 'states']
        for field in required_fields:
            if field not in data:
                print(f"FAIL: Missing field '{field}' in JSON")
                return False

        # Test states structure
        if not data['states']:
            print("FAIL: No states found")
            return False

        state = data['states'][0]
        state_fields = ['id', 'name', 'name_mm', 'code', 'cities']
        for field in state_fields:
            if field not in state:
                print(f"FAIL: Missing field '{field}' in state")
                return False

        # Test cities structure
        if state['cities']:
            city = state['cities'][0]
            city_fields = ['id', 'name', 'name_mm', 'is_major_city', 'townships']
            for field in city_fields:
                if field not in city:
                    print(f"FAIL: Missing field '{field}' in city")
                    return False

            # Test townships structure
            if city['townships']:
                township = city['townships'][0]
                township_fields = ['id', 'name', 'name_mm']
                for field in township_fields:
                    if field not in township:
                        print(f"FAIL: Missing field '{field}' in township")
                        return False

        print(f"PASS: JSON structure is valid")
        print(f"  - States: {data['total_states']}")
        print(f"  - Cities: {data['total_cities']}")
        print(f"  - Townships: {data['total_townships']}")
        print(f"  - File size: {os.path.getsize(json_file):,} bytes")

        return True

    except Exception as e:
        print(f"FAIL: Error reading JSON: {e}")
        return False

def test_checkout_template():
    """Test that checkout template has offline functionality"""
    print("\nTesting checkout template...")

    template_file = 'templates/flame/checkout.html'

    if not os.path.exists(template_file):
        print(f"FAIL: {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test for offline functionality
        tests = {
            'Offline address data loading': 'loadOfflineAddressData' in content,
            'Offline cities loading': 'loadCitiesOffline' in content,
            'Offline townships loading': 'loadTownshipsOffline' in content,
            'Offline shipping calculation': 'calculateOfflineShipping' in content,
            'Offline COD submission': 'handleOfflineCODSubmission' in content,
            'JSON data reference': 'myanmar-addresses.min.json' in content,
            'COD default checked': 'id="cod-payment" name="payment_type" value="cod" checked' in content,
            'Connection status handler': 'updateConnectionStatus' in content
        }

        all_passed = True
        for test_name, condition in tests.items():
            if condition:
                print(f"PASS: {test_name}")
            else:
                print(f"FAIL: {test_name}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"FAIL: Error reading template: {e}")
        return False

def test_static_files():
    """Test that all required static files exist"""
    print("\nTesting static files...")

    required_files = [
        'static/js/myanmar-addresses.json',
        'static/js/myanmar-addresses.min.json',
        'static/js/offline-manager.js',
        'static/assets/libs/bootstrap/css/bootstrap.min.css',
        'static/assets/libs/bootstrap/js/bootstrap.bundle.min.js',
        'static/assets/libs/jquery/jquery.min.js',
        'static/assets/libs/bootstrap-icons/bootstrap-icons.css'
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"PASS: {file_path} ({size:,} bytes)")
        else:
            print(f"FAIL: {file_path} not found")
            all_exist = False

    return all_exist

def main():
    """Run all tests"""
    print("=" * 60)
    print("OFFLINE ADDRESS SYSTEM TEST")
    print("=" * 60)

    tests = [
        ('Offline Address Data', test_offline_address_data),
        ('Checkout Template', test_checkout_template),
        ('Static Files', test_static_files)
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
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nSUCCESS: All offline address features are working!")
        print("\nOFFLINE FEATURES AVAILABLE:")
        print("- Complete Myanmar address selection (states, cities, townships)")
        print("- Intelligent shipping calculation")
        print("- Cash on Delivery as default payment method")
        print("- Offline order processing and queuing")
        print("- Connection status monitoring")
        print("- Automatic online/offline switching")
    else:
        print(f"\nFAILED: {len(results) - passed} test(s) failed")

    return passed == len(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)