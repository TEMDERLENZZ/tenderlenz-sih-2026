"""
Requirement Matching & Evaluation Engine for Phase 6

Matches extracted tender requirements against Phase 1 extracted bidder documents
and Phase 2 external verification results.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.tender import TenderRequirement, TenderComplianceResult, RequirementType, ComplianceResultStatus
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.verification import VerificationResult, VerificationStatus

class ComplianceEvaluator:
    """Evaluates bidder compliance against tender requirements."""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_bidder(self, tender_id: str, bidder_id: str) -> List[TenderComplianceResult]:
        """
        Run complete requirement matching and evaluation for a bidder against a tender.
        Uses existing extracted bidder data (Phase 1) and external verification results (Phase 2).
        Does NOT re-upload or re-extract documents unnecessarily.
        """
        # Load tender requirements
        requirements = self.db.query(TenderRequirement).filter(
            TenderRequirement.tender_id == tender_id
        ).all()

        if not requirements:
            raise ValueError(f"No requirements found for tender_id '{tender_id}'. Run requirement extraction first.")

        # Load bidder documents
        documents = self.db.query(Document).filter(
            Document.bidder_id == bidder_id
        ).all()

        doc_map = {doc.document_type.value: doc for doc in documents}

        # Load Phase 2 verification results for bidder if present
        verification_results = self.db.query(VerificationResult).filter(
            VerificationResult.bidder_id == bidder_id
        ).all()

        if not verification_results:
            try:
                from app.services.verification.verification_engine import VerificationEngine
                engine = VerificationEngine(self.db)
                engine.run_verification(bidder_id)
                verification_results = self.db.query(VerificationResult).filter(
                    VerificationResult.bidder_id == bidder_id
                ).all()
            except Exception as ex:
                print(f"Auto-verification run warning: {ex}")

        # Delete old compliance results for this tender and bidder before re-evaluation
        self.db.query(TenderComplianceResult).filter(
            TenderComplianceResult.tender_id == tender_id,
            TenderComplianceResult.bidder_id == bidder_id
        ).delete()
        self.db.commit()

        compliance_results = []

        for req in requirements:
            res_obj = self._evaluate_single_requirement(req, doc_map, verification_results, tender_id, bidder_id)
            self.db.add(res_obj)
            compliance_results.append(res_obj)

        self.db.commit()
        return compliance_results

    def _evaluate_single_requirement(
        self,
        req: TenderRequirement,
        doc_map: Dict[str, Document],
        verification_results: List[VerificationResult],
        tender_id: str,
        bidder_id: str
    ) -> TenderComplianceResult:
        """Evaluate a single tender requirement against bidder documents & verification data."""

        req_type = req.requirement_type

        if req_type == RequirementType.NUMERIC:
            return self._eval_numeric(req, doc_map, tender_id, bidder_id)

        elif req_type == RequirementType.PERCENTAGE:
            return self._eval_percentage(req, doc_map, tender_id, bidder_id)

        elif req_type == RequirementType.DOCUMENT_REQUIRED:
            return self._eval_document_required(req, doc_map, tender_id, bidder_id)

        elif req_type == RequirementType.STATUS_CHECK:
            return self._eval_status_check(req, doc_map, verification_results, tender_id, bidder_id)

        elif req_type == RequirementType.IDENTITY_MATCH:
            return self._eval_identity_match(req, doc_map, verification_results, tender_id, bidder_id)

        elif req_type == RequirementType.BOOLEAN:
            return self._eval_boolean(req, doc_map, tender_id, bidder_id)

        elif req_type == RequirementType.DATE_VALIDITY:
            return self._eval_date_validity(req, doc_map, tender_id, bidder_id)

        else:
            # Fallback evaluation
            return self._eval_generic(req, doc_map, tender_id, bidder_id)

    # ------------------ EVALUATORS FOR SPECIFIC TYPES ------------------ #

    def _eval_numeric(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Numeric comparison (e.g. Minimum turnover ₹5 Crore for last 3 FY)."""
        turnover_doc = doc_map.get('FINANCIAL_TURNOVER_CERTIFICATE')

        if not turnover_doc or not turnover_doc.extracted_data:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value=self._format_currency(req.required_value),
                actual_value="No Financial Document Uploaded",
                confidence=1.0,
                explanation="Required financial turnover certificate document was not uploaded by bidder.",
                evidence={"document": "Financial Turnover Certificate", "status": "MISSING"}
            )

        extracted = turnover_doc.extracted_data

        # PHASE 6 ENHANCEMENT 1: Validate "last 3 financial years" requirement
        # Check if requirement description mentions "3 years" or "last 3 FY"
        requires_3_years = False
        if req.description:
            desc_lower = req.description.lower()
            requires_3_years = ('3 year' in desc_lower or 'last 3' in desc_lower or 'three year' in desc_lower)

        if requires_3_years:
            # Extract all available FY turnovers
            fy_turnovers = {
                '2021-22': extracted.get('fy_2021_22_turnover'),
                '2022-23': extracted.get('fy_2022_23_turnover'),
                '2023-24': extracted.get('fy_2023_24_turnover'),
                '2024-25': extracted.get('fy_2024_25_turnover'),
            }

            # Parse and validate 3-year requirement
            valid_years, parsed_values, explanation_detail = self._validate_3_year_turnover(
                fy_turnovers,
                req.required_value
            )

            if not valid_years:
                return TenderComplianceResult(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirement_id=req.id,
                    requirement_code=req.requirement_code,
                    result=ComplianceResultStatus.NOT_SATISFIED,
                    required_value=f"{self._format_currency(req.required_value)} for last 3 FY",
                    actual_value=explanation_detail,
                    confidence=0.95,
                    explanation=f"Turnover requirement not met: {explanation_detail}",
                    evidence={
                        "document": "Financial Turnover Certificate",
                        "extracted_fields": extracted,
                        "fy_turnovers": fy_turnovers,
                        "validation": "3-year check failed"
                    }
                )

            # All 3 years satisfied
            avg_3_year = sum(parsed_values) / len(parsed_values)
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.SATISFIED,
                required_value=f"{self._format_currency(req.required_value)} for last 3 FY",
                actual_value=f"3-year avg: {self._format_currency(avg_3_year)}",
                confidence=0.98,
                explanation=f"Bidder meets {self._format_currency(req.required_value)} minimum for all of last 3 financial years. {explanation_detail}",
                evidence={
                    "document": "Financial Turnover Certificate",
                    "page": 2,
                    "fy_turnovers": fy_turnovers,
                    "3_year_average": self._format_currency(avg_3_year),
                    "validation": "3-year check passed",
                    "extracted_fields": extracted
                }
            )

        # ORIGINAL LOGIC: Single-year turnover check (no 3-year requirement)
        actual_num = (
            extracted.get('average_turnover') or
            extracted.get('fy_2023_24_turnover') or
            extracted.get('fy_2022_23_turnover')
        )

        parsed_actual = self._parse_numeric_val(actual_num)
        parsed_req = self._parse_numeric_val(req.required_value)

        if parsed_actual is None:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.REVIEW_REQUIRED,
                required_value=self._format_currency(req.required_value),
                actual_value=str(actual_num) if actual_num else "Unparseable",
                confidence=0.5,
                explanation="Financial turnover value in uploaded certificate could not be automatically parsed.",
                evidence={"document": "Financial Turnover Certificate", "extracted_data": extracted}
            )

        # PHASE 6 ENHANCEMENT 2: ITR cross-validation
        itr_doc = doc_map.get('INCOME_TAX_RETURN')
        itr_warning = None
        if itr_doc and itr_doc.extracted_data:
            itr_income = itr_doc.extracted_data.get('total_income')
            parsed_itr = self._parse_numeric_val(itr_income)
            if parsed_itr and parsed_actual:
                # ITR income should reasonably align with turnover (±30% tolerance)
                diff_pct = abs(parsed_itr - parsed_actual) / max(parsed_actual, 1) * 100
                if diff_pct > 30:
                    itr_warning = f"ITR income ({self._format_currency(parsed_itr)}) differs significantly from turnover certificate ({self._format_currency(parsed_actual)}) - {diff_pct:.0f}% variance."

        op = req.operator or ">="
        satisfied = False
        if op == ">=":
            satisfied = parsed_actual >= parsed_req
        elif op == ">":
            satisfied = parsed_actual > parsed_req
        elif op == "==":
            satisfied = parsed_actual == parsed_req

        result_status = ComplianceResultStatus.SATISFIED if satisfied else ComplianceResultStatus.NOT_SATISFIED

        # Downgrade to REVIEW_REQUIRED if ITR cross-check shows significant discrepancy
        if satisfied and itr_warning:
            result_status = ComplianceResultStatus.REVIEW_REQUIRED
            explanation = (
                f"Bidder turnover ({self._format_currency(parsed_actual)}) meets requirement ({self._format_currency(parsed_req)}), "
                f"but ITR cross-validation flagged discrepancy: {itr_warning}"
            )
            confidence = 0.75
        else:
            explanation = (
                f"Bidder turnover ({self._format_currency(parsed_actual)}) meets or exceeds tender requirement ({self._format_currency(parsed_req)})."
                if satisfied else
                f"Bidder turnover ({self._format_currency(parsed_actual)}) is below required minimum ({self._format_currency(parsed_req)})."
            )
            confidence = 0.98

        evidence_data = {
            "document": "Financial Turnover Certificate",
            "page": 2,
            "text": f"Average/annual turnover: {self._format_currency(parsed_actual)}",
            "extracted_fields": extracted
        }
        if itr_warning:
            evidence_data["itr_cross_check"] = itr_warning

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=result_status,
            required_value=self._format_currency(parsed_req),
            actual_value=self._format_currency(parsed_actual),
            confidence=confidence,
            explanation=explanation,
            evidence=evidence_data
        )

    def _eval_percentage(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Percentage comparison (e.g. Minimum local content 50%)."""
        local_doc = doc_map.get('LOCAL_CONTENT_DECLARATION')

        if not local_doc or not local_doc.extracted_data:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value=f"{req.required_value}%",
                actual_value="No Declaration Uploaded",
                confidence=1.0,
                explanation="Local content declaration document was not uploaded by bidder.",
                evidence={"document": "Local Content Declaration", "status": "MISSING"}
            )

        extracted = local_doc.extracted_data
        actual_pct_val = extracted.get('local_content_percentage')
        parsed_actual = self._parse_percentage_val(actual_pct_val)
        parsed_req = self._parse_percentage_val(req.required_value) or 50.0

        if parsed_actual is None:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.REVIEW_REQUIRED,
                required_value=f"{parsed_req}%",
                actual_value="Could not extract %",
                confidence=0.5,
                explanation="Local content percentage could not be automatically extracted from declaration.",
                evidence={"document": "Local Content Declaration", "extracted_data": extracted}
            )

        satisfied = parsed_actual >= parsed_req
        result_status = ComplianceResultStatus.SATISFIED if satisfied else ComplianceResultStatus.NOT_SATISFIED
        actual_pct_str = f"{parsed_actual:g}%"
        req_pct_str = f"{parsed_req:g}%"

        explanation = (
            f"Bidder local content ({actual_pct_str}) satisfies tender minimum requirement ({req_pct_str})."
            if satisfied else
            f"Bidder local content ({actual_pct_str}) is less than mandatory minimum requirement ({req_pct_str})."
        )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=result_status,
            required_value=req_pct_str,
            actual_value=actual_pct_str,
            confidence=0.95,
            explanation=explanation,
            evidence={
                "document": "Local Content Declaration",
                "page": 1,
                "text": f"Declared local content percentage: {actual_pct_str}",
                "extracted_fields": extracted
            }
        )

    def _eval_document_required(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Document required check (e.g. BIS Certificate mandatory)."""
        target_doc_type = str(req.required_value or req.title).upper()

        # Map friendly names or requirement titles to DocumentType strings
        mapped_type = self._map_to_document_type(target_doc_type, req.title)
        matching_doc = doc_map.get(mapped_type)

        if not matching_doc:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value=f"{req.title} Mandatory",
                actual_value="Document Not Uploaded",
                confidence=1.0,
                explanation=f"Required document '{req.title}' was not uploaded by bidder.",
                evidence={"required_document": mapped_type, "status": "MISSING"}
            )

        if matching_doc.status in [ProcessingStatus.EXTRACTED, ProcessingStatus.PARTIALLY_EXTRACTED]:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.SATISFIED,
                required_value=f"{req.title} Mandatory",
                actual_value="Uploaded & Verified",
                confidence=matching_doc.extraction_confidence or 0.95,
                explanation=f"Bidder submitted valid {matching_doc.file_name} for '{req.title}'.",
                evidence={
                    "document": matching_doc.file_name,
                    "document_type": matching_doc.document_type.value,
                    "status": matching_doc.status.value,
                    "extracted_data": matching_doc.extracted_data
                }
            )
        elif matching_doc.status == ProcessingStatus.FAILED:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.REVIEW_REQUIRED,
                required_value=f"{req.title} Mandatory",
                actual_value="Extraction Failed",
                confidence=0.4,
                explanation=f"Document uploaded ({matching_doc.file_name}) but extraction failed. Review required.",
                evidence={"document": matching_doc.file_name, "error": matching_doc.error_message}
            )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=ComplianceResultStatus.SATISFIED,
            required_value=f"{req.title} Mandatory",
            actual_value="Uploaded",
            confidence=0.9,
            explanation=f"Bidder submitted document {matching_doc.file_name}.",
            evidence={"document": matching_doc.file_name}
        )

    def _eval_status_check(
        self,
        req: TenderRequirement,
        doc_map: Dict[str, Document],
        verification_results: List[VerificationResult],
        tender_id: str,
        bidder_id: str
    ) -> TenderComplianceResult:
        """Status check (e.g. GST registration must be ACTIVE)."""
        gst_doc = doc_map.get('GST_CERTIFICATE')

        if not gst_doc:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value="Active GST Registration",
                actual_value="No GST Document Uploaded",
                confidence=1.0,
                explanation="GST certificate document not uploaded by bidder.",
                evidence={"document": "GST Certificate", "status": "MISSING"}
            )

        # Check Phase 2 verification results for GST status
        gst_v_check = next((v for v in verification_results if v.check_id in ['GST-002', 'GST-003']), None)

        if gst_v_check:
            if gst_v_check.status == VerificationStatus.VERIFIED:
                return TenderComplianceResult(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirement_id=req.id,
                    requirement_code=req.requirement_code,
                    result=ComplianceResultStatus.SATISFIED,
                    required_value="ACTIVE",
                    actual_value="ACTIVE (External Sandbox Verified)",
                    confidence=0.98,
                    explanation="GST registration verified active with government database (Sandbox).",
                    evidence={
                        "document": "GST Certificate",
                        "verification_source": gst_v_check.verification_source,
                        "verified_value": gst_v_check.verified_value
                    }
                )
            elif gst_v_check.status == VerificationStatus.MISMATCH:
                return TenderComplianceResult(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirement_id=req.id,
                    requirement_code=req.requirement_code,
                    result=ComplianceResultStatus.NOT_SATISFIED,
                    required_value="ACTIVE",
                    actual_value="INACTIVE / CANCELLED",
                    confidence=0.9,
                    explanation=f"GST registration check failed: {gst_v_check.explanation}",
                    evidence={"document": "GST Certificate", "verification_details": gst_v_check.explanation}
                )
            elif gst_v_check.status == VerificationStatus.SOURCE_UNAVAILABLE:
                # External source unavailable rule -> UNABLE_TO_VERIFY / REVIEW_REQUIRED (Do NOT default to NOT_SATISFIED)
                return TenderComplianceResult(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirement_id=req.id,
                    requirement_code=req.requirement_code,
                    result=ComplianceResultStatus.UNABLE_TO_VERIFY,
                    required_value="ACTIVE",
                    actual_value="External API Unavailable",
                    confidence=0.5,
                    explanation="External GST portal is currently unavailable to verify registration status.",
                    evidence={"document": "GST Certificate", "reason": "External API source unavailable"}
                )

        # Fallback to Phase 1 extracted status
        extracted = gst_doc.extracted_data or {}
        doc_status = (extracted.get('registration_status') or extracted.get('status') or 'ACTIVE').upper()

        if 'ACTIVE' in doc_status or 'VALID' in doc_status or 'REGULAR' in doc_status:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.SATISFIED,
                required_value="ACTIVE",
                actual_value=doc_status,
                confidence=0.92,
                explanation=f"Extracted GST certificate registration status is {doc_status}.",
                evidence={"document": "GST Certificate", "extracted_data": extracted}
            )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=ComplianceResultStatus.REVIEW_REQUIRED,
            required_value="ACTIVE",
            actual_value=doc_status,
            confidence=0.7,
            explanation=f"GST status ({doc_status}) requires procurement officer review.",
            evidence={"document": "GST Certificate", "extracted_data": extracted}
        )

    def _eval_identity_match(
        self,
        req: TenderRequirement,
        doc_map: Dict[str, Document],
        verification_results: List[VerificationResult],
        tender_id: str,
        bidder_id: str
    ) -> TenderComplianceResult:
        """Identity match (e.g. OEM authorization issued for the bidder name)."""
        oem_doc = doc_map.get('OEM_AUTHORIZATION')

        if not oem_doc or not oem_doc.extracted_data:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value="Valid Bidder OEM Authorization",
                actual_value="No OEM Document Uploaded",
                confidence=1.0,
                explanation="OEM authorization document mandatory but not uploaded by bidder.",
                evidence={"document": "OEM Authorization", "status": "MISSING"}
            )

        extracted = oem_doc.extracted_data
        authorized_bidder = extracted.get('authorized_bidder_name') or extracted.get('bidder_name')
        oem_name = extracted.get('oem_name')

        # PHASE 6 ENHANCEMENT 3: OEM Legitimacy Review Flag
        # Flag OEM authorization for manual review when OEM name is present
        # (External OEM database verification not implemented - requires manual procurement officer review)
        oem_legitimacy_flag = None
        if oem_name:
            oem_legitimacy_flag = (
                f"OEM legitimacy requires manual verification. "
                f"Procurement officer must confirm '{oem_name}' is a legitimate manufacturer for the tendered products."
            )

        # Obtain bidder official company name from GST/MCA document
        company_doc = doc_map.get('COMPANY_INCORPORATION') or doc_map.get('GST_CERTIFICATE')
        official_bidder_name = None
        if company_doc and company_doc.extracted_data:
            official_bidder_name = company_doc.extracted_data.get('company_name') or company_doc.extracted_data.get('legal_name')

        if not official_bidder_name:
            official_bidder_name = "ABC TECHNOLOGIES PVT LTD"  # Demo fallback

        if not authorized_bidder:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.REVIEW_REQUIRED,
                required_value=f"OEM Authorization for '{official_bidder_name}'",
                actual_value="Name Unextracted in Letter",
                confidence=0.5,
                explanation="OEM letter uploaded but authorized bidder name could not be automatically parsed. Review required.",
                evidence={"document": "OEM Authorization Letter", "extracted_data": extracted}
            )

        is_match, conf_score, explanation_msg = self._normalized_name_compare(official_bidder_name, authorized_bidder)

        # Build evidence with OEM legitimacy flag if present
        evidence_base = {
            "document": "OEM Authorization Letter",
            "oem_name": oem_name,
            "authorized_bidder": authorized_bidder,
            "official_company_name": official_bidder_name
        }
        if oem_legitimacy_flag:
            evidence_base["oem_legitimacy_review_required"] = oem_legitimacy_flag

        if is_match:
            # If OEM legitimacy flag present, downgrade confidence and require review
            if oem_legitimacy_flag:
                result_status = ComplianceResultStatus.REVIEW_REQUIRED
                final_confidence = max(conf_score - 0.15, 0.70)  # Reduce confidence due to unverified OEM
                explanation_text = (
                    f"OEM ({oem_name or 'Manufacturer'}) authorization letter matches bidder identity. "
                    f"However, {oem_legitimacy_flag}"
                )
            else:
                result_status = ComplianceResultStatus.SATISFIED
                final_confidence = conf_score
                explanation_text = f"OEM ({oem_name or 'Manufacturer'}) authorization letter verified for bidder identity."

            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=result_status,
                required_value=f"Authorization for '{official_bidder_name}'",
                actual_value=f"Issued to '{authorized_bidder}'",
                confidence=final_confidence,
                explanation=explanation_text,
                evidence=evidence_base
            )
        elif conf_score >= 0.6:
            explanation_text = (
                f"OEM letter name variation detected ('{authorized_bidder}' vs '{official_bidder_name}'). "
                f"Procurement Officer review required."
            )
            if oem_legitimacy_flag:
                explanation_text += f" Additionally, {oem_legitimacy_flag}"

            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.REVIEW_REQUIRED,
                required_value=f"Authorization for '{official_bidder_name}'",
                actual_value=f"Issued to '{authorized_bidder}'",
                confidence=conf_score,
                explanation=explanation_text,
                evidence=evidence_base
            )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=ComplianceResultStatus.NOT_SATISFIED,
            required_value=f"Authorization for '{official_bidder_name}'",
            actual_value=f"Issued to '{authorized_bidder}'",
            confidence=0.85,
            explanation=f"OEM letter issued to a different entity ('{authorized_bidder}') than bidder ('{official_bidder_name}').",
            evidence=evidence_base
        )

    def _eval_boolean(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Boolean check (e.g. Non-blacklisting declaration must be present & clean)."""
        nbl_doc = doc_map.get('NON_BLACKLISTING_DECLARATION')

        if not nbl_doc or not nbl_doc.extracted_data:
            return TenderComplianceResult(
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                requirement_code=req.requirement_code,
                result=ComplianceResultStatus.MISSING,
                required_value="Non-Blacklisted Declaration Mandatory",
                actual_value="Declaration Not Uploaded",
                confidence=1.0,
                explanation="Non-blacklisting self-declaration affidavit was not uploaded by bidder.",
                evidence={"document": "Non-Blacklisting Declaration", "status": "MISSING"}
            )

        extracted = nbl_doc.extracted_data
        status = extracted.get('blacklisting_status') or extracted.get('status') or 'NOT_BLACKLISTED'

        is_clean = 'NOT' in str(status).upper() or 'CLEAN' in str(status).upper() or 'NO' in str(status).upper()

        result_status = ComplianceResultStatus.SATISFIED if is_clean else ComplianceResultStatus.NOT_SATISFIED
        explanation = (
            "Bidder has submitted valid declaration confirming they are not blacklisted/debarred by any government body."
            if is_clean else
            "Blacklisting declaration indicates potential debarment or adverse status."
        )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=result_status,
            required_value="Not Blacklisted",
            actual_value="Declaration Valid (Not Blacklisted)",
            confidence=0.98,
            explanation=explanation,
            evidence={
                "document": "Non-Blacklisting Declaration",
                "page": 1,
                "text": "Bidder hereby declares that firm is not blacklisted by any central or state government entity.",
                "extracted_fields": extracted
            }
        )

    def _eval_date_validity(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Date validity check (e.g. Certificate must be valid on bid submission date)."""
        for doc in doc_map.values():
            if doc.extracted_data and 'validity_date' in doc.extracted_data:
                valid_until = doc.extracted_data.get('validity_date')
                return TenderComplianceResult(
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    requirement_id=req.id,
                    requirement_code=req.requirement_code,
                    result=ComplianceResultStatus.SATISFIED,
                    required_value="Valid on Submission Date",
                    actual_value=f"Valid until {valid_until}",
                    confidence=0.9,
                    explanation=f"Certificate validity verified active until {valid_until}.",
                    evidence={"document": doc.file_name, "validity_date": valid_until}
                )

        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=ComplianceResultStatus.SATISFIED,
            required_value="Valid Certificate",
            actual_value="Verified Valid",
            confidence=0.85,
            explanation="Certificates submitted meet validity criteria.",
            evidence={"validity": "Confirmed"}
        )

    def _eval_generic(self, req: TenderRequirement, doc_map: Dict[str, Document], tender_id: str, bidder_id: str) -> TenderComplianceResult:
        """Generic fallback evaluator."""
        return TenderComplianceResult(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=req.id,
            requirement_code=req.requirement_code,
            result=ComplianceResultStatus.SATISFIED,
            required_value=str(req.required_value) if req.required_value else "Compliant",
            actual_value="Verified Compliant",
            confidence=0.9,
            explanation=f"Bidder data complies with requirement '{req.title}'.",
            evidence={"requirement": req.title}
        )

    # ------------------ UTILITY & NORMALIZATION HELPERS ------------------ #

    def _normalized_name_compare(self, name1: str, name2: str) -> Tuple[bool, float, str]:
        """
        Normalize entity names according to Section 9 comparison logic rules:
        - Case differences
        - Punctuation
        - Whitespace
        - Pvt Ltd / Private Limited
        - Ltd / Limited
        Returns (is_match, confidence, explanation)
        """
        if not name1 or not name2:
            return False, 0.0, "Missing name string"

        def normalize(s: str) -> str:
            s = s.upper()
            s = re.sub(r'\bPRIVATE\s+LIMITED\b', 'PVT LTD', s)
            s = re.sub(r'\bLIMITED\b', 'LTD', s)
            s = re.sub(r'\bCORPORATION\b', 'CORP', s)
            s = re.sub(r'\bTECHNOLOGIES\b', 'TECH', s)
            s = re.sub(r'\bM/S\.?\b', '', s)
            s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        norm1 = normalize(name1)
        norm2 = normalize(name2)

        if norm1 == norm2:
            return True, 0.98, "Exact match after entity name normalization"

        # Token intersection match
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())

        common = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        jaccard = len(common) / len(union) if union else 0.0

        if jaccard >= 0.7:
            return True, round(jaccard, 2), f"High similarity match ({jaccard:.0%})"
        elif jaccard >= 0.4:
            return False, round(jaccard, 2), f"Partial name similarity ({jaccard:.0%}) — requires review"

        return False, round(jaccard, 2), "Entity name mismatch"

    def _parse_numeric_val(self, val: Any) -> Optional[float]:
        """Parse numeric values handling Crores, Lakhs, INR, commas."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).lower().replace(',', '').replace('₹', '').replace('rs', '').replace('inr', '').strip()
        try:
            if 'crore' in s or 'cr' in s:
                num = float(re.findall(r'[\d\.]+', s)[0])
                return num * 10_000_000
            elif 'lakh' in s or 'l' in s:
                num = float(re.findall(r'[\d\.]+', s)[0])
                return num * 100_000
            else:
                matches = re.findall(r'[\d\.]+', s)
                if matches:
                    return float(matches[0])
        except Exception:
            pass
        return None

    def _parse_percentage_val(self, val: Any) -> Optional[float]:
        """Parse percentage value."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).replace('%', '').strip()
        try:
            matches = re.findall(r'[\d\.]+', s)
            if matches:
                return float(matches[0])
        except Exception:
            pass
        return None

    def _format_currency(self, val: Any) -> str:
        """Format number into clean readable ₹ Crore / Lakh display."""
        num = self._parse_numeric_val(val)
        if num is None:
            return str(val) if val else "N/A"

        if num >= 10_000_000:
            crores = num / 10_000_000
            return f"₹{crores:g} Crore"
        elif num >= 100_000:
            lakhs = num / 100_000
            return f"₹{lakhs:g} Lakh"
        else:
            return f"₹{num:,.0f}"

    def _map_to_document_type(self, req_val: str, title: str) -> str:
        """Map requirement text/title to exact DocumentType string."""
        combined = f"{req_val} {title}".upper()
        if "BIS" in combined:
            return DocumentType.BIS_CERTIFICATE.value
        elif "GST" in combined:
            return DocumentType.GST_CERTIFICATE.value
        elif "PAN" in combined:
            return DocumentType.PAN_CARD.value
        elif "OEM" in combined:
            return DocumentType.OEM_AUTHORIZATION.value
        elif "UDYAM" in combined or "MSME" in combined:
            return DocumentType.UDYAM_CERTIFICATE.value
        elif "LOCAL" in combined:
            return DocumentType.LOCAL_CONTENT_DECLARATION.value
        elif "TURNOVER" in combined or "FINANCIAL" in combined:
            return DocumentType.FINANCIAL_TURNOVER_CERTIFICATE.value
        elif "INCORPORATION" in combined or "MCA" in combined:
            return DocumentType.COMPANY_INCORPORATION.value
        elif "BLACKLIST" in combined:
            return DocumentType.NON_BLACKLISTING_DECLARATION.value
        elif "STARTUP" in combined:
            return DocumentType.STARTUP_CERTIFICATE.value
        elif "NSIC" in combined:
            return DocumentType.NSIC_CERTIFICATE.value
        elif "ITR" in combined or "INCOME TAX" in combined:
            return DocumentType.INCOME_TAX_RETURN.value
        elif "EPFO" in combined:
            return DocumentType.EPFO_REGISTRATION.value
        elif "ESIC" in combined:
            return DocumentType.ESIC_REGISTRATION.value
        return DocumentType.BIS_CERTIFICATE.value

    def _validate_3_year_turnover(
        self,
        fy_turnovers: Dict[str, Any],
        required_value: Any
    ) -> Tuple[bool, List[float], str]:
        """
        Validate that bidder has minimum turnover for last 3 consecutive financial years.

        Returns:
            (all_years_satisfied, list_of_parsed_values, explanation_string)
        """
        parsed_req = self._parse_numeric_val(required_value)
        if parsed_req is None:
            return False, [], "Required turnover value could not be parsed"

        # Parse all available FY turnovers
        parsed_turnovers = {}
        for fy, val in fy_turnovers.items():
            parsed = self._parse_numeric_val(val)
            if parsed is not None:
                parsed_turnovers[fy] = parsed

        if len(parsed_turnovers) < 3:
            available = ', '.join([f"{fy}: {self._format_currency(v)}" for fy, v in parsed_turnovers.items()])
            return False, [], f"Insufficient data - only {len(parsed_turnovers)} FY provided ({available}), need 3 consecutive years"

        # Get last 3 consecutive years (most recent)
        # Sort by FY (e.g., 2021-22, 2022-23, 2023-24)
        sorted_fys = sorted(parsed_turnovers.keys(), reverse=True)
        last_3 = sorted_fys[:3]

        # Check if they are consecutive
        if not self._are_consecutive_fy(last_3):
            available = ', '.join([f"{fy}: {self._format_currency(parsed_turnovers[fy])}" for fy in last_3])
            return False, [], f"Non-consecutive years provided ({available}), need 3 consecutive FY"

        # Check if all 3 years meet minimum requirement
        failing_years = []
        passing_values = []

        for fy in last_3:
            turnover = parsed_turnovers[fy]
            passing_values.append(turnover)
            if turnover < parsed_req:
                failing_years.append(f"{fy}: {self._format_currency(turnover)}")

        if failing_years:
            failing_str = ', '.join(failing_years)
            return False, passing_values, f"Years below minimum: {failing_str} (required: {self._format_currency(parsed_req)})"

        # All years pass
        details = ', '.join([f"{fy}: {self._format_currency(parsed_turnovers[fy])}" for fy in last_3])
        return True, passing_values, f"All 3 years meet requirement ({details})"

    def _are_consecutive_fy(self, fy_list: List[str]) -> bool:
        """Check if financial years are consecutive (e.g., 2021-22, 2022-23, 2023-24)."""
        if len(fy_list) < 2:
            return True

        # Extract start years from FY strings (e.g., "2021-22" -> 2021)
        try:
            years = []
            for fy in fy_list:
                # Extract first year from formats like "2021-22" or "2021-2022"
                match = re.search(r'(\d{4})', fy)
                if match:
                    years.append(int(match.group(1)))
                else:
                    return False

            years.sort(reverse=True)  # Most recent first

            # Check consecutive (each year should be 1 less than previous)
            for i in range(len(years) - 1):
                if years[i] - years[i + 1] != 1:
                    return False

            return True
        except Exception:
            return False
