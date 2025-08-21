"""Calendar, Holiday, Capacity and Absence models."""

from datetime import date

from sqlalchemy import (
    JSON,
    Boolean,
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

from app.models.base import BaseModel, SoftDeleteMixin


class Calendar(BaseModel, SoftDeleteMixin):
    """Calendar model for work week definitions."""

    __tablename__ = "calendars"
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_calendars_org_name"),)

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    workweek = Column(JSON, nullable=False)  # Override default workweek
    description = Column(String(500), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="calendars")
    holidays = relationship(
        "Holiday", back_populates="calendar", cascade="all, delete-orphan"
    )
    capacities = relationship("Capacity", back_populates="calendar")

    def __repr__(self) -> str:
        return f"<Calendar(id={self.id}, name={self.name})>"


class Holiday(BaseModel):
    """Holiday model."""

    __tablename__ = "holidays"
    __table_args__ = (
        UniqueConstraint(
            "calendar_id", "date", "label", name="uq_holidays_calendar_date_label"
        ),
        Index("ix_holidays_date", "date"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    calendar_id = Column(
        UUID(as_uuid=True), ForeignKey("calendars.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False)
    label = Column(String(255), nullable=False)
    is_full_day = Column(Boolean, nullable=False, default=True)
    hours = Column(Numeric(5, 2), nullable=True)  # If not full day

    # Relationships
    calendar = relationship("Calendar", back_populates="holidays")


class Capacity(BaseModel):
    """Person capacity model."""

    __tablename__ = "capacities"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "period_start", name="uq_capacities_person_start"
        ),
        Index("ix_capacities_person_period", "person_id", "period_start", "period_end"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id"), nullable=True)
    period_start = Column(Date, nullable=False)  # Monday
    period_end = Column(Date, nullable=False)  # Sunday
    hours_per_week = Column(Numeric(5, 2), nullable=False)
    notes = Column(String(500), nullable=True)

    # Relationships
    person = relationship("Person", back_populates="capacities")
    calendar = relationship("Calendar", back_populates="capacities")


class Absence(BaseModel):
    """Person absence model."""

    __tablename__ = "absences"
    __table_args__ = (
        Index("ix_absences_person_dates", "person_id", "start_date", "end_date"),
        Index("ix_absences_type", "type"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    type = Column(String(50), nullable=False, default="vacation")
    hours_per_day = Column(Numeric(4, 2), nullable=True)
    notes = Column(String(500), nullable=True)
    approved = Column(Boolean, nullable=False, default=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    person = relationship("Person", back_populates="absences")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        return f"<Absence(id={self.id}, person_id={self.person_id}, type={self.type})>"
