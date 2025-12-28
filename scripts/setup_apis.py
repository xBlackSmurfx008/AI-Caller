#!/usr/bin/env python3
"""
Setup and test script for Twilio and OpenAI API configuration.
This script helps verify that your API credentials are correctly configured.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from openai import OpenAI
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def load_env_file() -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("⚠️  No .env file found. Please create one from .env.example")
        return env_vars
    
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def test_openai(api_key: str) -> Dict[str, Any]:
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI API...")
    
    if not api_key or api_key.startswith("sk-your-") or api_key == "":
        return {
            "success": False,
            "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
        }
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test 1: List models
        print("  → Testing model list access...")
        models = client.models.list()
        model_count = len(list(models))
        
        # Test 2: Simple completion test
        print("  → Testing API completion...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for testing
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=20
        )
        
        message = response.choices[0].message.content
        
        print(f"  ✅ OpenAI API connection successful!")
        print(f"     - Available models: {model_count}")
        print(f"     - Test response: {message}")
        
        return {
            "success": True,
            "models_available": model_count,
            "test_response": message
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ OpenAI API test failed: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def test_twilio(account_sid: str, auth_token: str, phone_number: str = None) -> Dict[str, Any]:
    """Test Twilio API connection"""
    print("\n🔍 Testing Twilio API...")
    
    if not account_sid or account_sid.startswith("ACxx") or account_sid == "":
        return {
            "success": False,
            "error": "Twilio Account SID not configured. Please set TWILIO_ACCOUNT_SID in .env"
        }
    
    if not auth_token or auth_token == "":
        return {
            "success": False,
            "error": "Twilio Auth Token not configured. Please set TWILIO_AUTH_TOKEN in .env"
        }
    
    try:
        client = TwilioClient(account_sid, auth_token)
        
        # Test 1: Try to fetch account info (works with Account SID, not API Key)
        account_name = None
        account_status = None
        is_api_key = account_sid.startswith('SK')
        
        if is_api_key:
            print("  → Testing API Key access...")
            print("     (Using API Key - account info not available)")
        else:
            print("  → Testing account access...")
            try:
                account = client.api.accounts(account_sid).fetch()
                account_name = account.friendly_name
                account_status = account.status
            except Exception as e:
                print(f"     ⚠️  Could not fetch account info: {str(e)}")
        
        # Test 2: List phone numbers (works with both Account SID and API Key)
        print("  → Fetching phone numbers...")
        incoming_phone_numbers = client.incoming_phone_numbers.list(limit=5)
        phone_numbers = [num.phone_number for num in incoming_phone_numbers]
        
        # Test 3: Verify configured phone number (if provided)
        phone_valid = False
        if phone_number:
            print(f"  → Verifying configured phone number: {phone_number}")
            phone_valid = phone_number in phone_numbers or any(
                num.phone_number == phone_number for num in incoming_phone_numbers
            )
            if not phone_valid:
                # Try to find it in all numbers
                all_numbers = client.incoming_phone_numbers.list()
                phone_valid = any(num.phone_number == phone_number for num in all_numbers)
        
        print(f"  ✅ Twilio API connection successful!")
        if account_name:
            print(f"     - Account Name: {account_name}")
            print(f"     - Account Status: {account_status}")
        else:
            print(f"     - Using API Key: {account_sid[:10]}...")
        print(f"     - Phone Numbers Found: {len(phone_numbers)}")
        if phone_number:
            status = "✅ Valid" if phone_valid else "⚠️  Not found in first 5 numbers"
            print(f"     - Configured Number ({phone_number}): {status}")
        
        return {
            "success": True,
            "account_name": account_name or "API Key",
            "account_status": account_status or "active",
            "phone_numbers": phone_numbers,
            "configured_phone_valid": phone_valid if phone_number else None
        }
        
    except TwilioException as e:
        error_msg = str(e)
        print(f"  ❌ Twilio API test failed: {error_msg}")
        
        # Provide helpful error messages
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg += "\n     💡 Tip: Check that your Account SID and Auth Token are correct"
        elif "404" in error_msg:
            error_msg += "\n     💡 Tip: Verify your Account SID is correct"
        
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Twilio API test failed: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def main():
    """Main setup and test function"""
    print("=" * 60)
    print("🚀 AI Caller - API Setup & Test Script")
    print("=" * 60)
    
    # Load environment variables
    env_vars = load_env_file()
    
    # Get API credentials
    openai_key = env_vars.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    twilio_sid = env_vars.get("TWILIO_ACCOUNT_SID") or os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = env_vars.get("TWILIO_AUTH_TOKEN") or os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = env_vars.get("TWILIO_PHONE_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
    
    # Run tests
    results = {
        "openai": test_openai(openai_key),
        "twilio": test_twilio(twilio_sid, twilio_token, twilio_phone)
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    openai_status = "✅ PASS" if results["openai"]["success"] else "❌ FAIL"
    twilio_status = "✅ PASS" if results["twilio"]["success"] else "❌ FAIL"
    
    print(f"OpenAI API:  {openai_status}")
    print(f"Twilio API:  {twilio_status}")
    
    if results["openai"]["success"] and results["twilio"]["success"]:
        print("\n🎉 All API tests passed! You're ready to use AI Caller.")
        return 0
    else:
        print("\n⚠️  Some API tests failed. Please check your configuration.")
        print("\n📝 Next steps:")
        if not results["openai"]["success"]:
            print("   1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
            print("   2. Add it to your .env file as OPENAI_API_KEY=sk-...")
        if not results["twilio"]["success"]:
            print("   1. Get your Twilio credentials from: https://console.twilio.com/")
            print("   2. Add them to your .env file:")
            print("      - TWILIO_ACCOUNT_SID=AC...")
            print("      - TWILIO_AUTH_TOKEN=...")
            print("      - TWILIO_PHONE_NUMBER=+1...")
        return 1


if __name__ == "__main__":
    sys.exit(main())

