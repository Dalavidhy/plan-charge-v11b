"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.people import router as people_router
from app.api.v1.teams import router as teams_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.allocations import router as allocations_router
from app.api.v1.calendars import router as calendars_router
from app.api.v1.reports import router as reports_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.benefits import router as benefits_router

api_router = APIRouter()

# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(organizations_router, prefix="/orgs", tags=["Organizations"])
api_router.include_router(people_router, prefix="/people", tags=["People"])
api_router.include_router(teams_router, prefix="/teams", tags=["Teams"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(allocations_router, prefix="/allocations", tags=["Allocations"])
api_router.include_router(calendars_router, prefix="/calendars", tags=["Calendars"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(benefits_router, prefix="/benefits", tags=["Benefits"])

__all__ = ["api_router"]