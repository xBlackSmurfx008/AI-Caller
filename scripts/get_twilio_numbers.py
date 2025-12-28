#!/usr/bin/env python3
"""Script to list available Twilio phone numbers"""

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

# Load environment variables
load_env()

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
except ImportError:
    print("❌ Missing required dependencies: No module named 'twilio'")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

def get_phone_numbers():
    """Get and display available Twilio phone numbers"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials not found in .env file")
        print("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        return
    
    try:
        print("🔍 Connecting to Twilio...")
        client = TwilioClient(account_sid, auth_token)
        
        # Get account info (skip if using API Key)
        try:
            if account_sid.startswith('AC'):
                account = client.api.accounts(account_sid).fetch()
                print(f"✅ Connected to account: {account.friendly_name}")
                print(f"   Account Status: {account.status}\n")
            else:
                print(f"✅ Connected using API Key: {account_sid[:10]}...\n")
        except Exception as e:
            print(f"✅ Connected to Twilio (using API Key)\n")
        
        # List phone numbers
        print("📱 Available Phone Numbers:")
        print("=" * 60)
        
        incoming_numbers = client.incoming_phone_numbers.list()
        
        if not incoming_numbers:
            print("⚠️  No phone numbers found in your account.")
            print("\n🔍 Searching for available phone numbers to purchase...")
            try:
                available_numbers = client.available_phone_numbers('US').local.list(limit=10)
                if available_numbers:
                    import random
                    print(f"   ✅ Found {len(available_numbers)} available numbers!")
                    print("\n   📞 Available Phone Numbers:")
                    for i, number in enumerate(available_numbers[:5], 1):
                        print(f"      {i}. {number.phone_number}")
                    
                    # Select a random one
                    selected = random.choice(available_numbers)
                    print(f"\n   ⭐ Randomly selected: {selected.phone_number}")
                    
                    # Try to purchase programmatically (may require Account SID, not API Key)
                    print(f"\n   🔄 Attempting to purchase {selected.phone_number}...")
                    try:
                        purchased = client.incoming_phone_numbers.create(phone_number=selected.phone_number)
                        print(f"   ✅ Successfully purchased: {purchased.phone_number}!")
                        print(f"   📝 Updating .env file...")
                        
                        # Update .env file
                        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                        if os.path.exists(env_file):
                            with open(env_file, 'r') as f:
                                lines = f.readlines()
                            
                            updated = False
                            with open(env_file, 'w') as f:
                                for line in lines:
                                    if line.startswith('TWILIO_PHONE_NUMBER='):
                                        f.write(f'TWILIO_PHONE_NUMBER={purchased.phone_number}\n')
                                        updated = True
                                    else:
                                        f.write(line)
                                
                                if not updated:
                                    f.write(f'\nTWILIO_PHONE_NUMBER={purchased.phone_number}\n')
                            
                            print(f"   ✅ Updated .env file with: {purchased.phone_number}")
                            return purchased.phone_number
                    except Exception as purchase_error:
                        error_msg = str(purchase_error)
                        if "403" in error_msg or "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                            print(f"   ⚠️  Cannot purchase with Standard API Key (limited permissions).")
                            print(f"   💡 Please purchase manually from Twilio Console:")
                            print(f"      1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/search")
                            print(f"      2. Search for or select: {selected.phone_number}")
                            print(f"      3. Purchase it (free for trial accounts)")
                            print(f"      4. Then run this script again to auto-configure it")
                        else:
                            print(f"   ⚠️  Purchase failed: {error_msg}")
                            print(f"   💡 Please purchase manually from Twilio Console")
                else:
                    print("   ⚠️  No available numbers found. Try a different area code.")
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                    print(f"   ⚠️  API Key doesn't have permission to search/purchase numbers.")
                    print(f"   💡 Please get a phone number manually:")
                    print(f"      1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
                    print(f"      2. Click 'Buy a number'")
                    print(f"      3. Select a number (free for trial accounts)")
                    print(f"      4. Copy the number and update your .env file")
                else:
                    print(f"   ⚠️  Could not check available numbers: {error_msg}")
            return None
        else:
            import random
            # Filter numbers with voice capability (preferred for calls)
            voice_numbers = [n for n in incoming_numbers if n.capabilities.get('voice', False)]
            # Use voice-capable numbers if available, otherwise use any number
            available_numbers = voice_numbers if voice_numbers else incoming_numbers
            selected_number = random.choice(available_numbers)
            
            print(f"📱 Found {len(incoming_numbers)} phone number(s) in your account:")
            print("=" * 60)
            
            for i, number in enumerate(incoming_numbers, 1):
                marker = " ⭐ SELECTED" if number.phone_number == selected_number.phone_number else ""
                print(f"\n{i}. Phone Number: {number.phone_number}{marker}")
                print(f"   SID: {number.sid}")
                print(f"   Friendly Name: {number.friendly_name or 'N/A'}")
                print(f"   Capabilities:")
                print(f"     - Voice: {'✅' if number.capabilities.get('voice', False) else '❌'}")
                print(f"     - SMS: {'✅' if number.capabilities.get('SMS', False) else '❌'}")
                print(f"     - MMS: {'✅' if number.capabilities.get('MMS', False) else '❌'}")
            
            print("\n" + "=" * 60)
            print(f"✅ Randomly selected: {selected_number.phone_number}")
            
            # Update .env file
            env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                updated = False
                with open(env_file, 'w') as f:
                    for line in lines:
                        if line.startswith('TWILIO_PHONE_NUMBER='):
                            f.write(f'TWILIO_PHONE_NUMBER={selected_number.phone_number}\n')
                            updated = True
                        else:
                            f.write(line)
                    
                    if not updated:
                        # Add it if it doesn't exist
                        f.write(f'\nTWILIO_PHONE_NUMBER={selected_number.phone_number}\n')
                
                print(f"✅ Updated .env file with: {selected_number.phone_number}")
            else:
                print(f"⚠️  .env file not found. Please manually set:")
                print(f"   TWILIO_PHONE_NUMBER={selected_number.phone_number}")
            
            return selected_number.phone_number
            
    except TwilioException as e:
        print(f"❌ Twilio API error: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   💡 Check that your Account SID and Auth Token are correct")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    get_phone_numbers()

