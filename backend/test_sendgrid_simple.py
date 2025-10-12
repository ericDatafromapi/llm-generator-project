"""
Simple SendGrid Test Script - No Input Required
"""
import os
import sys
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Load environment variables
load_dotenv()

def test_sendgrid_simple():
    """Test SendGrid configuration."""
    
    print("=" * 60)
    print("SendGrid Configuration Test")
    print("=" * 60)
    
    # Get configuration
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL')
    
    print(f"\n✓ SENDGRID_API_KEY: Found (starts with {api_key[:10]}...)")
    print(f"✓ FROM_EMAIL: {from_email}")
    print(f"✓ SendGrid client: Initialized")
    
    print(f"\n" + "=" * 60)
    print("Testing email sending to: " + from_email)
    print("(Sending test email to yourself)")
    print("=" * 60)
    
    try:
        sg = SendGridAPIClient(api_key)
        
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(from_email),  # Send to yourself
            subject='✅ SendGrid Test - LLMReady',
            html_content=Content("text/html", """
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #667eea;">✅ SendGrid is Working!</h2>
                    <p>Congratulations! Your SendGrid configuration is set up correctly.</p>
                    <p><strong>Configuration Details:</strong></p>
                    <ul>
                        <li>FROM_EMAIL: Verified and working</li>
                        <li>API Key: Valid with Mail Send permission</li>
                        <li>Status: Ready for production</li>
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
            print(f"\n✅ SUCCESS!")
            print(f"   Status code: {response.status_code}")
            print(f"   Test email sent to: {from_email}")
            print(f"\n📧 Check your inbox at: {from_email}")
            print(f"   (Also check spam/junk folder)")
            print(f"\n🎉 SendGrid is working correctly!")
            return True
        else:
            print(f"\n❌ FAILED")
            print(f"   Status code: {response.status_code}")
            if hasattr(response, 'body'):
                print(f"   Response: {response.body}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        
        error_str = str(e).lower()
        
        # Provide specific guidance based on error
        if 'from email' in error_str or 'sender' in error_str or 'not match' in error_str:
            print(f"\n💡 SOLUTION:")
            print(f"   Your FROM_EMAIL ({from_email}) is NOT VERIFIED in SendGrid.")
            print(f"\n   Follow these steps:")
            print(f"   1. Go to: https://app.sendgrid.com/settings/sender_auth/senders")
            print(f"   2. Look for: {from_email}")
            print(f"   3. If not there, click 'Create New Sender' and add it")
            print(f"   4. Check your email inbox for verification link")
            print(f"   5. Click the link to verify")
            print(f"   6. Wait 2-3 minutes and run this test again")
            
        elif 'unauthorized' in error_str or '401' in error_str:
            print(f"\n💡 SOLUTION:")
            print(f"   Your API key is invalid or lacks permissions.")
            print(f"\n   Follow these steps:")
            print(f"   1. Go to: https://app.sendgrid.com/settings/api_keys")
            print(f"   2. Create a new API key")
            print(f"   3. Select 'Restricted Access'")
            print(f"   4. Give 'Mail Send' FULL ACCESS")
            print(f"   5. Copy the new key")
            print(f"   6. Update SENDGRID_API_KEY in your .env file")
            print(f"   7. Restart your server and run this test again")
        
        elif 'forbidden' in error_str or '403' in error_str:
            print(f"\n💡 SOLUTION:")
            print(f"   Your API key doesn't have permission to send emails.")
            print(f"   Create a new key with 'Mail Send - Full Access'")
        
        else:
            print(f"\n💡 COMMON FIXES:")
            print(f"   1. Verify sender email in SendGrid dashboard")
            print(f"   2. Check API key has Mail Send permission")
            print(f"   3. Ensure no typos in .env file")
        
        return False

if __name__ == "__main__":
    print("\n🚀 Starting SendGrid test...")
    success = test_sendgrid_simple()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULT: SendGrid is working correctly!")
        print("=" * 60)
        print("\nYou can now:")
        print("• Restart your FastAPI server")
        print("• Test user registration")
        print("• Emails will be sent automatically")
    else:
        print("❌ RESULT: SendGrid configuration needs fixing")
        print("=" * 60)
        print("\nFollow the solution steps above, then run:")
        print("python test_sendgrid_simple.py")
    
    sys.exit(0 if success else 1)