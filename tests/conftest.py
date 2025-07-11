import pytest
from shared.infrastructure.database.connection import Base, get_db
import io
import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.main import app
# from src.infrastructure.database.connection import Base, get_db
# from src.infrastructure.repositories.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork


# Test Database Configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://admin:admin123@localhost:5432/ddd_app_test"
)

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = io.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a fresh database session for each test."""
    # Create tables
    with test_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS contas"))
        conn.commit()
    import src.iam.infrastructure.database.models
    import src.plans.infrastructure.database.models

    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after each test to ensure clean state
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def unit_of_work(db_session):
    """Create a Unit of Work instance for testing."""
    from src.iam.infrastructure.iam_unit_of_work import IAMUnitOfWork
    
    # Create unit of work with all available repositories
    repositories = ["user", "user_session", "organization", "user_organization_role", "role", "permission", "policy", "resource"]
    uow = IAMUnitOfWork(db_session, repositories)
    
    # Add convenient properties for test compatibility
    uow.users = uow.get_repository("user")
    uow.organizations = uow.get_repository("organization")
    uow.user_sessions = uow.get_repository("user_session")
    
    return uow


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client with database dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# @pytest.fixture
# def _client(db_session):
#     """Create an  test client for testing."""

#     def override_get_db():
#         try:
#             yield db_session
#         finally:
#             pass

#     app.dependency_overrides[get_db] = override_get_db
#     from httpx import Client, ASGITransport

#     transport = ASGITransport(app=app)
#     try:
#         with Client(transport=transport, base_url="http://test") as client:
#             yield client
#     finally:
#         app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {"email": "test@example.com", "name": "Test User", "password": "password123"}


@pytest.fixture
def sample_login_data():
    """Sample login data for testing."""
    return {"email": "test@example.com", "password": "password123"}


# Pytest markers for different test types
pytestmark = pytest.mark.io
