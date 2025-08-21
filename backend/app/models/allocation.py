"""Allocation models."""

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Allocation(BaseModel):
    """Resource allocation model."""

    __tablename__ = "allocations"
    __table_args__ = (
        CheckConstraint(
            "(percent IS NOT NULL) OR (hours_per_week IS NOT NULL)",
            name="ck_allocations_percent_or_hours",
        ),
        Index("ix_allocations_person_dates", "person_id", "start_date", "end_date"),
        Index("ix_allocations_project_dates", "project_id", "start_date", "end_date"),
        Index("ix_allocations_task", "task_id"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    percent = Column(Numeric(5, 2), nullable=True)  # 0.00 to 200.00
    hours_per_week = Column(Numeric(5, 2), nullable=True)  # 0.00 to 99.99
    source = Column(
        String(20),
        nullable=False,
        default="manual",
    )
    notes = Column(String(500), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="allocations")
    task = relationship("Task", back_populates="allocations")
    person = relationship("Person", back_populates="allocations")
    breakdowns = relationship(
        "AllocationBreakdown", back_populates="allocation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Allocation(id={self.id}, person_id={self.person_id}, project_id={self.project_id})>"


class AllocationBreakdown(BaseModel):
    """Daily breakdown of allocations (optional for v1)."""

    __tablename__ = "allocation_breakdowns"
    __table_args__ = (
        UniqueConstraint(
            "allocation_id", "date", name="uq_allocation_breakdowns_allocation_date"
        ),
        Index("ix_allocation_breakdowns_date", "date"),
    )

    allocation_id = Column(
        UUID(as_uuid=True), ForeignKey("allocations.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False)
    hours = Column(Numeric(4, 2), nullable=False)

    # Relationships
    allocation = relationship("Allocation", back_populates="breakdowns")
