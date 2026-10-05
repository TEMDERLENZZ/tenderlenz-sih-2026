"""
SQLAlchemy models for Phase 2 Verification Engine
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import enum

class VerificationSessionType(str, enum.Enum):
    DOCUMENT_CROSS_CHECK = "DOCUMENT_CROSS_CHECK"
    EXTERNAL_VERIFICATION = "EXTERNAL_VERIFICATION"
    FULL_VERIFICATION = "FULL_VERIFICATION"

class VerificationSessionStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    NOT_VERIFIED = "NOT_VERIFIED"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"

class VerificationSourceMode(str, enum.Enum):
    LIVE = "LIVE"
    SANDBOX = "SANDBOX"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"

class VerificationCategory(str, enum.Enum):
    IDENTITY = "IDENTITY"
    REGISTRATION = "REGISTRATION"
    FINANCIAL = "FINANCIAL"
    COMPLIANCE = "COMPLIANCE"
    CROSS_CHECK = "CROSS_CHECK"
    EXTERNAL = "EXTERNAL"

class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(String(100), index=True, nullable=False)
    session_type = Column(Enum(VerificationSessionType), nullable=False)
    status = Column(Enum(VerificationSessionStatus), default=VerificationSessionStatus.PENDING)

    # Summary counters
    total_checks = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    missing_count = Column(Integer, default=0)
    not_applicable_count = Column(Integer, default=0)
    source_unavailable_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Additional metadata
    meta_data = Column(JSON)
    error_message = Column(Text)

    def __repr__(self):
        return f"<VerificationSession(id={self.id}, bidder={self.bidder_id}, status={self.status})>"

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('verification_sessions.id'), index=True, nullable=False)
    bidder_id = Column(String(100), index=True, nullable=False)

    # Check identification
    check_id = Column(String(50), nullable=False)  # e.g., "GST-001", "CROSS-001"
    category = Column(Enum(VerificationCategory), nullable=False)
    requirement = Column(Text, nullable=False)  # Human-readable description

    # Source documents (for cross-checks)
    document_source_a = Column(String(100))  # DocumentType value
    document_source_b = Column(String(100))  # DocumentType value (nullable for external checks)

    # Values being compared
    extracted_value_a = Column(JSON)
    extracted_value_b = Column(JSON)
    verified_value = Column(JSON)  # From external source if applicable

    # Verification source
    verification_source = Column(String(100))  # e.g., "GST_PROVIDER", "DOCUMENT_CROSS_CHECK"
    source_mode = Column(Enum(VerificationSourceMode), nullable=False)

    # Result
    status = Column(Enum(VerificationStatus), nullable=False)
    confidence = Column(Float)  # 0.0 - 1.0
    explanation = Column(Text, nullable=False)  # Why this result?
    evidence = Column(JSON)  # Supporting evidence

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON)

    def __repr__(self):
        return f"<VerificationResult(id={self.id}, check={self.check_id}, status={self.status})>"
