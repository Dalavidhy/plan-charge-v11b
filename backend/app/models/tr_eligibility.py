"""
Database models for TR eligibility overrides
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TREligibilityOverride(BaseModel):
    """Store manual TR eligibility overrides for collaborators"""

    __tablename__ = "tr_eligibility_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Collaborator identification - can be from either Gryzzly or Payfit
    collaborator_id = Column(
        String(255), nullable=True, index=True
    )  # Gryzzly ID or Payfit prefixed ID
    email = Column(
        String(255), nullable=False, index=True, unique=True
    )  # Primary key for override

    # Override settings
    is_eligible = Column(Boolean, nullable=False)  # Manual override value
    reason = Column(String(255), nullable=True)  # Optional reason for override

    # Metadata
    modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    modified_by_user = relationship("User", foreign_keys=[modified_by], uselist=False)

    # Ensure unique override per email
    __table_args__ = (UniqueConstraint("email", name="uq_tr_eligibility_email"),)
