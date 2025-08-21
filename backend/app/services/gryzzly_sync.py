"""
Gryzzly synchronization service for managing data sync operations
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.services.gryzzly_client import GryzzlyAPIClient
from app.models.gryzzly import (
    GryzzlyCollaborator,
    GryzzlyProject,
    GryzzlyTask,
    GryzzlyDeclaration,
    GryzzlyCollaboratorProject,
    GryzzlySyncLog
)
from app.models.person import User

logger = logging.getLogger(__name__)


class GryzzlySyncService:
    """Service for synchronizing data from Gryzzly API to local database"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = GryzzlyAPIClient()
    
    async def sync_all(self, triggered_by: str = "system") -> Dict[str, Any]:
        """Perform complete synchronization of all Gryzzly data"""
        sync_log = GryzzlySyncLog(
            sync_type="full",
            sync_status="started",
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        self.session.add(sync_log)
        await self.session.commit()
        
        results = {
            "collaborators": {"created": 0, "updated": 0, "failed": 0},
            "projects": {"created": 0, "updated": 0, "failed": 0},
            "tasks": {"created": 0, "updated": 0, "failed": 0},
            "declarations": {"created": 0, "updated": 0, "failed": 0},
            "errors": []
        }
        
        try:
            # Sync collaborators first
            collaborator_result = await self.sync_collaborators()
            results["collaborators"] = collaborator_result
            
            # Then sync projects
            project_result = await self.sync_projects()
            results["projects"] = project_result
            
            # Then sync tasks
            task_result = await self.sync_tasks()
            results["tasks"] = task_result
            
            # Finally sync declarations
            declaration_result = await self.sync_declarations()
            results["declarations"] = declaration_result
            
            # Update sync log
            sync_log.sync_status = "success"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int(
                (sync_log.completed_at - sync_log.started_at).total_seconds()
            )
            sync_log.records_synced = (
                results["collaborators"]["created"] + results["collaborators"]["updated"] +
                results["projects"]["created"] + results["projects"]["updated"] +
                results["tasks"]["created"] + results["tasks"]["updated"] +
                results["declarations"]["created"] + results["declarations"]["updated"]
            )
            sync_log.records_created = (
                results["collaborators"]["created"] +
                results["projects"]["created"] +
                results["tasks"]["created"] +
                results["declarations"]["created"]
            )
            sync_log.records_updated = (
                results["collaborators"]["updated"] +
                results["projects"]["updated"] +
                results["tasks"]["updated"] +
                results["declarations"]["updated"]
            )
            sync_log.records_failed = (
                results["collaborators"]["failed"] +
                results["projects"]["failed"] +
                results["tasks"]["failed"] +
                results["declarations"]["failed"]
            )
            
        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}")
            sync_log.sync_status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            results["errors"].append(str(e))
        
        await self.session.commit()
        return results
    
    async def sync_collaborators(self) -> Dict[str, int]:
        """Sync collaborators from Gryzzly"""
        result = {"created": 0, "updated": 0, "failed": 0}
        
        try:
            # Get all collaborators from Gryzzly
            gryzzly_collaborators = await self.client.get_collaborators(active_only=False)
            
            for collab_data in gryzzly_collaborators:
                try:
                    # Check if collaborator already exists
                    query = select(GryzzlyCollaborator).where(
                        GryzzlyCollaborator.gryzzly_id == collab_data["id"]
                    )
                    existing_result = await self.session.execute(query)
                    existing = existing_result.scalar_one_or_none()
                    
                    # Parse collaborator data
                    collaborator_dict = self._parse_collaborator_data(collab_data)
                    
                    if existing:
                        # Update existing collaborator, preserving matricule if not provided
                        for key, value in collaborator_dict.items():
                            # Skip matricule if it's not provided to preserve existing value
                            if key == "matricule" and value is None and getattr(existing, "matricule", None) is not None:
                                logger.info(f"Gryzzly sync: Preserving existing matricule {getattr(existing, 'matricule')} for {existing.email}")
                                continue
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        result["updated"] += 1
                    else:
                        # Create new collaborator
                        new_collaborator = GryzzlyCollaborator(**collaborator_dict)
                        self.session.add(new_collaborator)
                        result["created"] += 1
                        
                        # Try to link with local user by email
                        await self._link_collaborator_to_user(new_collaborator)
                    
                except Exception as e:
                    logger.error(f"Failed to sync collaborator {collab_data.get('id')}: {str(e)}")
                    result["failed"] += 1
            
            await self.session.commit()
            logger.info(f"Collaborator sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Collaborator sync failed: {str(e)}")
            raise
        
        return result
    
    async def sync_projects(self) -> Dict[str, int]:
        """Sync projects from Gryzzly"""
        result = {"created": 0, "updated": 0, "failed": 0}
        
        try:
            # Get all projects from Gryzzly
            gryzzly_projects = await self.client.get_projects(active_only=False)
            
            for project_data in gryzzly_projects:
                try:
                    # Check if project already exists
                    query = select(GryzzlyProject).where(
                        GryzzlyProject.gryzzly_id == project_data["id"]
                    )
                    existing_result = await self.session.execute(query)
                    existing = existing_result.scalar_one_or_none()
                    
                    # Parse project data
                    project_dict = self._parse_project_data(project_data)
                    
                    if existing:
                        # Update existing project
                        for key, value in project_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        result["updated"] += 1
                    else:
                        # Create new project
                        new_project = GryzzlyProject(**project_dict)
                        self.session.add(new_project)
                        result["created"] += 1
                    
                    # Sync project collaborators
                    await self._sync_project_collaborators(project_data["id"])
                    
                except Exception as e:
                    logger.error(f"Failed to sync project {project_data.get('id')}: {str(e)}")
                    result["failed"] += 1
            
            await self.session.commit()
            logger.info(f"Project sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Project sync failed: {str(e)}")
            raise
        
        return result
    
    async def sync_tasks(self) -> Dict[str, int]:
        """Sync tasks from Gryzzly"""
        result = {"created": 0, "updated": 0, "failed": 0}
        
        try:
            # Get all tasks from Gryzzly
            gryzzly_tasks = await self.client.get_tasks()
            
            for task_data in gryzzly_tasks:
                try:
                    # Get the project ID in our database
                    gryzzly_project_id = task_data.get("projectId")
                    if not gryzzly_project_id:
                        logger.warning(f"No project ID for task {task_data['id']}")
                        result["failed"] += 1
                        continue
                    
                    project_query = select(GryzzlyProject).where(
                        GryzzlyProject.gryzzly_id == gryzzly_project_id
                    )
                    project_result = await self.session.execute(project_query)
                    project = project_result.scalar_one_or_none()
                    
                    if not project:
                        logger.warning(f"Project {gryzzly_project_id} not found for task {task_data['id']}")
                        result["failed"] += 1
                        continue
                    
                    # Check if task already exists
                    query = select(GryzzlyTask).where(
                        GryzzlyTask.gryzzly_id == task_data["id"]
                    )
                    existing_result = await self.session.execute(query)
                    existing = existing_result.scalar_one_or_none()
                    
                    # Parse task data
                    task_dict = self._parse_task_data(task_data, project.id)
                    
                    if existing:
                        # Update existing task
                        for key, value in task_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        result["updated"] += 1
                    else:
                        # Create new task
                        new_task = GryzzlyTask(**task_dict)
                        self.session.add(new_task)
                        result["created"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync task {task_data.get('id')}: {str(e)}")
                    result["failed"] += 1
            
            await self.session.commit()
            logger.info(f"Task sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Task sync failed: {str(e)}")
            raise
        
        return result
    
    async def sync_declarations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, int]:
        """Sync time declarations from Gryzzly"""
        result = {"created": 0, "updated": 0, "failed": 0}
        
        # Default to 6 months before and 6 months after current date if no dates provided
        if not start_date:
            # 6 months before current date, first day of that month
            six_months_ago = date.today() - timedelta(days=180)
            start_date = six_months_ago.replace(day=1)
        if not end_date:
            # 6 months after current date, last day of that month
            six_months_later = date.today() + timedelta(days=180)
            # Get last day of that month
            if six_months_later.month == 12:
                end_date = date(six_months_later.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(six_months_later.year, six_months_later.month + 1, 1) - timedelta(days=1)
        
        logger.info(f"Syncing declarations from {start_date} to {end_date} (approximately 13 months)")
        
        try:
            # Get all declarations from Gryzzly
            gryzzly_declarations = await self.client.get_declarations(
                start_date=start_date,
                end_date=end_date
            )
            
            for decl_data in gryzzly_declarations:
                try:
                    # Get related entities in our database
                    # API returns camelCase fields
                    collaborator_id = decl_data.get("collaboratorId")
                    if not collaborator_id:
                        logger.warning(f"No collaborator ID for declaration {decl_data.get('id')}")
                        result["failed"] += 1
                        continue
                    
                    collaborator_query = select(GryzzlyCollaborator).where(
                        GryzzlyCollaborator.gryzzly_id == collaborator_id
                    )
                    collaborator_result = await self.session.execute(collaborator_query)
                    collaborator = collaborator_result.scalar_one_or_none()
                    
                    if not collaborator:
                        logger.warning(f"Collaborator {collaborator_id} not found for declaration {decl_data.get('id')}")
                        result["failed"] += 1
                        continue
                    
                    # Project ID might be null for some declarations
                    project = None
                    project_id = decl_data.get("projectId")
                    if project_id:
                        project_query = select(GryzzlyProject).where(
                            GryzzlyProject.gryzzly_id == project_id
                        )
                        project_result = await self.session.execute(project_query)
                        project = project_result.scalar_one_or_none()
                        
                        if not project:
                            logger.warning(f"Project {project_id} not found for declaration {decl_data.get('id')}")
                            # Try to continue without project for now
                    
                    task = None
                    task_id = decl_data.get("taskId")
                    if task_id:
                        task_query = select(GryzzlyTask).where(
                            GryzzlyTask.gryzzly_id == task_id
                        )
                        task_result = await self.session.execute(task_query)
                        task = task_result.scalar_one_or_none()
                    
                    # Check if declaration already exists
                    query = select(GryzzlyDeclaration).where(
                        GryzzlyDeclaration.gryzzly_id == decl_data["id"]
                    )
                    existing_result = await self.session.execute(query)
                    existing = existing_result.scalar_one_or_none()
                    
                    # Parse declaration data
                    # Skip if no project (required field)
                    if not project:
                        result["failed"] += 1
                        continue
                    
                    declaration_dict = self._parse_declaration_data(
                        decl_data, 
                        collaborator.id, 
                        project.id,
                        task.id if task else None
                    )
                    
                    if existing:
                        # Update existing declaration
                        for key, value in declaration_dict.items():
                            setattr(existing, key, value)
                        existing.last_synced_at = datetime.utcnow()
                        result["updated"] += 1
                    else:
                        # Create new declaration
                        new_declaration = GryzzlyDeclaration(**declaration_dict)
                        self.session.add(new_declaration)
                        result["created"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync declaration {decl_data.get('id')}: {str(e)}")
                    result["failed"] += 1
            
            await self.session.commit()
            logger.info(f"Declaration sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Declaration sync failed: {str(e)}")
            raise
        
        return result
    
    async def _sync_project_collaborators(self, project_gryzzly_id: str):
        """Sync collaborators assigned to a project"""
        try:
            # Get project in our database
            project_query = select(GryzzlyProject).where(
                GryzzlyProject.gryzzly_id == project_gryzzly_id
            )
            project_result = await self.session.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if not project:
                return
            
            # Get project collaborators from API
            project_collaborators = await self.client.get_project_collaborators(project_gryzzly_id)
            
            for pc_data in project_collaborators:
                # Get collaborator in our database
                collab_query = select(GryzzlyCollaborator).where(
                    GryzzlyCollaborator.gryzzly_id == pc_data["collaborator_id"]
                )
                collab_result = await self.session.execute(collab_query)
                collaborator = collab_result.scalar_one_or_none()
                
                if not collaborator:
                    continue
                
                # Check if association exists
                assoc_query = select(GryzzlyCollaboratorProject).where(
                    and_(
                        GryzzlyCollaboratorProject.collaborator_id == collaborator.id,
                        GryzzlyCollaboratorProject.project_id == project.id
                    )
                )
                assoc_result = await self.session.execute(assoc_query)
                existing = assoc_result.scalar_one_or_none()
                
                if not existing:
                    # Create association
                    new_assoc = GryzzlyCollaboratorProject(
                        collaborator_id=collaborator.id,
                        project_id=project.id,
                        role=pc_data.get("role"),
                        allocation_percentage=pc_data.get("allocation_percentage"),
                        start_date=self._parse_date(pc_data.get("start_date")),
                        end_date=self._parse_date(pc_data.get("end_date")),
                        is_active=pc_data.get("is_active", True)
                    )
                    self.session.add(new_assoc)
                else:
                    # Update existing association
                    existing.role = pc_data.get("role")
                    existing.allocation_percentage = pc_data.get("allocation_percentage")
                    existing.start_date = self._parse_date(pc_data.get("start_date"))
                    existing.end_date = self._parse_date(pc_data.get("end_date"))
                    existing.is_active = pc_data.get("is_active", True)
            
        except Exception as e:
            logger.error(f"Failed to sync project collaborators: {str(e)}")
    
    def _parse_collaborator_data(self, data: Dict) -> Dict:
        """Parse Gryzzly collaborator data to match our model"""
        result = {
            "gryzzly_id": data["id"],
            "email": data.get("email", ""),
            "first_name": data.get("firstName", ""),
            "last_name": data.get("lastName", ""),
            "department": data.get("department"),
            "position": data.get("position"),
            "is_active": data.get("isActive", True),
            "is_admin": data.get("isAdmin", False),
            "raw_data": data
        }
        
        # Only include matricule if provided by Gryzzly API
        # This prevents overwriting existing matricules with None
        matricule = data.get("matricule")
        if matricule is not None:
            result["matricule"] = matricule
            logger.info(f"Gryzzly sync: Setting matricule {matricule} for {data.get('email', 'unknown')}")
        else:
            logger.info(f"Gryzzly sync: Preserving existing matricule for {data.get('email', 'unknown')}")
            
        return result
    
    def _parse_project_data(self, data: Dict) -> Dict:
        """Parse Gryzzly project data to match our model"""
        return {
            "gryzzly_id": data["id"],
            "name": data.get("name", ""),
            "code": data.get("code"),
            "description": data.get("description"),
            "client_name": data.get("clientName"),
            "project_type": data.get("projectType"),
            "start_date": self._parse_date(data.get("startDate")),
            "end_date": self._parse_date(data.get("endDate")),
            "is_active": data.get("isActive", True),
            "is_billable": data.get("isBillable", True),
            "budget_hours": data.get("budgetHours"),
            "budget_amount": data.get("budgetAmount"),
            "raw_data": data
        }
    
    def _parse_task_data(self, data: Dict, project_id: str) -> Dict:
        """Parse Gryzzly task data to match our model"""
        return {
            "gryzzly_id": data["id"],
            "project_id": project_id,
            "name": data.get("name", ""),
            "code": data.get("code"),
            "description": data.get("description"),
            "task_type": data.get("taskType"),
            "estimated_hours": data.get("estimatedHours"),
            "is_active": data.get("isActive", True),
            "is_billable": data.get("isBillable", True),
            "raw_data": data
        }
    
    def _parse_declaration_data(
        self, 
        data: Dict, 
        collaborator_id: str,
        project_id: str,
        task_id: Optional[str] = None
    ) -> Dict:
        """Parse Gryzzly declaration data to match our model"""
        # API returns durationHours and durationSeconds
        hours = data.get("durationHours", 0)
        duration_seconds = data.get("durationSeconds", 0)
        
        # If we have seconds but not hours, calculate hours
        if duration_seconds and not hours:
            hours = duration_seconds / 3600
        
        # Calculate minutes from the fractional part of hours or from seconds
        if duration_seconds:
            minutes = int((duration_seconds % 3600) / 60)
        else:
            # Extract minutes from fractional hours
            minutes = int((hours % 1) * 60) if hours else 0
        
        return {
            "gryzzly_id": data["id"],
            "collaborator_id": collaborator_id,
            "project_id": project_id,
            "task_id": task_id,
            "date": self._parse_date(data.get("date")),
            "duration_hours": int(hours) if hours else 0,
            "duration_minutes": minutes,
            "description": data.get("description", ""),
            "comment": data.get("comment"),
            "status": data.get("status", "submitted"),  # Default to submitted as most are
            "approved_by": data.get("approvedBy"),
            "approved_at": self._parse_datetime(data.get("approvedAt")),
            "is_billable": data.get("isBillable", False),  # API seems to return False by default
            "billing_rate": data.get("billingRate"),
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
    
    async def _link_collaborator_to_user(self, collaborator: GryzzlyCollaborator):
        """Try to link Gryzzly collaborator with local user by email"""
        if not collaborator.email:
            return
        
        # Check if user exists with this email
        query = select(User).where(User.email == collaborator.email)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            collaborator.local_user_id = user.id
            logger.info(f"Linked Gryzzly collaborator {collaborator.gryzzly_id} to user {user.id}")
    
    async def get_sync_status(self) -> Dict:
        """Get current synchronization status"""
        # Get last sync log
        query = select(GryzzlySyncLog).order_by(GryzzlySyncLog.created_at.desc()).limit(1)
        result = await self.session.execute(query)
        last_sync = result.scalar_one_or_none()
        
        # Count records
        collaborator_count_result = await self.session.execute(
            select(func.count()).select_from(GryzzlyCollaborator)
        )
        collaborator_count = collaborator_count_result.scalar() or 0
        
        project_count_result = await self.session.execute(
            select(func.count()).select_from(GryzzlyProject)
        )
        project_count = project_count_result.scalar() or 0
        
        task_count_result = await self.session.execute(
            select(func.count()).select_from(GryzzlyTask)
        )
        task_count = task_count_result.scalar() or 0
        
        declaration_count_result = await self.session.execute(
            select(func.count()).select_from(GryzzlyDeclaration)
        )
        declaration_count = declaration_count_result.scalar() or 0
        
        return {
            "last_sync": {
                "type": last_sync.sync_type if last_sync else None,
                "status": last_sync.sync_status if last_sync else None,
                "timestamp": last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None,
                "records_synced": last_sync.records_synced if last_sync else 0
            },
            "data_counts": {
                "collaborators": collaborator_count,
                "projects": project_count,
                "tasks": task_count,
                "declarations": declaration_count
            },
            "api_connected": await self.client.test_connection()
        }