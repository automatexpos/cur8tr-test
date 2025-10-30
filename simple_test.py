#!/usr/bin/env python3
"""Simple test to check if Flask home page loads"""
from app import create_app

print("Creating Flask app...")
app = create_app()

print("Creating test client...")
client = app.test_client()

print("Testing GET /...")
response = client.get('/')

print(f"Status Code: {response.status_code}")
print(f"Response Size: {len(response.data)} bytes")

if response.status_code == 200:
    print("SUCCESS - Home page loaded successfully!")
else:
    print(f"FAILED - Got status {response.status_code}")
    print("\nResponse:")
    print(response.data.decode('utf-8', errors='ignore')[:1000])
