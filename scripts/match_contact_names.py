#!/usr/bin/env python3
"""
Script to analyze contacts and their messages to match names to phone numbers.
"""
import os
import re
import json
import requests
from typing import Optional

API_URL = os.environ.get("AI_CALLER_API_URL", "https://ai-caller-ten.vercel.app")
AUTH_TOKEN = os.environ.get("AI_CALLER_AUTH_TOKEN", "ai-caller-auth-2025-secure")

HEADERS = {"X-Auth-Token": AUTH_TOKEN}

# Known service patterns (sender name: patterns to match)
SERVICE_PATTERNS = {
    "Coinbase": [r"coinbase", r"c.?o.?i.?n.?b.?a.?s.?e"],
    "DoorDash": [r"doordash", r"your dasher", r"your order from"],
    "Uber": [r"uber", r"your uber"],
    "Uber Eats": [r"uber eats", r"ubereats"],
    "Lyft": [r"lyft"],
    "Amazon": [r"amazon", r"your amazon"],
    "Pizza Hut": [r"pizza hut", r"pizzahut"],
    "Dominos": [r"domino", r"dominos"],
    "Grubhub": [r"grubhub"],
    "Postmates": [r"postmates"],
    "Instacart": [r"instacart"],
    "Target": [r"target"],
    "Walmart": [r"walmart"],
    "CVS": [r"cvs pharmacy", r"cvs:"],
    "Walgreens": [r"walgreens"],
    "Bank of America": [r"bank of america", r"bofa"],
    "Chase": [r"chase bank", r"jpmorgan chase"],
    "Wells Fargo": [r"wells fargo"],
    "Venmo": [r"venmo"],
    "PayPal": [r"paypal"],
    "Cash App": [r"cash app", r"cashapp"],
    "Apple": [r"apple id", r"apple pay"],
    "Google": [r"google verification", r"google:"],
    "Microsoft": [r"microsoft"],
    "Netflix": [r"netflix"],
    "Spotify": [r"spotify"],
    "FedEx": [r"fedex"],
    "UPS": [r"ups:"],
    "USPS": [r"usps"],
    "WhatsApp": [r"whatsapp"],
    "Telegram": [r"telegram"],
    "Signal": [r"signal:"],
    "Twitter/X": [r"twitter", r"@x.com"],
    "Instagram": [r"instagram"],
    "Facebook": [r"facebook", r"meta:"],
    "LinkedIn": [r"linkedin"],
    "Snapchat": [r"snapchat"],
    "TikTok": [r"tiktok"],
    "Discord": [r"discord"],
    "Slack": [r"slack"],
    "Zoom": [r"zoom"],
    "Ring": [r"ring doorbell", r"ring.com"],
    "ADT": [r"adt security"],
    "Airbnb": [r"airbnb"],
    "VRBO": [r"vrbo"],
    "Expedia": [r"expedia"],
    "Delta": [r"delta air"],
    "United": [r"united airlines"],
    "American Airlines": [r"american airlines"],
    "Southwest": [r"southwest"],
    "JetBlue": [r"jetblue"],
    "Hilton": [r"hilton"],
    "Marriott": [r"marriott"],
    "Hyatt": [r"hyatt"],
}

# Pattern to extract person names from delivery/ride messages
PERSON_NAME_PATTERNS = [
    r"your (?:driver|dasher|courier|shopper) (\w+)",
    r"(\w+) (?:is approaching|has arrived|will arrive|is on the way)",
    r"(\w+), your (?:driver|dasher|courier)",
    r"(?:meet|contact) (\w+) at",
    r"(\w+) has confirmed",
    r"(\w+) is delivering",
    r"delivered by (\w+)",
]


def get_contacts():
    """Fetch all contacts from the API."""
    response = requests.get(f"{API_URL}/api/contacts/", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_contact_interactions(contact_id: str):
    """Fetch interactions for a specific contact."""
    response = requests.get(
        f"{API_URL}/api/memory/contacts/{contact_id}/interactions?limit=100",
        headers=HEADERS
    )
    if response.status_code == 404:
        return {"items": []}
    response.raise_for_status()
    return response.json()


def identify_name_from_content(content: str) -> Optional[str]:
    """Try to identify a name from message content."""
    content_lower = content.lower()
    
    # First, check for known services
    for service_name, patterns in SERVICE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return service_name
    
    # Check for person names in delivery messages
    for pattern in PERSON_NAME_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            name = match.group(1)
            # Filter out common false positives
            if name.lower() not in ["your", "the", "a", "an", "is", "has", "will"]:
                return name.title()
    
    return None


def update_contact_name(contact_id: str, name: str):
    """Update a contact's name."""
    response = requests.put(
        f"{API_URL}/api/contacts/{contact_id}",
        headers=HEADERS,
        json={"name": name}
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Fetching contacts...")
    contacts = get_contacts()
    print(f"Found {len(contacts)} contacts\n")
    
    updates = []
    
    for contact in contacts:
        contact_id = contact["id"]
        current_name = contact["name"]
        phone = contact["phone_number"]
        
        # Skip if already has a proper name (not a phone number)
        if current_name and not current_name.startswith("+"):
            print(f"✓ {phone} -> {current_name} (already named)")
            continue
        
        print(f"\nAnalyzing {phone}...")
        
        # Get interactions for this contact
        interactions_data = get_contact_interactions(contact_id)
        interactions = interactions_data.get("items", [])
        
        if not interactions:
            print(f"  No interactions found")
            continue
        
        # Analyze all messages to find a name
        identified_name = None
        for interaction in interactions:
            content = interaction.get("raw_content", "")
            name = identify_name_from_content(content)
            if name:
                identified_name = name
                print(f"  Found name '{name}' in message:")
                print(f"    \"{content[:100]}...\"" if len(content) > 100 else f"    \"{content}\"")
                break
        
        if identified_name:
            updates.append({
                "contact_id": contact_id,
                "phone": phone,
                "current_name": current_name,
                "new_name": identified_name
            })
    
    print("\n" + "="*60)
    print("SUMMARY: Names to update")
    print("="*60)
    
    if not updates:
        print("No names could be automatically identified.")
        return
    
    for update in updates:
        print(f"  {update['phone']} -> {update['new_name']}")
    
    print(f"\nTotal: {len(updates)} contacts to update")
    
    # Ask for confirmation
    confirm = input("\nProceed with updates? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\nUpdating contacts...")
        for update in updates:
            try:
                update_contact_name(update["contact_id"], update["new_name"])
                print(f"  ✓ Updated {update['phone']} -> {update['new_name']}")
            except Exception as e:
                print(f"  ✗ Failed to update {update['phone']}: {e}")
        print("\nDone!")
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()

