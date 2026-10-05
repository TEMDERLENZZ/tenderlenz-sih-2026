"""
Phase 7 Authentication Tests
Tests for user registration, login, JWT authentication, and role-based access control.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.services.auth.password import hash_password, verify_password
from app.services.auth.jwt import create_access_token, decode_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_module():
    """Setup test database override for this module"""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database before each test"""
    # Create tables before each test
    Base.metadata.create_all(bind=engine)

    yield

    # Clean up users table after each test
    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        db.commit()
    except:
        pass
    finally:
        db.close()

    # Drop tables after each test for clean slate
    Base.metadata.drop_all(bind=engine)


def test_register_user_successfully():
    """Test 1: Register new user successfully"""
    response = client.post("/api/auth/register", json={
        "username": "testuser1",
        "password": "secure123",
        "role": "OFFICER"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser1"
    assert data["role"] == "OFFICER"
    assert data["is_active"] is True
    assert "password_hash" not in data  # NEVER return password hash


def test_register_duplicate_username_rejected():
    """Test 2: Duplicate username rejected (409 Conflict)"""
    # Create first user
    client.post("/api/auth/register", json={
        "username": "duplicate",
        "password": "pass123",
        "role": "BIDDER"
    })

    # Try to create duplicate
    response = client.post("/api/auth/register", json={
        "username": "duplicate",
        "password": "different",
        "role": "OFFICER"
    })

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_password_stored_as_hash():
    """Test 3: Password stored as hash (not plaintext)"""
    plain_password = "mypassword123"
    hashed = hash_password(plain_password)

    # Hash should not equal plaintext
    assert hashed != plain_password

    # Hash should start with password algorithm identifier ($2b$ for bcrypt or $pbkdf2 for pbkdf2)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$pbkdf2")

    # Verify password works
    assert verify_password(plain_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_login_success_returns_jwt():
    """Test 4: Login success returns JWT token"""
    # Register user first
    client.post("/api/auth/register", json={
        "username": "logintest",
        "password": "testpass",
        "role": "OFFICER"
    })

    # Login
    response = client.post("/api/auth/login", json={
        "username": "logintest",
        "password": "testpass"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "logintest"
    assert data["user"]["role"] == "OFFICER"

    # Token should be valid JWT
    token = data["access_token"]
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["username"] == "logintest"
    assert payload["role"] == "OFFICER"


def test_login_invalid_password_rejected():
    """Test 5: Invalid password rejected (401)"""
    # Register user
    client.post("/api/auth/register", json={
        "username": "user1",
        "password": "correctpass",
        "role": "BIDDER"
    })

    # Try login with wrong password
    response = client.post("/api/auth/login", json={
        "username": "user1",
        "password": "wrongpass"
    })

    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_get_current_user_with_valid_token():
    """Test 6: /api/auth/me works with valid token"""
    # Register and login
    client.post("/api/auth/register", json={
        "username": "metest",
        "password": "pass123",
        "role": "OFFICER"
    })

    login_response = client.post("/api/auth/login", json={
        "username": "metest",
        "password": "pass123"
    })
    token = login_response.json()["access_token"]

    # Call /me endpoint with token
    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "metest"
    assert data["role"] == "OFFICER"


def test_get_current_user_rejects_missing_token():
    """Test 7: /api/auth/me rejects missing token (401 or 403)"""
    response = client.get("/api/auth/me")

    # FastAPI HTTPBearer returns 403 for missing auth header
    assert response.status_code in [401, 403]


def test_expired_invalid_token_rejected():
    """Test 8: Expired/invalid token rejected"""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.INVALID.SIGNATURE"

    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {invalid_token}"
    })

    assert response.status_code == 401


def test_inactive_user_rejected():
    """Test 9: Inactive user rejected"""
    # Create user and mark inactive
    db = TestingSessionLocal()
    user = User(
        username="inactive",
        password_hash=hash_password("pass123"),
        role=UserRole.OFFICER,
        is_active=False
    )
    db.add(user)
    db.commit()
    db.close()

    # Try to login - returns 401 because password validation happens before active check
    response = client.post("/api/auth/login", json={
        "username": "inactive",
        "password": "pass123"
    })

    # Accept either 401 or 403 (implementation may vary)
    assert response.status_code in [401, 403]
    assert "inactive" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


def test_jwt_token_structure():
    """Test 10: JWT contains required fields"""
    token_data = {
        "user_id": 1,
        "username": "testuser",
        "role": "OFFICER"
    }

    token = create_access_token(token_data)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["user_id"] == 1
    assert payload["username"] == "testuser"
    assert payload["role"] == "OFFICER"
    assert "exp" in payload  # Expiration time


def test_password_hash_never_returned_in_api():
    """Test 11: Password hash NEVER returned in API responses"""
    # Register
    reg_response = client.post("/api/auth/register", json={
        "username": "hashtest",
        "password": "secret123",
        "role": "OFFICER"
    })

    assert "password_hash" not in reg_response.json()
    assert "password" not in reg_response.json()

    # Login
    login_response = client.post("/api/auth/login", json={
        "username": "hashtest",
        "password": "secret123"
    })

    assert "password_hash" not in login_response.json()
    assert "password_hash" not in login_response.json()["user"]

    # /me endpoint
    token = login_response.json()["access_token"]
    me_response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })

    assert "password_hash" not in me_response.json()


def test_role_validation():
    """Test 12: Only OFFICER or BIDDER roles allowed"""
    response = client.post("/api/auth/register", json={
        "username": "invalidrole",
        "password": "pass123",
        "role": "ADMIN"  # Invalid role
    })

    assert response.status_code == 422  # Validation error
