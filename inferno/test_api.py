"""
Simple test script to verify API functionality
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def test_api_endpoints():
    """
    Test basic API endpoints
    """
    print("Testing Django REST Framework API Implementation")
    print("=" * 50)
    
    # Test API documentation endpoint
    print("1. Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs/")
        if response.status_code == 200:
            print("[OK] API Documentation accessible")
        else:
            print(f"[FAIL] API Documentation failed: {response.status_code}")
    except requests.RequestException as e:
        print(f"[ERROR] API Documentation error: {e}")
    
    # Test products list endpoint
    print("\n2. Testing Products List Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/products/")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Products endpoint working - Found {len(data.get('results', []))} products")
            if data.get('results'):
                print(f"   Sample product: {data['results'][0].get('title', 'N/A')}")
        else:
            print(f"[FAIL] Products endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"[ERROR] Products endpoint error: {e}")
    
    # Test products search endpoint
    print("\n3. Testing Products Search Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/products/search/?q=laptop")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Search endpoint working - Found {len(data)} results for 'laptop'")
        else:
            print(f"[FAIL] Search endpoint failed: {response.status_code}")
    except requests.RequestException as e:
        print(f"[ERROR] Search endpoint error: {e}")
    
    # Test authentication endpoints
    print("\n4. Testing Authentication Endpoints...")
    try:
        # Test user registration
        registration_data = {
            "username": f"testuser_{int(__import__('time').time())}",
            "email": f"test_{int(__import__('time').time())}@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register/", json=registration_data)
        if response.status_code == 201:
            print("[OK] User registration endpoint working")
            
            # Test login with new user
            login_data = {
                "username": registration_data["username"],
                "password": registration_data["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
            if login_response.status_code == 200:
                token_data = login_response.json()
                print("[OK] Login endpoint working")
                print(f"   Access token received: {token_data.get('access', 'N/A')[:20]}...")
                
                # Test authenticated endpoint
                headers = {'Authorization': f'Bearer {token_data.get("access")}'}
                profile_response = requests.get(f"{BASE_URL}/auth/user/", headers=headers)
                if profile_response.status_code == 200:
                    print("[OK] Authenticated user info endpoint working")
                else:
                    print(f"[FAIL] User info endpoint failed: {profile_response.status_code}")
            else:
                print(f"[FAIL] Login endpoint failed: {login_response.status_code}")
        else:
            print(f"[FAIL] Registration endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"[ERROR] Authentication endpoints error: {e}")
    
    print("\n" + "=" * 50)
    print("API Test Complete!")
    print("\nAvailable API Endpoints:")
    print(f"   Documentation: {BASE_URL}/docs/")
    print(f"   Products: {BASE_URL}/products/")
    print(f"   Search: {BASE_URL}/products/search/?q=laptop")
    print(f"   Login: {BASE_URL}/auth/login/")
    print(f"   Register: {BASE_URL}/auth/register/")
    print(f"   Schema: {BASE_URL}/schema/")

if __name__ == "__main__":
    test_api_endpoints()