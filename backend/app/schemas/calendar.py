"""Calendar schemas."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseResponse


class CalendarCreate(BaseModel):
    """Schema for creating calendar."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    year: int
    country: str = "FR"


class CalendarUpdate(BaseModel):
    """Schema for updating calendar."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    country: Optional[str] = None


class CalendarResponse(BaseResponse):
    """Schema for calendar response."""

    name: str
    year: int
    country: str
    org_id: UUID


class HolidayCreate(BaseModel):
    """Schema for creating holiday."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    date: date
    is_national: bool = True


class HolidayResponse(BaseResponse):
    """Schema for holiday response."""

    calendar_id: UUID
    name: str
    date: date
    is_national: bool


class CapacityCreate(BaseModel):
    """Schema for creating capacity."""

    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    date: date
    hours_available: float


class CapacityResponse(BaseResponse):
    """Schema for capacity response."""

    person_id: UUID
    date: date
    hours_available: float


class AbsenceCreate(BaseModel):
    """Schema for creating absence."""

    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    start_date: date
    end_date: date
    absence_type: str
    reason: Optional[str] = None


class AbsenceResponse(BaseResponse):
    """Schema for absence response."""

    person_id: UUID
    start_date: date
    end_date: date
    absence_type: str
    reason: Optional[str]
    is_approved: bool
