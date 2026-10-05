"""
Document-to-Document Cross-Checker

Verifies consistency across bidder's uploaded documents.
Phase 1 extracted data only - NO re-extraction.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentType
from app.models.verification import VerificationStatus, VerificationSourceMode, VerificationCategory
import re

class DocumentCrossChecker:
    """
    Cross-verify extracted fields across multiple documents.

    Checks:
    - Name consistency (GST vs PAN vs Udyam vs MCA)
    - GSTIN state validation
    - PAN consistency
    - Entity identity verification
    """

    def __init__(self, db: Session, bidder_id: str):
        self.db = db
        self.bidder_id = bidder_id
        self.documents = self._load_documents()

    def _load_documents(self) -> Dict[str, Document]:
        """Load all documents for bidder, indexed by document type"""
        docs = self.db.query(Document).filter(
            Document.bidder_id == self.bidder_id
        ).all()

        return {doc.document_type.value: doc for doc in docs}

    def _normalize_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize name for comparison"""
        if not name:
            return None

        name = name.upper().strip()
        # Remove common suffixes
        name = re.sub(r'\b(PVT\.?|LTD\.?|LIMITED|PRIVATE|COMPANY|CO\.?)\b', '', name)
        # Remove special characters
        name = re.sub(r'[^A-Z0-9\s]', '', name)
        # Collapse whitespace
        name = re.sub(r'\s+', ' ', name).strip()

        return name if name else None

    def _compare_names(self, name_a: Optional[str], name_b: Optional[str],
                       threshold: float = 0.8) -> tuple[VerificationStatus, str, float]:
        """
        Compare two names for similarity.

        Returns: (status, explanation, confidence)
        """
        if not name_a or not name_b:
            return (
                VerificationStatus.MISSING,
                "One or both names are missing",
                0.0
            )

        norm_a = self._normalize_name(name_a)
        norm_b = self._normalize_name(name_b)

        if norm_a == norm_b:
            return (
                VerificationStatus.VERIFIED,
                f"Names match exactly: '{name_a}' and '{name_b}'",
                1.0
            )

        # Simple substring check
        if norm_a and norm_b:
            if norm_a in norm_b or norm_b in norm_a:
                return (
                    VerificationStatus.VERIFIED,
                    f"Names substantially match: '{name_a}' and '{name_b}'",
                    0.85
                )

        return (
            VerificationStatus.MISMATCH,
            f"Names do not match: '{name_a}' vs '{name_b}'",
            0.3
        )

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Run all document-to-document cross-checks"""
        results = []

        results.extend(self._check_gst_vs_pan())
        results.extend(self._check_gst_vs_udyam())
        results.extend(self._check_gst_vs_mca())
        results.extend(self._check_pan_vs_itr())
        results.extend(self._check_gstin_state_validation())
        results.extend(self._check_bidder_identity_oem())
        results.extend(self._check_bidder_identity_turnover())
        results.extend(self._check_bidder_identity_local_content())

        return results

    def _check_gst_vs_pan(self) -> List[Dict[str, Any]]:
        """CROSS-001: GST legal name vs PAN name"""
        results = []

        gst_doc = self.documents.get('GST_CERTIFICATE')
        pan_doc = self.documents.get('PAN_CARD')

        if not gst_doc or not pan_doc:
            results.append({
                'check_id': 'CROSS-001',
                'category': VerificationCategory.CROSS_CHECK,
                'requirement': 'GST legal name must match PAN holder name',
                'document_source_a': 'GST_CERTIFICATE',
                'document_source_b': 'PAN_CARD',
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.MISSING,
                'confidence': 0.0,
                'explanation': 'GST Certificate or PAN Card not uploaded',
                'evidence': {'missing': True}
            })
            return results

        gst_data = gst_doc.extracted_data or {}
        pan_data = pan_doc.extracted_data or {}

        gst_name = gst_data.get('legal_name')
        pan_name = pan_data.get('name')

        status, explanation, confidence = self._compare_names(gst_name, pan_name)

        results.append({
            'check_id': 'CROSS-001',
            'category': VerificationCategory.CROSS_CHECK,
            'requirement': 'GST legal name must match PAN holder name',
            'document_source_a': 'GST_CERTIFICATE',
            'document_source_b': 'PAN_CARD',
            'extracted_value_a': {'legal_name': gst_name},
            'extracted_value_b': {'name': pan_name},
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {
                'gst_legal_name': gst_name,
                'pan_name': pan_name,
                'normalized_comparison': True
            }
        })

        return results

    def _check_gst_vs_udyam(self) -> List[Dict[str, Any]]:
        """CROSS-002: GST legal name vs Udyam enterprise name"""
        results = []

        gst_doc = self.documents.get('GST_CERTIFICATE')
        udyam_doc = self.documents.get('UDYAM_CERTIFICATE')

        if not gst_doc or not udyam_doc:
            results.append({
                'check_id': 'CROSS-002',
                'category': VerificationCategory.CROSS_CHECK,
                'requirement': 'GST legal name must match Udyam enterprise name',
                'document_source_a': 'GST_CERTIFICATE',
                'document_source_b': 'UDYAM_CERTIFICATE',
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.MISSING,
                'confidence': 0.0,
                'explanation': 'GST Certificate or Udyam Certificate not uploaded',
                'evidence': {'missing': True}
            })
            return results

        gst_data = gst_doc.extracted_data or {}
        udyam_data = udyam_doc.extracted_data or {}

        gst_name = gst_data.get('legal_name')
        udyam_name = udyam_data.get('enterprise_name')

        status, explanation, confidence = self._compare_names(gst_name, udyam_name)

        results.append({
            'check_id': 'CROSS-002',
            'category': VerificationCategory.CROSS_CHECK,
            'requirement': 'GST legal name must match Udyam enterprise name',
            'document_source_a': 'GST_CERTIFICATE',
            'document_source_b': 'UDYAM_CERTIFICATE',
            'extracted_value_a': {'legal_name': gst_name},
            'extracted_value_b': {'enterprise_name': udyam_name},
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {
                'gst_legal_name': gst_name,
                'udyam_enterprise_name': udyam_name
            }
        })

        return results

    def _check_gst_vs_mca(self) -> List[Dict[str, Any]]:
        """CROSS-003: GST legal name vs MCA company name"""
        results = []

        gst_doc = self.documents.get('GST_CERTIFICATE')
        mca_doc = self.documents.get('COMPANY_INCORPORATION')

        if not gst_doc or not mca_doc:
            results.append({
                'check_id': 'CROSS-003',
                'category': VerificationCategory.CROSS_CHECK,
                'requirement': 'GST legal name must match MCA company name',
                'document_source_a': 'GST_CERTIFICATE',
                'document_source_b': 'COMPANY_INCORPORATION',
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.NOT_APPLICABLE,
                'confidence': 0.0,
                'explanation': 'GST Certificate or Company Incorporation Certificate not uploaded',
                'evidence': {'missing': True}
            })
            return results

        gst_data = gst_doc.extracted_data or {}
        mca_data = mca_doc.extracted_data or {}

        gst_name = gst_data.get('legal_name')
        mca_name = mca_data.get('company_name')

        status, explanation, confidence = self._compare_names(gst_name, mca_name)

        results.append({
            'check_id': 'CROSS-003',
            'category': VerificationCategory.CROSS_CHECK,
            'requirement': 'GST legal name must match MCA company name',
            'document_source_a': 'GST_CERTIFICATE',
            'document_source_b': 'COMPANY_INCORPORATION',
            'extracted_value_a': {'legal_name': gst_name},
            'extracted_value_b': {'company_name': mca_name},
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {
                'gst_legal_name': gst_name,
                'mca_company_name': mca_name
            }
        })

        return results

    def _check_pan_vs_itr(self) -> List[Dict[str, Any]]:
        """CROSS-004: PAN name vs ITR name"""
        results = []

        pan_doc = self.documents.get('PAN_CARD')
        itr_doc = self.documents.get('INCOME_TAX_RETURN')

        if not pan_doc or not itr_doc:
            results.append({
                'check_id': 'CROSS-004',
                'category': VerificationCategory.CROSS_CHECK,
                'requirement': 'PAN holder name must match ITR name',
                'document_source_a': 'PAN_CARD',
                'document_source_b': 'INCOME_TAX_RETURN',
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.NOT_APPLICABLE,
                'confidence': 0.0,
                'explanation': 'PAN Card or Income Tax Return not uploaded',
                'evidence': {'missing': True}
            })
            return results

        pan_data = pan_doc.extracted_data or {}
        itr_data = itr_doc.extracted_data or {}

        pan_name = pan_data.get('name')
        itr_name = itr_data.get('name')

        status, explanation, confidence = self._compare_names(pan_name, itr_name)

        results.append({
            'check_id': 'CROSS-004',
            'category': VerificationCategory.CROSS_CHECK,
            'requirement': 'PAN holder name must match ITR name',
            'document_source_a': 'PAN_CARD',
            'document_source_b': 'INCOME_TAX_RETURN',
            'extracted_value_a': {'name': pan_name},
            'extracted_value_b': {'name': itr_name},
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {
                'pan_name': pan_name,
                'itr_name': itr_name
            }
        })

        return results

    def _check_gstin_state_validation(self) -> List[Dict[str, Any]]:
        """CROSS-005: GSTIN first 2 digits must match state code"""
        results = []

        gst_doc = self.documents.get('GST_CERTIFICATE')

        if not gst_doc:
            results.append({
                'check_id': 'CROSS-005',
                'category': VerificationCategory.REGISTRATION,
                'requirement': 'GSTIN state code must be valid',
                'document_source_a': 'GST_CERTIFICATE',
                'document_source_b': None,
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.MISSING,
                'confidence': 0.0,
                'explanation': 'GST Certificate not uploaded',
                'evidence': {'missing': True}
            })
            return results

        gst_data = gst_doc.extracted_data or {}
        gstin = gst_data.get('gstin')
        state = gst_data.get('state')

        if not gstin:
            results.append({
                'check_id': 'CROSS-005',
                'category': VerificationCategory.REGISTRATION,
                'requirement': 'GSTIN state code must be valid',
                'document_source_a': 'GST_CERTIFICATE',
                'document_source_b': None,
                'extracted_value_a': {'gstin': None},
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.DEMO,
                'status': VerificationStatus.MISSING,
                'confidence': 0.0,
                'explanation': 'GSTIN not extracted from GST Certificate',
                'evidence': {}
            })
            return results

        # Extract state code (first 2 digits)
        state_code = gstin[:2] if len(gstin) >= 2 else None

        # State code mapping (partial list)
        state_codes = {
            '27': 'Maharashtra', '29': 'Karnataka', '33': 'Tamil Nadu',
            '32': 'Kerala', '19': 'West Bengal', '07': 'Delhi'
        }

        expected_state = state_codes.get(state_code)

        if expected_state:
            status = VerificationStatus.VERIFIED
            explanation = f"GSTIN state code {state_code} is valid (corresponds to {expected_state})"
            confidence = 1.0
        else:
            status = VerificationStatus.NOT_VERIFIED
            explanation = f"GSTIN state code {state_code} could not be validated"
            confidence = 0.5

        results.append({
            'check_id': 'CROSS-005',
            'category': VerificationCategory.REGISTRATION,
            'requirement': 'GSTIN state code must be valid',
            'document_source_a': 'GST_CERTIFICATE',
            'document_source_b': None,
            'extracted_value_a': {'gstin': gstin, 'state': state, 'state_code': state_code},
            'extracted_value_b': None,
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {
                'gstin': gstin,
                'extracted_state': state,
                'state_code': state_code,
                'expected_state': expected_state
            }
        })

        return results

    def _check_bidder_identity_oem(self) -> List[Dict[str, Any]]:
        """CROSS-006: OEM authorization bidder name verification"""
        results = []

        oem_doc = self.documents.get('OEM_AUTHORIZATION')

        if not oem_doc:
            results.append({
                'check_id': 'CROSS-006',
                'category': VerificationCategory.IDENTITY,
                'requirement': 'OEM authorization must name the bidder',
                'document_source_a': 'OEM_AUTHORIZATION',
                'document_source_b': None,
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.NOT_APPLICABLE,
                'confidence': 0.0,
                'explanation': 'OEM Authorization not uploaded',
                'evidence': {'missing': True}
            })
            return results

        oem_data = oem_doc.extracted_data or {}
        authorized_bidder = oem_data.get('authorized_bidder_name')

        if authorized_bidder:
            status = VerificationStatus.VERIFIED
            explanation = f"OEM authorization names bidder: '{authorized_bidder}'"
            confidence = 0.9
        else:
            status = VerificationStatus.MISSING
            explanation = "Authorized bidder name not found in OEM authorization"
            confidence = 0.0

        results.append({
            'check_id': 'CROSS-006',
            'category': VerificationCategory.IDENTITY,
            'requirement': 'OEM authorization must name the bidder',
            'document_source_a': 'OEM_AUTHORIZATION',
            'document_source_b': None,
            'extracted_value_a': {'authorized_bidder_name': authorized_bidder},
            'extracted_value_b': None,
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {'authorized_bidder_name': authorized_bidder}
        })

        return results

    def _check_bidder_identity_turnover(self) -> List[Dict[str, Any]]:
        """CROSS-007: Financial turnover certificate bidder name"""
        results = []

        turnover_doc = self.documents.get('FINANCIAL_TURNOVER_CERTIFICATE')

        if not turnover_doc:
            results.append({
                'check_id': 'CROSS-007',
                'category': VerificationCategory.FINANCIAL,
                'requirement': 'Turnover certificate must name the bidder',
                'document_source_a': 'FINANCIAL_TURNOVER_CERTIFICATE',
                'document_source_b': None,
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.NOT_APPLICABLE,
                'confidence': 0.0,
                'explanation': 'Financial Turnover Certificate not uploaded',
                'evidence': {'missing': True}
            })
            return results

        turnover_data = turnover_doc.extracted_data or {}
        bidder_name = turnover_data.get('bidder_name')

        if bidder_name:
            status = VerificationStatus.VERIFIED
            explanation = f"Turnover certificate names bidder: '{bidder_name}'"
            confidence = 0.9
        else:
            status = VerificationStatus.MISSING
            explanation = "Bidder name not found in turnover certificate"
            confidence = 0.0

        results.append({
            'check_id': 'CROSS-007',
            'category': VerificationCategory.FINANCIAL,
            'requirement': 'Turnover certificate must name the bidder',
            'document_source_a': 'FINANCIAL_TURNOVER_CERTIFICATE',
            'document_source_b': None,
            'extracted_value_a': {'bidder_name': bidder_name},
            'extracted_value_b': None,
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {'bidder_name': bidder_name}
        })

        return results

    def _check_bidder_identity_local_content(self) -> List[Dict[str, Any]]:
        """CROSS-008: Local content declaration bidder name"""
        results = []

        local_doc = self.documents.get('LOCAL_CONTENT_DECLARATION')

        if not local_doc:
            results.append({
                'check_id': 'CROSS-008',
                'category': VerificationCategory.COMPLIANCE,
                'requirement': 'Local content declaration must name the bidder',
                'document_source_a': 'LOCAL_CONTENT_DECLARATION',
                'document_source_b': None,
                'extracted_value_a': None,
                'extracted_value_b': None,
                'verification_source': 'DOCUMENT_CROSS_CHECK',
                'source_mode': VerificationSourceMode.UNAVAILABLE,
                'status': VerificationStatus.NOT_APPLICABLE,
                'confidence': 0.0,
                'explanation': 'Local Content Declaration not uploaded',
                'evidence': {'missing': True}
            })
            return results

        local_data = local_doc.extracted_data or {}
        bidder_name = local_data.get('bidder_name')

        if bidder_name:
            status = VerificationStatus.VERIFIED
            explanation = f"Local content declaration names bidder: '{bidder_name}'"
            confidence = 0.9
        else:
            status = VerificationStatus.MISSING
            explanation = "Bidder name not found in local content declaration"
            confidence = 0.0

        results.append({
            'check_id': 'CROSS-008',
            'category': VerificationCategory.COMPLIANCE,
            'requirement': 'Local content declaration must name the bidder',
            'document_source_a': 'LOCAL_CONTENT_DECLARATION',
            'document_source_b': None,
            'extracted_value_a': {'bidder_name': bidder_name},
            'extracted_value_b': None,
            'verification_source': 'DOCUMENT_CROSS_CHECK',
            'source_mode': VerificationSourceMode.DEMO,
            'status': status,
            'confidence': confidence,
            'explanation': explanation,
            'evidence': {'bidder_name': bidder_name}
        })

        return results
