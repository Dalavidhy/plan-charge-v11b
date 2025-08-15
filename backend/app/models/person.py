"""Person and User models."""

from typing import Optional
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Person(BaseModel, SoftDeleteMixin):
    """Person model - canonical identity for planning."""
    
    __tablename__ = "people"
    __table_args__ = (
        Index("ix_people_org_active", "org_id", "active"),
        Index("ix_people_manager", "manager_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)
    cost_center = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    weekly_hours_default = Column(Numeric(5, 2), nullable=True)
    source = Column(
        Enum("manual", "payfit", "gryzzly", "import", name="person_source"),
        nullable=False,
        default="manual",
    )
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="people")
    manager = relationship("Person", remote_side="Person.id", backref="reports")
    emails = relationship("PersonEmail", back_populates="person", cascade="all, delete-orphan")
    identifiers = relationship("PersonIdentifier", back_populates="person", cascade="all, delete-orphan")
    engagements = relationship("Engagement", back_populates="person", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="person", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", back_populates="person", cascade="all, delete-orphan")
    task_assignments = relationship("TaskAssignee", back_populates="person", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="person", cascade="all, delete-orphan")
    capacities = relationship("Capacity", back_populates="person", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="person", cascade="all, delete-orphan")
    benefits = relationship("PersonBenefit", back_populates="person", cascade="all, delete-orphan")
    external_accounts = relationship("ExternalAccount", back_populates="person")
    user = relationship("User", back_populates="person", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Person(id={self.id}, full_name={self.full_name})>"


class PersonEmail(BaseModel):
    """Person email addresses."""
    
    __tablename__ = "person_emails"
    __table_args__ = (
        UniqueConstraint("person_id", "email", name="uq_person_emails_person_email"),
        Index("ix_person_emails_email", "email"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True)
    email = Column(CITEXT, nullable=False)
    kind = Column(
        Enum("corporate", "personal", "integration", name="email_kind"),
        nullable=False,
        default="corporate",
    )
    is_primary = Column(Boolean, nullable=False, default=False)
    verified = Column(Boolean, nullable=False, default=False)
    source = Column(String(50), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="emails")


class PersonIdentifier(BaseModel):
    """Person identifiers from various sources."""
    
    __tablename__ = "person_identifiers"
    __table_args__ = (
        UniqueConstraint("org_id", "id_type", "id_value", name="uq_person_identifiers_org_type_value"),
        Index("ix_person_identifiers_person", "person_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True)
    id_type = Column(String(50), nullable=False)  # payfit_employee_id, payroll_number, etc.
    id_value = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    
    # Relationships
    person = relationship("Person", back_populates="identifiers")


class Engagement(BaseModel):
    """Person engagement/contract information."""
    
    __tablename__ = "engagements"
    __table_args__ = (
        Index("ix_engagements_person_dates", "person_id", "start_date", "end_date"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True)
    type = Column(
        Enum("employee", "contractor", "mandataire", "freelance", name="engagement_type"),
        nullable=False,
        default="employee",
    )
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    weekly_hours_default = Column(Numeric(5, 2), nullable=True)
    payroll_eligible = Column(Boolean, nullable=False, default=True)
    notes = Column(String(500), nullable=True)
    source = Column(String(50), nullable=False, default="manual")
    external_contract_id = Column(String(100), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="engagements")


class User(BaseModel, SoftDeleteMixin):
    """User account (optional, linked to Person)."""
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_users_org_email"),
        Index("ix_users_person", "person_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)
    email = Column(CITEXT, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for SSO users
    azure_id = Column(String(255), nullable=True, index=True)  # Azure AD Object ID
    locale = Column(String(10), nullable=False, default="fr")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    person = relationship("Person", back_populates="user")
    roles = relationship("UserOrgRole", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    api_tokens = relationship("ApiToken", back_populates="created_by_user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
    comments = relationship("Comment", back_populates="author")
    payfit_employee = relationship("PayfitEmployee", back_populates="local_user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class UserOrgRole(BaseModel):
    """User organization roles."""
    
    __tablename__ = "user_org_roles"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_user_org_roles_org_user"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(
        Enum("owner", "admin", "manager", "member", "viewer", name="role_type"),
        nullable=False,
    )
    
    # Relationships
    user = relationship("User", back_populates="roles")