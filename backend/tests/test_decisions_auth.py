"""
Updated tests for Officer Decision with Phase 7 Authentication
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.decision import OfficerDecision, AuditLog, DecisionStatus, AuditEvent
from app.models.tender import Tender, TenderComplianceResult, ComplianceResultStatus
from app.models.user import User, UserRole
from app.services.auth.password import hash_password

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_decisions_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Setup test database override for this module"""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test officer user
    officer = User(
        username="test_officer",
        password_hash=hash_password("testpass"),
        role=UserRole.OFFICER,
        is_active=True
    )
    db.add(officer)

    # Seed test tender data
    tender = Tender(
        tender_id="TEST_TENDER_001",
        title="Test Tender",
        status="EXTRACTED"
    )
    db.add(tender)

    compliance_result = TenderComplianceResult(
        tender_id="TEST_TENDER_001",
        bidder_id="TEST_BIDDER_001",
        requirement_code="REQ-001",
        result=ComplianceResultStatus.SATISFIED,
        explanation="Test compliance result"
    )
    db.add(compliance_result)
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)


def get_auth_headers(test_db):
    """Helper to get authentication token"""
    response = client.post("/api/auth/login", json={
        "username": "test_officer",
        "password": "testpass"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_record_decision_requires_auth(test_db):
    """Test that decision endpoint rejects unauthenticated requests"""
    response = client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED",
            "remarks": "Test"
        }
    )

    # FastAPI HTTPBearer returns 401 for missing Authorization header
    assert response.status_code == 401


def test_record_decision_success_with_auth(test_db):
    """Test successfully recording a decision with authentication"""
    headers = get_auth_headers(test_db)

    response = client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED",
            "remarks": "All requirements satisfied"
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVED"
    assert data["officer_id"] is not None  # Auto-populated from token
    assert data["remarks"] == "All requirements satisfied"
    assert "decided_at" in data


def test_officer_identity_from_token(test_db):
    """Test that officer identity comes from token, not request body"""
    headers = get_auth_headers(test_db)

    # Try to fake officer_id in request body (should be ignored)
    response = client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED",
            "officer_id": "FAKE_OFFICER",  # This should be ignored
            "officer_name": "Fake Name",   # This should be ignored
            "remarks": "Test"
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()

    # Officer identity should come from authenticated token, not request body
    assert data["officer_id"] != "FAKE_OFFICER"  # Should NOT use fake ID from request
    assert data["officer_name"] == "test_officer"  # Should use authenticated username
