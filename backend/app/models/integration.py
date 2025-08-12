"""Integration and identity matching models."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ExternalProvider(BaseModel):
    """External integration provider configuration."""
    
    __tablename__ = "external_providers"
    __table_args__ = (
        UniqueConstraint("org_id", "provider_key", name="uq_external_providers_org_key"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_key = Column(String(50), nullable=False)  # payfit, gryzzly, etc.
    name = Column(String(255), nullable=False)
    capabilities = Column(JSON, nullable=False)  # {roster: bool, absences: bool, ...}
    auth_type = Column(String(50), nullable=False, default="api_key")
    config = Column(JSON, nullable=True)  # Provider-specific configuration
    
    # Relationships
    organization = relationship("Organization", back_populates="external_providers")
    connections = relationship("ExternalConnection", back_populates="provider", cascade="all, delete-orphan")
    external_accounts = relationship("ExternalAccount", back_populates="provider", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="provider", cascade="all, delete-orphan")
    sync_events = relationship("SyncEvent", back_populates="provider", cascade="all, delete-orphan")


class ExternalConnection(BaseModel):
    """Active connection to external provider."""
    
    __tablename__ = "external_connections"
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="connected")
    credentials = Column(JSON, nullable=False)  # Encrypted credentials
    webhook_secret = Column(String(255), nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    provider = relationship("ExternalProvider", back_populates="connections")


class ExternalAccount(BaseModel):
    """External user account from provider."""
    
    __tablename__ = "external_accounts"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_user_id", name="uq_external_accounts_provider_user"),
        Index("ix_external_accounts_person", "person_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    external_user_id = Column(String(255), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)
    raw_profile = Column(JSON, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    provider = relationship("ExternalProvider", back_populates="external_accounts")
    person = relationship("Person", back_populates="external_accounts")
    identity_links = relationship("IdentityLink", back_populates="external_account", cascade="all, delete-orphan")


class SyncJob(BaseModel):
    """Synchronization job tracking."""
    
    __tablename__ = "sync_jobs"
    __table_args__ = (
        Index("ix_sync_jobs_state", "state"),
        Index("ix_sync_jobs_provider_kind", "provider_id", "kind"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    kind = Column(String(50), nullable=False)  # roster, absences, timesheets
    state = Column(String(20), nullable=False, default="queued")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    stats = Column(JSON, nullable=True)  # {created: N, updated: N, errors: N}
    error = Column(Text, nullable=True)
    
    # Relationships
    provider = relationship("ExternalProvider", back_populates="sync_jobs")


class SyncEvent(BaseModel):
    """Webhook/event from external provider."""
    
    __tablename__ = "sync_events"
    __table_args__ = (
        Index("ix_sync_events_provider_type", "provider_id", "event_type"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    provider = relationship("ExternalProvider", back_populates="sync_events")


class IdentityLink(BaseModel):
    """Identity matching decision audit."""
    
    __tablename__ = "identity_links"
    __table_args__ = (
        Index("ix_identity_links_external", "external_account_id"),
        Index("ix_identity_links_person", "person_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    external_account_id = Column(UUID(as_uuid=True), ForeignKey("external_accounts.id"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    action = Column(String(20), nullable=False)  # auto_link, manual_link, unlink
    reason = Column(String(500), nullable=True)
    score = Column(Numeric(4, 3), nullable=True)  # 0.000 to 1.000
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    
    # Relationships
    external_account = relationship("ExternalAccount", back_populates="identity_links")
    person = relationship("Person")
    decider = relationship("User", foreign_keys=[decided_by])


class IdentityMatchRule(BaseModel):
    """Custom identity matching rules."""
    
    __tablename__ = "identity_match_rules"
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    rule = Column(JSON, nullable=False)  # Rule configuration
    priority = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])


# Staging tables for external data
class StgRoster(BaseModel):
    """Staging table for roster data."""
    
    __tablename__ = "stg_roster"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_user_id", name="uq_stg_roster_provider_user"),
    )
    
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    external_user_id = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    seen_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")


class StgAbsence(BaseModel):
    """Staging table for absence data."""
    
    __tablename__ = "stg_absences"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_absence_id", name="uq_stg_absences_provider_absence"),
        Index("ix_stg_absences_user", "user_external_id"),
        Index("ix_stg_absences_dates", "start_date", "end_date"),
    )
    
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    external_absence_id = Column(String(255), nullable=False)
    user_external_id = Column(String(255), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    type = Column(String(50), nullable=False)
    hours_per_day = Column(Numeric(4, 2), nullable=True)
    payload = Column(JSON, nullable=False)


class StgTimesheet(BaseModel):
    """Staging table for timesheet data."""
    
    __tablename__ = "stg_timesheets"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_entry_id", name="uq_stg_timesheets_provider_entry"),
        Index("ix_stg_timesheets_user_date", "user_external_id", "date"),
    )
    
    provider_id = Column(UUID(as_uuid=True), ForeignKey("external_providers.id"), nullable=False, index=True)
    external_entry_id = Column(String(255), nullable=False)
    user_external_id = Column(String(255), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    hours = Column(Numeric(5, 2), nullable=False)
    project_key = Column(String(50), nullable=True)
    task_title = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=False)