"""Base service class for common database operations"""

from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

from src.utils.logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseService(Generic[ModelType]):
    """Base service class with common CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        """
        Initialize base service
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
            
        Returns:
            List of model instances
        """
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, filters: Optional[dict] = None) -> int:
        """
        Count records matching filters
        
        Args:
            db: Database session
            filters: Dictionary of filter conditions
            
        Returns:
            Count of matching records
        """
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

    def exists(self, db: Session, id: int) -> bool:
        """Check if a record exists by ID"""
        return db.query(self.model).filter(self.model.id == id).first() is not None

