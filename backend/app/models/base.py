"""Base model classes and mixins."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query

from app.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    @declared_attr
    def created_at(cls) -> Column:
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            index=True,
        )
    
    @declared_attr
    def updated_at(cls) -> Column:
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
            index=True,
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    @declared_attr
    def deleted_at(cls) -> Column:
        return Column(DateTime(timezone=True), nullable=True, index=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None
    
    @classmethod
    def filter_active(cls, query: Query) -> Query:
        """Filter out soft deleted records."""
        return query.filter(cls.deleted_at.is_(None))


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def dict(self, exclude: Optional[set] = None) -> dict[str, Any]:
        """Convert model to dictionary."""
        exclude = exclude or set()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }
    
    @classmethod
    def create(cls, **kwargs) -> "BaseModel":
        """Create a new instance."""
        return cls(**kwargs)
    
    def update(self, **kwargs) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)