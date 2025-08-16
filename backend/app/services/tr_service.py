"""
Service for calculating meal voucher (Titres Restaurant) rights
Based on working days and Payfit absences
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import calendar
import holidays

from app.models.gryzzly import GryzzlyCollaborator
from app.models.payfit import PayfitEmployee, PayfitAbsence

import logging
logger = logging.getLogger(__name__)


class TRService:
    """Service for calculating meal voucher rights"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Initialize French holidays
        self.fr_holidays = holidays.France()
    
    def get_working_days(self, year: int, month: int) -> Dict[str, Any]:
        """
        Calculate working days for a given month
        Returns dict with working days count and list of dates
        """
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        working_days = []
        holiday_dates = []
        weekend_dates = []
        
        current_date = first_day
        while current_date <= last_day:
            # Check if it's a weekend
            if current_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
                weekend_dates.append(current_date.isoformat())
            # Check if it's a holiday
            elif current_date in self.fr_holidays:
                holiday_dates.append(current_date.isoformat())
            # It's a working day
            else:
                working_days.append(current_date.isoformat())
            
            current_date += timedelta(days=1)
        
        return {
            "year": year,
            "month": month,
            "working_days_count": len(working_days),
            "working_days": working_days,
            "holidays": holiday_dates,
            "weekends": weekend_dates,
            "total_days": (last_day - first_day).days + 1
        }
    
    async def get_employee_absences(self, email: str, year: int, month: int) -> Dict[str, Any]:
        """
        Get absences for an employee from Payfit for a given month
        Returns dict with absence days count and details
        """
        # Get the Payfit employee by email (take the first if duplicates)
        employee_query = select(PayfitEmployee).where(
            func.lower(PayfitEmployee.email) == email.lower()
        ).limit(1)
        employee_result = await self.session.execute(employee_query)
        payfit_employee = employee_result.scalar_one_or_none()
        
        if not payfit_employee:
            logger.warning(f"No Payfit employee found for email: {email}")
            return {
                "email": email,
                "absence_days": 0,
                "absences": []
            }
        
        # Get date range for the month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get absences that overlap with this month
        absences_query = select(PayfitAbsence).where(
            and_(
                PayfitAbsence.payfit_employee_id == payfit_employee.payfit_id,
                # Absence overlaps with the month
                or_(
                    # Absence starts in this month
                    and_(
                        PayfitAbsence.start_date >= first_day,
                        PayfitAbsence.start_date <= last_day
                    ),
                    # Absence ends in this month
                    and_(
                        PayfitAbsence.end_date >= first_day,
                        PayfitAbsence.end_date <= last_day
                    ),
                    # Absence spans the entire month
                    and_(
                        PayfitAbsence.start_date < first_day,
                        PayfitAbsence.end_date > last_day
                    )
                )
            )
        )
        
        absences_result = await self.session.execute(absences_query)
        absences = absences_result.scalars().all()
        
        # Calculate working days absent
        total_absence_days = 0
        absence_details = []
        
        for absence in absences:
            # Calculate the overlap period with the month
            start = max(absence.start_date, first_day)
            end = min(absence.end_date, last_day)
            
            # Count only working days in the absence period
            absence_working_days = 0
            current_date = start
            while current_date <= end:
                # Only count if it's a working day (not weekend or holiday)
                if current_date.weekday() not in [5, 6] and current_date not in self.fr_holidays:
                    absence_working_days += 1
                current_date += timedelta(days=1)
            
            total_absence_days += absence_working_days
            
            absence_details.append({
                "type": absence.absence_type,
                "start_date": absence.start_date.isoformat(),
                "end_date": absence.end_date.isoformat(),
                "working_days_in_month": absence_working_days,
                "status": absence.status
            })
        
        return {
            "email": email,
            "payfit_employee_id": payfit_employee.payfit_id,
            "absence_days": total_absence_days,
            "absences": absence_details
        }
    
    async def calculate_tr_rights(self, email: str, year: int, month: int) -> Dict[str, Any]:
        """
        Calculate TR rights for an employee for a given month
        TR rights = Working days - Absence days
        """
        # Get working days for the month
        working_days_info = self.get_working_days(year, month)
        
        # Get absences for the employee
        absences_info = await self.get_employee_absences(email, year, month)
        
        # Get employee info from Gryzzly (for matricule and name)
        employee_query = select(GryzzlyCollaborator).where(
            func.lower(GryzzlyCollaborator.email) == email.lower()
        )
        employee_result = await self.session.execute(employee_query)
        gryzzly_employee = employee_result.scalar_one_or_none()
        
        # Calculate TR rights
        tr_rights = working_days_info["working_days_count"] - absences_info["absence_days"]
        tr_rights = max(0, tr_rights)  # Can't be negative
        
        return {
            "email": email,
            "matricule": gryzzly_employee.matricule if gryzzly_employee else None,
            "first_name": gryzzly_employee.first_name if gryzzly_employee else None,
            "last_name": gryzzly_employee.last_name if gryzzly_employee else None,
            "year": year,
            "month": month,
            "working_days": working_days_info["working_days_count"],
            "absence_days": absences_info["absence_days"],
            "tr_rights": tr_rights,
            "absences": absences_info["absences"],
            "holidays": working_days_info["holidays"]
        }
    
    async def calculate_all_tr_rights(self, year: int, month: int) -> Dict[str, Any]:
        """
        Calculate TR rights for all employees eligible for TR
        Determines eligibility based on active Payfit contracts and manual overrides
        """
        # Import necessary models
        from app.models.tr_eligibility import TREligibilityOverride
        from app.models.payfit import PayfitContract
        from sqlalchemy.orm import selectinload
        
        # Get all active Gryzzly collaborators with matricule
        collaborators_query = select(GryzzlyCollaborator).where(
            and_(
                GryzzlyCollaborator.matricule.isnot(None),
                GryzzlyCollaborator.is_active == True
            )
        )
        collaborators_result = await self.session.execute(collaborators_query)
        gryzzly_collabs = collaborators_result.scalars().all()
        
        # Get all Payfit employees with their contracts
        payfit_query = select(PayfitEmployee).options(selectinload(PayfitEmployee.contracts))
        payfit_result = await self.session.execute(payfit_query)
        payfit_employees = payfit_result.scalars().all()
        
        # Create a map of Payfit employees by email
        payfit_map = {}
        for emp in payfit_employees:
            if emp.email:
                email_lower = emp.email.lower()
                # Keep the most recently created employee record if duplicates
                if email_lower not in payfit_map:
                    payfit_map[email_lower] = emp
                elif emp.created_at and payfit_map[email_lower].created_at:
                    if emp.created_at > payfit_map[email_lower].created_at:
                        payfit_map[email_lower] = emp
        
        # Get all TR eligibility overrides
        overrides_result = await self.session.execute(select(TREligibilityOverride))
        overrides = overrides_result.scalars().all()
        overrides_by_email = {override.email.lower(): override for override in overrides}
        
        # Build list of eligible collaborators
        eligible_collaborators = []
        for collab in gryzzly_collabs:
            if not collab.email:
                continue
            
            email_lower = collab.email.lower()
            
            # Check for manual override first
            override = overrides_by_email.get(email_lower)
            if override:
                eligible_tr = override.is_eligible
            else:
                # Check if there's an active Payfit contract
                eligible_tr = False
                payfit_emp = payfit_map.get(email_lower)
                if payfit_emp and payfit_emp.contracts:
                    # Check if there's at least one active contract
                    active_contracts = [c for c in payfit_emp.contracts if c.is_active]
                    eligible_tr = len(active_contracts) > 0
                else:
                    # If no Payfit data, default to eligible for active Gryzzly collaborators
                    eligible_tr = True
            
            if eligible_tr:
                eligible_collaborators.append({
                    'email': collab.email,
                    'matricule': collab.matricule,
                    'actif': collab.is_active,
                    'eligibleTR': eligible_tr,
                    'nom': f"{collab.first_name or ''} {collab.last_name or ''}".strip()
                })
        
        logger.info(f"Found {len(eligible_collaborators)} eligible collaborators for TR rights calculation")
        
        # Get working days for the month
        working_days_info = self.get_working_days(year, month)
        
        # Calculate TR rights for each eligible employee
        employees_rights = []
        for collaborator in eligible_collaborators:
            tr_info = await self.calculate_tr_rights(collaborator['email'], year, month)
            employees_rights.append(tr_info)
        
        return {
            "year": year,
            "month": month,
            "working_days": working_days_info["working_days_count"],
            "holidays": working_days_info["holidays"],
            "employees": employees_rights
        }
    
    def generate_csv(self, tr_data: Dict[str, Any]) -> str:
        """
        Generate CSV content for TR rights export
        Format: Annee;Mois;Matricule;Nb jours
        According to template: /docs/template_gryzzly/modeleFichierCommand.csv
        """
        csv_lines = []
        
        # Header exactly as in template with semicolon separator
        csv_lines.append("Annee;Mois;Matricule;Nb jours")
        
        # Empty line after header as in template
        csv_lines.append("")
        
        # Get year and month from the data
        year = tr_data.get("year")
        month = tr_data.get("month")
        
        # Data rows
        for employee in tr_data.get("employees", []):
            matricule = employee.get("matricule")
            tr_rights = employee.get("tr_rights", 0)
            
            # Only include employees with matricule
            if matricule:
                # Format: Year;Month(2 digits);Matricule;TR days
                csv_lines.append(f"{year};{month:02d};{matricule};{tr_rights}")
        
        # Empty line at the end as in template
        csv_lines.append("")
        
        return '\n'.join(csv_lines)