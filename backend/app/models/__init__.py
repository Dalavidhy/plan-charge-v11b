"""Database models package."""

from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin
from app.models.organization import Organization
from app.models.person import (
    Person,
    PersonEmail,
    PersonIdentifier,
    Engagement,
    User,
    UserOrgRole,
)
from app.models.team import Team, TeamMember
from app.models.project import Project, ProjectMember, Epic, Task, TaskAssignee, TaskDependency
from app.models.allocation import Allocation, AllocationBreakdown
from app.models.calendar import Calendar, Holiday, Capacity, Absence
from app.models.integration import (
    ExternalProvider,
    ExternalConnection,
    ExternalAccount,
    SyncJob,
    SyncEvent,
    IdentityLink,
    IdentityMatchRule,
    StgRoster,
    StgAbsence,
    StgTimesheet,
)
from app.models.benefit import BenefitType, BenefitPolicy, PersonBenefit
from app.models.audit import AuditLog, RefreshToken, ApiToken
from app.models.misc import Comment, Attachment, Tag, EntityTag
from app.models.payfit import PayfitEmployee, PayfitContract, PayfitAbsence, PayfitSyncLog
from app.models.gryzzly import (
    GryzzlyCollaborator,
    GryzzlyProject,
    GryzzlyTask,
    GryzzlyDeclaration,
    GryzzlyCollaboratorProject,
    GryzzlySyncLog
)
from app.models.tr_eligibility import TREligibilityOverride
from app.models.forecast import Forecast

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Organization
    "Organization",
    # Person
    "Person",
    "PersonEmail",
    "PersonIdentifier",
    "Engagement",
    "User",
    "UserOrgRole",
    # Team
    "Team",
    "TeamMember",
    # Project
    "Project",
    "ProjectMember",
    "Epic",
    "Task",
    "TaskAssignee",
    "TaskDependency",
    # Allocation
    "Allocation",
    "AllocationBreakdown",
    # Calendar
    "Calendar",
    "Holiday",
    "Capacity",
    "Absence",
    # Integration
    "ExternalProvider",
    "ExternalConnection",
    "ExternalAccount",
    "SyncJob",
    "SyncEvent",
    "IdentityLink",
    "IdentityMatchRule",
    "StgRoster",
    "StgAbsence",
    "StgTimesheet",
    # Benefit
    "BenefitType",
    "BenefitPolicy",
    "PersonBenefit",
    # Audit
    "AuditLog",
    "RefreshToken",
    "ApiToken",
    # Misc
    "Comment",
    "Attachment",
    "Tag",
    "EntityTag",
    # Payfit
    "PayfitEmployee",
    "PayfitContract",
    "PayfitAbsence",
    "PayfitSyncLog",
    # Gryzzly
    "GryzzlyCollaborator",
    "GryzzlyProject",
    "GryzzlyTask",
    "GryzzlyDeclaration",
    "GryzzlyCollaboratorProject",
    "GryzzlySyncLog",
    # TR Eligibility
    "TREligibilityOverride",
    # Forecast
    "Forecast",
]