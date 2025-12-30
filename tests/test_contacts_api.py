"""Unit tests for contacts API routes"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.database import Base, get_db
from src.database.models import Contact
from src.main import app

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestContactsAPI:
    """Tests for contacts API endpoints"""
    
    def test_create_contact(self, client, db_session):
        """Test creating a contact"""
        response = client.post(
            "/api/contacts/",
            json={
                "name": "John Doe",
                "phone_number": "+1234567890",
                "email": "john@example.com",
                "organization": "Acme Corp"
            },
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["phone_number"] == "+1234567890"
        assert data["email"] == "john@example.com"
        assert "id" in data
    
    def test_create_contact_phone_normalization(self, client, db_session):
        """Test phone number normalization on create"""
        response = client.post(
            "/api/contacts/",
            json={
                "name": "John Doe",
                "phone_number": "1234567890"
            },
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+11234567890"
    
    def test_list_contacts(self, client, db_session):
        """Test listing contacts"""
        # Create test contacts
        contact1 = Contact(name="John Doe", phone_number="+1234567890")
        contact2 = Contact(name="Jane Smith", phone_number="+0987654321")
        db_session.add(contact1)
        db_session.add(contact2)
        db_session.commit()
        
        response = client.get(
            "/api/contacts/",
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(c["name"] == "John Doe" for c in data)
        assert any(c["name"] == "Jane Smith" for c in data)
    
    def test_search_contacts(self, client, db_session):
        """Test searching contacts"""
        contact1 = Contact(name="John Doe", phone_number="+1234567890")
        contact2 = Contact(name="Jane Smith", phone_number="+0987654321")
        db_session.add(contact1)
        db_session.add(contact2)
        db_session.commit()
        
        response = client.get(
            "/api/contacts/?search=John",
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "John Doe"
    
    def test_get_contact(self, client, db_session):
        """Test getting a single contact"""
        contact = Contact(name="John Doe", phone_number="+1234567890")
        db_session.add(contact)
        db_session.commit()
        contact_id = contact.id
        
        response = client.get(
            f"/api/contacts/{contact_id}",
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["id"] == contact_id
    
    def test_get_contact_not_found(self, client, db_session):
        """Test getting non-existent contact"""
        response = client.get(
            "/api/contacts/non-existent-id",
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 404
    
    def test_update_contact(self, client, db_session):
        """Test updating a contact"""
        contact = Contact(name="John Doe", phone_number="+1234567890")
        db_session.add(contact)
        db_session.commit()
        contact_id = contact.id
        
        response = client.put(
            f"/api/contacts/{contact_id}",
            json={"name": "John Updated", "email": "newemail@example.com"},
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Updated"
        assert data["email"] == "newemail@example.com"
        assert data["phone_number"] == "+1234567890"  # Unchanged
    
    def test_delete_contact(self, client, db_session):
        """Test deleting a contact"""
        contact = Contact(name="John Doe", phone_number="+1234567890")
        db_session.add(contact)
        db_session.commit()
        contact_id = contact.id
        
        response = client.delete(
            f"/api/contacts/{contact_id}",
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify contact is deleted
        get_response = client.get(
            f"/api/contacts/{contact_id}",
            headers={"X-User-ID": "test_user"}
        )
        assert get_response.status_code == 404
    
    def test_bulk_create_contacts(self, client, db_session):
        """Test bulk creating contacts"""
        response = client.post(
            "/api/contacts/bulk",
            json={
                "contacts": [
                    {"name": "John Doe", "phone_number": "+1234567890"},
                    {"name": "Jane Smith", "phone_number": "+0987654321"}
                ]
            },
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(c["name"] == "John Doe" for c in data)
        assert any(c["name"] == "Jane Smith" for c in data)
    
    def test_bulk_create_max_limit(self, client, db_session):
        """Test bulk create enforces maximum limit"""
        contacts = [{"name": f"Contact {i}"} for i in range(1001)]
        
        response = client.post(
            "/api/contacts/bulk",
            json={"contacts": contacts},
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 400
        assert "Maximum" in response.json()["detail"]
    
    def test_upload_vcard_file_size_limit(self, client, db_session):
        """Test vCard upload enforces file size limit"""
        # Create a file larger than 10MB
        large_content = "BEGIN:VCARD\n" + "A" * (11 * 1024 * 1024) + "\nEND:VCARD"
        
        response = client.post(
            "/api/contacts/upload/vcard",
            files={"file": ("test.vcf", large_content, "text/vcard")},
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 400
        assert "File size exceeds" in response.json()["detail"]
    
    def test_upload_csv_file_size_limit(self, client, db_session):
        """Test CSV upload enforces file size limit"""
        # Create a file larger than 10MB
        large_content = "name,phone\n" + "A," * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/contacts/upload/csv",
            files={"file": ("test.csv", large_content, "text/csv")},
            headers={"X-User-ID": "test_user"}
        )
        
        assert response.status_code == 400
        assert "File size exceeds" in response.json()["detail"]

