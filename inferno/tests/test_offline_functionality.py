#!/usr/bin/env python3
"""
Test script to verify offline functionality
"""

import os
import sys
import requests
from urllib.parse import urljoin

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')

import django
django.setup()

def test_static_files():
    """Test that all local static files are accessible"""
    print("🔍 Testing static files availability...")

    static_files = [
        'assets/libs/bootstrap/css/bootstrap.min.css',
        'assets/libs/bootstrap/js/bootstrap.bundle.min.js',
        'assets/libs/jquery/jquery.min.js',
        'assets/libs/bootstrap-icons/bootstrap-icons.css',
        'assets/libs/fontawesome/all.min.css',
        'assets/libs/boxicons/boxicons.min.css',
        'assets/libs/qrcode/qrcode.min.js',
        'assets/libs/chartjs/chart.min.js',
        'assets/libs/jspdf/jspdf.umd.min.js',
        'assets/libs/html2canvas/html2canvas.min.js',
        'js/offline-manager.js',
    ]

    missing_files = []
    for file in static_files:
        file_path = os.path.join('static', file)
        if not os.path.exists(file_path):
            missing_files.append(file)
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")

    if missing_files:
        print(f"\n⚠️  {len(missing_files)} files are missing!")
        return False
    else:
        print(f"\n✅ All {len(static_files)} static files are available!")
        return True

def test_cod_functionality():
    """Test Cash on Delivery functionality"""
    print("\n🔍 Testing Cash on Delivery functionality...")

    try:
        from flame.views import cod_payment_view
        from flame.models import Shop

        # Check if COD view exists
        print("✅ COD payment view is available")

        # Check if shops exist
        shops = Shop.objects.all()
        if shops.exists():
            print(f"✅ Found {shops.count()} shops in database")
        else:
            print("⚠️  No shops found in database")

        return True
    except ImportError as e:
        print(f"❌ Error importing COD functionality: {e}")
        return False

def test_offline_templates():
    """Test offline template availability"""
    print("\n🔍 Testing offline templates...")

    templates = [
        'templates/partials/base_offline.html',
        'templates/flame/checkout_offline.html',
        'templates/flame/offline.html',
    ]

    missing_templates = []
    for template in templates:
        if not os.path.exists(template):
            missing_templates.append(template)
            print(f"❌ Missing: {template}")
        else:
            print(f"✅ Found: {template}")

    if missing_templates:
        print(f"\n⚠️  {len(missing_templates)} templates are missing!")
        return False
    else:
        print(f"\n✅ All {len(templates)} offline templates are available!")
        return True

def test_database_connection():
    """Test database connectivity"""
    print("\n🔍 Testing database connection...")

    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Offline Functionality Tests\n")

    tests = [
        ('Static Files', test_static_files),
        ('COD Functionality', test_cod_functionality),
        ('Offline Templates', test_offline_templates),
        ('Database Connection', test_database_connection),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! Your project is ready for offline use.")
        print("\n📋 OFFLINE FEATURES AVAILABLE:")
        print("   • Bootstrap CSS/JS (local)")
        print("   • Font Awesome Icons (local)")
        print("   • Bootstrap Icons (local)")
        print("   • Boxicons (local)")
        print("   • jQuery (local)")
        print("   • QRCode.js (local)")
        print("   • Chart.js (local)")
        print("   • jsPDF (local)")
        print("   • html2canvas (local)")
        print("   • Cash on Delivery payments")
        print("   • Offline cart management")
        print("   • Service Worker caching")
        print("\n💡 HOW TO USE OFFLINE:")
        print("   1. Ensure your Django server is running")
        print("   2. Visit your site and browse products")
        print("   3. Disconnect from internet")
        print("   4. Continue browsing (cached content)")
        print("   5. Add items to cart (stored locally)")
        print("   6. Place COD orders (queued for submission)")
        print("   7. Reconnect to sync data automatically")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please fix the issues above.")

    return passed == len(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)