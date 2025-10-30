#!/usr/bin/env python3
"""
Email Test Script for Cur8tr

This script helps you test the email functionality before using it in the application.
Make sure to set your environment variables before running this script.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_configuration():
    """Test if email configuration is properly set"""
    app_email = os.environ.get('APP_EMAIL')
    app_password = os.environ.get('APP_PASSWORD')
    admin_email = os.environ.get('ADMIN_EMAIL')
    
    print("=== Email Configuration Test ===")
    print(f"APP_EMAIL: {'✓ Set' if app_email else '✗ Not set'}")
    print(f"APP_PASSWORD: {'✓ Set' if app_password else '✗ Not set'}")
    print(f"ADMIN_EMAIL: {'✓ Set' if admin_email else '✗ Not set'}")
    
    if not (app_email and app_password):
        print("\n❌ Error: APP_EMAIL and APP_PASSWORD must be set!")
        print("Please check your .env file or environment variables.")
        return False
    
    print("\n✅ Configuration looks good!")
    return True

def test_send_email():
    """Test sending a verification email"""
    from utils import send_verification_email
    
    if not test_email_configuration():
        return
    
    # Get test email address
    test_email = input("\nEnter email address to test (or press Enter to use admin email): ").strip()
    if not test_email:
        test_email = os.environ.get('ADMIN_EMAIL')
        if not test_email:
            print("No test email provided and ADMIN_EMAIL not set.")
            return
    
    print(f"\nSending test verification email to: {test_email}")
    
    # Generate test code
    import random
    import string
    test_code = ''.join(random.choices(string.digits, k=6))
    
    # Send email
    success = send_verification_email(test_email, test_code, "Test User")
    
    if success:
        print(f"✅ Email sent successfully!")
        print(f"Test verification code: {test_code}")
        print(f"Check {test_email} for the verification email.")
    else:
        print(f"❌ Failed to send email. Check the logs for error details.")

if __name__ == "__main__":
    print("Cur8tr Email Test Script")
    print("========================")
    
    try:
        test_send_email()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()