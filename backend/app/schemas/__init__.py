"""Pydantic schemas package."""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.person import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberCreate,
    TeamMemberResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)
from app.schemas.allocation import (
    AllocationCreate,
    AllocationUpdate,
    AllocationResponse,
    AllocationConflict,
)
from app.schemas.calendar import (
    CalendarCreate,
    CalendarUpdate,
    CalendarResponse,
    HolidayCreate,
    HolidayResponse,
    CapacityCreate,
    CapacityResponse,
    AbsenceCreate,
    AbsenceResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RefreshRequest",
    "RefreshResponse",
    "TokenResponse",
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # Person
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Team
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamMemberCreate",
    "TeamMemberResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # Allocation
    "AllocationCreate",
    "AllocationUpdate",
    "AllocationResponse",
    "AllocationConflict",
    # Calendar
    "CalendarCreate",
    "CalendarUpdate",
    "CalendarResponse",
    "HolidayCreate",
    "HolidayResponse",
    "CapacityCreate",
    "CapacityResponse",
    "AbsenceCreate",
    "AbsenceResponse",
]