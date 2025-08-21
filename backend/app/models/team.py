"""Team models."""

from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Team(BaseModel, SoftDeleteMixin):
    """Team model."""

    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_teams_org_name"),)

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    lead = relationship("Person", foreign_keys=[lead_id])
    members = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    projects = relationship("Project", back_populates="team")

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name})>"


class TeamMember(BaseModel):
    """Team membership model."""

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "person_id",
            "active_from",
            name="uq_team_members_team_person_from",
        ),
        Index("ix_team_members_person", "person_id"),
        Index("ix_team_members_dates", "active_from", "active_to"),
    )

    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    person_id = Column(
        UUID(as_uuid=True), ForeignKey("people.id"), nullable=False, index=True
    )
    active_from = Column(Date, nullable=False)
    active_to = Column(Date, nullable=True)
    role_in_team = Column(String(100), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="members")
    person = relationship("Person", back_populates="team_memberships")
