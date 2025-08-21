"""Project and Task models."""

from datetime import date

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Project(BaseModel, SoftDeleteMixin):
    """Project model."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("org_id", "key", name="uq_projects_org_key"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_dates", "start_date", "end_date"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    key = Column(String(20), nullable=False)  # Short code like "PRJ-001"
    status = Column(
        Enum(
            "proposed", "active", "paused", "done", "cancelled", name="project_status"
        ),
        nullable=False,
        default="proposed",
    )
    priority = Column(Integer, nullable=False, default=100)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    tags = Column(ARRAY(String), nullable=False, default=[])
    description = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    owner = relationship("Person", foreign_keys=[owner_id])
    team = relationship("Team", back_populates="projects")
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    allocations = relationship(
        "Allocation", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, key={self.key}, name={self.name})>"


class ProjectMember(BaseModel):
    """Project membership model."""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "person_id", name="uq_project_members_project_person"
        ),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )
    role = Column(
        Enum("manager", "contributor", "viewer", name="project_role"),
        nullable=False,
        default="contributor",
    )

    # Relationships
    project = relationship("Project", back_populates="members")
    person = relationship("Person", back_populates="project_memberships")


class Epic(BaseModel):
    """Epic model for grouping tasks."""

    __tablename__ = "epics"
    __table_args__ = (Index("ix_epics_project", "project_id"),)

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="open")
    order_index = Column(Integer, nullable=False, default=0)

    # Relationships
    project = relationship("Project", back_populates="epics")
    tasks = relationship("Task", back_populates="epic", cascade="all, delete-orphan")


class Task(BaseModel, SoftDeleteMixin):
    """Task model."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project", "project_id"),
        Index("ix_tasks_epic", "epic_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_dates", "start_date", "due_date"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    epic_id = Column(UUID(as_uuid=True), ForeignKey("epics.id"), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum("todo", "in_progress", "blocked", "done", "cancelled", name="task_status"),
        nullable=False,
        default="todo",
    )
    estimate_hours = Column(Numeric(6, 2), nullable=True)
    actual_hours = Column(Numeric(6, 2), nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    tags = Column(ARRAY(String), nullable=False, default=[])
    order_index = Column(Integer, nullable=False, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    epic = relationship("Epic", back_populates="tasks")
    assignees = relationship(
        "TaskAssignee", back_populates="task", cascade="all, delete-orphan"
    )
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependent_on = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on",
    )
    allocations = relationship(
        "Allocation", back_populates="task", cascade="all, delete-orphan"
    )
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title})>"


class TaskAssignee(BaseModel):
    """Task assignee model."""

    __tablename__ = "task_assignees"
    __table_args__ = (
        UniqueConstraint("task_id", "person_id", name="uq_task_assignees_task_person"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )

    # Relationships
    task = relationship("Task", back_populates="assignees")
    person = relationship("Person", back_populates="task_assignments")


class TaskDependency(BaseModel):
    """Task dependency model."""

    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "task_id", "depends_on_task_id", name="uq_task_dependencies_task_depends"
        ),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    depends_on_task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    type = Column(
        Enum("blocks", "relates", name="dependency_type"),
        nullable=False,
        default="blocks",
    )

    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship(
        "Task", foreign_keys=[depends_on_task_id], back_populates="dependent_on"
    )
