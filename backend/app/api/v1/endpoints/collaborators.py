"""
Collaborators API endpoints - Unified view of employees from multiple sources
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_async_session
from app.models.person import User
from app.models.payfit import PayfitEmployee, PayfitContract, PayfitAbsence
from app.models.gryzzly import GryzzlyCollaborator, GryzzlyDeclaration, GryzzlyProject, GryzzlyTask
from app.models.tr_eligibility import TREligibilityOverride
from app.models.forecast import Forecast
from datetime import date, datetime, timedelta
from calendar import monthrange
from pydantic import BaseModel
from typing import Optional as Opt
import holidays

router = APIRouter()

# Pydantic models for forecast operations
class ForecastCreate(BaseModel):
    """Model for creating forecast entries"""
    collaborator_id: str
    project_id: str
    task_id: Opt[str] = None
    date: date
    hours: float
    description: Opt[str] = None

class ForecastUpdate(BaseModel):
    """Model for updating forecast entries"""
    hours: float
    description: Opt[str] = None

class ForecastBatchCreate(BaseModel):
    """Model for creating multiple forecast entries at once"""
    collaborator_id: str
    project_id: str
    task_id: Opt[str] = None
    start_date: date
    end_date: date
    hours_per_day: float = 7.0
    description: Opt[str] = None

class ForecastGroupDelete(BaseModel):
    """Model for deleting a group of forecast entries"""
    forecast_ids: List[str]


@router.get("")
async def get_collaborators(
    active_only: bool = False,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get unified list of collaborators from both Payfit and Gryzzly
    Merges data from both sources based on email matching
    """
    
    # Get all Gryzzly collaborators
    gryzzly_query = select(GryzzlyCollaborator)
    if active_only:
        gryzzly_query = gryzzly_query.where(GryzzlyCollaborator.is_active == True)
    
    gryzzly_result = await session.execute(gryzzly_query)
    gryzzly_collaborators = gryzzly_result.scalars().all()
    
    # Get all Payfit employees with their contracts
    payfit_query = select(PayfitEmployee).options(selectinload(PayfitEmployee.contracts))
    if active_only:
        payfit_query = payfit_query.where(PayfitEmployee.is_active == True)
    
    payfit_result = await session.execute(payfit_query)
    payfit_employees = payfit_result.scalars().all()
    
    # Get all TR eligibility overrides
    overrides_result = await session.execute(select(TREligibilityOverride))
    overrides = overrides_result.scalars().all()
    overrides_by_email = {override.email.lower(): override for override in overrides}
    
    # Deduplicate Payfit employees by email (keep the most recent one)
    # This handles cases where employees have multiple records (e.g., internship → permanent contract)
    payfit_employees_by_email = {}
    for emp in payfit_employees:
        if emp.email:
            email_lower = emp.email.lower()
            # Keep the most recently created employee record
            if email_lower not in payfit_employees_by_email:
                payfit_employees_by_email[email_lower] = emp
            elif emp.created_at and payfit_employees_by_email[email_lower].created_at:
                if emp.created_at > payfit_employees_by_email[email_lower].created_at:
                    payfit_employees_by_email[email_lower] = emp
    
    # Create a map for quick lookup
    gryzzly_map = {collab.email.lower(): collab for collab in gryzzly_collaborators if collab.email}
    payfit_map = payfit_employees_by_email  # Already deduplicated by email
    
    # Merge collaborators
    collaborators = []
    processed_emails = set()
    
    # Process Gryzzly collaborators first (they have matricules)
    for gryzzly_collab in gryzzly_collaborators:
        if not gryzzly_collab.email:
            continue
            
        email_lower = gryzzly_collab.email.lower()
        processed_emails.add(email_lower)
        
        # Try to find matching Payfit employee
        payfit_emp = payfit_map.get(email_lower)
        
        # Determine eligibility for TR
        # First check for manual override
        override = overrides_by_email.get(email_lower)
        if override:
            eligible_tr = override.is_eligible
        else:
            # Otherwise, base on active contract
            eligible_tr = False
            if payfit_emp and payfit_emp.contracts:
                # Check if there's an active contract
                active_contracts = [c for c in payfit_emp.contracts if c.is_active]
                eligible_tr = len(active_contracts) > 0
        
        collaborator = {
            "id": str(gryzzly_collab.id),
            "nom": f"{gryzzly_collab.first_name or ''} {gryzzly_collab.last_name or ''}".strip() or gryzzly_collab.email,
            "email": gryzzly_collab.email,
            "matricule": gryzzly_collab.matricule,
            "department": gryzzly_collab.department or (payfit_emp.department if payfit_emp else None),
            "position": gryzzly_collab.position or (payfit_emp.position if payfit_emp else None),
            "actif": gryzzly_collab.is_active,
            "eligibleTR": eligible_tr,
            "source": "both" if payfit_emp else "gryzzly",
            "gryzzly_id": gryzzly_collab.gryzzly_id,
            "payfit_id": payfit_emp.payfit_id if payfit_emp else None,
            "has_active_contract": eligible_tr,
            "last_synced_at": gryzzly_collab.last_synced_at.isoformat() if gryzzly_collab.last_synced_at else None
        }
        
        collaborators.append(collaborator)
    
    # Process remaining Payfit employees not in Gryzzly
    for email_lower, payfit_emp in payfit_map.items():
        if email_lower in processed_emails:
            continue
        
        # Determine eligibility for TR  
        # First check for manual override
        override = overrides_by_email.get(email_lower)
        if override:
            eligible_tr = override.is_eligible
        else:
            # Otherwise, base on active contract
            eligible_tr = False
            if payfit_emp.contracts:
                active_contracts = [c for c in payfit_emp.contracts if c.is_active]
                eligible_tr = len(active_contracts) > 0
        
        collaborator = {
            "id": f"payfit_{payfit_emp.id}",
            "nom": f"{payfit_emp.first_name or ''} {payfit_emp.last_name or ''}".strip() or payfit_emp.email,
            "email": payfit_emp.email,
            "matricule": None,  # No matricule from Payfit only
            "department": payfit_emp.department,
            "position": payfit_emp.position,
            "actif": payfit_emp.is_active,
            "eligibleTR": eligible_tr,
            "source": "payfit",
            "gryzzly_id": None,
            "payfit_id": payfit_emp.payfit_id,
            "has_active_contract": eligible_tr,
            "last_synced_at": payfit_emp.last_synced_at.isoformat() if payfit_emp.last_synced_at else None
        }
        
        collaborators.append(collaborator)
    
    # Sort by name
    collaborators.sort(key=lambda x: x["nom"].lower())
    
    return collaborators


