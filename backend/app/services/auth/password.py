"""
Password Hashing Utilities
Uses passlib with bcrypt for secure password storage.
"""
from passlib.context import CryptContext

# Create password context with bcrypt and pbkdf2_sha256 as fallback
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt (or pbkdf2_sha256 fallback).

    Args:
        plain_password: Plaintext password string

    Returns:
        Hashed password string (safe to store in database)
    """
    try:
        return pwd_context.hash(plain_password)
    except Exception as e:
        # Fallback to pbkdf2_sha256 if bcrypt fails
        print(f"[WARNING] bcrypt unavailable, using pbkdf2_sha256: {e}")
        from passlib.hash import pbkdf2_sha256
        return pbkdf2_sha256.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        plain_password: Plaintext password from user input
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback verification
        from passlib.hash import pbkdf2_sha256
        return pbkdf2_sha256.verify(plain_password, hashed_password)
