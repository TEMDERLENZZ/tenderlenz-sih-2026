"""
Pydantic schemas for document extraction results
Each document type has its own structured schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# ============================================================
# 1. GST CERTIFICATE
# ============================================================
class GSTCertificateData(BaseModel):
    gstin: Optional[str] = Field(None, description="15-digit GSTIN")
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    registration_date: Optional[str] = None
    status: Optional[str] = None  # ACTIVE, CANCELLED, etc.
    address: Optional[str] = None
    state: Optional[str] = None
    principal_place_of_business: Optional[str] = None

# ============================================================
# 2. UDYAM / MSME CERTIFICATE
# ============================================================
class UdyamCertificateData(BaseModel):
    udyam_registration_number: Optional[str] = None
    enterprise_name: Optional[str] = None
    enterprise_type: Optional[str] = None  # Micro, Small, Medium
    date_of_incorporation: Optional[str] = None
    date_of_udyam_registration: Optional[str] = None
    major_activity: Optional[str] = None
    social_category: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None

# ============================================================
# 3. PAN CARD
# ============================================================
class PANCardData(BaseModel):
    pan_number: Optional[str] = Field(None, description="10-character PAN")
    name: Optional[str] = None
    father_name: Optional[str] = None
    date_of_birth: Optional[str] = None

# ============================================================
# 4. INCOME TAX RETURN
# ============================================================
class IncomeTaxReturnData(BaseModel):
    pan: Optional[str] = None
    name: Optional[str] = None
    assessment_year: Optional[str] = None
    financial_year: Optional[str] = None
    total_income: Optional[str] = None
    total_tax_paid: Optional[str] = None
    filing_date: Optional[str] = None
    acknowledgement_number: Optional[str] = None

# ============================================================
# 5. OEM AUTHORIZATION
# ============================================================
class OEMAuthorizationData(BaseModel):
    oem_name: Optional[str] = None
    authorized_bidder_name: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    authorization_date: Optional[str] = None
    expiry_date: Optional[str] = None
    authorization_number: Optional[str] = None
    status: Optional[str] = None  # VALID, EXPIRED
    scope: Optional[str] = None

# ============================================================
# 6. EPFO REGISTRATION
# ============================================================
class EPFORegistrationData(BaseModel):
    establishment_id: Optional[str] = None
    establishment_name: Optional[str] = None
    registration_date: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None  # ACTIVE, INACTIVE

# ============================================================
# 7. ESIC REGISTRATION
# ============================================================
class ESICRegistrationData(BaseModel):
    esic_registration_number: Optional[str] = None
    establishment_name: Optional[str] = None
    registration_date: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

# ============================================================
# 8. LOCAL CONTENT DECLARATION
# ============================================================
class LocalContentDeclarationData(BaseModel):
    bidder_name: Optional[str] = None
    local_content_percentage: Optional[str] = None
    declaration_date: Optional[str] = None
    product_description: Optional[str] = None
    category: Optional[str] = None  # Class-I, Class-II
    signatory_name: Optional[str] = None
    signatory_designation: Optional[str] = None

# ============================================================
# 9. BIS CERTIFICATE
# ============================================================
class BISCertificateData(BaseModel):
    license_number: Optional[str] = None
    licensee_name: Optional[str] = None
    product_name: Optional[str] = None
    is_standard: Optional[str] = None  # IS 1234:2020
    date_of_grant: Optional[str] = None
    valid_upto: Optional[str] = None
    status: Optional[str] = None

# ============================================================
# 10. STARTUP CERTIFICATE
# ============================================================
class StartupCertificateData(BaseModel):
    certificate_number: Optional[str] = None
    startup_name: Optional[str] = None
    date_of_incorporation: Optional[str] = None
    recognition_date: Optional[str] = None
    valid_upto: Optional[str] = None
    dpiit_number: Optional[str] = None

# ============================================================
# 11. NSIC CERTIFICATE
# ============================================================
class NSICCertificateData(BaseModel):
    registration_number: Optional[str] = None
    enterprise_name: Optional[str] = None
    validity_from: Optional[str] = None
    validity_to: Optional[str] = None
    category: Optional[str] = None

# ============================================================
# 12. COMPANY INCORPORATION / MCA
# ============================================================
class CompanyIncorporationData(BaseModel):
    cin: Optional[str] = Field(None, description="Corporate Identity Number")
    company_name: Optional[str] = None
    date_of_incorporation: Optional[str] = None
    company_category: Optional[str] = None
    company_subcategory: Optional[str] = None
    authorized_capital: Optional[str] = None
    paid_up_capital: Optional[str] = None
    registered_office_address: Optional[str] = None
    status: Optional[str] = None

# ============================================================
# 13. NON-BLACKLISTING DECLARATION
# ============================================================
class NonBlacklistingDeclarationData(BaseModel):
    bidder_name: Optional[str] = None
    declaration_date: Optional[str] = None
    declaration_statement: Optional[str] = None
    signatory_name: Optional[str] = None
    signatory_designation: Optional[str] = None

# ============================================================
# 14. FINANCIAL TURNOVER CERTIFICATE
# ============================================================
class FinancialTurnoverCertificateData(BaseModel):
    bidder_name: Optional[str] = None
    fy_2021_22_turnover: Optional[str] = None
    fy_2022_23_turnover: Optional[str] = None
    fy_2023_24_turnover: Optional[str] = None
    fy_2024_25_turnover: Optional[str] = None
    average_turnover: Optional[str] = None
    certificate_issuer: Optional[str] = None
    issuer_registration_number: Optional[str] = None
    issue_date: Optional[str] = None

# ============================================================
# RESPONSE MODELS
# ============================================================
from pydantic import BaseModel, ConfigDict

class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bidder_id: str
    document_type: str
    file_name: str
    status: str
    uploaded_at: datetime


class DocumentExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bidder_id: str
    document_type: str
    status: str
    extraction_confidence: Optional[float] = None
    extracted_data: dict
    extraction_trace: Optional[list] = None
    raw_text: Optional[str] = None
    processing_completed_at: Optional[datetime] = None


class BatchDocumentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    file_name: str
    document_type: str
    detected_type: Optional[str] = None
    expected_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    status: str
    extraction_confidence: Optional[float] = None
    is_duplicate: bool = False
    classification_mismatch: bool = False
    message: Optional[str] = None
    extracted_data: Optional[dict] = None
    error_message: Optional[str] = None


class BatchUploadResponse(BaseModel):
    bidder_id: str
    total_files: int
    processed: int
    successful: int
    partially_extracted: int = 0
    failed: int = 0
    needs_review: int = 0
    duplicates: int = 0
    documents: List[BatchDocumentItem]