@router.patch("/{collaborator_id}")
async def update_collaborator(
    collaborator_id: str,
    update_data: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update collaborator properties (active status, TR eligibility)
    """
    
    # Determine the email for this collaborator
    email = None
    
    # Check if it's a Gryzzly collaborator or Payfit employee
    if collaborator_id.startswith("payfit_"):
        # It's a Payfit-only employee
        payfit_id = collaborator_id.replace("payfit_", "")
        
        # Get the Payfit employee
        result = await session.execute(
            select(PayfitEmployee).where(PayfitEmployee.id == payfit_id)
        )
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        email = employee.email
        
        # Update active status if provided
        if "actif" in update_data:
            employee.is_active = update_data["actif"]
        
        await session.commit()
    
    else:
        # It's a Gryzzly collaborator
        result = await session.execute(
            select(GryzzlyCollaborator).where(GryzzlyCollaborator.id == collaborator_id)
        )
        collaborator = result.scalar_one_or_none()
        
        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator not found")
        
        email = collaborator.email
        
        # Update active status if provided
        if "actif" in update_data:
            collaborator.is_active = update_data["actif"]
        
        # Update matricule if provided
        if "matricule" in update_data:
            collaborator.matricule = update_data["matricule"]
        
        await session.commit()
        
        # Also check if we need to update the corresponding Payfit employee
        if collaborator.email:
            payfit_result = await session.execute(
                select(PayfitEmployee).where(
                    PayfitEmployee.email.ilike(collaborator.email)
                )
                .order_by(PayfitEmployee.created_at.desc())  # Take the most recent in case of duplicates
                .limit(1)
            )
            payfit_emp = payfit_result.scalar_one_or_none()
            
            if payfit_emp and "actif" in update_data:
                payfit_emp.is_active = update_data["actif"]
                await session.commit()
    
    # Handle TR eligibility updates via override table
    if "eligibleTR" in update_data and email:
        # Check if an override already exists
        override_result = await session.execute(
            select(TREligibilityOverride).where(
                TREligibilityOverride.email.ilike(email)
            )
        )
        override = override_result.scalar_one_or_none()
        
        if override:
            # Update existing override
            override.is_eligible = update_data["eligibleTR"]
            override.modified_by = current_user.id if current_user else None
        else:
            # Create new override
            override = TREligibilityOverride(
                collaborator_id=collaborator_id,
                email=email.lower(),
                is_eligible=update_data["eligibleTR"],
                modified_by=current_user.id if current_user else None,
                reason="Manual override from collaborateurs page"
            )
            session.add(override)
        
        await session.commit()
    
    return {
        "success": True,
        "message": "Collaborator updated successfully",
        "id": collaborator_id
    }


@router.get("/stats")
async def get_collaborator_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get statistics about collaborators
    """
    
    # Count Gryzzly collaborators
    gryzzly_count_result = await session.execute(
        select(GryzzlyCollaborator).where(GryzzlyCollaborator.is_active == True)
    )
    gryzzly_active = len(gryzzly_count_result.scalars().all())
    
    gryzzly_total_result = await session.execute(select(GryzzlyCollaborator))
    gryzzly_total = len(gryzzly_total_result.scalars().all())
    
    # Count Payfit employees
    payfit_count_result = await session.execute(
        select(PayfitEmployee).where(PayfitEmployee.is_active == True)
    )
    payfit_active = len(payfit_count_result.scalars().all())
    
    payfit_total_result = await session.execute(select(PayfitEmployee))
    payfit_total = len(payfit_total_result.scalars().all())
    
    # Count employees with active contracts (eligible for TR)
    contracts_result = await session.execute(
        select(PayfitContract).where(PayfitContract.is_active == True)
    )
    active_contracts = contracts_result.scalars().all()
    
    # Get unique employee IDs with active contracts
    employees_with_contracts = set()
    for contract in active_contracts:
        employees_with_contracts.add(contract.payfit_employee_id)
    
    return {
        "total_collaborators": max(gryzzly_total, payfit_total),  # Use max to avoid double counting
        "active_collaborators": max(gryzzly_active, payfit_active),
        "gryzzly": {
            "total": gryzzly_total,
            "active": gryzzly_active
        },
        "payfit": {
            "total": payfit_total,
            "active": payfit_active
        },
        "eligible_tr": len(employees_with_contracts),
        "active_contracts": len(active_contracts)
    }


@router.get("/plan-charge")
async def get_plan_charge(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get plan de charge data for a specific month
    Returns Gryzzly declarations and Payfit absences for all active collaborators
    """
    
    # Get the date range for the month (for display)
    _, last_day = monthrange(year, month)
    month_start_date = date(year, month, 1)
    month_end_date = date(year, month, last_day)
    
    # Query declarations from 6 months before to 6 months after the requested month
    # This ensures we have data available when navigating between months
    query_start_date = month_start_date - timedelta(days=180)
    query_end_date = month_end_date + timedelta(days=180)
    
    # Get all active collaborators using the existing get_collaborators logic
    # Get all Gryzzly collaborators
    gryzzly_query = select(GryzzlyCollaborator).where(GryzzlyCollaborator.is_active == True)
    gryzzly_result = await session.execute(gryzzly_query)
    gryzzly_collaborators = gryzzly_result.scalars().all()
    
    # Get all active Payfit employees with their contracts
    payfit_query = select(PayfitEmployee).options(
        selectinload(PayfitEmployee.contracts)
    ).where(PayfitEmployee.is_active == True)
    payfit_result = await session.execute(payfit_query)
    payfit_employees = payfit_result.scalars().all()
    
    # Deduplicate Payfit employees by email
    payfit_employees_by_email = {}
    for emp in payfit_employees:
        if emp.email:
            email_lower = emp.email.lower()
            if email_lower not in payfit_employees_by_email:
                payfit_employees_by_email[email_lower] = emp
            elif emp.created_at and payfit_employees_by_email[email_lower].created_at:
                if emp.created_at > payfit_employees_by_email[email_lower].created_at:
                    payfit_employees_by_email[email_lower] = emp
    
    # Get all Gryzzly declarations for the wider date range with project info
    # We fetch 6 months before and after to have data ready for navigation
    declarations_query = select(GryzzlyDeclaration).options(
        selectinload(GryzzlyDeclaration.project),
        selectinload(GryzzlyDeclaration.collaborator)
    ).where(
        and_(
            GryzzlyDeclaration.date >= query_start_date,
            GryzzlyDeclaration.date <= query_end_date
        )
    )
    declarations_result = await session.execute(declarations_query)
    all_declarations = declarations_result.scalars().all()
    
    # Get all Payfit absences for the month
    absences_query = select(PayfitAbsence).options(
        selectinload(PayfitAbsence.employee)
    ).where(
        and_(
            PayfitAbsence.start_date <= month_end_date,
            PayfitAbsence.end_date >= month_start_date,
            PayfitAbsence.status.in_(['approved', 'pending'])  # Only show approved or pending absences
        )
    )
    absences_result = await session.execute(absences_query)
    all_absences = absences_result.scalars().all()
    
    # Build the response structure
    plan_charge_data = []
    
    # Process Gryzzly collaborators
    for gryzzly_collab in gryzzly_collaborators:
        if not gryzzly_collab.email:
            continue
            
        email_lower = gryzzly_collab.email.lower()
        payfit_emp = payfit_employees_by_email.get(email_lower)
        
        # Get declarations for this collaborator within the requested month
        collab_declarations = [
            d for d in all_declarations 
            if d.collaborator_id == gryzzly_collab.id
            and d.date >= month_start_date
            and d.date <= month_end_date
        ]
        
        # Get absences for this collaborator (if they have a Payfit record)
        collab_absences = []
        if payfit_emp:
            collab_absences = [
                a for a in all_absences 
                if a.payfit_employee_id == payfit_emp.id
            ]
        
        # Format declarations by date
        declarations_by_date = {}
        for decl in collab_declarations:
            date_str = decl.date.isoformat()
            if date_str not in declarations_by_date:
                declarations_by_date[date_str] = []
            
            declarations_by_date[date_str].append({
                "project_id": str(decl.project_id),
                "project_name": decl.project.name if decl.project else "Unknown",
                "project_code": decl.project.code if decl.project else None,
                "hours": decl.duration_hours,
                "description": decl.description,
                "status": decl.status,
                "is_billable": decl.is_billable
            })
        
        # Format absences
        absences_list = []
        for absence in collab_absences:
            # Calculate which days of the month this absence covers
            absence_start = max(absence.start_date, month_start_date)
            absence_end = min(absence.end_date, month_end_date)
            
            absences_list.append({
                "type": absence.absence_type,
                "start_date": absence_start.isoformat(),
                "end_date": absence_end.isoformat(),
                "duration_days": absence.duration_days,
                "status": absence.status
            })
        
        plan_charge_data.append({
            "collaborator_id": str(gryzzly_collab.id),
            "name": f"{gryzzly_collab.first_name or ''} {gryzzly_collab.last_name or ''}".strip() or gryzzly_collab.email,
            "email": gryzzly_collab.email,
            "matricule": gryzzly_collab.matricule,
            "gryzzly_id": gryzzly_collab.gryzzly_id,
            "payfit_id": payfit_emp.payfit_id if payfit_emp else None,
            "declarations": declarations_by_date,
            "absences": absences_list
        })
    
    # Process Payfit-only employees (no Gryzzly record)
    processed_emails = {c.email.lower() for c in gryzzly_collaborators if c.email}
    
    for email_lower, payfit_emp in payfit_employees_by_email.items():
        if email_lower in processed_emails:
            continue
        
        # Get absences for this employee
        collab_absences = [
            a for a in all_absences 
            if a.payfit_employee_id == payfit_emp.id
        ]
        
        # Format absences
        absences_list = []
        for absence in collab_absences:
            # Calculate which days of the month this absence covers
            absence_start = max(absence.start_date, month_start_date)
            absence_end = min(absence.end_date, month_end_date)
            
            absences_list.append({
                "type": absence.absence_type,
                "start_date": absence_start.isoformat(),
                "end_date": absence_end.isoformat(),
                "duration_days": absence.duration_days,
                "status": absence.status
            })
        
        plan_charge_data.append({
            "collaborator_id": f"payfit_{payfit_emp.id}",
            "name": f"{payfit_emp.first_name or ''} {payfit_emp.last_name or ''}".strip() or payfit_emp.email,
            "email": payfit_emp.email,
            "matricule": None,
            "gryzzly_id": None,
            "payfit_id": payfit_emp.payfit_id,
            "declarations": {},  # No Gryzzly declarations
            "absences": absences_list
        })
    
    return {
        "year": year,
        "month": month,
        "start_date": month_start_date.isoformat(),
        "end_date": month_end_date.isoformat(),
        "collaborators": plan_charge_data
    }


@router.get("/projects-with-tasks")
async def get_projects_with_tasks(
    active_only: bool = True,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get active projects with their associated tasks
    Used for forecast dialog project/task selection
    """
    from app.models.gryzzly import GryzzlyTask
    from sqlalchemy.orm import selectinload
    
    # Get projects with their tasks
    query = select(GryzzlyProject).options(selectinload(GryzzlyProject.tasks))
    
    if active_only:
        query = query.where(GryzzlyProject.is_active == True)
    
    query = query.order_by(GryzzlyProject.name)
    result = await session.execute(query)
    projects = result.scalars().all()
    
    # Format response
    projects_data = []
    for project in projects:
        # Filter active tasks if needed
        tasks = project.tasks
        if active_only:
            tasks = [t for t in tasks if t.is_active]
        
        projects_data.append({
            "id": str(project.id),
            "gryzzly_id": project.gryzzly_id,
            "name": project.name,
            "code": project.code,
            "description": project.description,
            "client_name": project.client_name,
            "is_active": project.is_active,
            "is_billable": project.is_billable,
            "tasks": [
                {
                    "id": str(task.id),
                    "gryzzly_id": task.gryzzly_id,
                    "name": task.name,
                    "code": task.code,
                    "description": task.description,
                    "task_type": task.task_type,
                    "is_active": task.is_active,
                    "is_billable": task.is_billable
                }
                for task in tasks
            ]
        })
    
    return projects_data


@router.post("/forecast")
async def create_forecast(
    forecast_data: ForecastCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a single forecast entry
    """
    # Check if forecast already exists for this date/collaborator/project
    existing_query = select(Forecast).where(
        and_(
            Forecast.collaborator_id == forecast_data.collaborator_id,
            Forecast.project_id == forecast_data.project_id,
            Forecast.date == forecast_data.date
        )
    )
    
    if forecast_data.task_id:
        existing_query = existing_query.where(Forecast.task_id == forecast_data.task_id)
    else:
        existing_query = existing_query.where(Forecast.task_id == None)
    
    existing_result = await session.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # Update existing forecast
        existing.hours = forecast_data.hours
        existing.description = forecast_data.description
        existing.modified_by = current_user.id if current_user else None
        existing.updated_at = datetime.utcnow()
        
        await session.commit()
        
        return {
            "id": str(existing.id),
            "message": "Forecast updated",
            "action": "updated"
        }
    else:
        # Create new forecast
        forecast = Forecast(
            collaborator_id=forecast_data.collaborator_id,
            project_id=forecast_data.project_id,
            task_id=forecast_data.task_id,
            date=forecast_data.date,
            hours=forecast_data.hours,
            description=forecast_data.description,
            created_by=current_user.id if current_user else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(forecast)
        await session.commit()
        
        return {
            "id": str(forecast.id),
            "message": "Forecast created",
            "action": "created"
        }


@router.post("/forecast/batch")
async def create_forecast_batch(
    forecast_data: ForecastBatchCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create multiple forecast entries for a date range
    Skips weekends and holidays
    """
    from app.models.gryzzly import GryzzlyTask
    
    # Get list of dates in range (excluding weekends and holidays)
    fr_holidays = holidays.France()
    dates_to_create = []
    current_date = forecast_data.start_date
    
    while current_date <= forecast_data.end_date:
        # Skip weekends and holidays
        if current_date.weekday() < 5 and current_date not in fr_holidays:  # Monday = 0, Friday = 4
            dates_to_create.append(current_date)
        current_date += timedelta(days=1)
    
    created_count = 0
    updated_count = 0
    
    for forecast_date in dates_to_create:
        # Check if forecast already exists
        existing_query = select(Forecast).where(
            and_(
                Forecast.collaborator_id == forecast_data.collaborator_id,
                Forecast.project_id == forecast_data.project_id,
                Forecast.date == forecast_date
            )
        )
        
        if forecast_data.task_id:
            existing_query = existing_query.where(Forecast.task_id == forecast_data.task_id)
        else:
            existing_query = existing_query.where(Forecast.task_id == None)
        
        existing_result = await session.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update existing forecast
            existing.hours = forecast_data.hours_per_day
            existing.description = forecast_data.description
            existing.modified_by = current_user.id if current_user else None
            existing.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new forecast
            forecast = Forecast(
                collaborator_id=forecast_data.collaborator_id,
                project_id=forecast_data.project_id,
                task_id=forecast_data.task_id,
                date=forecast_date,
                hours=forecast_data.hours_per_day,
                description=forecast_data.description,
                created_by=current_user.id if current_user else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(forecast)
            created_count += 1
    
    await session.commit()
    
    return {
        "message": f"Batch forecast operation completed",
        "created": created_count,
        "updated": updated_count,
        "total_days": len(dates_to_create)
    }


@router.get("/forecast")
async def get_forecasts(
    year: int,
    month: int,
    collaborator_id: Opt[str] = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get forecast entries for a specific month
    """
    from app.models.gryzzly import GryzzlyTask
    from sqlalchemy.orm import selectinload
    
    # Get the date range for the month
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # Build query
    query = select(Forecast).options(
        selectinload(Forecast.collaborator),
        selectinload(Forecast.project),
        selectinload(Forecast.task)
    ).where(
        and_(
            Forecast.date >= start_date,
            Forecast.date <= end_date
        )
    )
    
    if collaborator_id:
        query = query.where(Forecast.collaborator_id == collaborator_id)
    
    query = query.order_by(Forecast.date, Forecast.collaborator_id)
    
    result = await session.execute(query)
    forecasts = result.scalars().all()
    
    # Group forecasts by collaborator and date
    forecasts_by_collaborator = {}
    
    for forecast in forecasts:
        collab_id = str(forecast.collaborator_id)
        
        if collab_id not in forecasts_by_collaborator:
            forecasts_by_collaborator[collab_id] = {
                "collaborator_id": collab_id,
                "collaborator_name": f"{forecast.collaborator.first_name or ''} {forecast.collaborator.last_name or ''}".strip() if forecast.collaborator else "Unknown",
                "forecasts": {}
            }
        
        date_str = forecast.date.isoformat()
        
        if date_str not in forecasts_by_collaborator[collab_id]["forecasts"]:
            forecasts_by_collaborator[collab_id]["forecasts"][date_str] = []
        
        forecasts_by_collaborator[collab_id]["forecasts"][date_str].append({
            "id": str(forecast.id),
            "project_id": str(forecast.project_id),
            "project_name": forecast.project.name if forecast.project else "Unknown",
            "project_code": forecast.project.code if forecast.project else None,
            "task_id": str(forecast.task_id) if forecast.task_id else None,
            "task_name": forecast.task.name if forecast.task else None,
            "hours": forecast.hours,
            "description": forecast.description,
            "created_at": forecast.created_at.isoformat() if forecast.created_at else None,
            "updated_at": forecast.updated_at.isoformat() if forecast.updated_at else None
        })
    
    return {
        "year": year,
        "month": month,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "collaborators": list(forecasts_by_collaborator.values())
    }


@router.put("/forecast/{forecast_id}")
async def update_forecast(
    forecast_id: str,
    update_data: ForecastUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update a specific forecast entry
    """
    # Get the forecast
    result = await session.execute(
        select(Forecast).where(Forecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    # Update fields
    forecast.hours = update_data.hours
    forecast.description = update_data.description
    forecast.modified_by = current_user.id if current_user else None
    forecast.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return {
        "id": str(forecast.id),
        "message": "Forecast updated successfully"
    }


@router.delete("/forecast/group")
async def delete_forecast_group(
    group_data: ForecastGroupDelete,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a group of forecast entries
    """
    deleted_count = 0
    
    for forecast_id in group_data.forecast_ids:
        result = await session.execute(
            select(Forecast).where(Forecast.id == forecast_id)
        )
        forecast = result.scalar_one_or_none()
        
        if forecast:
            await session.delete(forecast)
            deleted_count += 1
    
    await session.commit()
    
    return {
        "message": f"Deleted {deleted_count} forecast entries",
        "deleted_count": deleted_count
    }


@router.delete("/forecast/{forecast_id}")
async def delete_forecast(
    forecast_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a specific forecast entry
    """
    # Get the forecast
    result = await session.execute(
        select(Forecast).where(Forecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    # Delete the forecast
    await session.delete(forecast)
    await session.commit()
    
    return {
        "message": "Forecast deleted successfully"
    }


@router.get("/forecast/{forecast_id}/group")
async def get_forecast_group(
    forecast_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the group of forecasts that were created together.
    Identifies forecasts that belong to the same batch based on:
    - Same collaborator, project, task
    - Same hours per day
    - Same description
    - Created within a small time window
    """
    from sqlalchemy import func
    from datetime import timedelta
    
    # Get the reference forecast
    result = await session.execute(
        select(Forecast).where(Forecast.id == forecast_id)
    )
    reference_forecast = result.scalar_one_or_none()
    
    if not reference_forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    # Define time window for grouping (forecasts created within 2 seconds of each other)
    time_window = timedelta(seconds=2)
    min_time = reference_forecast.created_at - time_window
    max_time = reference_forecast.created_at + time_window
    
    # Find all forecasts in the same group
    group_query = select(Forecast).where(
        and_(
            Forecast.collaborator_id == reference_forecast.collaborator_id,
            Forecast.project_id == reference_forecast.project_id,
            Forecast.hours == reference_forecast.hours,
            Forecast.created_at >= min_time,
            Forecast.created_at <= max_time
        )
    )
    
    # Handle task_id (can be None)
    if reference_forecast.task_id:
        group_query = group_query.where(Forecast.task_id == reference_forecast.task_id)
    else:
        group_query = group_query.where(Forecast.task_id == None)
    
    # Handle description (can be None)
    if reference_forecast.description:
        group_query = group_query.where(Forecast.description == reference_forecast.description)
    else:
        group_query = group_query.where(Forecast.description == None)
    
    result = await session.execute(group_query.order_by(Forecast.date))
    group_forecasts = result.scalars().all()
    
    if not group_forecasts:
        # If no group found, return just the single forecast
        group_forecasts = [reference_forecast]
    
    # Get min and max dates
    dates = [f.date for f in group_forecasts]
    start_date = min(dates)
    end_date = max(dates)
    
    # Get project and task info
    project_result = await session.execute(
        select(GryzzlyProject).where(GryzzlyProject.id == reference_forecast.project_id)
    )
    project = project_result.scalar_one_or_none()
    
    task = None
    if reference_forecast.task_id:
        task_result = await session.execute(
            select(GryzzlyTask).where(GryzzlyTask.id == reference_forecast.task_id)
        )
        task = task_result.scalar_one_or_none()
    
    return {
        "forecast_ids": [str(f.id) for f in group_forecasts],
        "collaborator_id": str(reference_forecast.collaborator_id),
        "project_id": str(reference_forecast.project_id),
        "project_name": project.name if project else None,
        "task_id": str(reference_forecast.task_id) if reference_forecast.task_id else None,
        "task_name": task.name if task else None,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hours_per_day": reference_forecast.hours,
        "description": reference_forecast.description,
        "total_days": len(group_forecasts)
    }