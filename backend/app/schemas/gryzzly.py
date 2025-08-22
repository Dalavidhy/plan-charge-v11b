"""
Pydantic schemas for Gryzzly integration
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base schemas
class GryzzlyCollaboratorBase(BaseModel):
    """Base schema for Gryzzly collaborator"""

    gryzzly_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    matricule: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


class GryzzlyProjectBase(BaseModel):
    """Base schema for Gryzzly project"""

    gryzzly_id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    project_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    is_billable: bool = True
    budget_hours: Optional[float] = None
    budget_amount: Optional[float] = None


class GryzzlyTaskBase(BaseModel):
    """Base schema for Gryzzly task"""

    gryzzly_id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    estimated_hours: Optional[float] = None
    is_active: bool = True
    is_billable: bool = True


class GryzzlyDeclarationBase(BaseModel):
    """Base schema for Gryzzly declaration"""

    gryzzly_id: str
    date: date
    duration_hours: float
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    comment: Optional[str] = None
    status: str = "draft"
    is_billable: bool = True
    billing_rate: Optional[float] = None


# Response schemas with enrichment
class GryzzlyCollaboratorInDB(GryzzlyCollaboratorBase):
    """Schema for Gryzzly collaborator in database"""

    id: uuid.UUID
    local_user_id: Optional[uuid.UUID] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    full_name: Optional[str] = None
    local_user_email: Optional[str] = None

    class Config:
        orm_mode = True

    def __init__(self, **data) -> None:  # type: ignore
        super().__init__(**data)
        # Calculate full name
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name


class GryzzlyProjectInDB(GryzzlyProjectBase):
    """Schema for Gryzzly project in database"""

    id: uuid.UUID
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    total_hours_tracked: Optional[float] = None
    total_hours_remaining: Optional[float] = None
    collaborators_count: Optional[int] = None

    class Config:
        orm_mode = True


class GryzzlyTaskInDB(GryzzlyTaskBase):
    """Schema for Gryzzly task in database"""

    id: uuid.UUID
    project_id: uuid.UUID
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    total_hours_tracked: Optional[float] = None

    class Config:
        orm_mode = True


class GryzzlyDeclarationInDB(GryzzlyDeclarationBase):
    """Schema for Gryzzly declaration in database"""

    id: uuid.UUID
    collaborator_id: uuid.UUID
    project_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    collaborator_name: Optional[str] = None
    collaborator_email: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    task_name: Optional[str] = None
    total_cost: Optional[float] = None

    class Config:
        orm_mode = True

    def __init__(self, **data) -> None:  # type: ignore
        super().__init__(**data)
        # Calculate total cost if billing rate is available
        if self.billing_rate and self.duration_hours:
            self.total_cost = self.billing_rate * self.duration_hours


class GryzzlySyncLogInDB(BaseModel):
    """Schema for Gryzzly sync log in database"""

    id: uuid.UUID
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
    error_details: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None
    sync_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Request schemas
class SyncTriggerRequest(BaseModel):
    """Request schema for triggering sync"""

    sync_type: str = Field(
        ...,
        description="Type of sync: collaborators, projects, tasks, declarations, full",
    )
    start_date: Optional[date] = Field(
        None, description="Start date for declarations sync"
    )
    end_date: Optional[date] = Field(None, description="End date for declarations sync")


class SyncTriggerResponse(BaseModel):
    """Response schema for sync trigger"""

    sync_type: str
    sync_id: uuid.UUID
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    """Response schema for sync status"""

    collaborators: Optional[Dict[str, Any]] = None
    projects: Optional[Dict[str, Any]] = None
    tasks: Optional[Dict[str, Any]] = None
    declarations: Optional[Dict[str, Any]] = None
    full: Optional[Dict[str, Any]] = None
    is_syncing: bool = False


class GryzzlyStatsResponse(BaseModel):
    """Response schema for Gryzzly statistics"""

    total_collaborators: int = 0
    active_collaborators: int = 0
    linked_collaborators: int = 0

    total_projects: int = 0
    active_projects: int = 0
    billable_projects: int = 0

    total_tasks: int = 0

    total_declarations: int = 0
    total_hours: float = 0.0
    total_days: float = 0.0
    billable_hours: float = 0.0
    billable_amount: float = 0.0

    last_sync_date: Optional[datetime] = None
    sync_health: str = "unknown"  # healthy, warning, error, unknown


# List response schemas
class GryzzlyCollaboratorListResponse(BaseModel):
    """Response schema for collaborator list"""

    items: List[GryzzlyCollaboratorInDB]
    total: int
    page: int = 1
    size: int = 100
    has_more: bool = False


class GryzzlyProjectListResponse(BaseModel):
    """Response schema for project list"""

    items: List[GryzzlyProjectInDB]
    total: int
    page: int = 1
    size: int = 100
    has_more: bool = False


class GryzzlyTaskListResponse(BaseModel):
    """Response schema for task list"""

    items: List[GryzzlyTaskInDB]
    total: int
    page: int = 1
    size: int = 100
    has_more: bool = False


class GryzzlyDeclarationListResponse(BaseModel):
    """Response schema for declaration list"""

    items: List[GryzzlyDeclarationInDB]
    total: int
    page: int = 1
    size: int = 100
    has_more: bool = False

    # Aggregations
    total_hours: Optional[float] = None
    total_days: Optional[float] = None
    total_cost: Optional[float] = None


# Report schemas
class TimeReportEntry(BaseModel):
    """Entry in time report"""

    period: str
    collaborator_id: Optional[uuid.UUID] = None
    collaborator_name: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    project_name: Optional[str] = None
    task_id: Optional[uuid.UUID] = None
    task_name: Optional[str] = None
    total_hours: float
    total_days: float
    billable_hours: float
    billable_amount: float
    declaration_count: int


class TimeReport(BaseModel):
    """Time tracking report"""

    start_date: date
    end_date: date
    group_by: str
    entries: List[TimeReportEntry]
    totals: Dict[str, float]


class ProjectMetrics(BaseModel):
    """Project metrics"""

    project_id: uuid.UUID
    project_name: str
    project_code: Optional[str] = None
    budget_hours: Optional[float] = None
    tracked_hours: float
    remaining_hours: Optional[float] = None
    budget_utilization: Optional[float] = None
    collaborators_count: int
    tasks_count: int
    average_hours_per_day: float
    last_activity: Optional[date] = None
