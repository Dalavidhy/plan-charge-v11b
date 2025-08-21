"""
Gryzzly API endpoints for synchronization and data management
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_async_session, get_current_user
from app.models.gryzzly import (
    GryzzlyCollaborator,
    GryzzlyDeclaration,
    GryzzlyProject,
    GryzzlySyncLog,
    GryzzlyTask,
)
from app.models.person import User
from app.services.gryzzly_client import GryzzlyAPIClient
from app.services.gryzzly_sync import GryzzlySyncService

router = APIRouter()


@router.get("/status")
async def get_sync_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current Gryzzly synchronization status"""
    # Get last sync log
    last_sync_query = (
        select(GryzzlySyncLog).order_by(GryzzlySyncLog.created_at.desc()).limit(1)
    )
    last_sync_result = await session.execute(last_sync_query)
    last_sync = last_sync_result.scalar_one_or_none()

    # Count records
    collaborator_count_result = await session.execute(
        select(func.count()).select_from(GryzzlyCollaborator)
    )
    collaborator_count = collaborator_count_result.scalar() or 0

    project_count_result = await session.execute(
        select(func.count()).select_from(GryzzlyProject)
    )
    project_count = project_count_result.scalar() or 0

    task_count_result = await session.execute(
        select(func.count()).select_from(GryzzlyTask)
    )
    task_count = task_count_result.scalar() or 0

    declaration_count_result = await session.execute(
        select(func.count()).select_from(GryzzlyDeclaration)
    )
    declaration_count = declaration_count_result.scalar() or 0

    # Test API connection
    try:
        client = GryzzlyAPIClient()
        api_connected = await client.test_connection()
    except ValueError:
        # API key not configured
        api_connected = False

    return {
        "last_sync": {
            "type": last_sync.sync_type if last_sync else None,
            "status": last_sync.sync_status if last_sync else None,
            "timestamp": (
                last_sync.completed_at.isoformat()
                if last_sync and last_sync.completed_at
                else None
            ),
            "records_synced": last_sync.records_synced if last_sync else 0,
        },
        "data_counts": {
            "collaborators": collaborator_count,
            "projects": project_count,
            "tasks": task_count,
            "declarations": declaration_count,
        },
        "api_connected": api_connected,
    }


