"""
Payfit API endpoints for synchronization and data management
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_async_session
from app.models.person import User
from app.models.payfit import PayfitEmployee, PayfitContract, PayfitAbsence, PayfitSyncLog
from app.services.payfit_sync import PayfitSyncService
from app.services.payfit_client import PayfitAPIClient

router = APIRouter()


@router.get("/status")
async def get_sync_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current Payfit synchronization status"""
    # Get last sync log
    last_sync_query = select(PayfitSyncLog).order_by(PayfitSyncLog.created_at.desc()).limit(1)
    last_sync_result = await session.execute(last_sync_query)
    last_sync = last_sync_result.scalar_one_or_none()
    
    # Count records
    employee_count_result = await session.execute(select(func.count()).select_from(PayfitEmployee))
    employee_count = employee_count_result.scalar() or 0
    
    contract_count_result = await session.execute(select(func.count()).select_from(PayfitContract))
    contract_count = contract_count_result.scalar() or 0
    
    absence_count_result = await session.execute(select(func.count()).select_from(PayfitAbsence))
    absence_count = absence_count_result.scalar() or 0
    
    # Test API connection
    client = PayfitAPIClient()
    api_connected = await client.test_connection()
    
    return {
        "last_sync": {
            "type": last_sync.sync_type if last_sync else None,
            "status": last_sync.sync_status if last_sync else None,
            "timestamp": last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None,
            "records_synced": last_sync.records_synced if last_sync else 0
        },
        "data_counts": {
            "employees": employee_count,
            "contracts": contract_count,
            "absences": absence_count
        },
        "api_connected": api_connected
    }


@router.get("/stats")
async def get_payfit_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get Payfit data statistics"""
    # Count employees
    total_employees_result = await session.execute(select(func.count()).select_from(PayfitEmployee))
    total_employees = total_employees_result.scalar() or 0
    
    active_employees_result = await session.execute(
        select(func.count()).select_from(PayfitEmployee).where(PayfitEmployee.is_active == True)
    )
    active_employees = active_employees_result.scalar() or 0
    
    # Count contracts
    total_contracts_result = await session.execute(select(func.count()).select_from(PayfitContract))
    total_contracts = total_contracts_result.scalar() or 0
    
    active_contracts_result = await session.execute(
        select(func.count()).select_from(PayfitContract).where(PayfitContract.is_active == True)
    )
    active_contracts = active_contracts_result.scalar() or 0
    
    # Count absences
    total_absences_result = await session.execute(select(func.count()).select_from(PayfitAbsence))
    total_absences = total_absences_result.scalar() or 0
    
    approved_absences_result = await session.execute(
        select(func.count()).select_from(PayfitAbsence).where(PayfitAbsence.status == "approved")
    )
    approved_absences = approved_absences_result.scalar() or 0
    
    pending_absences_result = await session.execute(
        select(func.count()).select_from(PayfitAbsence).where(PayfitAbsence.status == "pending")
    )
    pending_absences = pending_absences_result.scalar() or 0
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_contracts": total_contracts,
        "active_contracts": active_contracts,
        "total_absences": total_absences,
        "approved_absences": approved_absences,
        "pending_absences": pending_absences
    }


@router.post("/sync/test-connection")
async def test_payfit_connection(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test Payfit API connection"""
    try:
        client = PayfitAPIClient()
        connected = await client.test_connection()
        
        if not connected:
            raise HTTPException(status_code=503, detail="Unable to connect to Payfit API")
        
        return {
            "status": "success",
            "message": "Successfully connected to Payfit API",
            "api_url": client.base_url,
            "company_id": client.company_id
        }
    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Connection failed: {str(e)}")


