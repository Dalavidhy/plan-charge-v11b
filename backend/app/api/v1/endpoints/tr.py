"""
API endpoints for Titres Restaurant (meal voucher) management
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_async_session
from app.services.tr_service import TRService

router = APIRouter()


@router.get("/rights/{year}/{month}")
async def get_tr_rights(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Calculate TR rights for all employees for a given month
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
    
    Returns:
        Dictionary with TR rights for all employees
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    if year < 2020 or year > 2030:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
    
    tr_service = TRService(db)
    result = await tr_service.calculate_all_tr_rights(year, month)
    
    return result


@router.get("/rights/{year}/{month}/{email}")
async def get_employee_tr_rights(
    year: int,
    month: int,
    email: str,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Calculate TR rights for a specific employee for a given month
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        email: Employee email
    
    Returns:
        Dictionary with TR rights for the employee
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    if year < 2020 or year > 2030:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
    
    tr_service = TRService(db)
    result = await tr_service.calculate_tr_rights(email, year, month)
    
    if result.get("matricule") is None:
        raise HTTPException(status_code=404, detail=f"Employee not found: {email}")
    
    return result


@router.get("/working-days/{year}/{month}")
async def get_working_days(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get working days information for a given month
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
    
    Returns:
        Dictionary with working days, holidays, and weekends
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    if year < 2020 or year > 2030:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
    
    tr_service = TRService(db)
    result = tr_service.get_working_days(year, month)
    
    return result


@router.get("/export/{year}/{month}")
async def export_tr_rights_csv(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_async_session)
) -> Response:
    """
    Export TR rights as CSV for a given month
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
    
    Returns:
        CSV file with TR rights for all employees
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    if year < 2020 or year > 2030:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
    
    tr_service = TRService(db)
    
    # Get TR rights data
    tr_data = await tr_service.calculate_all_tr_rights(year, month)
    
    # Generate CSV content
    csv_content = tr_service.generate_csv(tr_data)
    
    # Return as CSV file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=tr_rights_{year}_{month:02d}.csv"
        }
    )