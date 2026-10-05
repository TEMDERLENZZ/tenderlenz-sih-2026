"""
Pydantic schemas for Phase 2 Verification Engine
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.verification import (
    VerificationSessionType,
    VerificationSessionStatus,
    VerificationStatus,
    VerificationSourceMode,
    VerificationCategory
)

# ============================================================
# VERIFICATION SESSION SCHEMAS
# ============================================================

class VerificationSessionCreate(BaseModel):
    bidder_id: str
    session_type: VerificationSessionType = VerificationSessionType.FULL_VERIFICATION

class VerificationSessionSummary(BaseModel):
    id: int
    bidder_id: str
    session_type: VerificationSessionType
    status: VerificationSessionStatus
    total_checks: int
    verified_count: int
    mismatch_count: int
    missing_count: int
    not_applicable_count: int
    source_unavailable_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    meta_data: Optional[Dict[str, Any]] = Field(None, validation_alias="meta_data", serialization_alias="metadata")
    error_message: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True

# ============================================================
# VERIFICATION RESULT SCHEMAS
# ============================================================

class VerificationResultDetail(BaseModel):
    id: int
    session_id: int
    bidder_id: str
    check_id: str
    category: VerificationCategory
    requirement: str
    document_source_a: Optional[str]
    document_source_b: Optional[str]
    extracted_value_a: Optional[Dict[str, Any]]
    extracted_value_b: Optional[Dict[str, Any]]
    verified_value: Optional[Dict[str, Any]]
    verification_source: str
    source_mode: VerificationSourceMode
    status: VerificationStatus
    confidence: Optional[float]
    explanation: str
    evidence: Optional[Dict[str, Any]]
    timestamp: datetime
    meta_data: Optional[Dict[str, Any]] = Field(None, validation_alias="meta_data", serialization_alias="metadata")

    class Config:
        from_attributes = True
        populate_by_name = True

# ============================================================
# VERIFICATION RESPONSE SCHEMAS
# ============================================================

class VerificationRunResponse(BaseModel):
    session_id: int
    bidder_id: str
    status: VerificationSessionStatus
    message: str
    summary: VerificationSessionSummary

class VerificationResultsResponse(BaseModel):
    session: VerificationSessionSummary
    results: List[VerificationResultDetail]
    grouped_by_category: Dict[str, List[VerificationResultDetail]]

# ============================================================
# PROVIDER STATUS SCHEMAS
# ============================================================

class ProviderStatus(BaseModel):
    provider_name: str
    mode: VerificationSourceMode
    available: bool
    description: str
    supported_checks: List[str]

class ProvidersStatusResponse(BaseModel):
    providers: List[ProviderStatus]
    sandbox_mode_active: bool
    warning: str
