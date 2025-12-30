"""Contacts routes for managing user contacts"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import re
from datetime import datetime

from src.database.database import get_db
from src.database.models import Contact
from src.utils.contact_parser import parse_vcard, parse_csv, normalize_contact_picker_data
from src.utils.logging import get_logger
from src.utils.rate_limit import limiter, get_rate_limit
from src.utils.auth import require_user_id, filter_by_user

logger = get_logger(__name__)
router = APIRouter()

# File size limits (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BULK_CONTACTS = 1000  # Maximum contacts per bulk operation


class ContactCreate(BaseModel):
    name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactResponse(BaseModel):
    id: str
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkContactsCreate(BaseModel):
    contacts: List[ContactCreate]


def validate_phone_number(phone: Optional[str]) -> Optional[str]:
    """Validate and normalize phone number to E.164 format"""
    if not phone:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Basic E.164 validation: + followed by 1-15 digits
    if cleaned.startswith('+'):
        if re.match(r'^\+[1-9]\d{1,14}$', cleaned):
            return cleaned
    elif cleaned.isdigit():
        # Try to format as US number
        if len(cleaned) == 10:
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"+{cleaned}"
    
    return None


@router.get("/", response_model=List[ContactResponse])
@limiter.limit(get_rate_limit("contacts_list"))
async def list_contacts(
    request: Request,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """List all contacts with optional search"""
    # Enforce max limit
    if limit > 1000:
        limit = 1000
    
    query = db.query(Contact)
    query = filter_by_user(query, user_id, Contact, db)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Contact.name.ilike(search_term),
                Contact.phone_number.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.organization.ilike(search_term)
            )
        )
    
    contacts = query.order_by(Contact.name).offset(skip).limit(limit).all()
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
@limiter.limit(get_rate_limit("contacts_list"))
async def get_contact(
    request: Request,
    contact_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Get a specific contact by ID"""
    query = db.query(Contact).filter(Contact.id == contact_id)
    query = filter_by_user(query, user_id, Contact, db)
    contact = query.first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse)
@limiter.limit(get_rate_limit("contacts_create"))
async def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Create a new contact"""
    # Validate phone number if provided
    phone_number = validate_phone_number(contact.phone_number)
    if contact.phone_number and not phone_number:
        logger.warning(f"Invalid phone number format: {contact.phone_number}")
    
    db_contact = Contact(
        name=contact.name,
        phone_number=phone_number,
        email=contact.email,
        organization=contact.organization,
        notes=contact.notes,
        tags=contact.tags or []
    )
    
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    
    logger.info(f"contact_created", contact_id=db_contact.id, name=db_contact.name, user_id=user_id)
    return db_contact


@router.post("/bulk", response_model=List[ContactResponse])
@limiter.limit(get_rate_limit("contacts_bulk"))
async def bulk_create_contacts(
    request: Request,
    data: BulkContactsCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Create multiple contacts at once"""
    # Enforce max bulk size
    if len(data.contacts) > MAX_BULK_CONTACTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_CONTACTS} contacts allowed per bulk operation"
        )
    
    created_contacts = []
    
    for contact_data in data.contacts:
        phone_number = validate_phone_number(contact_data.phone_number)
        
        db_contact = Contact(
            name=contact_data.name,
            phone_number=phone_number,
            email=contact_data.email,
            organization=contact_data.organization,
            notes=contact_data.notes,
            tags=contact_data.tags or []
        )
        db.add(db_contact)
        created_contacts.append(db_contact)
    
    db.commit()
    
    for contact in created_contacts:
        db.refresh(contact)
    
    logger.info(f"bulk_contacts_created", count=len(created_contacts), user_id=user_id)
    return created_contacts


