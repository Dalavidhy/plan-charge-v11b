"""Organization endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_active_user, require_admin
from app.models import Organization, User
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


@router.get("/")
async def list_organizations(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List organizations accessible to the current user."""
    query = select(Organization).where(Organization.deleted_at.is_(None))

    # Filter by user's organization
    query = query.where(Organization.id == current_user.org_id)

    result = await paginate(session, query, pagination)
    return result


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: dict,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new organization."""
    # Simplified for now - full implementation needed
    org = Organization(
        name=data["name"],
        timezone=data.get("timezone", "Europe/Paris"),
        default_workweek=data.get(
            "default_workweek",
            {
                "monday": 7,
                "tuesday": 7,
                "wednesday": 7,
                "thursday": 7,
                "friday": 7,
                "saturday": 0,
                "sunday": 0,
            },
        ),
    )
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


@router.get("/{org_id}")
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get organization details."""
    if org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    query = select(Organization).where(
        Organization.id == org_id,
        Organization.deleted_at.is_(None),
    )
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.patch("/{org_id}")
async def update_organization(
    org_id: UUID,
    data: dict,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Update organization."""
    if org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    query = select(Organization).where(
        Organization.id == org_id,
        Organization.deleted_at.is_(None),
    )
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update fields
    for key, value in data.items():
        if hasattr(org, key):
            setattr(org, key, value)

    await session.commit()
    await session.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Soft delete organization."""
    if org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    query = select(Organization).where(
        Organization.id == org_id,
        Organization.deleted_at.is_(None),
    )
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    org.soft_delete()
    await session.commit()
