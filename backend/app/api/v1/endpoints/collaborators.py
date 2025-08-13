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
from app.models.gryzzly import GryzzlyCollaborator, GryzzlyDeclaration, GryzzlyProject
from app.models.tr_eligibility import TREligibilityOverride
from datetime import date, datetime, timedelta
from calendar import monthrange

router = APIRouter()


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
    
    # Get the date range for the month
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
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
    
    # Get all Gryzzly declarations for the month with project info
    declarations_query = select(GryzzlyDeclaration).options(
        selectinload(GryzzlyDeclaration.project),
        selectinload(GryzzlyDeclaration.collaborator)
    ).where(
        and_(
            GryzzlyDeclaration.date >= start_date,
            GryzzlyDeclaration.date <= end_date
        )
    )
    declarations_result = await session.execute(declarations_query)
    all_declarations = declarations_result.scalars().all()
    
    # Get all Payfit absences for the month
    absences_query = select(PayfitAbsence).options(
        selectinload(PayfitAbsence.employee)
    ).where(
        and_(
            PayfitAbsence.start_date <= end_date,
            PayfitAbsence.end_date >= start_date,
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
        
        # Get declarations for this collaborator
        collab_declarations = [
            d for d in all_declarations 
            if d.collaborator_id == gryzzly_collab.id
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
            absence_start = max(absence.start_date, start_date)
            absence_end = min(absence.end_date, end_date)
            
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
            absence_start = max(absence.start_date, start_date)
            absence_end = min(absence.end_date, end_date)
            
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
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "collaborators": plan_charge_data
    }