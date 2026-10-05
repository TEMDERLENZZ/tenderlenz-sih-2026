"""
Pydantic schemas for Phase 6 Tender Requirement Engine
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.tender import RequirementType, ComplianceResultStatus

class TenderUploadResponse(BaseModel):
    id: int
    tender_id: str
    title: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class TenderRequirementBase(BaseModel):
    requirement_code: str
    category: str
    title: str
    description: Optional[str] = None
    requirement_type: RequirementType
    mandatory: bool = True
    operator: Optional[str] = ">="
    required_value: Any = None
    unit: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    evidence_text: Optional[str] = None
    extraction_confidence: Optional[float] = 1.0

class TenderRequirementCreate(TenderRequirementBase):
    pass

class TenderRequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    requirement_type: Optional[RequirementType] = None
    mandatory: Optional[bool] = None
    operator: Optional[str] = None
    required_value: Optional[Any] = None
    unit: Optional[str] = None
    evidence_text: Optional[str] = None

class TenderRequirementResponse(TenderRequirementBase):
    id: int
    tender_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TenderExtractionResponse(BaseModel):
    tender_id: str
    total_requirements: int
    requirements: List[TenderRequirementResponse]

class TenderComplianceResultDetail(BaseModel):
    id: int
    tender_id: str
    bidder_id: str
    requirement_id: Optional[int] = None
    requirement_code: str
    result: ComplianceResultStatus
    required_value: Any = None
    actual_value: Any = None
    confidence: Optional[float] = 1.0
    explanation: str
    evidence: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TenderComplianceSummary(BaseModel):
    tender_id: str
    bidder_id: str
    total_requirements: int
    satisfied: int
    not_satisfied: int
    missing: int
    review_required: int
    unable_to_verify: int
    not_applicable: int = 0
    compliance_percentage: float
    disclaimer: str = "Final procurement decision remains with the authorized Procurement Officer."
    results: List[TenderComplianceResultDetail]
