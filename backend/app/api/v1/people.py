"""People endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/")
async def list_people(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List people in the organization."""
    return {"message": "People endpoint - to be implemented"}