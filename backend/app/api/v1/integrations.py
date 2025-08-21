"""Integrations endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List available integration providers."""
    return {"message": "Integration providers - to be implemented"}


@router.post("/connections")
async def create_connection(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new integration connection."""
    return {"message": "Create connection - to be implemented"}
