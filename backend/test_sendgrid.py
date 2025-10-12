"""
SendGrid Configuration Test Script
Run this to verify your SendGrid setup is working correctly.
"""
import os
import sys
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Load environment variables
load_dotenv()

def test_sendgrid():
    """Test SendGrid configuration and send a test email."""
    
    print("=" * 60)
    print("SendGrid Configuration Test")
    print("=" * 60)
    
    # Check environment variables
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL')
    
    print(f"\n1. Checking environment variables...")
    print(f"   SENDGRID_API_KEY: {'✓ Found' if api_key else '✗ Missing'}")
    if api_key:
        print(f"   Key starts with: {api_key[:10]}...")
    print(f"   FROM_EMAIL: {from_email if from_email else '✗ Missing'}")
    
    if not api_key or not from_email:
        print("\n❌ Error: Missing required environment variables!")
        print("   Please check your .env file.")
        return False
    
    # Validate API key format
    if not api_key.startswith('SG.'):
        print("\n⚠️  Warning: API key doesn't start with 'SG.'")
        print("   This might not be a valid SendGrid API key.")
    
    # Test SendGrid connection
    print(f"\n2. Testing SendGrid connection...")
    try:
        sg = SendGridAPIClient(api_key)
        print("   ✓ SendGrid client initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize SendGrid client: {e}")
        return False
    
    # Prompt for test email
    print(f"\n3. Sending test email...")
    test_recipient = input("   Enter your email to receive test (or press Enter to skip): ").strip()
    
    if not test_recipient:
        print("   Skipped test email sending")
        return True
    
    # Create and send test email
    try:
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(test_recipient),
            subject='SendGrid Test Email - LLMReady',
            html_content=Content("text/html", """
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #667eea;">✅ SendGrid is Working!</h2>
                    <p>Congratulations! Your SendGrid configuration is set up correctly.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Send verification emails</li>
                        <li>Send password reset emails</li>
                        <li>Send generation complete notifications</li>
                    </ul>
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        This is a test email from LLMReady authentication system.
                    </p>
                </body>
                </html>
            """)
        )
        
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"   ✓ Test email sent successfully!")
            print(f"   Status code: {response.status_code}")
            print(f"   Check your inbox: {test_recipient}")
            print(f"   (Also check spam/junk folder)")
            return True
        else:
            print(f"   ✗ Failed to send test email")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.body}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error sending test email: {e}")
        if hasattr(e, 'body'):
            print(f"   Error details: {e.body}")
        
        # Common error messages
        error_str = str(e).lower()
        if 'from email' in error_str or 'sender' in error_str:
            print(f"\n💡 Common Fix:")
            print(f"   Your FROM_EMAIL ({from_email}) is not verified in SendGrid.")
            print(f"   Go to: https://app.sendgrid.com/settings/sender_auth/senders")
            print(f"   And verify this email address.")
        elif 'unauthorized' in error_str or '401' in error_str:
            print(f"\n💡 Common Fix:")
            print(f"   Your API key is invalid or doesn't have Mail Send permission.")
            print(f"   Create a new API key with 'Mail Send - Full Access':")
            print(f"   https://app.sendgrid.com/settings/api_keys")
        
        return False

def main():
    """Run the test."""
    success = test_sendgrid()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SendGrid Configuration: WORKING")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Restart your FastAPI server")
        print("2. Test user registration")
        print("3. Check that verification emails are sent")
    else:
        print("❌ SendGrid Configuration: FAILED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review SENDGRID_SETUP_GUIDE.md")
        print("2. Verify sender email in SendGrid dashboard")
        print("3. Check API key permissions")
        print("4. Run this script again")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())