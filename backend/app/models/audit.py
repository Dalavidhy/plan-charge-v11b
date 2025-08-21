"""Audit and security models."""

from datetime import datetime, timezone

from sqlalchemy import ARRAY, JSON, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit log for tracking changes."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "ix_audit_logs_org_entity",
            "org_id",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index("ix_audit_logs_actor", "actor_id"),
        Index("ix_audit_logs_action", "action"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    actor_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # Null for system
    action = Column(String(100), nullable=False)  # create, update, delete, etc.
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")


class RefreshToken(BaseModel):
    """JWT refresh tokens."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user", "user_id"),
        Index("ix_refresh_tokens_expires", "expires_at"),
    )

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    device_info = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_expired and not self.is_revoked


class ApiToken(BaseModel):
    """API tokens for service accounts."""

    __tablename__ = "api_tokens"
    __table_args__ = (Index("ix_api_tokens_org", "org_id"),)

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    scopes = Column(ARRAY(String), nullable=False, default=[])
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    created_by_user = relationship(
        "User", back_populates="api_tokens", foreign_keys=[created_by]
    )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_expired and not self.is_revoked
