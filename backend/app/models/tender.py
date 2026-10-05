"""
SQLAlchemy models for Phase 6 Tender Requirement Engine
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import enum

class RequirementType(str, enum.Enum):
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"
    BOOLEAN = "BOOLEAN"
    NUMERIC = "NUMERIC"
    TEXT_MATCH = "TEXT_MATCH"
    IDENTITY_MATCH = "IDENTITY_MATCH"
    DATE_VALIDITY = "DATE_VALIDITY"
    PERCENTAGE = "PERCENTAGE"
    LIST_MATCH = "LIST_MATCH"
    STATUS_CHECK = "STATUS_CHECK"

class ComplianceResultStatus(str, enum.Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    MISSING = "MISSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))

    extracted_text = Column(Text)
    status = Column(String(50), default="UPLOADED")

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Tender(id={self.id}, tender_id={self.tender_id}, title={self.title})>"

class TenderRequirement(Base):
    __tablename__ = "tender_requirements"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), ForeignKey("tenders.tender_id"), index=True, nullable=False)
    requirement_code = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False, default="ELIGIBILITY")
    title = Column(String(255), nullable=False)
    description = Column(Text)
    requirement_type = Column(Enum(RequirementType), nullable=False)
    mandatory = Column(Boolean, default=True)
    operator = Column(String(20), default=">=")
    required_value = Column(JSON)
    unit = Column(String(50))
    source_document = Column(String(100))
    source_page = Column(Integer)
    evidence_text = Column(Text)
    extraction_confidence = Column(Float, default=1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TenderRequirement(id={self.id}, code={self.requirement_code}, title={self.title})>"

class TenderComplianceResult(Base):
    __tablename__ = "tender_compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), index=True, nullable=False)
    bidder_id = Column(String(100), index=True, nullable=False)
    requirement_id = Column(Integer, ForeignKey("tender_requirements.id"), index=True, nullable=True)
    requirement_code = Column(String(50), nullable=False)

    result = Column(Enum(ComplianceResultStatus), nullable=False)
    required_value = Column(JSON)
    actual_value = Column(JSON)
    confidence = Column(Float, default=1.0)
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TenderComplianceResult(id={self.id}, bidder={self.bidder_id}, req={self.requirement_code}, result={self.result})>"

class BidderRiskAssessment(Base):
    __tablename__ = "bidder_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), ForeignKey("tenders.tender_id"), index=True, nullable=False)
    bidder_id = Column(String(100), index=True, nullable=False)

    risk_level = Column(Enum(RiskLevel), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100

    factors = Column(JSON, nullable=False)  # List of risk factors
    summary = Column(Text, nullable=False)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BidderRiskAssessment(id={self.id}, bidder={self.bidder_id}, level={self.risk_level}, score={self.risk_score})>"
