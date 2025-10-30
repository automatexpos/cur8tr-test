#!/usr/bin/env python3
"""
Test script to simulate loading the Flask app and making requests
"""
import sys
import traceback
from app import create_app

print("=" * 70)
print("TESTING FLASK APP - SIMULATING PAGE LOAD")
print("=" * 70)

try:
    print("\n1. Creating Flask app...")
    app = create_app()
    print("   ✓ App created")
    
    print("\n2. Creating test client...")
    client = app.test_client()
    print("   ✓ Test client created")
    
    print("\n3. Testing GET / (home page)...")
    response = client.get('/')
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    print(f"   Response Size: {len(response.data)} bytes")
    
    if response.status_code == 200:
        print("   ✓ Home page returned successfully (200 OK)")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
    
    # Check if response has content
    if response.data:
        response_text = response.data.decode('utf-8', errors='ignore')
        
        # Look for common HTML markers
        checks = [
            ('<html', 'HTML root element'),
            ('<head', 'Head section'),
            ('<body', 'Body section'),
            ('<title', 'Title tag'),
            ('<!DOCTYPE', 'DOCTYPE declaration'),
            ('Cur8tr', 'App name reference'),
        ]
        
        print("\n4. Checking HTML content...")
        for marker, description in checks:
            if marker.lower() in response_text.lower():
                print(f"   ✓ Found: {description}")
            else:
                print(f"   ✗ Missing: {description}")
        
        # Show first 500 chars of response
        print("\n5. First 500 characters of response:")
        print("   " + "-" * 60)
        for line in response_text[:500].split('\n'):
            if line.strip():
                print(f"   {line[:60]}")
        print("   " + "-" * 60)
        
        # Check for errors in response
        error_keywords = ['error', 'exception', 'traceback', 'failed', '500', '404']
        found_errors = [kw for kw in error_keywords if kw in response_text.lower()]
        
        if found_errors:
            print(f"\n6. ⚠ WARNINGS - Found error keywords in response: {found_errors}")
            # Find and print the error section
            print("\n   Full response content:")
            print("   " + "-" * 60)
            print(response_text[:2000])
            print("   " + "-" * 60)
        else:
            print("\n6. ✓ No error keywords found in response")
    else:
        print("\n4. ✗ Response is empty!")
    
    # Test a few other routes
    print("\n7. Testing other routes...")
    test_routes = [
        ('/auth/login', 'Login page'),
        ('/auth/register', 'Register page'),
        ('/api/recommendations', 'API endpoint'),
    ]
    
    for route, description in test_routes:
        try:
            r = client.get(route)
            status_symbol = '✓' if r.status_code in [200, 302, 401, 403] else '✗'
            print(f"   {status_symbol} {route}: {r.status_code} ({description})")
        except Exception as e:
            print(f"   ✗ {route}: {str(e)[:50]}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nIf all tests passed with status 200, the app is working correctly.")
    print("Try these steps:")
    print("  1. Make sure Flask is running: python main.py")
    print("  2. Open http://localhost:5000 in your browser")
    print("  3. Press Ctrl+Shift+R to do a hard refresh")
    print("  4. Check browser console (F12) for any JavaScript errors")
    
except Exception as e:
    print(f"\n✗ TEST FAILED WITH ERROR:")
    print(f"{type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
