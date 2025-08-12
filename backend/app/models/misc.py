"""Miscellaneous models for comments, attachments, and tags."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Comment(BaseModel):
    """Comment model for various entities."""
    
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_entity", "entity_type", "entity_id"),
        Index("ix_comments_author", "author_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # project, task, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="comments")


class Attachment(BaseModel):
    """File attachment model."""
    
    __tablename__ = "attachments"
    __table_args__ = (
        Index("ix_attachments_entity", "entity_type", "entity_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    storage_key = Column(String(500), nullable=False)  # S3 key or file path
    size_bytes = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])


class Tag(BaseModel):
    """Tag model for categorization."""
    
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_tags_org_name"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color
    description = Column(String(255), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="tags")
    entity_tags = relationship("EntityTag", back_populates="tag", cascade="all, delete-orphan")


class EntityTag(BaseModel):
    """Many-to-many relationship for tags."""
    
    __tablename__ = "entity_tags"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "tag_id", name="uq_entity_tags_entity_tag"),
        Index("ix_entity_tags_entity", "entity_type", "entity_id"),
        Index("ix_entity_tags_tag", "tag_id"),
    )
    
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False)
    
    # Relationships
    tag = relationship("Tag", back_populates="entity_tags")