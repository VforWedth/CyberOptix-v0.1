#!/usr/bin/env python
"""
Test script for KBZPay Mock Payment Integration
This script tests the mock KBZPay API endpoints
"""

import requests
import json
import time
import hashlib


def generate_signature(params, api_key='6ab2757c99c54f9c882dbb819d2fe8e1'):
    """Generate MD5 signature for KBZPay API"""
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params if v and k != 'sign'])
    sign_string = param_string + api_key
    return hashlib.md5(sign_string.encode()).hexdigest()


def test_precreate_api():
    """Test the precreate API endpoint with enhanced order data"""
    print("\n=== Testing Enhanced KBZPay Mock Precreate API ===")

    # API endpoint
    url = "http://localhost:8000/kbzpay/api/precreate/"

    # Enhanced test data with order details
    order_data = {
        'customer_name': 'John Doe',
        'customer_email': 'john.doe@example.com',
        'order_items': [
            {
                'name': 'Gaming Laptop ASUS ROG',
                'quantity': 1,
                'price': 2500000,
                'total': 2500000
            },
            {
                'name': 'Wireless Mouse',
                'quantity': 2,
                'price': 25000,
                'total': 50000
            }
        ],
        'shipping_address': {
            'state': 'Yangon Region',
            'city': 'Yangon',
            'address': '123 Main Street, Downtown'
        }
    }

    test_order = {
        'partner_id': '2018082000010170',
        'seller_id': '2018082000010170',
        'appid': '2018082000010171',
        'out_trade_no': f'LAPTOP_ORDER_{int(time.time())}',
        'total_amount': '2550000',  # Total from order items
        'currency': 'MMK',
        'subject': 'LaptopMart Order - Gaming Setup',
        'notify_url': 'http://localhost:8000/kbzpay/callback/',
        'order_data': json.dumps(order_data)
    }

    # Add signature
    test_order['sign'] = generate_signature(test_order)

    # Make request
    response = requests.post(url, json=test_order)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if data.get('code') == 'SUCCESS':
            print(f"Enhanced Precreate API test PASSED")
            print(f"Prepay ID: {data['data']['prepay_id']}")
            print(f"QR Code Data: {data['data'].get('qr_code_data', 'N/A')}")
            print(f"Payment URL: http://localhost:8000{data['data']['payment_url']}")
            print(f"Session Timeout: {data['data'].get('session_timeout', 'N/A')}")
            return data['data']['prepay_id']
        else:
            print(f"Precreate API test FAILED: {data.get('msg')}")
    else:
        print(f"Precreate API test FAILED with status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Raw Response: {response.text}")

    return None


def test_query_status_api(prepay_id):
    """Test the query status API endpoint"""
    print("\n=== Testing KBZPay Mock Query Status API ===")

    url = "http://localhost:8000/kbzpay/api/query/"

    test_query = {
        'prepay_id': prepay_id
    }

    response = requests.post(url, json=test_query)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 'SUCCESS':
            print(f"Query Status API test PASSED")
            print(f"Trade Status: {data['data']['trade_status']}")
            return True
        else:
            print(f"Query Status API test FAILED: {data.get('msg')}")
    else:
        print(f"Query Status API test FAILED with status {response.status_code}")

    return False


def test_simulate_payment(prepay_id):
    """Test simulating a successful payment"""
    print("\n=== Testing Payment Simulation ===")

    url = f"http://localhost:8000/kbzpay/simulate/success/{prepay_id}/"

    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 'SUCCESS':
            print(f"Payment simulation PASSED")
            return True
        else:
            print(f"Payment simulation FAILED: {data.get('msg')}")
    else:
        print(f"Payment simulation FAILED with status {response.status_code}")

    return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("KBZPay Mock Payment Integration Test Suite")
    print("=" * 50)

    try:
        # Test 1: Create a payment
        prepay_id = test_precreate_api()

        if prepay_id:
            # Test 2: Query payment status
            test_query_status_api(prepay_id)

            # Test 3: Simulate successful payment
            test_simulate_payment(prepay_id)

            # Test 4: Query status again to verify payment
            print("\n=== Verifying Payment Status After Simulation ===")
            test_query_status_api(prepay_id)

        print("\n" + "=" * 50)
        print("All tests completed!")
        print("=" * 50)

    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to server. Make sure Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nERROR: {str(e)}")


if __name__ == "__main__":
    main()