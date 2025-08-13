"""Person and User schemas."""

from typing import Optional, List
from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from app.schemas.base import BaseResponse


class PersonCreate(BaseModel):
    """Schema for creating person."""
    
    model_config = ConfigDict(from_attributes=True)
    
    first_name: str
    last_name: str
    email: EmailStr
    matricule: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PersonUpdate(BaseModel):
    """Schema for updating person."""
    
    model_config = ConfigDict(from_attributes=True)
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    matricule: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PersonResponse(BaseResponse):
    """Schema for person response."""
    
    first_name: str
    last_name: str
    email: EmailStr
    matricule: Optional[str]
    phone_number: Optional[str]
    department: Optional[str]
    location: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]


class UserCreate(BaseModel):
    """Schema for creating user."""
    
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user."""
    
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(BaseResponse):
    """Schema for user response."""
    
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_superuser: bool
    person_id: Optional[UUID]