@router.put("/{contact_id}", response_model=ContactResponse)
@limiter.limit(get_rate_limit("contacts_update"))
async def update_contact(
    request: Request,
    contact_id: str,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Update an existing contact"""
    query = db.query(Contact).filter(Contact.id == contact_id)
    query = filter_by_user(query, user_id, Contact, db)
    db_contact = query.first()
    
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Update fields if provided
    if contact.name is not None:
        db_contact.name = contact.name
    if contact.phone_number is not None:
        db_contact.phone_number = validate_phone_number(contact.phone_number)
    if contact.email is not None:
        db_contact.email = contact.email
    if contact.organization is not None:
        db_contact.organization = contact.organization
    if contact.notes is not None:
        db_contact.notes = contact.notes
    if contact.tags is not None:
        db_contact.tags = contact.tags
    
    db.commit()
    db.refresh(db_contact)
    
    logger.info(f"contact_updated", contact_id=contact_id, user_id=user_id)
    return db_contact


@router.delete("/{contact_id}")
@limiter.limit(get_rate_limit("contacts_delete"))
async def delete_contact(
    request: Request,
    contact_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Delete a contact"""
    query = db.query(Contact).filter(Contact.id == contact_id)
    query = filter_by_user(query, user_id, Contact, db)
    contact = query.first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(contact)
    db.commit()
    
    logger.info(f"contact_deleted", contact_id=contact_id, user_id=user_id)
    return {"success": True, "message": "Contact deleted"}


@router.post("/upload/vcard")
@limiter.limit(get_rate_limit("contacts_upload"))
async def upload_vcard(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Upload and parse vCard file"""
    try:
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        vcard_content = content.decode('utf-8', errors='ignore')
        
        contacts_data = parse_vcard(vcard_content)
        
        if not contacts_data:
            raise HTTPException(status_code=400, detail="No contacts found in vCard file")
        
        # Create contacts in database
        created_contacts = []
        for contact_data in contacts_data:
            phone_number = validate_phone_number(contact_data.get("phone_number"))
            
            db_contact = Contact(
                name=contact_data["name"],
                phone_number=phone_number,
                email=contact_data.get("email"),
                organization=contact_data.get("organization"),
                notes=contact_data.get("notes"),
                tags=[]
            )
            db.add(db_contact)
            created_contacts.append(db_contact)
        
        db.commit()
        
        for contact in created_contacts:
            db.refresh(contact)
        
        logger.info(f"vcard_uploaded", file=file.filename, contacts_created=len(created_contacts), user_id=user_id)
        return {
            "success": True,
            "contacts_created": len(created_contacts),
            "contacts": created_contacts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vcard_upload_error", error=str(e), user_id=user_id)
        raise HTTPException(status_code=400, detail=f"Failed to parse vCard: {str(e)}")


@router.post("/upload/csv")
@limiter.limit(get_rate_limit("contacts_upload"))
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Upload and parse CSV file"""
    try:
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        csv_content = content.decode('utf-8', errors='ignore')
        
        contacts_data = parse_csv(csv_content)
        
        if not contacts_data:
            raise HTTPException(status_code=400, detail="No contacts found in CSV file")
        
        # Create contacts in database
        created_contacts = []
        for contact_data in contacts_data:
            phone_number = validate_phone_number(contact_data.get("phone_number"))
            
            db_contact = Contact(
                name=contact_data["name"],
                phone_number=phone_number,
                email=contact_data.get("email"),
                organization=contact_data.get("organization"),
                notes=contact_data.get("notes"),
                tags=[]
            )
            db.add(db_contact)
            created_contacts.append(db_contact)
        
        db.commit()
        
        for contact in created_contacts:
            db.refresh(contact)
        
        logger.info(f"csv_uploaded", file=file.filename, contacts_created=len(created_contacts), user_id=user_id)
        return {
            "success": True,
            "contacts_created": len(created_contacts),
            "contacts": created_contacts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"csv_upload_error", error=str(e), user_id=user_id)
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.post("/upload/picker")
@limiter.limit(get_rate_limit("contacts_upload"))
async def upload_from_picker(
    request: Request,
    contacts: List[dict],
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Upload contacts from Contact Picker API"""
    try:
        # Enforce max contacts per upload
        if len(contacts) > MAX_BULK_CONTACTS:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_BULK_CONTACTS} contacts allowed per upload"
            )
        
        created_contacts = []
        for contact_data in contacts:
            normalized = normalize_contact_picker_data(contact_data)
            
            if not normalized.get("name"):
                continue  # Skip contacts without names
            
            phone_number = validate_phone_number(normalized.get("phone_number"))
            
            db_contact = Contact(
                name=normalized["name"],
                phone_number=phone_number,
                email=normalized.get("email"),
                organization=normalized.get("organization"),
                notes=normalized.get("notes"),
                tags=[]
            )
            db.add(db_contact)
            created_contacts.append(db_contact)
        
        db.commit()
        
        for contact in created_contacts:
            db.refresh(contact)
        
        logger.info(f"picker_contacts_uploaded", contacts_created=len(created_contacts), user_id=user_id)
        return {
            "success": True,
            "contacts_created": len(created_contacts),
            "contacts": created_contacts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"picker_upload_error", error=str(e), user_id=user_id)
        raise HTTPException(status_code=400, detail=f"Failed to process contacts: {str(e)}")

