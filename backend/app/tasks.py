"""
Celery tasks for async processing.

NOTE: Most async tasks are placeholders for future implementation.
See tasks_future.py.example for detailed implementation plans.
"""

from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "plan_charge",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=settings.CELERY_TASK_EAGER_PROPAGATES,
)

# Periodic tasks are disabled until implementation is needed
# See tasks_future.py.example for planned periodic tasks
celery_app.conf.beat_schedule = {}


# Active tasks (currently implemented)
# None at the moment - all tasks are placeholders

# Placeholder tasks - return success for compatibility
# These will be implemented when needed (see tasks_future.py.example)

@celery_app.task(name="app.tasks.sync_external_data")
def sync_external_data():
    """Placeholder for external data sync. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "message": "Task not yet implemented"}


@celery_app.task(name="app.tasks.calculate_utilization")
def calculate_utilization():
    """Placeholder for utilization calculation. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "message": "Task not yet implemented"}


@celery_app.task(name="app.tasks.cleanup_old_sessions")
def cleanup_old_sessions():
    """Placeholder for session cleanup. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "message": "Task not yet implemented"}


@celery_app.task(name="app.tasks.send_email")
def send_email(to: str, subject: str, body: str):
    """Placeholder for email sending. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "message": f"Email to {to} not sent - task not implemented"}


@celery_app.task(name="app.tasks.generate_report")
def generate_report(report_type: str, params: dict):
    """Placeholder for report generation. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "report_id": None, "message": "Task not yet implemented"}


@celery_app.task(name="app.tasks.process_bulk_import")
def process_bulk_import(file_path: str, import_type: str):
    """Placeholder for bulk import. See tasks_future.py.example for implementation plan."""
    return {"status": "skipped", "imported": 0, "errors": 0, "message": "Task not yet implemented"}