"""Project and Task schemas."""

from typing import Optional, List
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseResponse


class ProjectCreate(BaseModel):
    """Schema for creating project."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    code: str
    description: Optional[str] = None
    team_id: UUID
    start_date: date
    end_date: Optional[date] = None
    status: str = "active"


class ProjectUpdate(BaseModel):
    """Schema for updating project."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ProjectResponse(BaseResponse):
    """Schema for project response."""
    
    name: str
    code: str
    description: Optional[str]
    team_id: UUID
    start_date: date
    end_date: Optional[date]
    status: str


class TaskCreate(BaseModel):
    """Schema for creating task."""
    
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    description: Optional[str] = None
    project_id: UUID
    epic_id: Optional[UUID] = None
    status: str = "todo"
    priority: int = 0
    estimated_hours: Optional[float] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    """Schema for updating task."""
    
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    epic_id: Optional[UUID] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_at: Optional[date] = None


class TaskResponse(BaseResponse):
    """Schema for task response."""
    
    title: str
    description: Optional[str]
    project_id: UUID
    epic_id: Optional[UUID]
    status: str
    priority: int
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    start_date: Optional[date]
    due_date: Optional[date]
    completed_at: Optional[date]