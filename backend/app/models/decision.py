"""
Officer Decision and Audit Trail Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import enum


class DecisionStatus(str, enum.Enum):
    """Officer decision statuses"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class OfficerDecision(Base):
    """
    Stores final procurement officer decisions for tender-bidder evaluations.
    Single source of truth for officer approvals/rejections.
    """
    __tablename__ = "officer_decisions"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), ForeignKey("tenders.tender_id"), index=True, nullable=False)
    bidder_id = Column(String(100), index=True, nullable=False)

    decision = Column(Enum(DecisionStatus), nullable=False)
    officer_id = Column(String(100), nullable=False)  # User/officer identifier
    officer_name = Column(String(255), nullable=True)  # Optional display name

    remarks = Column(Text, nullable=True)  # Decision justification/notes

    decided_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<OfficerDecision(id={self.id}, tender={self.tender_id}, bidder={self.bidder_id}, decision={self.decision})>"


class AuditEvent(str, enum.Enum):
    """Audit event types"""
    TENDER_UPLOADED = "TENDER_UPLOADED"
    REQUIREMENTS_EXTRACTED = "REQUIREMENTS_EXTRACTED"
    BIDDER_DOCUMENTS_UPLOADED = "BIDDER_DOCUMENTS_UPLOADED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    COMPLIANCE_EVALUATED = "COMPLIANCE_EVALUATED"
    RISK_ASSESSED = "RISK_ASSESSED"
    DECISION_MADE = "DECISION_MADE"
    REQUIREMENT_EDITED = "REQUIREMENT_EDITED"
    REPORT_GENERATED = "REPORT_GENERATED"


class AuditLog(Base):
    """
    Comprehensive audit trail for all system operations.
    Records who did what, when, and on which entities.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AuditEvent), nullable=False, index=True)

    tender_id = Column(String(100), index=True, nullable=True)
    bidder_id = Column(String(100), index=True, nullable=True)

    user_id = Column(String(100), nullable=True)  # Actor (officer, system, etc.)
    user_name = Column(String(255), nullable=True)

    action_description = Column(Text, nullable=False)  # Human-readable action
    event_metadata = Column(Text, nullable=True)  # JSON-encoded additional context

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event={self.event_type}, timestamp={self.timestamp})>"
