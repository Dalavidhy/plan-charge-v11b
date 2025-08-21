"""Team schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseResponse


class TeamCreate(BaseModel):
    """Schema for creating team."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None
    parent_team_id: Optional[UUID] = None


class TeamUpdate(BaseModel):
    """Schema for updating team."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    description: Optional[str] = None
    parent_team_id: Optional[UUID] = None


class TeamResponse(BaseResponse):
    """Schema for team response."""

    name: str
    description: Optional[str]
    parent_team_id: Optional[UUID]
    org_id: UUID


class TeamMemberCreate(BaseModel):
    """Schema for adding team member."""

    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    role: str = "member"


class TeamMemberResponse(BaseResponse):
    """Schema for team member response."""

    team_id: UUID
    person_id: UUID
    role: str
