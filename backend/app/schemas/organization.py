"""Organization schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseResponse


class OrganizationCreate(BaseModel):
    """Schema for creating organization."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    timezone: str = "Europe/Paris"
    default_workweek: Dict[str, float] = {
        "monday": 7,
        "tuesday": 7,
        "wednesday": 7,
        "thursday": 7,
        "friday": 7,
        "saturday": 0,
        "sunday": 0,
    }


class OrganizationUpdate(BaseModel):
    """Schema for updating organization."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    timezone: Optional[str] = None
    default_workweek: Optional[Dict[str, float]] = None


class OrganizationResponse(BaseResponse):
    """Schema for organization response."""
    
    name: str
    timezone: str
    default_workweek: Dict[str, float]