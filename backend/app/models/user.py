"""
User Model for Authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    OFFICER = "OFFICER"
    BIDDER = "BIDDER"


class User(Base):
    """
    User model for authentication and authorization.

    Fields:
    - id: Primary key
    - username: Unique username for login
    - password_hash: Securely hashed password (never store plaintext)
    - role: User role (OFFICER or BIDDER)
    - is_active: Account status
    - created_at: Account creation timestamp
    - updated_at: Last modification timestamp
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}', active={self.is_active})>"
