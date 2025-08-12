"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_async_session
from app.main import app
from app.models import Organization, Person, User, UserOrgRole
from app.utils.security import get_password_hash

# Override settings for testing
settings.ENVIRONMENT = "testing"
settings.DATABASE_URL = "postgresql+asyncpg://plancharge_test:plancharge_test@localhost:5433/plancharge_test"
settings.RATE_LIMIT_ENABLED = False

# Test database engine
test_engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Get async test client."""
    
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session
    
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> TestClient:
    """Get sync test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def test_org(async_session: AsyncSession) -> Organization:
    """Create test organization."""
    org = Organization(
        name="Test Organization",
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
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_person(async_session: AsyncSession, test_org: Organization) -> Person:
    """Create test person."""
    person = Person(
        org_id=test_org.id,
        full_name="Test Person",
        active=True,
        weekly_hours_default=35,
        source="manual",
    )
    async_session.add(person)
    await async_session.commit()
    await async_session.refresh(person)
    return person


@pytest_asyncio.fixture
async def test_user(
    async_session: AsyncSession,
    test_org: Organization,
    test_person: Person,
) -> User:
    """Create test user."""
    user = User(
        org_id=test_org.id,
        person_id=test_person.id,
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("testpassword"),
        locale="fr",
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()
    
    # Add role
    role = UserOrgRole(
        org_id=test_org.id,
        user_id=user.id,
        role="admin",
    )
    async_session.add(role)
    
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict[str, str]:
    """Get authentication headers."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}