@router.post("/sync/employees")
async def sync_employees(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger employee synchronization from Payfit"""
    
    # Check if sync is already running
    result = await session.execute(
        select(PayfitSyncLog).where(
            PayfitSyncLog.sync_type == "employees",
            PayfitSyncLog.sync_status == "started"
        )
    )
    running_sync = result.scalar_one_or_none()
    
    if running_sync:
        raise HTTPException(
            status_code=400,
            detail="Employee sync is already running"
        )
    
    try:
        # Create sync service
        sync_service = PayfitSyncService(session)
        
        # Start sync in background
        background_tasks.add_task(sync_service.sync_employees)
        
        return {
            "status": "triggered",
            "message": "Employee synchronization has been triggered"
        }
    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.post("/sync/contracts")
async def sync_contracts(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger contract synchronization from Payfit"""
    
    # Check if sync is already running
    result = await session.execute(
        select(PayfitSyncLog).where(
            PayfitSyncLog.sync_type == "contracts",
            PayfitSyncLog.sync_status == "started"
        )
    )
    running_sync = result.scalar_one_or_none()
    
    if running_sync:
        raise HTTPException(
            status_code=400,
            detail="Contract sync is already running"
        )
    
    try:
        # Create sync service
        sync_service = PayfitSyncService(session)
        
        # Start sync in background
        background_tasks.add_task(sync_service.sync_contracts)
        
        return {
            "status": "triggered",
            "message": "Contract synchronization has been triggered"
        }
    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.post("/sync/absences")
async def sync_absences(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger absence synchronization from Payfit"""
    
    # Check if sync is already running
    result = await session.execute(
        select(PayfitSyncLog).where(
            PayfitSyncLog.sync_type == "absences",
            PayfitSyncLog.sync_status == "started"
        )
    )
    running_sync = result.scalar_one_or_none()
    
    if running_sync:
        raise HTTPException(
            status_code=400,
            detail="Absence sync is already running"
        )
    
    try:
        # Create sync service
        sync_service = PayfitSyncService(session)
        
        # Default to 6 months before and 6 months after current date
        today = date.today()
        if not start_date:
            # 6 months before today
            start_date = today - timedelta(days=180)
        if not end_date:
            # 6 months after today
            end_date = today + timedelta(days=180)
        
        # Start sync in background
        background_tasks.add_task(
            sync_service.sync_absences,
            start_date,
            end_date
        )
        
        return {
            "status": "triggered",
            "message": f"Absence synchronization from {start_date.isoformat()} to {end_date.isoformat()} has been triggered"
        }
    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.post("/sync/full")
async def sync_full(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Trigger full synchronization from Payfit"""
    
    # Check if any sync is already running
    result = await session.execute(
        select(func.count()).select_from(PayfitSyncLog).where(
            PayfitSyncLog.sync_status == "started"
        )
    )
    running_count = result.scalar()
    
    if running_count > 0:
        raise HTTPException(
            status_code=400,
            detail="A synchronization is already running"
        )
    
    try:
        # Create sync service
        sync_service = PayfitSyncService(session)
        
        # Start full sync in background
        background_tasks.add_task(sync_service.sync_all, "manual")
        
        return {
            "status": "triggered",
            "message": "Full Payfit synchronization has been triggered"
        }
    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.get("/employees")
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get list of synchronized Payfit employees"""
    query = select(PayfitEmployee)
    
    if active_only:
        query = query.where(PayfitEmployee.is_active == True)
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    employees = result.scalars().all()
    
    return [
        {
            "id": str(emp.id),
            "payfit_id": emp.payfit_id,
            "email": emp.email,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "department": emp.department,
            "position": emp.position,
            "is_active": emp.is_active,
            "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
            "local_user_id": str(emp.local_user_id) if emp.local_user_id else None,
            "last_synced_at": emp.last_synced_at.isoformat() if emp.last_synced_at else None,
            "created_at": emp.created_at.isoformat() if emp.created_at else None,
            "updated_at": emp.updated_at.isoformat() if emp.updated_at else None
        }
        for emp in employees
    ]


@router.get("/contracts")
async def get_contracts(
    employee_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get list of synchronized Payfit contracts with employee information"""
    # Join with PayfitEmployee to get employee information
    from sqlalchemy.orm import selectinload
    query = select(PayfitContract).options(selectinload(PayfitContract.employee))
    
    if employee_id:
        query = query.where(PayfitContract.payfit_employee_id == employee_id)
    
    if active_only:
        query = query.where(PayfitContract.is_active == True)
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    contracts = result.scalars().all()
    
    return [
        {
            "id": str(contract.id),
            "payfit_id": contract.payfit_id,
            "payfit_employee_id": contract.payfit_employee_id,
            # Employee information
            "employee_first_name": contract.employee.first_name if contract.employee else None,
            "employee_last_name": contract.employee.last_name if contract.employee else None,
            "employee_email": contract.employee.email if contract.employee else None,
            "employee_full_name": f"{contract.employee.first_name} {contract.employee.last_name}" if contract.employee and contract.employee.first_name and contract.employee.last_name else None,
            # Contract information
            "contract_type": contract.contract_type,
            "job_title": contract.job_title,
            "start_date": contract.start_date.isoformat() if contract.start_date else None,
            "end_date": contract.end_date.isoformat() if contract.end_date else None,
            "weekly_hours": contract.weekly_hours,
            "part_time_percentage": contract.part_time_percentage,
            "is_active": contract.is_active,
            "last_synced_at": contract.last_synced_at.isoformat() if contract.last_synced_at else None,
            "created_at": contract.created_at.isoformat() if contract.created_at else None,
            "updated_at": contract.updated_at.isoformat() if contract.updated_at else None
        }
        for contract in contracts
    ]


@router.get("/absences")
async def get_absences(
    employee_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get list of synchronized Payfit absences with employee information"""
    # Join with PayfitEmployee to get employee information
    from sqlalchemy.orm import selectinload
    query = select(PayfitAbsence).options(selectinload(PayfitAbsence.employee))
    
    if employee_id:
        query = query.where(PayfitAbsence.payfit_employee_id == employee_id)
    
    if start_date:
        query = query.where(PayfitAbsence.end_date >= start_date)
    
    if end_date:
        query = query.where(PayfitAbsence.start_date <= end_date)
    
    if status:
        query = query.where(PayfitAbsence.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    absences = result.scalars().all()
    
    return [
        {
            "id": str(absence.id),
            "payfit_id": absence.payfit_id,
            "payfit_employee_id": absence.payfit_employee_id,
            # Employee information
            "employee_first_name": absence.employee.first_name if absence.employee else None,
            "employee_last_name": absence.employee.last_name if absence.employee else None,
            "employee_email": absence.employee.email if absence.employee else None,
            "employee_full_name": f"{absence.employee.first_name} {absence.employee.last_name}" if absence.employee and absence.employee.first_name and absence.employee.last_name else None,
            # Absence information
            "absence_type": absence.absence_type,
            "absence_code": absence.absence_code,
            "start_date": absence.start_date.isoformat() if absence.start_date else None,
            "end_date": absence.end_date.isoformat() if absence.end_date else None,
            "duration_days": absence.duration_days,
            "duration_hours": absence.duration_hours,
            "status": absence.status,
            "reason": absence.reason,
            "comment": absence.comment,
            "last_synced_at": absence.last_synced_at.isoformat() if absence.last_synced_at else None,
            "created_at": absence.created_at.isoformat() if absence.created_at else None,
            "updated_at": absence.updated_at.isoformat() if absence.updated_at else None
        }
        for absence in absences
    ]


@router.get("/sync-logs")
async def get_sync_logs(
    sync_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get synchronization logs"""
    query = select(PayfitSyncLog)
    
    if sync_type:
        query = query.where(PayfitSyncLog.sync_type == sync_type)
    
    if status:
        query = query.where(PayfitSyncLog.sync_status == status)
    
    query = query.order_by(PayfitSyncLog.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "sync_type": log.sync_type,
            "sync_status": log.sync_status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": log.duration_seconds,
            "records_synced": log.records_synced,
            "records_created": log.records_created,
            "records_updated": log.records_updated,
            "records_failed": log.records_failed,
            "error_message": log.error_message,
            "triggered_by": log.triggered_by,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]