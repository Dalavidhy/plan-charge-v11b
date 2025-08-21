"""
Gryzzly API Client for interacting with Gryzzly RPC API
"""

import asyncio
import logging
import os
from collections import deque
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from httpx import AsyncClient, HTTPStatusError

from app.config import settings

logger = logging.getLogger(__name__)

# Check if mock mode is enabled
USE_MOCK = settings.GRYZZLY_USE_MOCK

if USE_MOCK:
    from app.services.gryzzly_mock import mock_service

    logger.info("Gryzzly API Client running in MOCK mode")


class RateLimiter:
    """
    Rate limiter for API requests
    Implements sliding window algorithm
    """

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """
        Wait if necessary to respect rate limits
        """
        async with self._lock:
            now = datetime.now()

            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - timedelta(
                seconds=self.time_window
            ):
                self.requests.popleft()

            # If we've hit the limit, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = (
                    self.requests[0] + timedelta(seconds=self.time_window) - now
                ).total_seconds()
                if sleep_time > 0:
                    logger.debug(
                        f"Rate limit reached, sleeping for {sleep_time:.2f} seconds"
                    )
                    await asyncio.sleep(sleep_time)
                    # Recursive call to recheck after sleep
                    await self.acquire()
                    return

            # Record this request
            self.requests.append(now)