@router.get("/stats")
async def get_gryzzly_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get Gryzzly data statistics"""
    # Count collaborators
    total_collaborators_result = await session.execute(
        select(func.count()).select_from(GryzzlyCollaborator)
    )
    total_collaborators = total_collaborators_result.scalar() or 0

    active_collaborators_result = await session.execute(
        select(func.count())
        .select_from(GryzzlyCollaborator)
        .where(GryzzlyCollaborator.is_active == True)
    )
    active_collaborators = active_collaborators_result.scalar() or 0

    # Count projects
    total_projects_result = await session.execute(
        select(func.count()).select_from(GryzzlyProject)
    )
    total_projects = total_projects_result.scalar() or 0

    active_projects_result = await session.execute(
        select(func.count())
        .select_from(GryzzlyProject)
        .where(GryzzlyProject.is_active == True)
    )
    active_projects = active_projects_result.scalar() or 0

    billable_projects_result = await session.execute(
        select(func.count())
        .select_from(GryzzlyProject)
        .where(GryzzlyProject.is_billable == True)
    )
    billable_projects = billable_projects_result.scalar() or 0

    # Count tasks
    total_tasks_result = await session.execute(
        select(func.count()).select_from(GryzzlyTask)
    )
    total_tasks = total_tasks_result.scalar() or 0

    # Count declarations
    total_declarations_result = await session.execute(
        select(func.count()).select_from(GryzzlyDeclaration)
    )
    total_declarations = total_declarations_result.scalar() or 0

    approved_declarations_result = await session.execute(
        select(func.count())
        .select_from(GryzzlyDeclaration)
        .where(GryzzlyDeclaration.status == "approved")
    )
    approved_declarations = approved_declarations_result.scalar() or 0

    pending_declarations_result = await session.execute(
        select(func.count())
        .select_from(GryzzlyDeclaration)
        .where(GryzzlyDeclaration.status.in_(["draft", "submitted"]))
    )
    pending_declarations = pending_declarations_result.scalar() or 0

    return {
        "total_collaborators": total_collaborators,
        "active_collaborators": active_collaborators,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "billable_projects": billable_projects,
        "total_tasks": total_tasks,
        "total_declarations": total_declarations,
        "approved_declarations": approved_declarations,
        "pending_declarations": pending_declarations,
    }


@router.post("/sync/test-connection")
async def test_gryzzly_connection(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Test Gryzzly API connection"""
    try:
        client = GryzzlyAPIClient()
        connected = await client.test_connection()

        if not connected:
            raise HTTPException(
                status_code=503, detail="Unable to connect to Gryzzly API"
            )

        return {
            "status": "success",
            "message": "Successfully connected to Gryzzly API",
            "api_url": client.base_url,
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/sync/collaborators")
async def sync_collaborators(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Trigger collaborator synchronization from Gryzzly.

    Note: Currently runs synchronously. For large datasets, consider
    implementing as a background task using Celery (see tasks_future.py.example).
    """
    sync_service = GryzzlySyncService(session)
    try:
        result = await sync_service.sync_collaborators()
        return {
            "status": "completed",
            "message": f"Synchronisation terminée: {result['created']} créés, {result['updated']} mis à jour",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Erreur lors de la synchronisation: {str(e)}",
        }


@router.post("/sync/projects")
async def sync_projects(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger project synchronization from Gryzzly"""
    sync_service = GryzzlySyncService(session)
    try:
        result = await sync_service.sync_projects()
        return {
            "status": "completed",
            "message": f"Synchronisation terminée: {result['created']} créés, {result['updated']} mis à jour",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Erreur lors de la synchronisation: {str(e)}",
        }


@router.post("/sync/tasks")
async def sync_tasks(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger task synchronization from Gryzzly"""
    sync_service = GryzzlySyncService(session)
    try:
        result = await sync_service.sync_tasks()
        return {
            "status": "completed",
            "message": f"Synchronisation terminée: {result['created']} créés, {result['updated']} mis à jour",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Erreur lors de la synchronisation: {str(e)}",
        }


@router.post("/sync/declarations")
async def sync_declarations(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger declaration synchronization from Gryzzly"""
    sync_service = GryzzlySyncService(session)
    try:
        result = await sync_service.sync_declarations(start_date, end_date)
        return {
            "status": "completed",
            "message": f"Synchronisation terminée: {result['created']} créés, {result['updated']} mis à jour",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Erreur lors de la synchronisation: {str(e)}",
        }


@router.post("/sync/full")
async def sync_full(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger full synchronization from Gryzzly"""
    sync_service = GryzzlySyncService(session)
    try:
        result = await sync_service.sync_all(triggered_by=current_user.email)
        return {
            "status": "completed",
            "message": "Synchronisation complète terminée",
            "details": result,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Erreur lors de la synchronisation: {str(e)}",
        }


@router.get("/collaborators")
async def get_collaborators(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get list of synchronized Gryzzly collaborators"""
    query = select(GryzzlyCollaborator)

    if active_only:
        query = query.where(GryzzlyCollaborator.is_active == True)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    collaborators = result.scalars().all()

    return [
        {
            "id": str(collab.id),
            "gryzzly_id": collab.gryzzly_id,
            "email": collab.email,
            "first_name": collab.first_name,
            "last_name": collab.last_name,
            "matricule": collab.matricule,
            "department": collab.department,
            "position": collab.position,
            "is_active": collab.is_active,
            "is_admin": collab.is_admin,
            "local_user_id": (
                str(collab.local_user_id) if collab.local_user_id else None
            ),
            "last_synced_at": (
                collab.last_synced_at.isoformat() if collab.last_synced_at else None
            ),
            "created_at": collab.created_at.isoformat() if collab.created_at else None,
            "updated_at": collab.updated_at.isoformat() if collab.updated_at else None,
        }
        for collab in collaborators
    ]


@router.get("/projects")
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    billable_only: bool = Query(False),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get list of synchronized Gryzzly projects"""
    query = select(GryzzlyProject)

    if active_only:
        query = query.where(GryzzlyProject.is_active == True)

    if billable_only:
        query = query.where(GryzzlyProject.is_billable == True)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    projects = result.scalars().all()

    return [
        {
            "id": str(project.id),
            "gryzzly_id": project.gryzzly_id,
            "name": project.name,
            "code": project.code,
            "description": project.description,
            "client_name": project.client_name,
            "project_type": project.project_type,
            "start_date": (
                project.start_date.isoformat() if project.start_date else None
            ),
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "is_active": project.is_active,
            "is_billable": project.is_billable,
            "budget_hours": project.budget_hours,
            "budget_amount": project.budget_amount,
            "last_synced_at": (
                project.last_synced_at.isoformat() if project.last_synced_at else None
            ),
            "created_at": (
                project.created_at.isoformat() if project.created_at else None
            ),
            "updated_at": (
                project.updated_at.isoformat() if project.updated_at else None
            ),
        }
        for project in projects
    ]


@router.get("/tasks")
async def get_tasks(
    project_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get list of synchronized Gryzzly tasks"""
    query = select(GryzzlyTask)

    if project_id:
        query = query.where(GryzzlyTask.project_id == project_id)

    if active_only:
        query = query.where(GryzzlyTask.is_active == True)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "id": str(task.id),
            "gryzzly_id": task.gryzzly_id,
            "project_id": str(task.project_id),
            "name": task.name,
            "code": task.code,
            "description": task.description,
            "task_type": task.task_type,
            "estimated_hours": task.estimated_hours,
            "is_active": task.is_active,
            "is_billable": task.is_billable,
            "last_synced_at": (
                task.last_synced_at.isoformat() if task.last_synced_at else None
            ),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
        for task in tasks
    ]


@router.get("/declarations")
async def get_declarations(
    collaborator_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get list of synchronized Gryzzly declarations"""
    query = select(GryzzlyDeclaration)

    if collaborator_id:
        query = query.where(GryzzlyDeclaration.collaborator_id == collaborator_id)

    if project_id:
        query = query.where(GryzzlyDeclaration.project_id == project_id)

    if start_date:
        query = query.where(GryzzlyDeclaration.date >= start_date)

    if end_date:
        query = query.where(GryzzlyDeclaration.date <= end_date)

    if status:
        query = query.where(GryzzlyDeclaration.status == status)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    declarations = result.scalars().all()

    return [
        {
            "id": str(decl.id),
            "gryzzly_id": decl.gryzzly_id,
            "collaborator_id": str(decl.collaborator_id),
            "project_id": str(decl.project_id),
            "task_id": str(decl.task_id) if decl.task_id else None,
            "date": decl.date.isoformat() if decl.date else None,
            "duration_hours": decl.duration_hours,
            "duration_minutes": decl.duration_minutes,
            "description": decl.description,
            "comment": decl.comment,
            "status": decl.status,
            "approved_by": decl.approved_by,
            "approved_at": decl.approved_at.isoformat() if decl.approved_at else None,
            "is_billable": decl.is_billable,
            "billing_rate": decl.billing_rate,
            "last_synced_at": (
                decl.last_synced_at.isoformat() if decl.last_synced_at else None
            ),
            "created_at": decl.created_at.isoformat() if decl.created_at else None,
            "updated_at": decl.updated_at.isoformat() if decl.updated_at else None,
        }
        for decl in declarations
    ]


@router.get("/sync-logs")
async def get_sync_logs(
    sync_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get synchronization logs"""
    query = select(GryzzlySyncLog)

    if sync_type:
        query = query.where(GryzzlySyncLog.sync_type == sync_type)

    if status:
        query = query.where(GryzzlySyncLog.sync_status == status)

    query = query.order_by(GryzzlySyncLog.created_at.desc()).offset(skip).limit(limit)
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
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
