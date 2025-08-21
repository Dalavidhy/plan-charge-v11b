"""
Mock service for Gryzzly API - provides simulated data for development and testing
"""

import random
import string
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4


class GryzzlyMockService:
    """Mock service that simulates Gryzzly API responses"""

    def __init__(self):
        self.collaborators = self._generate_collaborators()
        self.projects = self._generate_projects()
        self.tasks = self._generate_tasks()
        self.declarations = self._generate_declarations()

    def _generate_id(self) -> str:
        """Generate a random ID"""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=24))

    def _generate_collaborators(self, count: int = 15) -> List[Dict]:
        """Generate mock collaborators"""
        collaborators = []
        departments = [
            "Engineering",
            "Design",
            "Product",
            "Marketing",
            "Sales",
            "Finance",
        ]
        positions = [
            "Developer",
            "Designer",
            "Manager",
            "Analyst",
            "Consultant",
            "Director",
        ]

        first_names = [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Eve",
            "Frank",
            "Grace",
            "Henry",
            "Iris",
            "Jack",
            "Kate",
            "Leo",
            "Maya",
            "Noah",
            "Olivia",
        ]
        last_names = [
            "Martin",
            "Bernard",
            "Dubois",
            "Thomas",
            "Robert",
            "Richard",
            "Petit",
            "Durand",
            "Leroy",
            "Moreau",
            "Simon",
            "Laurent",
            "Michel",
            "Garcia",
            "David",
        ]

        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            collaborators.append(
                {
                    "id": self._generate_id(),
                    "email": f"{first_name.lower()}.{last_name.lower()}@company.com",
                    "firstName": first_name,
                    "lastName": last_name,
                    "matricule": f"EMP{str(i+1001)}",
                    "department": random.choice(departments),
                    "position": random.choice(positions),
                    "isActive": random.random() > 0.1,  # 90% active
                    "isAdmin": random.random() > 0.8,  # 20% admins
                    "createdAt": (
                        datetime.now() - timedelta(days=random.randint(30, 365))
                    ).isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                }
            )

        return collaborators

    def _generate_projects(self, count: int = 20) -> List[Dict]:
        """Generate mock projects"""
        projects = []
        project_types = ["Fixed Price", "Time & Material", "Retainer", "Internal"]
        clients = [
            "Acme Corp",
            "TechStart",
            "Global Industries",
            "Innovate Ltd",
            "Digital Solutions",
            "Future Systems",
            "Smart Tech",
            "Cloud Nine",
            "Data Dynamics",
            "AI Ventures",
        ]

        project_names = [
            "Website Redesign",
            "Mobile App Development",
            "API Integration",
            "Data Migration",
            "Security Audit",
            "Performance Optimization",
            "Cloud Migration",
            "DevOps Setup",
            "UI/UX Refresh",
            "Backend Refactoring",
            "Analytics Dashboard",
            "E-commerce Platform",
            "CRM Implementation",
            "Machine Learning POC",
            "Blockchain Integration",
            "IoT Platform",
            "Microservices Architecture",
            "Real-time System",
            "Payment Gateway",
            "Content Management System",
        ]

        for i in range(count):
            start_date = datetime.now() - timedelta(days=random.randint(0, 180))
            end_date = start_date + timedelta(days=random.randint(30, 365))

            projects.append(
                {
                    "id": self._generate_id(),
                    "name": random.choice(project_names) + f" {i+1}",
                    "code": f"PRJ-{str(i+1001)}",
                    "description": f"Project description for {project_names[i % len(project_names)]}",
                    "clientName": (
                        random.choice(clients) if random.random() > 0.3 else None
                    ),
                    "projectType": random.choice(project_types),
                    "startDate": start_date.date().isoformat(),
                    "endDate": (
                        end_date.date().isoformat() if random.random() > 0.3 else None
                    ),
                    "isActive": random.random() > 0.2,  # 80% active
                    "isBillable": random.random() > 0.3,  # 70% billable
                    "budgetHours": (
                        random.randint(40, 1000) if random.random() > 0.4 else None
                    ),
                    "budgetAmount": (
                        random.randint(5000, 100000) if random.random() > 0.5 else None
                    ),
                    "createdAt": (
                        datetime.now() - timedelta(days=random.randint(30, 365))
                    ).isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                }
            )

        return projects

    def _generate_tasks(self, count: int = 50) -> List[Dict]:
        """Generate mock tasks"""
        tasks = []
        task_types = [
            "Development",
            "Design",
            "Testing",
            "Documentation",
            "Meeting",
            "Review",
            "Research",
        ]

        task_names = [
            "Frontend Development",
            "Backend Development",
            "Database Design",
            "API Development",
            "Unit Testing",
            "Integration Testing",
            "Code Review",
            "Documentation",
            "Sprint Planning",
            "Daily Standup",
            "Retrospective",
            "Bug Fixing",
            "Performance Tuning",
            "Security Review",
            "Deployment",
            "User Research",
            "Wireframing",
            "Prototyping",
            "UI Design",
            "UX Testing",
        ]

        for i in range(count):
            project = random.choice(self.projects)

            tasks.append(
                {
                    "id": self._generate_id(),
                    "projectId": project["id"],
                    "name": random.choice(task_names),
                    "code": f"TSK-{str(i+1001)}",
                    "description": f"Task description for {task_names[i % len(task_names)]}",
                    "taskType": random.choice(task_types),
                    "estimatedHours": (
                        random.randint(4, 80) if random.random() > 0.3 else None
                    ),
                    "isActive": project["isActive"] and random.random() > 0.1,
                    "isBillable": project["isBillable"],
                    "createdAt": project["createdAt"],
                    "updatedAt": datetime.now().isoformat(),
                }
            )

        return tasks

    def _generate_declarations(self, count: int = 200) -> List[Dict]:
        """Generate mock time declarations"""
        declarations = []
        statuses = ["draft", "submitted", "approved", "rejected"]
        descriptions = [
            "Development work",
            "Bug fixing",
            "Code review",
            "Testing",
            "Documentation",
            "Meeting",
            "Research",
            "Design work",
            "Planning",
            "Deployment",
            "Support",
            "Training",
            "Analysis",
            "Optimization",
        ]

        for i in range(count):
            collaborator = random.choice(self.collaborators)
            project = random.choice(self.projects)
            task = random.choice(
                [t for t in self.tasks if t["projectId"] == project["id"]]
            )

            declaration_date = datetime.now().date() - timedelta(
                days=random.randint(0, 60)
            )
            hours = round(random.uniform(0.5, 8), 2)
            status = random.choice(statuses)

            declarations.append(
                {
                    "id": self._generate_id(),
                    "collaboratorId": collaborator["id"],
                    "projectId": project["id"],
                    "taskId": task["id"],
                    "date": declaration_date.isoformat(),
                    "durationHours": int(hours),
                    "durationMinutes": int((hours % 1) * 60),
                    "description": random.choice(descriptions),
                    "comment": (
                        f"Work on {task['name']}" if random.random() > 0.5 else None
                    ),
                    "status": status,
                    "approvedBy": (
                        random.choice(self.collaborators)["email"]
                        if status == "approved"
                        else None
                    ),
                    "approvedAt": (
                        datetime.now().isoformat() if status == "approved" else None
                    ),
                    "isBillable": project["isBillable"],
                    "billingRate": (
                        random.randint(50, 200) if project["isBillable"] else None
                    ),
                    "createdAt": declaration_date.isoformat() + "T09:00:00",
                    "updatedAt": datetime.now().isoformat(),
                }
            )

        return declarations

    async def test_connection(self) -> bool:
        """Test connection (always returns True for mock)"""
        return True

    async def get_collaborators(self, active_only: bool = False) -> List[Dict]:
        """Get mock collaborators"""
        if active_only:
            return [c for c in self.collaborators if c["isActive"]]
        return self.collaborators

    async def get_collaborator(self, collaborator_id: str) -> Dict:
        """Get single collaborator"""
        for c in self.collaborators:
            if c["id"] == collaborator_id:
                return c
        raise Exception(f"Collaborator {collaborator_id} not found")

    async def get_projects(self, active_only: bool = False) -> List[Dict]:
        """Get mock projects"""
        if active_only:
            return [p for p in self.projects if p["isActive"]]
        return self.projects

    async def get_project(self, project_id: str) -> Dict:
        """Get single project"""
        for p in self.projects:
            if p["id"] == project_id:
                return p
        raise Exception(f"Project {project_id} not found")

    async def get_project_collaborators(self, project_id: str) -> List[Dict]:
        """Get collaborators assigned to a project"""
        # Return a random subset of collaborators
        return random.sample(self.collaborators, min(5, len(self.collaborators)))

    async def get_tasks(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get mock tasks"""
        if project_id:
            return [t for t in self.tasks if t["projectId"] == project_id]
        return self.tasks

    async def get_task(self, task_id: str) -> Dict:
        """Get single task"""
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        raise Exception(f"Task {task_id} not found")

    async def get_declarations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        collaborator_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get mock declarations with filters"""
        result = self.declarations.copy()

        if start_date:
            result = [d for d in result if d["date"] >= start_date.isoformat()]
        if end_date:
            result = [d for d in result if d["date"] <= end_date.isoformat()]
        if collaborator_id:
            result = [d for d in result if d["collaboratorId"] == collaborator_id]
        if project_id:
            result = [d for d in result if d["projectId"] == project_id]
        if status:
            result = [d for d in result if d["status"] == status]

        return result

    async def get_declaration(self, declaration_id: str) -> Dict:
        """Get single declaration"""
        for d in self.declarations:
            if d["id"] == declaration_id:
                return d
        raise Exception(f"Declaration {declaration_id} not found")

    async def create_declaration(
        self,
        collaborator_id: str,
        project_id: str,
        task_id: str,
        date: date,
        hours: float,
        description: Optional[str] = None,
    ) -> Dict:
        """Create a new declaration"""
        new_declaration = {
            "id": self._generate_id(),
            "collaboratorId": collaborator_id,
            "projectId": project_id,
            "taskId": task_id,
            "date": date.isoformat(),
            "durationHours": int(hours),
            "durationMinutes": int((hours % 1) * 60),
            "description": description or "New declaration",
            "status": "draft",
            "isBillable": next(
                (p["isBillable"] for p in self.projects if p["id"] == project_id), False
            ),
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }
        self.declarations.append(new_declaration)
        return new_declaration

    async def update_declaration(
        self,
        declaration_id: str,
        hours: Optional[float] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """Update a declaration"""
        for d in self.declarations:
            if d["id"] == declaration_id:
                if hours is not None:
                    d["durationHours"] = int(hours)
                    d["durationMinutes"] = int((hours % 1) * 60)
                if description is not None:
                    d["description"] = description
                if status is not None:
                    d["status"] = status
                    if status == "approved":
                        d["approvedBy"] = random.choice(self.collaborators)["email"]
                        d["approvedAt"] = datetime.now().isoformat()
                d["updatedAt"] = datetime.now().isoformat()
                return d
        raise Exception(f"Declaration {declaration_id} not found")

    async def delete_declaration(self, declaration_id: str) -> bool:
        """Delete a declaration"""
        self.declarations = [d for d in self.declarations if d["id"] != declaration_id]
        return True

    async def get_sync_status(self) -> Dict:
        """Get sync status"""
        return {
            "lastSync": datetime.now().isoformat(),
            "status": "connected",
            "recordCounts": {
                "collaborators": len(self.collaborators),
                "projects": len(self.projects),
                "tasks": len(self.tasks),
                "declarations": len(self.declarations),
            },
        }

    async def trigger_sync(self, sync_type: str = "full") -> Dict:
        """Trigger sync (simulated)"""
        return {
            "status": "success",
            "syncType": sync_type,
            "timestamp": datetime.now().isoformat(),
            "recordsSynced": {
                "collaborators": (
                    len(self.collaborators)
                    if sync_type in ["full", "collaborators"]
                    else 0
                ),
                "projects": (
                    len(self.projects) if sync_type in ["full", "projects"] else 0
                ),
                "tasks": len(self.tasks) if sync_type in ["full", "tasks"] else 0,
                "declarations": (
                    len(self.declarations)
                    if sync_type in ["full", "declarations"]
                    else 0
                ),
            },
        }

    async def get_time_report(
        self, start_date: date, end_date: date, group_by: str = "project"
    ) -> Dict:
        """Get time report"""
        declarations = await self.get_declarations(
            start_date=start_date, end_date=end_date
        )

        if group_by == "project":
            report = {}
            for d in declarations:
                project_id = d["projectId"]
                if project_id not in report:
                    project = next(
                        (p for p in self.projects if p["id"] == project_id), None
                    )
                    report[project_id] = {
                        "projectName": project["name"] if project else "Unknown",
                        "totalHours": 0,
                        "billableHours": 0,
                        "nonBillableHours": 0,
                    }
                hours = d["durationHours"] + d["durationMinutes"] / 60
                report[project_id]["totalHours"] += hours
                if d["isBillable"]:
                    report[project_id]["billableHours"] += hours
                else:
                    report[project_id]["nonBillableHours"] += hours
            return {"data": list(report.values())}

        return {"data": []}

    async def get_billing_report(
        self, start_date: date, end_date: date, project_id: Optional[str] = None
    ) -> Dict:
        """Get billing report"""
        declarations = await self.get_declarations(
            start_date=start_date, end_date=end_date, project_id=project_id
        )

        billable_declarations = [d for d in declarations if d["isBillable"]]
        total_hours = sum(
            d["durationHours"] + d["durationMinutes"] / 60
            for d in billable_declarations
        )
        total_amount = sum(
            (d["durationHours"] + d["durationMinutes"] / 60)
            * (d.get("billingRate", 100))
            for d in billable_declarations
        )

        return {
            "totalHours": total_hours,
            "totalAmount": total_amount,
            "declarationCount": len(billable_declarations),
            "averageRate": total_amount / total_hours if total_hours > 0 else 0,
        }

    async def search_collaborators(self, query: str) -> List[Dict]:
        """Search collaborators"""
        query_lower = query.lower()
        return [
            c
            for c in self.collaborators
            if query_lower in c["email"].lower()
            or query_lower in c["firstName"].lower()
            or query_lower in c["lastName"].lower()
        ]

    async def search_projects(self, query: str) -> List[Dict]:
        """Search projects"""
        query_lower = query.lower()
        return [
            p
            for p in self.projects
            if query_lower in p["name"].lower()
            or query_lower in p.get("code", "").lower()
        ]

    async def get_activity_summary(
        self, collaborator_id: str, start_date: date, end_date: date
    ) -> Dict:
        """Get activity summary for a collaborator"""
        declarations = await self.get_declarations(
            collaborator_id=collaborator_id, start_date=start_date, end_date=end_date
        )

        total_hours = sum(
            d["durationHours"] + d["durationMinutes"] / 60 for d in declarations
        )
        projects_worked = len(set(d["projectId"] for d in declarations))

        return {
            "collaboratorId": collaborator_id,
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "totalHours": total_hours,
            "declarationCount": len(declarations),
            "projectsWorked": projects_worked,
            "averageHoursPerDay": total_hours / ((end_date - start_date).days + 1),
        }


# Singleton instance
mock_service = GryzzlyMockService()
