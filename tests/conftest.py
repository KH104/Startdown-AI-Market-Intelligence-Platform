"""
Pytest configuration and fixtures for testing
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.company import Company
from app.models.lead import Lead
from app.auth.security import get_password_hash, create_access_token


# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_app():
    """Create test FastAPI application"""
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield app
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create test client for API requests"""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="function")
def test_db():
    """Create test database session"""
    # Create fresh tables for each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after each test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Create JWT token for test user"""
    token = create_access_token(data={"sub": test_user.email})
    return token


@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers for API requests"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_company(test_db):
    """Create a test company"""
    company = Company(
        name="Test Tech Company",
        industry="Technology",
        location="San Francisco, CA",
        funding_amount=5000000.0
    )
    test_db.add(company)
    test_db.commit()
    test_db.refresh(company)
    return company


@pytest.fixture
def test_lead(test_db, test_company):
    """Create a test lead"""
    lead = Lead(
        company_id=test_company.id,
        main_contact_email="john.doe@testtech.com",
        score=75.5,
        enrichment_status="completed"
    )
    test_db.add(lead)
    test_db.commit()
    test_db.refresh(lead)
    return lead


@pytest.fixture
def sample_companies_data():
    """Sample company data for testing"""
    return [
        {
            "name": "TechCorp Solutions",
            "industry": "Technology",
            "location": "San Francisco, CA",
            "funding_amount": 2500000.0
        },
        {
            "name": "FinanceFlow Inc",
            "industry": "Fintech",
            "location": "New York, NY", 
            "funding_amount": 1200000.0
        },
        {
            "name": "HealthTech Innovations",
            "industry": "Healthcare",
            "location": "Boston, MA",
            "funding_amount": 8000000.0
        }
    ]


@pytest.fixture
def sample_leads_data(test_company):
    """Sample lead data for testing"""
    return [
        {
            "company_id": test_company.id,
            "main_contact_email": "ceo@testtech.com",
            "score": 85.0,
            "enrichment_status": "pending"
        },
        {
            "company_id": test_company.id,
            "main_contact_email": "sales@testtech.com", 
            "score": 70.0,
            "enrichment_status": "completed"
        }
    ]