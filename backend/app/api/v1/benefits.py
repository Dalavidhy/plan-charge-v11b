"""Benefits endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/types")
async def list_benefit_types(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List benefit types."""
    return {"message": "Benefit types - to be implemented"}


@router.get("/policies")
async def list_benefit_policies(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List benefit policies."""
    return {"message": "Benefit policies - to be implemented"}
