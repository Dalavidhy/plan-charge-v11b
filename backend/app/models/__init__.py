"""Database models package."""

from app.models.allocation import Allocation, AllocationBreakdown
from app.models.audit import ApiToken, AuditLog, RefreshToken
from app.models.base import BaseModel, SoftDeleteMixin, TimestampMixin
from app.models.benefit import BenefitPolicy, BenefitType, PersonBenefit
from app.models.calendar import Absence, Calendar, Capacity, Holiday
from app.models.forecast import Forecast
from app.models.gryzzly import (
    GryzzlyCollaborator,
    GryzzlyCollaboratorProject,
    GryzzlyDeclaration,
    GryzzlyProject,
    GryzzlySyncLog,
    GryzzlyTask,
)
from app.models.integration import (
    ExternalAccount,
    ExternalConnection,
    ExternalProvider,
    IdentityLink,
    IdentityMatchRule,
    StgAbsence,
    StgRoster,
    StgTimesheet,
    SyncEvent,
    SyncJob,
)
from app.models.misc import Attachment, Comment, EntityTag, Tag
from app.models.organization import Organization
from app.models.payfit import (
    PayfitAbsence,
    PayfitContract,
    PayfitEmployee,
    PayfitSyncLog,
)
from app.models.person import (
    Engagement,
    Person,
    PersonEmail,
    PersonIdentifier,
    User,
    UserOrgRole,
)
from app.models.project import (
    Epic,
    Project,
    ProjectMember,
    Task,
    TaskAssignee,
    TaskDependency,
)
from app.models.team import Team, TeamMember
from app.models.tr_eligibility import TREligibilityOverride

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
