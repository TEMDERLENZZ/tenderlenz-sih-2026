"""
Phase 8 Security Tests - FastAPI Endpoint Protection Verification
Verifies:
1. Unauthenticated requests to protected endpoints return 401 Unauthorized.
2. Authenticated BIDDER attempting OFFICER endpoints returns 403 Forbidden.
3. Authenticated OFFICER executing officer operations is allowed.
4. Public endpoints remains accessible without authentication.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.services.auth.password import hash_password

# Setup isolated test database for security tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase8_security.db"
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
    """Setup test database override for Phase 8 security test module"""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    # Create test users
    officer = User(
        username="sec_officer",
        password_hash=hash_password("officerpass123"),
        role=UserRole.OFFICER,
        is_active=True
    )
    bidder = User(
        username="sec_bidder",
        password_hash=hash_password("bidderpass123"),
        role=UserRole.BIDDER,
        is_active=True
    )
    db.add(officer)
    db.add(bidder)
    db.commit()
    db.close()

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def get_token(username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]


# ============================================================================
# 1. PUBLIC ENDPOINT TESTS
# ============================================================================

def test_public_root_accessible():
    res = client.get("/")
    assert res.status_code == 200


def test_public_health_accessible():
    res = client.get("/health")
    assert res.status_code == 200


def test_public_auth_login_accessible():
    res = client.post("/api/auth/login", json={"username": "invalid", "password": "bad"})
    assert res.status_code == 401


# ============================================================================
# 2. UNAUTHENTICATED REQUEST TESTS (MUST RETURN 401 UNAUTHORIZED)
# ============================================================================

@pytest.mark.parametrize("method,path", [
    ("GET", "/api/auth/me"),
    ("POST", "/api/documents/upload"),
    ("POST", "/api/documents/upload-batch"),
    ("GET", "/api/documents/bidder/BIDDER_001"),
    ("GET", "/api/documents/1"),
    ("GET", "/api/documents/bidder/BIDDER_001/summary"),
    ("POST", "/api/documents/reprocess/1"),
    ("DELETE", "/api/documents/clear-all"),
    ("DELETE", "/api/documents/bidder/BIDDER_001/clear"),
    ("GET", "/api/documents/classify-test/1"),
    ("POST", "/api/tenders/upload"),
    ("POST", "/api/tenders/seed-demo"),
    ("GET", "/api/tenders/list"),
    ("POST", "/api/tenders/DEMO_TENDER_001/extract-requirements"),
    ("GET", "/api/tenders/DEMO_TENDER_001/requirements"),
    ("POST", "/api/tenders/DEMO_TENDER_001/requirements"),
    ("PUT", "/api/tenders/requirements/1"),
    ("DELETE", "/api/tenders/requirements/1"),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/evaluate"),
    ("GET", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/compliance"),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/assess-risk"),
    ("GET", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/risk"),
    ("POST", "/api/verification/run/BIDDER_001"),
    ("GET", "/api/verification/session/1"),
    ("GET", "/api/verification/session/1/results"),
    ("GET", "/api/verification/bidder/BIDDER_001/latest"),
    ("GET", "/api/verification/providers/status"),
    ("DELETE", "/api/verification/session/1"),
    ("DELETE", "/api/verification/bidder/BIDDER_001/clear"),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/decision"),
    ("GET", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/decision"),
    ("GET", "/api/tenders/audit-logs"),
])
def test_unauthenticated_requests_return_401(method, path):
    res = client.request(method, path)
    assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


# ============================================================================
# 3. BIDDER ROLE FORBIDDEN TESTS (MUST RETURN 403 FORBIDDEN FOR OFFICER ROUTES)
# ============================================================================

@pytest.mark.parametrize("method,path,payload", [
    ("POST", "/api/tenders/upload", None),
    ("POST", "/api/tenders/seed-demo", None),
    ("POST", "/api/tenders/DEMO_TENDER_001/extract-requirements", None),
    ("POST", "/api/tenders/DEMO_TENDER_001/requirements", {"requirement_code": "REQ-TEST", "title": "Test", "description": "Desc", "requirement_type": "ELIGIBILITY"}),
    ("PUT", "/api/tenders/requirements/1", {"title": "Updated"}),
    ("DELETE", "/api/tenders/requirements/1", None),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/evaluate", None),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/assess-risk", None),
    ("POST", "/api/verification/run/BIDDER_001", None),
    ("DELETE", "/api/verification/session/1", None),
    ("DELETE", "/api/verification/bidder/BIDDER_001/clear", None),
    ("POST", "/api/documents/reprocess/1", None),
    ("DELETE", "/api/documents/clear-all", None),
    ("DELETE", "/api/documents/bidder/BIDDER_001/clear", None),
    ("POST", "/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/decision", {"decision": "APPROVED"}),
    ("GET", "/api/tenders/audit-logs", None),
])
def test_bidder_role_forbidden_on_officer_routes(method, path, payload):
    token = get_token("sec_bidder", "bidderpass123")
    headers = {"Authorization": f"Bearer {token}"}
    kwargs = {"headers": headers}
    if payload:
        kwargs["json"] = payload
    res = client.request(method, path, **kwargs)
    assert res.status_code == 403, f"Expected 403 for BIDDER on {method} {path}, got {res.status_code}"


# ============================================================================
# 4. OFFICER ROLE AUTHORIZED TESTS
# ============================================================================

def test_officer_role_allowed_on_officer_routes():
    token = get_token("sec_officer", "officerpass123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test seed demo tender
    res = client.post("/api/tenders/seed-demo", headers=headers)
    assert res.status_code == 200, f"Expected 200 for OFFICER on seed-demo, got {res.status_code}"

    # Test audit logs
    res_audit = client.get("/api/tenders/audit-logs", headers=headers)
    assert res_audit.status_code == 200, f"Expected 200 for OFFICER on audit-logs, got {res_audit.status_code}"

    # Test tenders list
    res_list = client.get("/api/tenders/list", headers=headers)
    assert res_list.status_code == 200, f"Expected 200 for OFFICER on tenders list, got {res_list.status_code}"


def test_bidder_role_allowed_on_user_routes():
    token = get_token("sec_bidder", "bidderpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Test auth me
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "BIDDER"

    # Test bidder summary
    res_summary = client.get("/api/documents/bidder/BIDDER_001/summary", headers=headers)
    assert res_summary.status_code == 200
