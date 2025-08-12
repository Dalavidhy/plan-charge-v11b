"""Seed database with initial data."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import (
    Organization,
    User,
    UserOrgRole,
    Person,
    PersonEmail,
    Team,
    TeamMember,
    Project,
    Calendar,
)
from app.utils.security import get_password_hash


async def seed_database():
    """Seed the database with initial data."""
    async with AsyncSessionLocal() as session:
        # Check if data already exists
        result = await session.execute(select(Organization))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping...")
            return
        
        print("Seeding database...")
        
        # Create organization
        org = Organization(
            name="Demo Company",
            timezone="Europe/Paris",
            default_workweek={
                "monday": 7,
                "tuesday": 7,
                "wednesday": 7,
                "thursday": 7,
                "friday": 7,
                "saturday": 0,
                "sunday": 0,
            },
        )
        session.add(org)
        await session.flush()
        
        # Create people
        people = []
        for i, (name, email, role) in enumerate([
            ("Admin User", "admin@demo.com", "admin"),
            ("John Manager", "john@demo.com", "manager"),
            ("Jane Developer", "jane@demo.com", "member"),
            ("Bob Designer", "bob@demo.com", "member"),
            ("Alice Analyst", "alice@demo.com", "member"),
        ]):
            person = Person(
                org_id=org.id,
                full_name=name,
                active=True,
                weekly_hours_default=35,
                source="manual",
            )
            session.add(person)
            await session.flush()
            people.append(person)
            
            # Add email
            person_email = PersonEmail(
                org_id=org.id,
                person_id=person.id,
                email=email,
                kind="corporate",
                is_primary=True,
                verified=True,
                source="manual",
            )
            session.add(person_email)
            
            # Create user account
            user = User(
                org_id=org.id,
                person_id=person.id,
                email=email,
                full_name=name,
                password_hash=get_password_hash("demo123"),
                locale="fr",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            
            # Assign role
            user_role = UserOrgRole(
                org_id=org.id,
                user_id=user.id,
                role=role if i < 2 else "member",
            )
            session.add(user_role)
        
        # Create teams
        teams = []
        for name, lead_idx in [
            ("Engineering", 1),
            ("Design", 3),
            ("Analytics", 4),
        ]:
            team = Team(
                org_id=org.id,
                name=name,
                lead_id=people[lead_idx].id,
                color="#" + "".join([f"{i:02x}" for i in [100, 150, 200]]),
            )
            session.add(team)
            await session.flush()
            teams.append(team)
            
            # Add team members
            for person_idx in range(1, 5):
                if (name == "Engineering" and person_idx in [1, 2]) or \
                   (name == "Design" and person_idx == 3) or \
                   (name == "Analytics" and person_idx == 4):
                    team_member = TeamMember(
                        org_id=org.id,
                        team_id=team.id,
                        person_id=people[person_idx].id,
                        active_from=datetime.now().date(),
                    )
                    session.add(team_member)
        
        # Create projects
        projects = []
        for i, (name, key, status, team_idx) in enumerate([
            ("Website Redesign", "WEB", "active", 1),
            ("Mobile App", "MOB", "active", 0),
            ("Data Pipeline", "DATA", "proposed", 2),
            ("API v2", "API", "active", 0),
        ]):
            project = Project(
                org_id=org.id,
                name=name,
                key=key,
                status=status,
                priority=100 - i * 10,
                owner_id=people[1].id,
                team_id=teams[team_idx].id if team_idx < len(teams) else None,
                tags=["important"] if i == 0 else [],
            )
            session.add(project)
            projects.append(project)
        
        # Create calendar
        calendar = Calendar(
            org_id=org.id,
            name="France 2025",
            workweek={
                "monday": 7,
                "tuesday": 7,
                "wednesday": 7,
                "thursday": 7,
                "friday": 7,
                "saturday": 0,
                "sunday": 0,
            },
        )
        session.add(calendar)
        
        # Commit all data
        await session.commit()
        print("Database seeded successfully!")


async def main():
    """Main function."""
    # Initialize database tables
    await init_db()
    
    # Seed data
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())