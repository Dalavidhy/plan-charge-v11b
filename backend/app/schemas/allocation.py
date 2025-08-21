"""Allocation schemas."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseResponse


class AllocationCreate(BaseModel):
    """Schema for creating allocation."""

    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    project_id: UUID
    start_date: date
    end_date: date
    percentage: float
    hours_per_week: Optional[float] = None
    source: str = "manual"
    notes: Optional[str] = None


class AllocationUpdate(BaseModel):
    """Schema for updating allocation."""

    model_config = ConfigDict(from_attributes=True)

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    percentage: Optional[float] = None
    hours_per_week: Optional[float] = None
    notes: Optional[str] = None


class AllocationResponse(BaseResponse):
    """Schema for allocation response."""

    person_id: UUID
    project_id: UUID
    start_date: date
    end_date: date
    percentage: float
    hours_per_week: Optional[float]
    source: str
    notes: Optional[str]


class AllocationConflict(BaseModel):
    """Schema for allocation conflict."""

    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    date: date
    total_percentage: float
    allocations: List[AllocationResponse]
