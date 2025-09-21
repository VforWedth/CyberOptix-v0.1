#!/usr/bin/env python3
"""
Test script to verify PWA implementation
"""
import requests
import json
import os

def test_pwa_endpoints():
    """Test PWA endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("Testing PWA Implementation...")
    print("=" * 50)

    # Test 1: PWA Manifest
    print("1. Testing PWA Manifest...")
    try:
        response = requests.get(f"{base_url}/manifest.json", timeout=5)
        if response.status_code == 200:
            manifest = response.json()
            print(f"   [OK] Manifest accessible: {len(manifest)} keys")
            print(f"   [OK] App name: {manifest.get('name', 'Not set')}")
            print(f"   [OK] Theme color: {manifest.get('theme_color', 'Not set')}")
            print(f"   [OK] Icons: {len(manifest.get('icons', []))} found")
        else:
            print(f"   [FAIL] Manifest failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Manifest error: {e}")

    # Test 2: Service Worker
    print("\n2. Testing Service Worker...")
    try:
        response = requests.get(f"{base_url}/serviceworker.js", timeout=5)
        if response.status_code == 200:
            print(f"   [OK] Service Worker accessible: {len(response.text)} characters")
            if "LaptopMart" in response.text:
                print("   [OK] Service Worker contains app-specific content")
            else:
                print("   [WARN] Service Worker might be generic")
        else:
            print(f"   [FAIL] Service Worker failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Service Worker error: {e}")

    # Test 3: Offline Page
    print("\n3. Testing Offline Page...")
    try:
        response = requests.get(f"{base_url}/en/offline/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Offline page accessible")
            if "offline" in response.text.lower():
                print("   ✅ Offline page contains offline content")
            else:
                print("   ⚠️ Offline page might not be properly configured")
        else:
            print(f"   ❌ Offline page failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Offline page error: {e}")

    # Test 4: Static Assets
    print("\n4. Testing Static Assets...")
    static_files = [
        "/static/js/serviceworker.js",
        "/static/js/offline-manager.js",
        "/static/images/icons/icon-192x192.png",
        "/static/images/icons/favicon.ico"
    ]

    for file_path in static_files:
        try:
            response = requests.get(f"{base_url}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {file_path} - OK")
            else:
                print(f"   ❌ {file_path} - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {file_path} - Error: {e}")

    # Test 5: Icon Files
    print("\n5. Testing Generated Icons...")
    icon_dir = "static/images/icons"
    if os.path.exists(icon_dir):
        icons = [f for f in os.listdir(icon_dir) if f.endswith('.png') or f.endswith('.ico')]
        print(f"   ✅ Found {len(icons)} icon files")

        required_icons = ['icon-192x192.png', 'icon-512x512.png', 'favicon.ico']
        for icon in required_icons:
            if icon in icons:
                print(f"   ✅ {icon} - Found")
            else:
                print(f"   ❌ {icon} - Missing")
    else:
        print(f"   ❌ Icon directory not found: {icon_dir}")

    print("\n" + "=" * 50)
    print("🎯 PWA Testing Complete!")
    print("\nNext Steps:")
    print("1. Open browser and visit http://127.0.0.1:8000")
    print("2. Check browser DevTools > Application > Manifest")
    print("3. Check DevTools > Application > Service Workers")
    print("4. Try going offline and visiting /en/offline/")
    print("5. Test 'Add to Home Screen' functionality")

if __name__ == "__main__":
    test_pwa_endpoints()