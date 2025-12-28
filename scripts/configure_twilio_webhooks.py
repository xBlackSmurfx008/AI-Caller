#!/usr/bin/env python3
"""Script to configure Twilio webhooks for phone numbers"""

import os
import sys

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
except ImportError:
    print("❌ Missing required dependencies: No module named 'twilio'")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

def configure_webhooks():
    """Configure webhooks for Twilio phone numbers"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "").rstrip('/')
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials not found in .env file")
        return
    
    if not webhook_url:
        print("⚠️  TWILIO_WEBHOOK_URL not set in .env file")
        print("\n💡 For local development, you can use ngrok:")
        print("   1. Install ngrok: https://ngrok.com/download")
        print("   2. Run: ngrok http 8000")
        print("   3. Copy the https URL (e.g., https://abc123.ngrok.io)")
        print("   4. Set TWILIO_WEBHOOK_URL in .env file")
        print("\n   For production, use your actual domain URL")
        return
    
    try:
        print("🔍 Connecting to Twilio...")
        client = TwilioClient(account_sid, auth_token)
        
        # Get all phone numbers
        print("📱 Fetching phone numbers...")
        incoming_numbers = client.incoming_phone_numbers.list()
        
        if not incoming_numbers:
            print("⚠️  No phone numbers found in your account")
            return
        
        # Webhook URLs
        voice_webhook = f"{webhook_url}/webhooks/twilio/voice"
        status_webhook = f"{webhook_url}/webhooks/twilio/status"
        
        print(f"\n🔗 Webhook URLs:")
        print(f"   Voice: {voice_webhook}")
        print(f"   Status: {status_webhook}")
        print("\n" + "=" * 60)
        
        updated_count = 0
        for number in incoming_numbers:
            print(f"\n📞 Configuring: {number.phone_number}")
            
            try:
                # Update webhooks
                updated = number.update(
                    voice_url=voice_webhook,
                    voice_method='POST',
                    status_callback=status_webhook,
                    status_callback_method='POST'
                )
                
                print(f"   ✅ Successfully configured webhooks!")
                print(f"      - Voice URL: {updated.voice_url}")
                print(f"      - Status Callback: {updated.status_callback}")
                updated_count += 1
                
            except TwilioException as e:
                error_msg = str(e)
                if "403" in error_msg or "permission" in error_msg.lower():
                    print(f"   ⚠️  API Key doesn't have permission to update webhooks")
                    print(f"   💡 Please configure manually in Twilio Console:")
                    print(f"      1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
                    print(f"      2. Click on: {number.phone_number}")
                    print(f"      3. Set Voice & Fax webhook URL to: {voice_webhook}")
                    print(f"      4. Set Status Callback URL to: {status_webhook}")
                else:
                    print(f"   ❌ Error: {error_msg}")
        
        print("\n" + "=" * 60)
        if updated_count > 0:
            print(f"✅ Successfully configured webhooks for {updated_count} number(s)")
        else:
            print("⚠️  No webhooks were updated")
            print("\n💡 Manual Configuration:")
            print(f"   1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
            print(f"   2. For each phone number, set:")
            print(f"      - Voice & Fax webhook URL: {voice_webhook}")
            print(f"      - Status Callback URL: {status_webhook}")
        
    except TwilioException as e:
        print(f"❌ Twilio API error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    configure_webhooks()