class GryzzlyAPIClient:
    """Client for Gryzzly RPC API with rate limiting"""

    def __init__(self):
        self.base_url = settings.GRYZZLY_API_URL
        self.api_key = settings.GRYZZLY_API_KEY
        self.rate_limiter = RateLimiter(50, 10)  # 50 requests per 10 seconds
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3
        self.retry_delay = 1.0

        if not self.api_key:
            raise ValueError("GRYZZLY_API_KEY is required in settings")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, retry_count: int = 0
    ) -> Any:
        """Make RPC request to Gryzzly API with rate limiting and retries"""
        # Respect rate limits
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint}"

        # For Gryzzly RPC API, all requests are POST with JSON payload
        # Empty payload if no params
        json_data = params or {}

        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=url, headers=self.headers, json=json_data
                )

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 429:  # Rate limited
                    # Wait and retry
                    if retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2**retry_count)
                        logger.warning(
                            f"Rate limited, retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                        return await self._make_request(
                            endpoint, params, retry_count + 1
                        )
                    else:
                        raise Exception(f"Max retries reached for rate limiting")
                else:
                    error_msg = (
                        f"API request failed: {response.status_code} - {response.text}"
                    )
                    # Use debug for 404 errors (common for disabled users)
                    if response.status_code == 404:
                        logger.debug(error_msg)
                    else:
                        logger.error(error_msg)

                    # Retry on server errors
                    if response.status_code >= 500 and retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2**retry_count)
                        logger.warning(
                            f"Server error, retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                        return await self._make_request(
                            endpoint, params, retry_count + 1
                        )

                    raise Exception(error_msg)

        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2**retry_count)
                logger.warning(f"Request timeout, retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                return await self._make_request(endpoint, params, retry_count + 1)
            else:
                logger.error(
                    f"Request timeout after {self.max_retries} retries: {str(e)}"
                )
                raise
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def test_connection(self) -> bool:
        """Test connection to Gryzzly API"""
        if USE_MOCK:
            return await mock_service.test_connection()

        try:
            # Try to list users with limit 1 to test the connection
            result = await self._make_request("users.list", {"limit": 1})
            return result is not None
        except Exception as e:
            logger.error(f"Failed to connect to Gryzzly API: {e}")
            return False

    # User methods (previously called collaborators)
    async def get_collaborators(self, active_only: bool = False) -> List[Dict]:
        """Get list of users"""
        if USE_MOCK:
            return await mock_service.get_collaborators(active_only)

        params = {"limit": 1000, "offset": 0}  # Maximum allowed

        result = await self._make_request("users.list", params)

        # Transform to our expected format
        # Gryzzly API returns data in "data" field
        users = result.get("data", []) if isinstance(result, dict) else []

        collaborators = []
        for user in users:
            # Parse the name field to get first and last name
            name = user.get("name", "")
            name_parts = name.split(" ", 1) if name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            collaborators.append(
                {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "firstName": first_name,
                    "lastName": last_name,
                    "isActive": not user.get("is_disabled", False),
                    "isAdmin": user.get("role") == "manager",
                    "createdAt": user.get("created_at"),
                    "updatedAt": user.get("updated_at"),
                }
            )

        if active_only:
            collaborators = [c for c in collaborators if c["isActive"]]

        return collaborators

    async def get_collaborator(self, collaborator_id: str) -> Dict:
        """Get single user by ID"""
        if USE_MOCK:
            return await mock_service.get_collaborator(collaborator_id)

        params = {"id": collaborator_id}
        result = await self._make_request("users.get", params)

        return {
            "id": result.get("id"),
            "email": result.get("email"),
            "firstName": result.get("first_name", ""),
            "lastName": result.get("last_name", ""),
            "isActive": result.get("is_enabled", True),
            "isAdmin": result.get("is_admin", False),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    # Project methods
    async def get_projects(self, active_only: bool = False) -> List[Dict]:
        """Get list of projects"""
        if USE_MOCK:
            return await mock_service.get_projects(active_only)

        params = {"limit": 1000, "offset": 0}

        result = await self._make_request("projects.list", params)

        # Transform to our expected format
        # Gryzzly API returns data in "data" field
        projects = result.get("data", []) if isinstance(result, dict) else []

        transformed = []
        for project in projects:
            transformed.append(
                {
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "code": project.get("code"),
                    "description": project.get("description"),
                    "customerId": project.get("customer_id"),
                    "startDate": project.get("start_at"),
                    "endDate": project.get("end_at"),
                    "isActive": project.get("status") == "active",
                    "isBillable": project.get("is_billable", False),
                    "budgetHours": project.get("budget_hours"),
                    "budgetAmount": project.get("budget_amount"),
                    "createdAt": project.get("created_at"),
                    "updatedAt": project.get("updated_at"),
                }
            )

        if active_only:
            transformed = [p for p in transformed if p["isActive"]]

        return transformed

    async def get_project(self, project_id: str) -> Dict:
        """Get single project by ID"""
        if USE_MOCK:
            return await mock_service.get_project(project_id)

        params = {"id": project_id}
        result = await self._make_request("projects.get", params)

        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "code": result.get("code"),
            "description": result.get("description"),
            "customerId": result.get("customer_id"),
            "startDate": result.get("start_at"),
            "endDate": result.get("end_at"),
            "isActive": result.get("is_enabled", True),
            "isBillable": result.get("is_billable", False),
            "budgetHours": result.get("budget_hours"),
            "budgetAmount": result.get("budget_amount"),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    async def get_project_collaborators(self, project_id: str) -> List[Dict]:
        """Get collaborators assigned to a project"""
        if USE_MOCK:
            return await mock_service.get_project_collaborators(project_id)

        # Get project details to get contributors
        project = await self.get_project(project_id)
        contributor_ids = project.get("contributors", [])

        # Get user details for each contributor
        collaborators = []
        for user_id in contributor_ids:
            try:
                user = await self.get_collaborator(user_id)
                collaborators.append(user)
            except:
                pass  # Skip if user not found

        return collaborators

    # Task methods
    async def get_tasks(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get list of tasks"""
        if USE_MOCK:
            return await mock_service.get_tasks(project_id)

        params = {"limit": 1000, "offset": 0}

        if project_id:
            params["project_ids"] = [project_id]

        result = await self._make_request("tasks.list", params)

        # Transform to our expected format
        # Gryzzly API returns data in "data" field
        tasks = result.get("data", []) if isinstance(result, dict) else []

        transformed = []
        for task in tasks:
            transformed.append(
                {
                    "id": task.get("id"),
                    "projectId": task.get("project_id"),
                    "parentId": task.get("parent_id"),  # For subtasks
                    "name": task.get("name"),
                    "code": task.get("code"),
                    "description": task.get("description"),
                    "isActive": task.get("status") == "active",
                    "isBillable": task.get("is_billable", False),
                    "createdAt": task.get("created_at"),
                    "updatedAt": task.get("updated_at"),
                }
            )

        return transformed

    async def get_task(self, task_id: str) -> Dict:
        """Get single task by ID"""
        if USE_MOCK:
            return await mock_service.get_task(task_id)

        params = {"id": task_id}
        result = await self._make_request("tasks.get", params)

        return {
            "id": result.get("id"),
            "projectId": result.get("project_id"),
            "parentId": result.get("parent_id"),
            "name": result.get("name"),
            "code": result.get("code"),
            "description": result.get("description"),
            "isActive": result.get("is_enabled", True),
            "isBillable": result.get("is_billable", False),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    # Declaration methods
    async def get_declarations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        collaborator_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get time declarations with filters"""
        if USE_MOCK:
            return await mock_service.get_declarations(
                start_date, end_date, collaborator_id, project_id, status
            )

        # First, get all tasks to create a mapping of task_id to project_id
        tasks = await self.get_tasks()
        task_project_map = {t["id"]: t.get("projectId") for t in tasks}
        task_billable_map = {t["id"]: t.get("isBillable", False) for t in tasks}

        # For declarations, we need to fetch for each user
        users = await self.get_collaborators()
        all_declarations = []

        for user in users:
            # Skip if filtering by collaborator and this isn't the one
            if collaborator_id and user["id"] != collaborator_id:
                continue

            params = {
                "user_ids": [user["id"]],
                "task_ids": [],  # Required but can be empty for all tasks
            }

            if start_date:
                params["from"] = start_date.isoformat()
            if end_date:
                params["to"] = end_date.isoformat()

            try:
                result = await self._make_request("declarations.list", params)

                # Gryzzly API returns data in "data" field
                declarations = []
                if isinstance(result, dict) and "data" in result:
                    declarations = result["data"]
                elif isinstance(result, list):
                    declarations = result
                elif isinstance(result, dict):
                    declarations = [result]

                for decl in declarations:
                    # Get the task to find the project ID
                    task_id = decl.get("task_id")
                    project_id_from_task = (
                        task_project_map.get(task_id) if task_id else None
                    )
                    is_billable_from_task = (
                        task_billable_map.get(task_id, False) if task_id else False
                    )

                    # Skip if filtering by project and this isn't it
                    if project_id and project_id_from_task != project_id:
                        continue

                    # Transform to our expected format
                    all_declarations.append(
                        {
                            "id": decl.get("id"),
                            "collaboratorId": decl.get("user_id"),
                            "projectId": project_id_from_task,  # Get from task mapping
                            "taskId": task_id,
                            "date": decl.get("date"),
                            "durationSeconds": decl.get("duration", 0),
                            "durationHours": (
                                decl.get("duration", 0) / 3600
                                if decl.get("duration")
                                else 0
                            ),
                            "description": decl.get("description"),
                            "status": "submitted",  # Gryzzly doesn't return status in list
                            "isBillable": is_billable_from_task,  # Get from task mapping
                            "createdAt": decl.get("created_at"),
                            "updatedAt": decl.get("updated_at"),
                        }
                    )
            except Exception as e:
                # Log but continue with other users - some might be disabled
                logger.debug(f"Skipping declarations for user {user['id']}: {str(e)}")
                continue

        return all_declarations

    async def get_declaration(self, declaration_id: str) -> Dict:
        """Get single declaration by ID"""
        if USE_MOCK:
            return await mock_service.get_declaration(declaration_id)

        params = {"id": declaration_id}
        result = await self._make_request("declarations.get", params)

        return {
            "id": result.get("id"),
            "collaboratorId": result.get("user_id"),
            "projectId": result.get("project_id"),
            "taskId": result.get("task_id"),
            "date": result.get("date"),
            "durationSeconds": result.get("duration", 0),
            "durationHours": result.get("duration", 0) / 3600,
            "description": result.get("description"),
            "status": result.get("status", "submitted"),
            "isBillable": result.get("is_billable", False),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    async def create_declaration(
        self,
        collaborator_id: str,
        project_id: str,
        task_id: str,
        date: date,
        hours: float,
        description: Optional[str] = None,
    ) -> Dict:
        """Create a new time declaration"""
        if USE_MOCK:
            return await mock_service.create_declaration(
                collaborator_id, project_id, task_id, date, hours, description
            )

        params = {
            "user_id": collaborator_id,
            "task_id": task_id,
            "date": date.isoformat(),
            "duration": int(hours * 3600),  # Convert hours to seconds
            "description": description,
        }

        result = await self._make_request("declarations.create", params)

        return {
            "id": result.get("id"),
            "collaboratorId": result.get("user_id"),
            "projectId": result.get("project_id"),
            "taskId": result.get("task_id"),
            "date": result.get("date"),
            "durationSeconds": result.get("duration", 0),
            "durationHours": result.get("duration", 0) / 3600,
            "description": result.get("description"),
            "status": result.get("status", "submitted"),
            "isBillable": result.get("is_billable", False),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    async def update_declaration(
        self,
        declaration_id: str,
        hours: Optional[float] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """Update an existing declaration"""
        if USE_MOCK:
            return await mock_service.update_declaration(
                declaration_id, hours, description, status
            )

        params = {"id": declaration_id}

        if hours is not None:
            params["duration"] = int(hours * 3600)
        if description is not None:
            params["description"] = description

        result = await self._make_request("declarations.update", params)

        return {
            "id": result.get("id"),
            "collaboratorId": result.get("user_id"),
            "projectId": result.get("project_id"),
            "taskId": result.get("task_id"),
            "date": result.get("date"),
            "durationSeconds": result.get("duration", 0),
            "durationHours": result.get("duration", 0) / 3600,
            "description": result.get("description"),
            "status": result.get("status", "submitted"),
            "isBillable": result.get("is_billable", False),
            "createdAt": result.get("created_at"),
            "updatedAt": result.get("updated_at"),
        }

    async def delete_declaration(self, declaration_id: str) -> bool:
        """Delete a declaration"""
        if USE_MOCK:
            return await mock_service.delete_declaration(declaration_id)

        params = {"id": declaration_id}
        await self._make_request("declarations.delete", params)
        return True

    # Additional helper methods
    async def get_sync_status(self) -> Dict:
        """Get synchronization status"""
        if USE_MOCK:
            return await mock_service.get_sync_status()

        # Return a status based on API connectivity
        connected = await self.test_connection()
        return {
            "status": "connected" if connected else "disconnected",
            "lastSync": datetime.now().isoformat(),
        }

    async def trigger_sync(self, sync_type: str = "full") -> Dict:
        """Trigger synchronization - not needed for Gryzzly as we fetch directly"""
        if USE_MOCK:
            return await mock_service.trigger_sync(sync_type)

        return {
            "status": "success",
            "syncType": sync_type,
            "timestamp": datetime.now().isoformat(),
        }

    # Utility methods
    async def search_collaborators(self, query: str) -> List[Dict]:
        """Search collaborators by name or email"""
        if USE_MOCK:
            return await mock_service.search_collaborators(query)

        # Get all users and filter locally
        users = await self.get_collaborators()
        query_lower = query.lower()

        return [
            u
            for u in users
            if query_lower in u.get("email", "").lower()
            or query_lower in u.get("firstName", "").lower()
            or query_lower in u.get("lastName", "").lower()
        ]

    async def search_projects(self, query: str) -> List[Dict]:
        """Search projects by name or code"""
        if USE_MOCK:
            return await mock_service.search_projects(query)

        # Get all projects and filter locally
        projects = await self.get_projects()
        query_lower = query.lower()

        return [
            p
            for p in projects
            if query_lower in p.get("name", "").lower()
            or query_lower in (p.get("code") or "").lower()
        ]

    # Report methods (simplified versions)
    async def get_time_report(
        self, start_date: date, end_date: date, group_by: str = "project"
    ) -> Dict:
        """Get time tracking report"""
        if USE_MOCK:
            return await mock_service.get_time_report(start_date, end_date, group_by)

        declarations = await self.get_declarations(
            start_date=start_date, end_date=end_date
        )

        if group_by == "project":
            projects = await self.get_projects()
            project_map = {p["id"]: p["name"] for p in projects}

            report = {}
            for decl in declarations:
                project_id = decl["projectId"]
                if project_id not in report:
                    report[project_id] = {
                        "projectName": project_map.get(project_id, "Unknown"),
                        "totalHours": 0,
                        "billableHours": 0,
                        "nonBillableHours": 0,
                    }
                hours = decl["durationHours"]
                report[project_id]["totalHours"] += hours
                if decl.get("isBillable"):
                    report[project_id]["billableHours"] += hours
                else:
                    report[project_id]["nonBillableHours"] += hours

            return {"data": list(report.values())}

        return {"data": []}

    async def get_billing_report(
        self, start_date: date, end_date: date, project_id: Optional[str] = None
    ) -> Dict:
        """Get billing report"""
        if USE_MOCK:
            return await mock_service.get_billing_report(
                start_date, end_date, project_id
            )

        declarations = await self.get_declarations(
            start_date=start_date, end_date=end_date, project_id=project_id
        )

        billable_declarations = [d for d in declarations if d.get("isBillable")]
        total_hours = sum(d["durationHours"] for d in billable_declarations)

        return {
            "totalHours": total_hours,
            "totalAmount": 0,  # Would need rate information
            "declarationCount": len(billable_declarations),
        }

    async def get_activity_summary(
        self, collaborator_id: str, start_date: date, end_date: date
    ) -> Dict:
        """Get activity summary for a collaborator"""
        if USE_MOCK:
            return await mock_service.get_activity_summary(
                collaborator_id, start_date, end_date
            )

        declarations = await self.get_declarations(
            collaborator_id=collaborator_id, start_date=start_date, end_date=end_date
        )

        total_hours = sum(d["durationHours"] for d in declarations)
        projects_worked = len(set(d["projectId"] for d in declarations))

        return {
            "collaboratorId": collaborator_id,
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "totalHours": total_hours,
            "declarationCount": len(declarations),
            "projectsWorked": projects_worked,
            "averageHoursPerDay": (
                total_hours / ((end_date - start_date).days + 1)
                if (end_date - start_date).days > 0
                else total_hours
            ),
        }
