"""
Database models for Gryzzly integration
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Text, Integer, Date, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import BaseModel


class GryzzlyCollaborator(BaseModel):
    """Store synchronized Gryzzly collaborators"""
    __tablename__ = "gryzzly_collaborators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gryzzly_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Additional info
    matricule = Column(String(50), nullable=True, index=True)
    department = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Link to local user
    local_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    local_user = relationship("User", foreign_keys=[local_user_id], uselist=False)
    declarations = relationship("GryzzlyDeclaration", back_populates="collaborator")
    projects = relationship("GryzzlyProject", secondary="gryzzly_collaborator_projects", back_populates="collaborators")


class GryzzlyProject(BaseModel):
    """Store Gryzzly projects"""
    __tablename__ = "gryzzly_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gryzzly_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Project details
    client_name = Column(String(255), nullable=True)
    project_type = Column(String(100), nullable=True)  # internal, client, R&D, etc.
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_billable = Column(Boolean, default=True)
    
    # Budget
    budget_hours = Column(Float, nullable=True)
    budget_amount = Column(Float, nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("GryzzlyTask", back_populates="project")
    declarations = relationship("GryzzlyDeclaration", back_populates="project")
    collaborators = relationship("GryzzlyCollaborator", secondary="gryzzly_collaborator_projects", back_populates="projects")


class GryzzlyTask(BaseModel):
    """Store Gryzzly tasks"""
    __tablename__ = "gryzzly_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gryzzly_id = Column(String(255), unique=True, nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Task details
    task_type = Column(String(100), nullable=True)  # development, design, meeting, etc.
    estimated_hours = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_billable = Column(Boolean, default=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("GryzzlyProject", back_populates="tasks")
    declarations = relationship("GryzzlyDeclaration", back_populates="task")


class GryzzlyDeclaration(BaseModel):
    """Store time declarations from Gryzzly"""
    __tablename__ = "gryzzly_declarations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gryzzly_id = Column(String(255), unique=True, nullable=False, index=True)
    collaborator_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_collaborators.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_tasks.id"), nullable=True)
    
    # Declaration details
    date = Column(Date, nullable=False, index=True)
    duration_hours = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default='draft')  # draft, submitted, approved, rejected
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Billing
    is_billable = Column(Boolean, default=True)
    billing_rate = Column(Float, nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collaborator = relationship("GryzzlyCollaborator", back_populates="declarations")
    project = relationship("GryzzlyProject", back_populates="declarations")
    task = relationship("GryzzlyTask", back_populates="declarations")


class GryzzlyCollaboratorProject(BaseModel):
    """Association table for collaborators and projects"""
    __tablename__ = "gryzzly_collaborator_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collaborator_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_collaborators.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_projects.id"), nullable=False)
    
    # Assignment details
    role = Column(String(100), nullable=True)  # developer, manager, reviewer, etc.
    allocation_percentage = Column(Float, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GryzzlySyncLog(BaseModel):
    """Track Gryzzly synchronization history"""
    __tablename__ = "gryzzly_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_type = Column(String(50), nullable=False)  # collaborators, projects, tasks, declarations, full
    sync_status = Column(String(50), nullable=False)  # started, success, failed, partial
    
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Statistics
    records_synced = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default={})
    
    # Metadata
    triggered_by = Column(String(255), nullable=True)  # username or 'system'
    sync_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)