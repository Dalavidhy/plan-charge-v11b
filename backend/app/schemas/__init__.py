"""Pydantic schemas package."""

from app.schemas.allocation import (
    AllocationConflict,
    AllocationCreate,
    AllocationResponse,
    AllocationUpdate,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
)
from app.schemas.calendar import (
    AbsenceCreate,
    AbsenceResponse,
    CalendarCreate,
    CalendarResponse,
    CalendarUpdate,
    CapacityCreate,
    CapacityResponse,
    HolidayCreate,
    HolidayResponse,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.schemas.person import (
    PersonCreate,
    PersonResponse,
    PersonUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.team import (
    TeamCreate,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
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
