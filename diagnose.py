#!/usr/bin/env python3
"""
Diagnostic script to check if the Flask app loads correctly
"""
import sys
import traceback

print("=" * 60)
print("DIAGNOSING FLASK APP STARTUP")
print("=" * 60)

# Check environment
print("\n1. Checking environment variables...")
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ["SUPABASE_PASSWORD", "ENVIRONMENT"]
for var in required_vars:
    value = os.environ.get(var)
    if value:
        print(f"   ✓ {var} = {value[:20]}..." if len(str(value)) > 20 else f"   ✓ {var} = {value}")
    else:
        print(f"   ✗ {var} is NOT set")

# Check imports
print("\n2. Checking imports...")
try:
    from flask import Flask
    print("   ✓ Flask imported")
except Exception as e:
    print(f"   ✗ Flask import failed: {e}")
    sys.exit(1)

try:
    from app import create_app
    print("   ✓ create_app imported")
except Exception as e:
    print(f"   ✗ create_app import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Try to create app
print("\n3. Creating Flask app...")
try:
    app = create_app()
    print("   ✓ App created successfully")
except Exception as e:
    print(f"   ✗ App creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Check routes
print("\n4. Checking routes...")
try:
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(str(rule))
    
    print(f"   ✓ Found {len(routes)} routes")
    
    # Show first 10 routes
    print("\n   First 10 routes:")
    for i, route in enumerate(sorted(routes)[:10]):
        print(f"      {i+1}. {route}")
    
    if len(routes) > 10:
        print(f"      ... and {len(routes) - 10} more routes")
    
    # Check if home route exists
    if any('/' in route and 'static' not in route for route in routes):
        print("\n   ✓ Home route (/) found")
    else:
        print("\n   ✗ Home route (/) NOT found!")
        
except Exception as e:
    print(f"   ✗ Route inspection failed: {e}")
    traceback.print_exc()

# Check templates
print("\n5. Checking templates...")
try:
    import os
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if os.path.exists(template_dir):
        templates = os.listdir(template_dir)
        print(f"   ✓ Templates directory found with {len(templates)} items:")
        for t in templates[:5]:
            print(f"      - {t}")
        if len(templates) > 5:
            print(f"      ... and {len(templates) - 5} more")
    else:
        print(f"   ✗ Templates directory NOT found at {template_dir}")
except Exception as e:
    print(f"   ✗ Template inspection failed: {e}")

# Check database connection
print("\n6. Testing database connection...")
try:
    with app.app_context():
        from sqlalchemy import text
        result = app.config.get("SQLALCHEMY_DATABASE_URI", "NOT SET")
        print(f"   Database URI: {result[:50]}..." if len(str(result)) > 50 else f"   Database URI: {result}")
        
        # Try to execute a simple query
        try:
            from models import User
            user_count = User.query.count()
            print(f"   ✓ Database connection working (Found {user_count} users)")
        except Exception as db_error:
            print(f"   ⚠ Database query failed: {str(db_error)[:100]}")
            print(f"     This might be expected if DB is not yet seeded")
except Exception as e:
    print(f"   ✗ Database check failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
print("\nTo start the app, run: python main.py")
print("Then visit: http://localhost:5000")
