"""Utilities for parsing contact data from various formats (vCard, CSV, Contact Picker API)"""

import csv
import io
import re
from typing import List, Dict, Optional, Any
import vobject


def parse_vcard(vcard_content: str) -> List[Dict[str, Any]]:
    """
    Parse vCard (.vcf) file content into list of contact dictionaries
    
    Args:
        vcard_content: String content of vCard file
        
    Returns:
        List of contact dictionaries with keys: name, phone_number, email, organization, notes
    """
    contacts = []
    
    try:
        # vobject can parse multiple vCards separated by blank lines
        vcards = vobject.readComponents(vcard_content)
        
        for vcard in vcards:
            contact = {
                "name": "",
                "phone_number": None,
                "email": None,
                "organization": None,
                "notes": None,
            }
            
            # Extract name
            if hasattr(vcard, 'fn') and vcard.fn.value:
                contact["name"] = vcard.fn.value
            elif hasattr(vcard, 'n'):
                name_parts = []
                if vcard.n.value.given:
                    name_parts.append(vcard.n.value.given)
                if vcard.n.value.family:
                    name_parts.append(vcard.n.value.family)
                contact["name"] = " ".join(name_parts) if name_parts else "Unknown"
            
            # Extract phone numbers (take first one)
            if hasattr(vcard, 'tel_list') and vcard.tel_list:
                phone = vcard.tel_list[0].value
                # Clean phone number (remove non-digits except +)
                phone = re.sub(r'[^\d+]', '', phone)
                if phone:
                    # Ensure E.164 format (add + if not present and it's a valid number)
                    if not phone.startswith('+') and phone[0].isdigit():
                        # Assume US number if starts with 1, otherwise add +1
                        if len(phone) == 10:
                            phone = f"+1{phone}"
                        elif len(phone) == 11 and phone[0] == '1':
                            phone = f"+{phone}"
                    contact["phone_number"] = phone
            
            # Extract email (take first one)
            if hasattr(vcard, 'email_list') and vcard.email_list:
                contact["email"] = vcard.email_list[0].value
            
            # Extract organization
            if hasattr(vcard, 'org') and vcard.org.value:
                if isinstance(vcard.org.value, list):
                    contact["organization"] = " ".join(vcard.org.value)
                else:
                    contact["organization"] = str(vcard.org.value)
            
            # Extract notes
            if hasattr(vcard, 'note') and vcard.note.value:
                contact["notes"] = vcard.note.value
            
            # Only add contact if it has at least a name
            if contact["name"]:
                contacts.append(contact)
                
    except Exception as e:
        # If parsing fails, return empty list
        import logging
        logging.getLogger(__name__).error(f"Failed to parse vCard: {e}")
        return []
    
    return contacts


def parse_csv(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV file content into list of contact dictionaries
    
    Expected CSV format:
    - Headers: name, phone_number, email, organization, notes (or variations)
    - At minimum: name column required
    
    Args:
        csv_content: String content of CSV file
        
    Returns:
        List of contact dictionaries
    """
    contacts = []
    
    try:
        # Try to detect delimiter
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(csv_content[:1024]).delimiter
        
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        
        # Normalize column names (case-insensitive, handle variations)
        field_mapping = {
            'name': ['name', 'full name', 'fullname', 'contact name'],
            'phone_number': ['phone_number', 'phone', 'phone number', 'mobile', 'tel'],
            'email': ['email', 'e-mail', 'email address'],
            'organization': ['organization', 'org', 'company', 'work'],
            'notes': ['notes', 'note', 'comments', 'description'],
        }
        
        for row in reader:
            contact = {
                "name": "",
                "phone_number": None,
                "email": None,
                "organization": None,
                "notes": None,
            }
            
            # Map fields
            for field, possible_names in field_mapping.items():
                for col_name in row.keys():
                    if col_name.lower().strip() in [n.lower() for n in possible_names]:
                        value = row[col_name].strip() if row[col_name] else None
                        if value:
                            # Clean phone numbers
                            if field == "phone_number":
                                value = re.sub(r'[^\d+]', '', value)
                                if value and not value.startswith('+'):
                                    if len(value) == 10:
                                        value = f"+1{value}"
                                    elif len(value) == 11 and value[0] == '1':
                                        value = f"+{value}"
                            contact[field] = value
                            break
            
            # Only add contact if it has at least a name
            if contact["name"]:
                contacts.append(contact)
                
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to parse CSV: {e}")
        return []
    
    return contacts


def normalize_contact_picker_data(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize contact data from Contact Picker API to our contact format
    
    Args:
        contact_data: Contact data from navigator.contacts.select()
        
    Returns:
        Normalized contact dictionary
    """
    contact = {
        "name": "",
        "phone_number": None,
        "email": None,
        "organization": None,
        "notes": None,
    }
    
    # Extract name
    if contact_data.get("name"):
        if isinstance(contact_data["name"], list) and len(contact_data["name"]) > 0:
            contact["name"] = " ".join(contact_data["name"])
        else:
            contact["name"] = str(contact_data["name"])
    
    # Extract phone (take first one)
    if contact_data.get("tel"):
        if isinstance(contact_data["tel"], list) and len(contact_data["tel"]) > 0:
            phone = contact_data["tel"][0]
            if isinstance(phone, dict):
                phone = phone.get("value", phone.get("number", ""))
            phone = re.sub(r'[^\d+]', '', str(phone))
            if phone:
                if not phone.startswith('+'):
                    if len(phone) == 10:
                        phone = f"+1{phone}"
                    elif len(phone) == 11 and phone[0] == '1':
                        phone = f"+{phone}"
                contact["phone_number"] = phone
    
    # Extract email (take first one)
    if contact_data.get("email"):
        if isinstance(contact_data["email"], list) and len(contact_data["email"]) > 0:
            email = contact_data["email"][0]
            if isinstance(email, dict):
                email = email.get("value", email.get("address", ""))
            contact["email"] = str(email)
    
    # Extract organization
    if contact_data.get("org"):
        contact["organization"] = str(contact_data["org"])
    
    return contact

