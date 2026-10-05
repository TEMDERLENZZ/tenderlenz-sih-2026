"""
Authentication API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth.password import hash_password, verify_password
from app.services.auth.jwt import create_access_token
from app.services.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Validates:
    - Username uniqueness
    - Password strength (min 6 characters)
    - Role validity (OFFICER or BIDDER)

    Returns:
        Safe user information (NO password_hash)

    Raises:
        409 Conflict: Username already exists
        400 Bad Request: Invalid input
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_data.username}' is already registered"
        )

    # Hash password (NEVER store plaintext)
    password_hash = hash_password(user_data.password)

    # Create user
    new_user = User(
        username=user_data.username,
        password_hash=password_hash,
        role=UserRole[user_data.role],  # Convert string to enum
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_data.username}' is already registered"
        )

    # Return safe user info (NEVER return password_hash)
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role.value,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Flow:
    1. Validate username exists
    2. Verify password
    3. Check user is active
    4. Generate JWT token
    5. Return token + user info

    Returns:
        TokenResponse with access_token and user info

    Raises:
        401 Unauthorized: Invalid username or password
        403 Forbidden: User account is inactive
    """
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Contact administrator."
        )

    # Create JWT token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }
    access_token = create_access_token(token_data)

    # Return token + user info
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header:
    Authorization: Bearer <token>

    Returns:
        Safe user information

    Raises:
        401 Unauthorized: Missing or invalid token
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
