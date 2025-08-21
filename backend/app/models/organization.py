"""Organization model."""

from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Organization(BaseModel, SoftDeleteMixin):
    """Organization model."""

    __tablename__ = "organizations"
    __allow_unmapped__ = True  # Allow legacy SQLAlchemy 1.x style annotations

    name = Column(String(255), nullable=False, unique=True, index=True)
    timezone = Column(String(50), nullable=False, default="Europe/Paris")
    default_workweek = Column(
        JSON,
        nullable=False,
        default={
            "monday": 7,
            "tuesday": 7,
            "wednesday": 7,
            "thursday": 7,
            "friday": 7,
            "saturday": 0,
            "sunday": 0,
        },
    )

    # Relationships
    people = relationship(
        "Person", back_populates="organization", cascade="all, delete-orphan"
    )
    teams = relationship(
        "Team", back_populates="organization", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )
    calendars = relationship(
        "Calendar", back_populates="organization", cascade="all, delete-orphan"
    )
    users = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    external_providers = relationship(
        "ExternalProvider", back_populates="organization", cascade="all, delete-orphan"
    )
    benefit_types = relationship(
        "BenefitType", back_populates="organization", cascade="all, delete-orphan"
    )
    tags = relationship(
        "Tag", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
