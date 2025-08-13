"""Base schemas with common fields."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base response schema with common fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


class BaseCreateUpdate(BaseModel):
    """Base schema for create/update operations."""
    
    model_config = ConfigDict(from_attributes=True)