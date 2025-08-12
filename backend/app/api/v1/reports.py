"""Reports endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/utilization")
async def utilization_report(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get utilization report."""
    return {"message": "Utilization report - to be implemented"}


@router.get("/overbookings")
async def overbooking_report(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get overbooking report."""
    return {"message": "Overbooking report - to be implemented"}


@router.get("/capacity-vs-load")
async def capacity_vs_load_report(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get capacity vs load report."""
    return {"message": "Capacity vs load report - to be implemented"}