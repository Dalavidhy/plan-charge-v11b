"""
Database models for Payfit integration
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Text, Integer, Date, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import BaseModel


class PayfitEmployee(BaseModel):
    """Store synchronized Payfit employees"""
    __tablename__ = "payfit_employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payfit_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Additional info
    registration_number = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(10), nullable=True)
    
    # Work info
    department = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Manager info
    manager_payfit_id = Column(String(255), nullable=True)
    
    # Link to local user
    local_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    local_user = relationship("User", foreign_keys=[local_user_id], uselist=False)
    contracts = relationship("PayfitContract", back_populates="employee")
    absences = relationship("PayfitAbsence", back_populates="employee")


class PayfitContract(BaseModel):
    """Store employee contracts from Payfit"""
    __tablename__ = "payfit_contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payfit_id = Column(String(255), unique=True, nullable=False, index=True)
    payfit_employee_id = Column(String(255), ForeignKey("payfit_employees.payfit_id"), nullable=False)
    
    # Contract details
    contract_type = Column(String(100))  # CDI, CDD, etc.
    job_title = Column(String(255))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Working time
    weekly_hours = Column(Float, nullable=True)
    daily_hours = Column(Float, nullable=True)
    annual_hours = Column(Float, nullable=True)
    part_time_percentage = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    probation_end_date = Column(Date, nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("PayfitEmployee", back_populates="contracts")


class PayfitAbsence(BaseModel):
    """Store synchronized absences from Payfit"""
    __tablename__ = "payfit_absences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payfit_id = Column(String(255), unique=True, nullable=False, index=True)
    payfit_employee_id = Column(String(255), ForeignKey("payfit_employees.payfit_id"), nullable=False)
    
    # Absence details
    absence_type = Column(String(100), nullable=False)  # vacation, sick_leave, etc.
    absence_code = Column(String(50), nullable=True)  # Payfit specific code
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Duration
    duration_days = Column(Float, nullable=True)
    duration_hours = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default='pending')  # pending, approved, rejected, cancelled
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Additional info
    reason = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default={})
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("PayfitEmployee", back_populates="absences")


class PayfitSyncLog(BaseModel):
    """Track synchronization history"""
    __tablename__ = "payfit_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_type = Column(String(50), nullable=False)  # employees, absences, contracts, full
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