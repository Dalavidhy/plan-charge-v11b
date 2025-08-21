"""
Forecast model for plan de charge predictions
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Forecast(BaseModel):
    """Store forecast entries for plan de charge"""

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecasts_collaborator_date", "collaborator_id", "date"),
        Index("ix_forecasts_date", "date"),
        Index("ix_forecasts_project", "project_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who this forecast is for
    collaborator_id = Column(
        UUID(as_uuid=True), ForeignKey("gryzzly_collaborators.id"), nullable=False
    )

    # What project and task
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("gryzzly_projects.id"), nullable=False
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_tasks.id"), nullable=True)

    # When
    date = Column(Date, nullable=False, index=True)

    # How many hours
    hours = Column(Float, nullable=False)

    # Optional description
    description = Column(Text, nullable=True)

    # Who created/modified this
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timestamps are inherited from BaseModel (TimestampMixin)
    # Do not redefine created_at and updated_at here

    # Relationships
    collaborator = relationship("GryzzlyCollaborator", foreign_keys=[collaborator_id])
    project = relationship("GryzzlyProject", foreign_keys=[project_id])
    task = relationship("GryzzlyTask", foreign_keys=[task_id])
    creator = relationship("User", foreign_keys=[created_by])
    modifier = relationship("User", foreign_keys=[modified_by])

    def __repr__(self) -> str:
        return f"<Forecast(id={self.id}, collaborator_id={self.collaborator_id}, date={self.date}, hours={self.hours})>"
