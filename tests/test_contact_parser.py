"""Unit tests for contact parser utilities"""

import pytest
from src.utils.contact_parser import parse_vcard, parse_csv, normalize_contact_picker_data


class TestParseVCard:
    """Tests for vCard parsing"""
    
    def test_parse_simple_vcard(self):
        """Test parsing a simple vCard"""
        vcard_content = """BEGIN:VCARD
VERSION:3.0
FN:John Doe
TEL:+1234567890
EMAIL:john@example.com
ORG:Acme Corp
NOTE:Test contact
END:VCARD"""
        
        contacts = parse_vcard(vcard_content)
        
        assert len(contacts) == 1
        assert contacts[0]["name"] == "John Doe"
        assert contacts[0]["phone_number"] == "+1234567890"
        assert contacts[0]["email"] == "john@example.com"
        assert contacts[0]["organization"] == "Acme Corp"
        assert contacts[0]["notes"] == "Test contact"
    
    def test_parse_vcard_with_name_parts(self):
        """Test parsing vCard with separate name parts"""
        vcard_content = """BEGIN:VCARD
VERSION:3.0
N:Doe;John;;;
TEL:+1234567890
END:VCARD"""
        
        contacts = parse_vcard(vcard_content)
        
        assert len(contacts) == 1
        assert contacts[0]["name"] == "John Doe"
    
    def test_parse_multiple_vcards(self):
        """Test parsing multiple vCards"""
        vcard_content = """BEGIN:VCARD
VERSION:3.0
FN:John Doe
TEL:+1234567890
END:VCARD

BEGIN:VCARD
VERSION:3.0
FN:Jane Smith
TEL:+0987654321
END:VCARD"""
        
        contacts = parse_vcard(vcard_content)
        
        assert len(contacts) == 2
        assert contacts[0]["name"] == "John Doe"
        assert contacts[1]["name"] == "Jane Smith"
    
    def test_parse_vcard_phone_normalization(self):
        """Test phone number normalization in vCard"""
        vcard_content = """BEGIN:VCARD
VERSION:3.0
FN:John Doe
TEL:1234567890
END:VCARD"""
        
        contacts = parse_vcard(vcard_content)
        
        assert len(contacts) == 1
        assert contacts[0]["phone_number"] == "+11234567890"
    
    def test_parse_invalid_vcard(self):
        """Test parsing invalid vCard returns empty list"""
        vcard_content = "Invalid vCard content"
        
        contacts = parse_vcard(vcard_content)
        
        assert len(contacts) == 0


class TestParseCSV:
    """Tests for CSV parsing"""
    
    def test_parse_simple_csv(self):
        """Test parsing a simple CSV"""
        csv_content = """name,phone_number,email,organization
John Doe,+1234567890,john@example.com,Acme Corp"""
        
        contacts = parse_csv(csv_content)
        
        assert len(contacts) == 1
        assert contacts[0]["name"] == "John Doe"
        assert contacts[0]["phone_number"] == "+1234567890"
        assert contacts[0]["email"] == "john@example.com"
        assert contacts[0]["organization"] == "Acme Corp"
    
    def test_parse_csv_flexible_columns(self):
        """Test CSV parsing with different column names"""
        csv_content = """Full Name,Phone,Email Address,Company
John Doe,1234567890,john@example.com,Acme Corp"""
        
        contacts = parse_csv(csv_content)
        
        assert len(contacts) == 1
        assert contacts[0]["name"] == "John Doe"
        assert contacts[0]["phone_number"] == "+11234567890"
        assert contacts[0]["email"] == "john@example.com"
        assert contacts[0]["organization"] == "Acme Corp"
    
    def test_parse_csv_phone_normalization(self):
        """Test phone number normalization in CSV"""
        csv_content = """name,phone
John Doe,1234567890"""
        
        contacts = parse_csv(csv_content)
        
        assert len(contacts) == 1
        assert contacts[0]["phone_number"] == "+11234567890"
    
    def test_parse_csv_multiple_contacts(self):
        """Test parsing multiple contacts from CSV"""
        csv_content = """name,phone,email
John Doe,+1234567890,john@example.com
Jane Smith,+0987654321,jane@example.com"""
        
        contacts = parse_csv(csv_content)
        
        assert len(contacts) == 2
        assert contacts[0]["name"] == "John Doe"
        assert contacts[1]["name"] == "Jane Smith"
    
    def test_parse_csv_missing_name(self):
        """Test CSV parsing skips contacts without names"""
        csv_content = """name,phone,email
,+1234567890,john@example.com
Jane Smith,+0987654321,jane@example.com"""
        
        contacts = parse_csv(csv_content)
        
        assert len(contacts) == 1
        assert contacts[0]["name"] == "Jane Smith"


class TestNormalizeContactPickerData:
    """Tests for Contact Picker API data normalization"""
    
    def test_normalize_simple_contact(self):
        """Test normalizing simple contact data"""
        contact_data = {
            "name": "John Doe",
            "tel": ["+1234567890"],
            "email": ["john@example.com"],
            "org": "Acme Corp"
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["name"] == "John Doe"
        assert normalized["phone_number"] == "+1234567890"
        assert normalized["email"] == "john@example.com"
        assert normalized["organization"] == "Acme Corp"
    
    def test_normalize_name_array(self):
        """Test normalizing name as array"""
        contact_data = {
            "name": ["John", "Doe"],
            "tel": ["+1234567890"]
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["name"] == "John Doe"
    
    def test_normalize_phone_object(self):
        """Test normalizing phone as object"""
        contact_data = {
            "name": "John Doe",
            "tel": [{"value": "+1234567890"}]
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["phone_number"] == "+1234567890"
    
    def test_normalize_phone_normalization(self):
        """Test phone number normalization"""
        contact_data = {
            "name": "John Doe",
            "tel": ["1234567890"]
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["phone_number"] == "+11234567890"
    
    def test_normalize_email_object(self):
        """Test normalizing email as object"""
        contact_data = {
            "name": "John Doe",
            "email": [{"value": "john@example.com"}]
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["email"] == "john@example.com"
    
    def test_normalize_missing_fields(self):
        """Test normalizing contact with missing fields"""
        contact_data = {
            "name": "John Doe"
        }
        
        normalized = normalize_contact_picker_data(contact_data)
        
        assert normalized["name"] == "John Doe"
        assert normalized["phone_number"] is None
        assert normalized["email"] is None

