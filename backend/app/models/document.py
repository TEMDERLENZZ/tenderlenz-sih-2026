"""
SQLAlchemy models for document storage
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, Float
from sqlalchemy.sql import func
from app.database import Base
import enum

class DocumentType(str, enum.Enum):
    GST_CERTIFICATE = "GST_CERTIFICATE"
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    PAN_CARD = "PAN_CARD"
    INCOME_TAX_RETURN = "INCOME_TAX_RETURN"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    EPFO_REGISTRATION = "EPFO_REGISTRATION"
    ESIC_REGISTRATION = "ESIC_REGISTRATION"
    LOCAL_CONTENT_DECLARATION = "LOCAL_CONTENT_DECLARATION"
    BIS_CERTIFICATE = "BIS_CERTIFICATE"
    STARTUP_CERTIFICATE = "STARTUP_CERTIFICATE"
    NSIC_CERTIFICATE = "NSIC_CERTIFICATE"
    COMPANY_INCORPORATION = "COMPANY_INCORPORATION"
    NON_BLACKLISTING_DECLARATION = "NON_BLACKLISTING_DECLARATION"
    FINANCIAL_TURNOVER_CERTIFICATE = "FINANCIAL_TURNOVER_CERTIFICATE"

class ProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    PARTIALLY_EXTRACTED = "PARTIALLY_EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(String(100), index=True)  # Links all docs for one bidder
    document_type = Column(Enum(DocumentType), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))

    # Processing info
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))

    # Extracted data - stored as JSON
    extracted_data = Column(JSON)

    # Raw text from OCR/PDF extraction
    raw_text = Column(Text)

    # Overall extraction confidence score (0.0 - 1.0)
    extraction_confidence = Column(Float, nullable=True)

    # SHA-256 hash of the file bytes for duplicate detection
    file_hash = Column(String(64), index=True)

    # Extraction trace: list of {field, value, confidence, status, evidence, method} dicts
    extraction_trace = Column(JSON)

    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Error tracking
    error_message = Column(Text)

    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, bidder={self.bidder_id})>"
