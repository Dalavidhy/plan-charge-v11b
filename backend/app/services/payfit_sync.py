"""
Payfit synchronization service for managing data sync operations
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from app.services.payfit_client import PayfitAPIClient
from app.models.payfit import (
    PayfitEmployee,
    PayfitContract,
    PayfitAbsence,
    PayfitSyncLog
)
from app.models.person import User

logger = logging.getLogger(__name__)


class PayfitSyncService:
    """Service for synchronizing data from Payfit API to local database"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = PayfitAPIClient()
    
    async def sync_all(self, triggered_by: str = "system") -> Dict[str, Any]:
        """Perform complete synchronization of all Payfit data"""
        sync_log = PayfitSyncLog(
            sync_type="full",
            sync_status="started",
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        self.db.add(sync_log)
        await self.db.commit()
        
        results = {
            "employees": {"created": 0, "updated": 0, "failed": 0},
            "contracts": {"created": 0, "updated": 0, "failed": 0},
            "absences": {"created": 0, "updated": 0, "failed": 0},
            "errors": []
        }
        
        # Check if Payfit is properly configured
        if not self.client.is_configured:
            logger.info("Payfit API is in mock mode - skipping sync")
            sync_log.sync_status = "success"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = 0
            sync_log.records_synced = 0
            results["errors"].append("Payfit API not configured - mock mode active")
            await self.db.commit()
            return results
        
        try:
            # Sync employees first
            employee_result = await self.sync_employees()
            results["employees"] = employee_result
            
            # Then sync contracts
            contract_result = await self.sync_contracts()
            results["contracts"] = contract_result
            
            # Finally sync absences
            absence_result = await self.sync_absences()
            results["absences"] = absence_result
            
            # Update sync log
            sync_log.sync_status = "success"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int(
                (sync_log.completed_at - sync_log.started_at).total_seconds()
            )
            sync_log.records_synced = (
                results["employees"]["created"] + results["employees"]["updated"] +
                results["contracts"]["created"] + results["contracts"]["updated"] +
                results["absences"]["created"] + results["absences"]["updated"]
            )
            sync_log.records_created = (
                results["employees"]["created"] +
                results["contracts"]["created"] +
                results["absences"]["created"]
            )
            sync_log.records_updated = (
                results["employees"]["updated"] +
                results["contracts"]["updated"] +
                results["absences"]["updated"]
            )
            sync_log.records_failed = (
                results["employees"]["failed"] +
                results["contracts"]["failed"] +
                results["absences"]["failed"]
            )
            
        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}")
            sync_log.sync_status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            results["errors"].append(str(e))
        
        await self.db.commit()
        return results
    
    async def sync_employees(self) -> Dict[str, int]:
        """Sync employees from Payfit"""
        sync_result = {"created": 0, "updated": 0, "failed": 0}
        
        # Check if Payfit is properly configured
        if not self.client.is_configured:
            logger.info("Payfit API is in mock mode - skipping employee sync")
            return sync_result
        
        try:
            # Get all employees from Payfit
            payfit_employees = await self.client.get_all_employees(include_terminated=True)
            
            for emp_data in payfit_employees:
                try:
                    # Check if employee already exists
                    stmt = select(PayfitEmployee).where(
                        PayfitEmployee.payfit_id == emp_data["id"]
                    )
                    db_result = await self.db.execute(stmt)
                    existing = db_result.scalar_one_or_none()
                    
                    # Parse employee data
                    employee_dict = self._parse_employee_data(emp_data)
                    
                    if existing:
                        # Update existing employee
                        for key, value in employee_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        sync_result["updated"] += 1
                    else:
                        # Create new employee
                        new_employee = PayfitEmployee(**employee_dict)
                        self.db.add(new_employee)
                        sync_result["created"] += 1
                        
                        # Try to link with local user by email
                        await self._link_employee_to_user(new_employee)
                    
                except Exception as e:
                    logger.error(f"Failed to sync employee {emp_data.get('id')}: {str(e)}")
                    sync_result["failed"] += 1
            
            await self.db.commit()
            logger.info(f"Employee sync completed: {sync_result}")
            
        except Exception as e:
            logger.error(f"Employee sync failed: {str(e)}")
            raise
        
        return sync_result
    
    async def sync_contracts(self) -> Dict[str, int]:
        """Sync contracts from Payfit"""
        sync_result = {"created": 0, "updated": 0, "failed": 0}
        
        try:
            # Get all contracts from Payfit
            payfit_contracts = await self.client.get_all_contracts()
            
            for contract_data in payfit_contracts:
                try:
                    # Check if contract already exists
                    stmt = select(PayfitContract).where(
                        PayfitContract.payfit_id == contract_data["id"]
                    )
                    db_result = await self.db.execute(stmt)
                    existing = db_result.scalar_one_or_none()
                    
                    # Parse contract data
                    contract_dict = self._parse_contract_data(contract_data)
                    
                    if existing:
                        # Update existing contract
                        for key, value in contract_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        sync_result["updated"] += 1
                    else:
                        # Create new contract
                        new_contract = PayfitContract(**contract_dict)
                        self.db.add(new_contract)
                        sync_result["created"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync contract {contract_data.get('id')}: {str(e)}")
                    sync_result["failed"] += 1
            
            await self.db.commit()
            logger.info(f"Contract sync completed: {sync_result}")
            
        except Exception as e:
            logger.error(f"Contract sync failed: {str(e)}")
            raise
        
        return sync_result
    
    async def sync_absences(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, int]:
        """Sync absences from Payfit"""
        sync_result = {"created": 0, "updated": 0, "failed": 0}
        
        # Default to 6 months before and 6 months after current date
        today = date.today()
        if not start_date:
            # 6 months before today
            start_date = today - timedelta(days=180)
        if not end_date:
            # 6 months after today
            end_date = today + timedelta(days=180)
        
        try:
            # Build a mapping of contract ID to employee ID
            contract_employee_map = {}
            stmt = select(PayfitContract)
            db_result = await self.db.execute(stmt)
            contracts = db_result.scalars().all()
            for contract in contracts:
                if contract.payfit_id and contract.payfit_employee_id:
                    contract_employee_map[contract.payfit_id] = contract.payfit_employee_id
            
            # Get all absences from Payfit
            payfit_absences = await self.client.get_all_absences(
                start_date=start_date,
                end_date=end_date
            )
            
            for absence_data in payfit_absences:
                try:
                    # Check if absence already exists
                    stmt = select(PayfitAbsence).where(
                        PayfitAbsence.payfit_id == absence_data["id"]
                    )
                    db_result = await self.db.execute(stmt)
                    existing = db_result.scalar_one_or_none()
                    
                    # Add the contract-to-employee mapping if we have a contractId
                    contract_id = absence_data.get("contractId")
                    if contract_id and contract_id in contract_employee_map:
                        absence_data["collaboratorId"] = contract_employee_map[contract_id]
                    
                    # Parse absence data
                    absence_dict = self._parse_absence_data(absence_data)
                    
                    # Skip if we don't have a valid employee ID
                    if not absence_dict.get("payfit_employee_id"):
                        logger.warning(f"Skipping absence {absence_data.get('id')} - no employee ID found")
                        sync_result["failed"] += 1
                        continue
                    
                    # Verify that the employee exists
                    stmt_emp = select(PayfitEmployee).where(
                        PayfitEmployee.payfit_id == absence_dict["payfit_employee_id"]
                    )
                    emp_result = await self.db.execute(stmt_emp)
                    employee = emp_result.scalar_one_or_none()
                    
                    if not employee:
                        logger.warning(f"Skipping absence {absence_data.get('id')} - employee {absence_dict['payfit_employee_id']} not found")
                        sync_result["failed"] += 1
                        continue
                    
                    if existing:
                        # Update existing absence
                        for key, value in absence_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        sync_result["updated"] += 1
                    else:
                        # Create new absence
                        new_absence = PayfitAbsence(**absence_dict)
                        self.db.add(new_absence)
                        sync_result["created"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync absence {absence_data.get('id')}: {str(e)}")
                    sync_result["failed"] += 1
            
            await self.db.commit()
            logger.info(f"Absence sync completed: {sync_result}")
            
        except Exception as e:
            logger.error(f"Absence sync failed: {str(e)}")
            raise
        
        return sync_result
    
    def _parse_employee_data(self, data: Dict) -> Dict:
        """Parse Payfit employee data to match our model"""
        # Extract email from emails array
        email = ""
        emails = data.get("emails", [])
        if emails and len(emails) > 0:
            # Prefer professional email, fallback to personal
            for email_obj in emails:
                if email_obj.get("type") == "professional":
                    email = email_obj.get("email", "")
                    break
            if not email and emails:
                email = emails[0].get("email", "")
        
        # Get first active contract if available
        contracts = data.get("contracts", [])
        position = None
        hire_date = None
        termination_date = None
        is_active = False
        
        for contract in contracts:
            if contract.get("status") == "ACTIVE":
                is_active = True
                hire_date = self._parse_date(contract.get("startDate"))
                position = contract.get("jobTitle")
                break
            # Get termination date from ended contracts
            if contract.get("endDate"):
                termination_date = self._parse_date(contract.get("endDate"))
        
        return {
            "payfit_id": data["id"],
            "email": email,
            "first_name": data.get("firstName", ""),
            "last_name": data.get("lastName", ""),
            "registration_number": data.get("matricule"),
            "birth_date": self._parse_date(data.get("birthDate")),
            "gender": data.get("gender"),
            "nationality": data.get("nationality"),
            "department": data.get("teamName"),  # Team name is closest to department
            "position": position,
            "hire_date": hire_date,
            "termination_date": termination_date,
            "is_active": is_active,
            "manager_payfit_id": data.get("managerId"),
            "raw_data": data
        }
    
    def _parse_contract_data(self, data: Dict) -> Dict:
        """Parse Payfit contract data to match our model"""
        # Contracts come from within collaborators, so they have different structure
        # Make sure we have a valid start date
        start_date = self._parse_date(data.get("startDate"))
        if not start_date:
            # Use a default date if no start date is provided
            start_date = date(2020, 1, 1)
            logger.warning(f"Contract {data.get('id')} has no start date, using default")
        
        return {
            "payfit_id": data.get("id", ""),
            "payfit_employee_id": data.get("collaboratorId", ""),  # Added by our client
            "contract_type": data.get("contractType"),
            "job_title": data.get("jobTitle"),
            "start_date": start_date,  # Required field
            "end_date": self._parse_date(data.get("endDate")),
            "weekly_hours": data.get("weeklyHours"),
            "daily_hours": data.get("dailyHours"),
            "annual_hours": data.get("annualHours"),
            "part_time_percentage": data.get("partTimePercentage"),
            "is_active": data.get("status") == "ACTIVE",
            "probation_end_date": self._parse_date(data.get("probationEndDate")),
            "raw_data": data
        }
    
    def _parse_absence_data(self, data: Dict) -> Dict:
        """Parse Payfit absence data to match our model"""
        # Payfit API returns dates as objects with date and moment
        start_date_obj = data.get("startDate", {})
        end_date_obj = data.get("endDate", {})
        
        start_date = self._parse_date(start_date_obj.get("date") if isinstance(start_date_obj, dict) else start_date_obj)
        end_date = self._parse_date(end_date_obj.get("date") if isinstance(end_date_obj, dict) else end_date_obj)
        
        # Calculate duration if not provided
        duration_days = data.get("durationDays")
        if duration_days is None and start_date and end_date:
            duration_days = (end_date - start_date).days + 1
        
        # In Payfit, absences are linked to contracts, but we need to link to employees
        # We'll use the collaboratorId if available, otherwise try to find it from contract
        employee_id = data.get("collaboratorId")
        if not employee_id:
            # Try to find the employee ID from the contract
            contract_id = data.get("contractId")
            if contract_id:
                # We'll need to look up the contract to get the employee ID
                # For now, we'll use the contract ID and fix it later
                employee_id = contract_id
                logger.warning(f"Absence {data.get('id')} has contractId {contract_id} but no collaboratorId")
        
        return {
            "payfit_id": data.get("id", ""),
            "payfit_employee_id": employee_id or "",  # This needs to be the employee ID
            "absence_type": data.get("type", ""),
            "absence_code": data.get("code"),
            "start_date": start_date,
            "end_date": end_date,
            "duration_days": duration_days,
            "duration_hours": data.get("durationHours"),
            "status": data.get("status", "pending"),
            "approved_by": data.get("approvedBy"),
            "approved_at": self._parse_datetime(data.get("approvedAt")),
            "reason": data.get("reason"),
            "comment": data.get("comment"),
            "raw_data": data
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except:
            return None
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None
    
    async def _link_employee_to_user(self, employee: PayfitEmployee):
        """Try to link Payfit employee with local user by email"""
        if not employee.email:
            return
        
        # Check if user exists with this email
        result = await self.db.execute(
            select(User).where(
                User.email == employee.email
            )
        )
        user = result.scalar_one_or_none()
        
        if user:
            employee.local_user_id = user.id
            logger.info(f"Linked Payfit employee {employee.payfit_id} to user {user.id}")
        else:
            # Optionally create user automatically
            # This depends on your business logic
            pass
    
    async def get_sync_status(self) -> Dict:
        """Get current synchronization status"""
        # Get last sync log
        result = await self.db.execute(
            select(PayfitSyncLog).order_by(
                PayfitSyncLog.created_at.desc()
            ).limit(1)
        )
        last_sync = result.scalar_one_or_none()
        
        # Count records
        employee_count_result = await self.db.execute(select(func.count()).select_from(PayfitEmployee))
        employee_count = employee_count_result.scalar() or 0
        
        contract_count_result = await self.db.execute(select(func.count()).select_from(PayfitContract))
        contract_count = contract_count_result.scalar() or 0
        
        absence_count_result = await self.db.execute(select(func.count()).select_from(PayfitAbsence))
        absence_count = absence_count_result.scalar() or 0
        
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
            "api_connected": await self.client.test_connection()
        }