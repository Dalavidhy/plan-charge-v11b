"""Pagination utilities."""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Query(1, ge=1, description="Page number")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page",
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        """Pydantic config."""

        from_attributes = True


async def paginate(
    session: AsyncSession,
    query: Select,
    pagination: PaginationParams,
) -> Dict[str, Any]:
    """Apply pagination to a query and return results with metadata."""

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Apply pagination
    query = query.offset(pagination.offset).limit(pagination.limit)

    # Execute query
    result = await session.execute(query)
    items = result.scalars().all()

    # Calculate pages
    pages = (
        (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }
