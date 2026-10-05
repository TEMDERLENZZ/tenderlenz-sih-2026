"""
Tests for Officer Decision and Audit Trail functionality
UPDATED FOR PHASE 7: All tests now include proper authentication
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_decisions.db"
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

    # PHASE 7: Create test officer user for authentication
    officer = User(
        username="test_officer",
        password_hash=hash_password("testpass"),
        role=UserRole.OFFICER,
        is_active=True
    )
    db.add(officer)

    # Seed test data
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
    """PHASE 7: Helper to get authentication token for tests"""
    response = client.post("/api/auth/login", json={
        "username": "test_officer",
        "password": "testpass"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_record_decision_success(test_db):
    """Test successfully recording a decision (PHASE 7: with authentication)"""
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
    # PHASE 7: officer_id now comes from authenticated token, not request
    assert data["officer_id"] is not None
    assert data["officer_name"] == "test_officer"  # From token
    assert data["remarks"] == "All requirements satisfied"
    assert "decided_at" in data


def test_record_decision_creates_audit_event(test_db):
    """Test that recording decision creates audit event (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)

    client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "REJECTED",
            "remarks": "Failed compliance"
        },
        headers=headers
    )

    # Check audit log
    audit_logs = test_db.query(AuditLog).filter(
        AuditLog.event_type == AuditEvent.DECISION_MADE
    ).all()

    assert len(audit_logs) == 1
    assert audit_logs[0].tender_id == "TEST_TENDER_001"
    assert audit_logs[0].bidder_id == "TEST_BIDDER_001"
    # PHASE 7: user_id now comes from authenticated token
    assert audit_logs[0].user_id is not None
    assert "REJECTED" in audit_logs[0].action_description


def test_record_decision_missing_tender(test_db):
    """Test recording decision for non-existent tender (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)

    response = client.post(
        "/api/tenders/MISSING_TENDER/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED"
        },
        headers=headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_record_decision_missing_compliance(test_db):
    """Test recording decision without compliance evaluation (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)

    # Add tender but no compliance results
    tender = Tender(
        tender_id="NO_COMPLIANCE_TENDER",
        title="Test",
        status="EXTRACTED"
    )
    test_db.add(tender)
    test_db.commit()

    response = client.post(
        "/api/tenders/NO_COMPLIANCE_TENDER/bidders/NEW_BIDDER/decision",
        json={
            "decision": "APPROVED"
        },
        headers=headers
    )

    assert response.status_code == 400
    assert "compliance evaluation" in response.json()["detail"].lower()


def test_record_decision_duplicate_conflict(test_db):
    """Test duplicate decision prevention (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)

    # First decision
    client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED"
        },
        headers=headers
    )

    # Try to record again
    response = client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "REJECTED"
        },
        headers=headers
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_get_decision_success(test_db):
    """Test retrieving existing decision (PHASE 8: with authentication)"""
    headers = get_auth_headers(test_db)

    # Record decision first
    client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "REQUIRES_REVIEW",
            "remarks": "Needs further review"
        },
        headers=headers
    )

    # Retrieve it
    response = client.get(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REQUIRES_REVIEW"
    assert data["remarks"] == "Needs further review"


def test_get_decision_not_found(test_db):
    """Test retrieving non-existent decision (PHASE 8: with authentication)"""
    headers = get_auth_headers(test_db)

    response = client.get(
        "/api/tenders/TEST_TENDER_001/bidders/NO_DECISION_BIDDER/decision",
        headers=headers
    )

    assert response.status_code == 404


def test_decision_persistence_after_refresh(test_db):
    """Test decision persists correctly (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)

    # Record decision
    response1 = client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={
            "decision": "APPROVED"
        },
        headers=headers
    )
    decision_id = response1.json()["id"]

    # Retrieve from database directly
    decision = test_db.query(OfficerDecision).filter(
        OfficerDecision.id == decision_id
    ).first()

    assert decision is not None
    assert decision.decision == DecisionStatus.APPROVED
    assert decision.tender_id == "TEST_TENDER_001"
    assert decision.bidder_id == "TEST_BIDDER_001"


def test_get_audit_logs(test_db):
    """Test retrieving audit logs (PHASE 8: with authentication)"""
    headers = get_auth_headers(test_db)

    # Create some decisions to generate audit events
    client.post(
        "/api/tenders/TEST_TENDER_001/bidders/TEST_BIDDER_001/decision",
        json={"decision": "APPROVED"},
        headers=headers
    )

    response = client.get(
        "/api/tenders/audit-logs?tender_id=TEST_TENDER_001",
        headers=headers
    )

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    assert logs[0]["event_type"] == "DECISION_MADE"


def test_all_decision_states(test_db):
    """Test all valid decision states (PHASE 7: with authentication)"""
    headers = get_auth_headers(test_db)
    states = ["APPROVED", "REJECTED", "REQUIRES_REVIEW"]

    for i, state in enumerate(states):
        # Create new bidder for each decision
        bidder_id = f"BIDDER_{i}"

        # Add compliance result for this bidder
        compliance = TenderComplianceResult(
            tender_id="TEST_TENDER_001",
            bidder_id=bidder_id,
            requirement_code="REQ-001",
            result=ComplianceResultStatus.SATISFIED,
            explanation="Test"
        )
        test_db.add(compliance)
        test_db.commit()

        response = client.post(
            f"/api/tenders/TEST_TENDER_001/bidders/{bidder_id}/decision",
            json={
                "decision": state
            },
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["decision"] == state
