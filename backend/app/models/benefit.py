"""Benefit models."""

from datetime import date

from sqlalchemy import Boolean, Column, Date, ForeignKey, JSON, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BenefitType(BaseModel):
    """Benefit type definition."""
    
    __tablename__ = "benefit_types"
    __table_args__ = (
        UniqueConstraint("org_id", "key", name="uq_benefit_types_org_key"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    key = Column(String(50), nullable=False)  # meal_voucher, health, transport
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="benefit_types")
    policies = relationship("BenefitPolicy", back_populates="benefit_type", cascade="all, delete-orphan")
    person_benefits = relationship("PersonBenefit", back_populates="benefit_type", cascade="all, delete-orphan")


class BenefitPolicy(BaseModel):
    """Benefit eligibility policy."""
    
    __tablename__ = "benefit_policies"
    __table_args__ = (
        Index("ix_benefit_policies_active", "active"),
        Index("ix_benefit_policies_dates", "effective_from", "effective_to"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    benefit_type_id = Column(UUID(as_uuid=True), ForeignKey("benefit_types.id"), nullable=False, index=True)
    rules = Column(JSON, nullable=False)  # {includes: {...}, excludes: {...}}
    active = Column(Boolean, nullable=False, default=True)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    
    # Relationships
    benefit_type = relationship("BenefitType", back_populates="policies")


class PersonBenefit(BaseModel):
    """Person benefit eligibility."""
    
    __tablename__ = "person_benefits"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "benefit_type_id", "effective_from",
            name="uq_person_benefits_person_type_from"
        ),
        Index("ix_person_benefits_person", "person_id"),
        Index("ix_person_benefits_dates", "effective_from", "effective_to"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True)
    benefit_type_id = Column(UUID(as_uuid=True), ForeignKey("benefit_types.id"), nullable=False, index=True)
    eligible = Column(Boolean, nullable=False, default=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    source = Column(String(50), nullable=False, default="policy")  # policy, manual
    reason = Column(String(500), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="benefits")
    benefit_type = relationship("BenefitType", back_populates="person_benefits")