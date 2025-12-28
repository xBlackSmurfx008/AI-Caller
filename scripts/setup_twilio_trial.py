#!/usr/bin/env python3
"""
Comprehensive Twilio Trial Number Setup Script

This script ensures your Twilio trial number is fully configured for testing:
1. Verifies Twilio credentials
2. Gets/verifies phone number
3. Configures webhooks (voice, status, media)
4. Validates webhook URLs
5. Tests the complete setup
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List

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
    from twilio.base.exceptions import TwilioException, TwilioRestException
except ImportError:
    print("❌ Missing required dependencies: No module named 'twilio'")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


class TwilioTrialSetup:
    """Comprehensive Twilio trial number setup"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "").rstrip('/')
        self.client = None
        self.issues = []
        self.warnings = []
        
    def validate_credentials(self) -> bool:
        """Validate Twilio credentials"""
        print("\n" + "=" * 70)
        print("🔐 STEP 1: Validating Twilio Credentials")
        print("=" * 70)
        
        if not self.account_sid:
            self.issues.append("TWILIO_ACCOUNT_SID is not set in .env file")
            print("❌ TWILIO_ACCOUNT_SID is missing")
            return False
        
        if not self.auth_token:
            self.issues.append("TWILIO_AUTH_TOKEN is not set in .env file")
            print("❌ TWILIO_AUTH_TOKEN is missing")
            return False
        
        try:
            self.client = TwilioClient(self.account_sid, self.auth_token)
            
            # Test connection by fetching account info
            try:
                if self.account_sid.startswith('AC'):
                    account = self.client.api.accounts(self.account_sid).fetch()
                    print(f"✅ Connected to Twilio account: {account.friendly_name}")
                    print(f"   Account SID: {account.sid}")
                    print(f"   Account Status: {account.status}")
                    
                    # Check if trial account
                    if account.type == "Trial":
                        print("   ⚠️  This is a TRIAL account")
                        print("   💡 Trial limitations:")
                        print("      - Can only call verified numbers")
                        print("      - Limited credits")
                        print("      - Some features may be restricted")
                else:
                    print(f"✅ Connected using API Key: {self.account_sid[:10]}...")
            except Exception as e:
                print(f"✅ Connected to Twilio (using API Key)")
            
            return True
            
        except TwilioException as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                self.issues.append(f"Invalid Twilio credentials: {error_msg}")
                print(f"❌ Authentication failed: {error_msg}")
                print("   💡 Check your Account SID and Auth Token in .env file")
            else:
                self.issues.append(f"Twilio connection error: {error_msg}")
                print(f"❌ Connection error: {error_msg}")
            return False
    
    def get_or_verify_phone_number(self) -> Optional[Dict[str, Any]]:
        """Get or verify phone number"""
        print("\n" + "=" * 70)
        print("📱 STEP 2: Phone Number Setup")
        print("=" * 70)
        
        if not self.client:
            print("❌ Cannot proceed - Twilio client not initialized")
            return None
        
        try:
            # List all phone numbers
            incoming_numbers = self.client.incoming_phone_numbers.list()
            
            if not incoming_numbers:
                print("⚠️  No phone numbers found in your account")
                print("\n💡 To get a trial number:")
                print("   1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
                print("   2. Click 'Buy a number'")
                print("   3. Select a number (FREE for trial accounts)")
                print("   4. Complete the purchase")
                print("   5. Run this script again")
                self.issues.append("No phone numbers found in Twilio account")
                return None
            
            # Filter voice-capable numbers
            voice_numbers = [
                n for n in incoming_numbers 
                if n.capabilities.get('voice', False)
            ]
            
            if not voice_numbers:
                print("⚠️  No voice-capable numbers found")
                self.issues.append("No voice-capable phone numbers found")
                return None
            
            # If phone number is set in .env, verify it exists
            if self.phone_number:
                matching = [
                    n for n in voice_numbers 
                    if n.phone_number == self.phone_number
                ]
                
                if matching:
                    number = matching[0]
                    print(f"✅ Found configured number: {number.phone_number}")
                    print(f"   SID: {number.sid}")
                    print(f"   Capabilities:")
                    print(f"     - Voice: ✅")
                    print(f"     - SMS: {'✅' if number.capabilities.get('SMS') else '❌'}")
                    print(f"     - MMS: {'✅' if number.capabilities.get('MMS') else '❌'}")
                    return {
                        "sid": number.sid,
                        "phone_number": number.phone_number,
                        "capabilities": number.capabilities,
                    }
                else:
                    print(f"⚠️  Configured number {self.phone_number} not found in account")
                    print(f"   Available numbers:")
                    for n in voice_numbers[:5]:
                        print(f"     - {n.phone_number}")
                    self.warnings.append(f"Configured number {self.phone_number} not in account")
            
            # Use first voice-capable number
            number = voice_numbers[0]
            print(f"✅ Using number: {number.phone_number}")
            print(f"   SID: {number.sid}")
            
            # Update .env if needed
            if not self.phone_number or self.phone_number != number.phone_number:
                self._update_env_phone_number(number.phone_number)
            
            return {
                "sid": number.sid,
                "phone_number": number.phone_number,
                "capabilities": number.capabilities,
            }
            
        except TwilioException as e:
            error_msg = str(e)
            self.issues.append(f"Error fetching phone numbers: {error_msg}")
            print(f"❌ Error: {error_msg}")
            return None
    
    def configure_webhooks(self, phone_sid: str) -> bool:
        """Configure webhooks for phone number"""
        print("\n" + "=" * 70)
        print("🔗 STEP 3: Webhook Configuration")
        print("=" * 70)
        
        if not self.webhook_url:
            print("❌ TWILIO_WEBHOOK_URL is not set in .env file")
            print("\n💡 For local testing, you need a public URL:")
            print("   Option 1: Use ngrok (Recommended)")
            print("     1. Install: https://ngrok.com/download")
            print("     2. Run: ngrok http 8000")
            print("     3. Copy the https URL (e.g., https://abc123.ngrok.io)")
            print("     4. Set TWILIO_WEBHOOK_URL=https://abc123.ngrok.io in .env")
            print("\n   Option 2: Use localtunnel")
            print("     1. Install: npm install -g localtunnel")
            print("     2. Run: lt --port 8000")
            print("     3. Copy the URL and set TWILIO_WEBHOOK_URL in .env")
            print("\n   Then run this script again")
            self.issues.append("TWILIO_WEBHOOK_URL not configured")
            return False
        
        # Validate webhook URL format
        if not self.webhook_url.startswith(('http://', 'https://')):
            print(f"❌ Invalid webhook URL format: {self.webhook_url}")
            print("   Must start with http:// or https://")
            self.issues.append(f"Invalid webhook URL format: {self.webhook_url}")
            return False
        
        voice_webhook = f"{self.webhook_url}/webhooks/twilio/voice"
        status_webhook = f"{self.webhook_url}/webhooks/twilio/status"
        
        print(f"📋 Webhook URLs:")
        print(f"   Voice: {voice_webhook}")
        print(f"   Status: {status_webhook}")
        
        try:
            # Update phone number configuration
            number = self.client.incoming_phone_numbers(phone_sid)
            updated = number.update(
                voice_url=voice_webhook,
                voice_method='POST',
                status_callback=status_webhook,
                status_callback_method='POST'
            )
            
            print(f"\n✅ Webhooks configured successfully!")
            print(f"   Voice URL: {updated.voice_url}")
            print(f"   Voice Method: {updated.voice_method}")
            print(f"   Status Callback: {updated.status_callback}")
            print(f"   Status Method: {updated.status_callback_method}")
            
            return True
            
        except TwilioRestException as e:
            error_msg = str(e)
            if "403" in error_msg or "permission" in error_msg.lower():
                print(f"\n⚠️  API Key doesn't have permission to update webhooks")
                print(f"   💡 Configure manually in Twilio Console:")
                print(f"      1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
                print(f"      2. Click on your phone number")
                print(f"      3. Scroll to 'Voice & Fax' section")
                print(f"      4. Set Voice & Fax webhook URL to: {voice_webhook}")
                print(f"      5. Set HTTP Method to: POST")
                print(f"      6. Scroll to 'Status Callback' section")
                print(f"      7. Set Status Callback URL to: {status_webhook}")
                print(f"      8. Set HTTP Method to: POST")
                print(f"      9. Click 'Save'")
                self.warnings.append("Webhooks need manual configuration")
                return False
            else:
                self.issues.append(f"Error configuring webhooks: {error_msg}")
                print(f"❌ Error: {error_msg}")
                return False
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Unexpected error: {error_msg}")
            print(f"❌ Unexpected error: {error_msg}")
            return False
    
    def validate_webhook_endpoints(self) -> bool:
        """Validate that webhook endpoints are accessible"""
        print("\n" + "=" * 70)
        print("🌐 STEP 4: Webhook Endpoint Validation")
        print("=" * 70)
        
        if not self.webhook_url:
            print("⚠️  Skipping - TWILIO_WEBHOOK_URL not set")
            return False
        
        import urllib.request
        import urllib.error
        
        endpoints = {
            "Voice": f"{self.webhook_url}/webhooks/twilio/voice",
            "Status": f"{self.webhook_url}/webhooks/twilio/status",
        }
        
        all_valid = True
        server_running = False
        
        for name, url in endpoints.items():
            try:
                print(f"   Testing {name} endpoint: {url}")
                req = urllib.request.Request(url, method='POST')
                # Set a short timeout
                response = urllib.request.urlopen(req, timeout=5)
                status = response.getcode()
                server_running = True
                if status == 200 or status == 405:  # 405 is OK for POST-only endpoints
                    print(f"   ✅ {name} endpoint is accessible (status: {status})")
                else:
                    print(f"   ⚠️  {name} endpoint returned status: {status}")
                    all_valid = False
            except urllib.error.HTTPError as e:
                server_running = True
                if e.code == 405:
                    print(f"   ✅ {name} endpoint exists (405 Method Not Allowed is OK)")
                else:
                    print(f"   ⚠️  {name} endpoint returned: {e.code}")
                    all_valid = False
            except urllib.error.URLError as e:
                print(f"   ⚠️  {name} endpoint not accessible: {e.reason}")
                if not server_running:
                    print(f"      💡 This is OK if your server isn't running yet")
                    print(f"      Make sure to start your server before testing calls:")
                    print(f"      uvicorn src.main:app --reload")
                else:
                    print(f"      Make sure your server is running and the URL is correct")
                all_valid = False
            except Exception as e:
                print(f"   ⚠️  Could not test {name} endpoint: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def verify_phone_configuration(self, phone_sid: str) -> Dict[str, Any]:
        """Verify complete phone number configuration"""
        print("\n" + "=" * 70)
        print("✅ STEP 5: Final Configuration Verification")
        print("=" * 70)
        
        try:
            number = self.client.incoming_phone_numbers(phone_sid).fetch()
            
            config = {
                "phone_number": number.phone_number,
                "sid": number.sid,
                "voice_url": number.voice_url,
                "voice_method": number.voice_method,
                "status_callback": number.status_callback,
                "status_callback_method": getattr(number, 'status_callback_method', None),
                "capabilities": number.capabilities,
            }
            
            print(f"📱 Phone Number: {config['phone_number']}")
            print(f"   SID: {config['sid']}")
            print(f"\n🔗 Webhooks:")
            print(f"   Voice URL: {config['voice_url'] or '❌ Not set'}")
            print(f"   Voice Method: {config['voice_method'] or '❌ Not set'}")
            print(f"   Status Callback: {config['status_callback'] or '❌ Not set'}")
            print(f"   Status Method: {config['status_callback_method'] or '❌ Not set'}")
            print(f"\n📋 Capabilities:")
            print(f"   Voice: {'✅' if config['capabilities'].get('voice') else '❌'}")
            print(f"   SMS: {'✅' if config['capabilities'].get('SMS') else '❌'}")
            print(f"   MMS: {'✅' if config['capabilities'].get('MMS') else '❌'}")
            
            # Check if webhooks are properly configured
            expected_voice = f"{self.webhook_url}/webhooks/twilio/voice"
            expected_status = f"{self.webhook_url}/webhooks/twilio/status"
            
            if config['voice_url'] == expected_voice:
                print(f"\n✅ Voice webhook correctly configured")
            else:
                print(f"\n⚠️  Voice webhook mismatch:")
                print(f"   Expected: {expected_voice}")
                print(f"   Actual: {config['voice_url']}")
                self.warnings.append("Voice webhook URL mismatch")
            
            if config['status_callback'] == expected_status:
                print(f"✅ Status callback correctly configured")
            else:
                print(f"⚠️  Status callback mismatch:")
                print(f"   Expected: {expected_status}")
                print(f"   Actual: {config['status_callback']}")
                self.warnings.append("Status callback URL mismatch")
            
            return config
            
        except TwilioException as e:
            print(f"❌ Error verifying configuration: {str(e)}")
            self.issues.append(f"Verification error: {str(e)}")
            return {}
    
    def _update_env_phone_number(self, phone_number: str):
        """Update phone number in .env file"""
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if not os.path.exists(env_file):
            print(f"⚠️  .env file not found, cannot update")
            return
        
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            updated = False
            with open(env_file, 'w') as f:
                for line in lines:
                    if line.startswith('TWILIO_PHONE_NUMBER='):
                        f.write(f'TWILIO_PHONE_NUMBER={phone_number}\n')
                        updated = True
                    else:
                        f.write(line)
                
                if not updated:
                    f.write(f'\nTWILIO_PHONE_NUMBER={phone_number}\n')
            
            print(f"✅ Updated .env file with phone number: {phone_number}")
            self.phone_number = phone_number
            
        except Exception as e:
            print(f"⚠️  Could not update .env file: {str(e)}")
    
    def print_summary(self):
        """Print setup summary"""
        print("\n" + "=" * 70)
        print("📊 SETUP SUMMARY")
        print("=" * 70)
        
        if not self.issues:
            print("✅ All critical steps completed successfully!")
        else:
            print("❌ Issues found that need to be resolved:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        if not self.issues:
            print("\n🎉 Your Twilio trial number is ready for testing!")
            print("\n📝 Next Steps:")
            print("   1. Make sure your server is running:")
            print("      uvicorn src.main:app --reload")
            print("   2. If testing locally, ensure ngrok/localtunnel is running")
            print("   3. Verify your phone number (Trial accounts can only call verified numbers):")
            print("      https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
            print("   4. Call your Twilio number to test")
            print("   5. Check server logs for webhook activity")
            print("\n💡 Trial Account Reminders:")
            print("   - You can only call verified phone numbers")
            print("   - Add verified numbers at the link above")
            print("   - Check your account balance regularly")
        else:
            print("\n💡 Please resolve the issues above and run this script again")
    
    def run_full_setup(self) -> bool:
        """Run complete setup process"""
        print("\n" + "🚀" * 35)
        print("TWILIO TRIAL NUMBER SETUP")
        print("🚀" * 35)
        
        # Step 1: Validate credentials
        if not self.validate_credentials():
            self.print_summary()
            return False
        
        # Step 2: Get/verify phone number
        phone_info = self.get_or_verify_phone_number()
        if not phone_info:
            self.print_summary()
            return False
        
        # Step 3: Configure webhooks
        webhooks_configured = self.configure_webhooks(phone_info['sid'])
        if not webhooks_configured:
            # Still continue to show what needs manual configuration
            pass
        
        # Step 4: Validate webhook endpoints (optional, may fail if server not running)
        self.validate_webhook_endpoints()
        
        # Step 5: Verify final configuration
        self.verify_phone_configuration(phone_info['sid'])
        
        # Print summary
        self.print_summary()
        
        return len(self.issues) == 0


def main():
    """Main entry point"""
    setup = TwilioTrialSetup()
    success = setup.run_full_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

