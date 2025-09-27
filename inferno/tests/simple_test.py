import requests

base_url = "http://127.0.0.1:8000"

print("Testing PWA Implementation...")
print("=" * 40)

# Test manifest
try:
    response = requests.get(f"{base_url}/manifest.json", timeout=5)
    print(f"Manifest: HTTP {response.status_code}")
    if response.status_code == 200:
        manifest = response.json()
        print(f"  App name: {manifest.get('name', 'Not set')}")
        print(f"  Icons: {len(manifest.get('icons', []))}")
except Exception as e:
    print(f"Manifest error: {e}")

# Test service worker
try:
    response = requests.get(f"{base_url}/serviceworker.js", timeout=5)
    print(f"Service Worker: HTTP {response.status_code}")
except Exception as e:
    print(f"Service Worker error: {e}")

# Test offline page
try:
    response = requests.get(f"{base_url}/en/offline/", timeout=5)
    print(f"Offline page: HTTP {response.status_code}")
except Exception as e:
    print(f"Offline page error: {e}")

print("\nDone! If all show HTTP 200, PWA is working!")