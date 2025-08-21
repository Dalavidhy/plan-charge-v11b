"""
Pydantic schemas for Payfit integration
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Employee schemas
class PayfitEmployeeBase(BaseModel):
    payfit_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    registration_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_active: bool = True
    manager_payfit_id: Optional[str] = None


class PayfitEmployeeResponse(PayfitEmployeeBase):
    id: UUID
    local_user_id: Optional[UUID] = None
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Contract schemas
class PayfitContractBase(BaseModel):
    payfit_id: str
    payfit_employee_id: str
    contract_type: Optional[str] = None
    job_title: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    weekly_hours: Optional[float] = None
    daily_hours: Optional[float] = None
    annual_hours: Optional[float] = None
    part_time_percentage: Optional[float] = None
    is_active: bool = True
    probation_end_date: Optional[date] = None


class PayfitContractResponse(PayfitContractBase):
    id: UUID
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Absence schemas
class PayfitAbsenceBase(BaseModel):
    payfit_id: str
    payfit_employee_id: str
    absence_type: str
    absence_code: Optional[str] = None
    start_date: date
    end_date: date
    duration_days: Optional[float] = None
    duration_hours: Optional[float] = None
    status: str = "pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class PayfitAbsenceResponse(PayfitAbsenceBase):
    id: UUID
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Sync log schemas
class PayfitSyncLogResponse(BaseModel):
    id: UUID
    sync_type: str
    sync_status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    records_synced: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


# Sync request/response schemas
class PayfitSyncRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PayfitSyncStatusResponse(BaseModel):
    last_sync: Optional[Dict[str, Any]] = None
    data_counts: Dict[str, int]
    api_connected: bool


class PayfitStatsResponse(BaseModel):
    total_employees: int
    active_employees: int
    total_contracts: int
    active_contracts: int
    total_absences: int
    approved_absences: int
    pending_absences: int
