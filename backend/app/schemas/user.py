"""
User Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserRole(str):
    """User role type"""
    OFFICER = "OFFICER"
    BIDDER = "BIDDER"


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=6, max_length=100, description="Password (min 6 characters)")
    role: str = Field(..., description="User role: OFFICER or BIDDER")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is OFFICER or BIDDER"""
        if v not in ['OFFICER', 'BIDDER']:
            raise ValueError('Role must be OFFICER or BIDDER')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v.strip()


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class UserResponse(BaseModel):
    """Safe user information (NEVER includes password_hash)"""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
