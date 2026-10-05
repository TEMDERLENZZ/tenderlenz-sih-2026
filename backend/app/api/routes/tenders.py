"""
Phase 6 Tender Requirement Engine API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path
from datetime import datetime

from app.database import get_db
from app.models.tender import Tender, TenderRequirement, TenderComplianceResult, RequirementType, ComplianceResultStatus, BidderRiskAssessment, RiskLevel
from app.models.decision import AuditLog, AuditEvent
from app.schemas.tender_schemas import (
    TenderUploadResponse,
    TenderRequirementCreate,
    TenderRequirementUpdate,
    TenderRequirementResponse,
    TenderExtractionResponse,
    TenderComplianceResultDetail,
    TenderComplianceSummary
)
from app.services.document_processor import DocumentProcessor
from app.services.tender.requirement_extractor import RequirementExtractor
from app.services.tender.compliance_evaluator import ComplianceEvaluator
from app.services.auth.dependencies import get_current_user, get_current_officer
from app.models.user import User
import json

router = APIRouter()

UPLOAD_DIR = Path("uploads/tenders")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=TenderUploadResponse)
async def upload_tender(
    title: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    1. TENDER DOCUMENT UPLOAD
    Accepts PDF/image tender documents, extracts digital text via OCR/PDF parsing,
    stores document metadata and extracted text, and generates a unique tender_id.
    """
    tender_id = f"TENDER-{uuid.uuid4().hex[:8].upper()}"
    file_name = None
    file_path = None
    file_size = 0
    mime_type = None
    extracted_text = ""

    if file:
        file_bytes = await file.read()
        file_size = len(file_bytes)
        file_name = file.filename
        mime_type = file.content_type

        # Save to disk
        dest_path = UPLOAD_DIR / f"{tender_id}_{file.filename}"
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        file_path = str(dest_path)

        # Extract text using DocumentProcessor
        processor = DocumentProcessor()
        extracted_text = processor.extract_text(file_path, mime_type or "application/pdf")

    tender_title = title or (file_name.replace(".pdf", "").replace("_", " ") if file_name else f"Tender Specification {tender_id}")

    tender = Tender(
        tender_id=tender_id,
        title=tender_title,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        extracted_text=extracted_text,
        status="EXTRACTED" if extracted_text else "UPLOADED"
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    # Create TENDER_UPLOADED audit event
    audit_log = AuditLog(
        event_type=AuditEvent.TENDER_UPLOADED,
        tender_id=tender.tender_id,
        action_description=f"Tender document uploaded: {tender.title}",
        event_metadata=json.dumps({
            "tender_id": tender.tender_id,
            "file_name": tender.file_name,
            "file_size": tender.file_size,
            "status": tender.status
        })
    )
    db.add(audit_log)
    db.commit()

    return tender


@router.post("/seed-demo", response_model=TenderUploadResponse)
async def seed_demo_tender(
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Seed/Create the canonical demo tender specified in Section 16 of prompt.
    Tender ID: DEMO_TENDER_001
    """
    existing = db.query(Tender).filter(Tender.tender_id == "DEMO_TENDER_001").first()
    if existing:
        # Re-extract standard requirements
        extractor = RequirementExtractor()
        std_reqs = extractor.get_standard_demo_requirements()

        db.query(TenderRequirement).filter(TenderRequirement.tender_id == "DEMO_TENDER_001").delete()

        for req_data in std_reqs:
            req = TenderRequirement(tender_id="DEMO_TENDER_001", **req_data)
            db.add(req)
        db.commit()
        return existing

    demo_text = """
    TENDER SPECIFICATION DEMO_TENDER_001
    Procurement of Information Technology Equipment & Solutions
    
    ELIGIBILITY CRITERIA:
    1. Minimum Turnover: Bidder must have minimum annual turnover of ₹5 Crore for last 3 financial years.
    2. GST Registration: GST registration certificate mandatory; registration status must be Active.
    3. BIS Certification: BIS certificate must be submitted along with technical bid.
    4. OEM Authorization: OEM authorization letter must be issued specifically for the bidder.
    5. Local Content Percentage: Minimum local content requirement of 50% under Class-I Local Supplier category.
    6. Non-Blacklisting Condition: Affidavit/Declaration stating bidder is not blacklisted by any central or state government entity.
    """

    tender = Tender(
        tender_id="DEMO_TENDER_001",
        title="Demo Procurement Tender (IT Equipment & Services)",
        description="Demo tender for Phase 6 Requirement Matching Engine testing",
        extracted_text=demo_text,
        status="EXTRACTED"
    )
    db.add(tender)
    db.commit()

    # Create standard demo requirements
    extractor = RequirementExtractor()
    std_reqs = extractor.get_standard_demo_requirements()

    for req_data in std_reqs:
        req = TenderRequirement(tender_id="DEMO_TENDER_001", **req_data)
        db.add(req)

    db.commit()
    db.refresh(tender)
    return tender


@router.get("/list", response_model=List[TenderUploadResponse])
async def list_tenders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all uploaded tenders."""
    return db.query(Tender).order_by(Tender.uploaded_at.desc()).all()


@router.post("/{tender_id}/extract-requirements", response_model=TenderExtractionResponse)
async def extract_requirements(
    tender_id: str,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    2. & 5. TENDER REQUIREMENT EXTRACTION API
    Extracts structured tender requirements from stored tender text.
    """
    tender = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found")

    extractor = RequirementExtractor()
    req_list = extractor.extract_requirements(tender.extracted_text or "", tender_id)

    # Replace old requirements for this tender
    db.query(TenderRequirement).filter(TenderRequirement.tender_id == tender_id).delete()

    created_reqs = []
    for r in req_list:
        db_req = TenderRequirement(tender_id=tender_id, **r)
        db.add(db_req)
        created_reqs.append(db_req)

    db.commit()
    for r in created_reqs:
        db.refresh(r)

    # Create REQUIREMENTS_EXTRACTED audit event
    audit_log = AuditLog(
        event_type=AuditEvent.REQUIREMENTS_EXTRACTED,
        tender_id=tender_id,
        action_description=f"Extracted {len(created_reqs)} requirements from tender document",
        event_metadata=json.dumps({
            "total_requirements": len(created_reqs),
            "requirement_codes": [r.requirement_code for r in created_reqs[:10]]  # First 10
        })
    )
    db.add(audit_log)
    db.commit()

    return TenderExtractionResponse(
        tender_id=tender_id,
        total_requirements=len(created_reqs),
        requirements=[TenderRequirementResponse.model_validate(r) for r in created_reqs]
    )


@router.get("/{tender_id}/requirements", response_model=List[TenderRequirementResponse])
async def get_tender_requirements(
    tender_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """5. GET TENDER REQUIREMENTS"""
    reqs = db.query(TenderRequirement).filter(
        TenderRequirement.tender_id == tender_id
    ).order_by(TenderRequirement.requirement_code.asc()).all()
    return reqs


@router.post("/{tender_id}/requirements", response_model=TenderRequirementResponse)
async def add_custom_requirement(
    tender_id: str,
    req_data: TenderRequirementCreate,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """Add a custom requirement to a tender."""
    tender = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found")

    db_req = TenderRequirement(
        tender_id=tender_id,
        **req_data.dict()
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req


@router.put("/requirements/{requirement_id}", response_model=TenderRequirementResponse)
async def update_requirement(
    requirement_id: int,
    update_data: TenderRequirementUpdate,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    13. REQUIREMENT REVIEW & EDITING API
    Allows Procurement Officer to review and modify requirement details before running evaluation.
    """
    req = db.query(TenderRequirement).filter(TenderRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(req, key, value)

    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    # Create REQUIREMENT_EDITED audit event
    audit_log = AuditLog(
        event_type=AuditEvent.REQUIREMENT_EDITED,
        tender_id=req.tender_id,
        user_id="OFFICER",  # Would be real user in production
        action_description=f"Requirement edited: {req.requirement_code} - {req.title}",
        event_metadata=json.dumps({
            "requirement_id": req.id,
            "requirement_code": req.requirement_code,
            "changes": list(update_data.model_dump(exclude_unset=True).keys())
        })
    )
    db.add(audit_log)
    db.commit()

    return req


@router.delete("/requirements/{requirement_id}")
async def delete_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """Delete a requirement."""
    req = db.query(TenderRequirement).filter(TenderRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(req)
    db.commit()
    return {"message": f"Requirement {requirement_id} deleted"}


@router.post("/{tender_id}/bidders/{bidder_id}/evaluate", response_model=TenderComplianceSummary)
async def evaluate_bidder_compliance(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    6. & 7. BIDDER REQUIREMENT MATCHING & EVALUATION
    Runs evaluation using Phase 1 extracted bidder document data and Phase 2 verification results.
    """
    tender = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not tender:
        if tender_id == "DEMO_TENDER_001":
            await seed_demo_tender(db)
            tender = db.query(Tender).filter(Tender.tender_id == tender_id).first()
        else:
            raise HTTPException(status_code=404, detail=f"Tender '{tender_id}' not found")

    evaluator = ComplianceEvaluator(db)
    results = evaluator.evaluate_bidder(tender_id, bidder_id)

    # Compute summary breakdown
    satisfied = sum(1 for r in results if r.result == ComplianceResultStatus.SATISFIED)
    not_satisfied = sum(1 for r in results if r.result == ComplianceResultStatus.NOT_SATISFIED)
    missing = sum(1 for r in results if r.result == ComplianceResultStatus.MISSING)
    review_req = sum(1 for r in results if r.result == ComplianceResultStatus.REVIEW_REQUIRED)
    unable_verify = sum(1 for r in results if r.result == ComplianceResultStatus.UNABLE_TO_VERIFY)
    not_applicable = sum(1 for r in results if r.result == ComplianceResultStatus.NOT_APPLICABLE)

    total = len(results)
    pct = round((satisfied / total) * 100.0, 1) if total > 0 else 0.0

    # Create COMPLIANCE_EVALUATED audit event (evaluate endpoint)
    audit_log = AuditLog(
        event_type=AuditEvent.COMPLIANCE_EVALUATED,
        tender_id=tender_id,
        bidder_id=bidder_id,
        action_description=f"Compliance evaluation completed: {satisfied}/{total} satisfied ({pct}%)",
        event_metadata=json.dumps({"total": total, "satisfied": satisfied, "percentage": pct})
    )
    db.add(audit_log)
    db.commit()

    return TenderComplianceSummary(
        tender_id=tender_id,
        bidder_id=bidder_id,
        total_requirements=total,
        satisfied=satisfied,
        not_satisfied=not_satisfied,
        missing=missing,
        review_required=review_req,
        unable_to_verify=unable_verify,
        not_applicable=not_applicable,
        compliance_percentage=pct,
        disclaimer="Final procurement decision remains with the authorized Procurement Officer.",
        results=[TenderComplianceResultDetail.model_validate(r) for r in results]
    )


@router.get("/{tender_id}/bidders/{bidder_id}/compliance", response_model=TenderComplianceSummary)
async def get_bidder_compliance(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    11. COMPLIANCE SUMMARY API
    Returns requirement-by-requirement compliance results and summary metrics.
    """
    results = db.query(TenderComplianceResult).filter(
        TenderComplianceResult.tender_id == tender_id,
        TenderComplianceResult.bidder_id == bidder_id
    ).all()

    if not results:
        # Run evaluation dynamically if not run yet
        evaluator = ComplianceEvaluator(db)
        results = evaluator.evaluate_bidder(tender_id, bidder_id)

    satisfied = sum(1 for r in results if r.result == ComplianceResultStatus.SATISFIED)
    not_satisfied = sum(1 for r in results if r.result == ComplianceResultStatus.NOT_SATISFIED)
    missing = sum(1 for r in results if r.result == ComplianceResultStatus.MISSING)
    review_req = sum(1 for r in results if r.result == ComplianceResultStatus.REVIEW_REQUIRED)
    unable_verify = sum(1 for r in results if r.result == ComplianceResultStatus.UNABLE_TO_VERIFY)
    not_applicable = sum(1 for r in results if r.result == ComplianceResultStatus.NOT_APPLICABLE)

    total = len(results)
    pct = round((satisfied / total) * 100.0, 1) if total > 0 else 0.0

    # Create COMPLIANCE_EVALUATED audit event (evaluate endpoint)
    audit_log = AuditLog(
        event_type=AuditEvent.COMPLIANCE_EVALUATED,
        tender_id=tender_id,
        bidder_id=bidder_id,
        action_description=f"Compliance evaluation completed: {satisfied}/{total} satisfied ({pct}%)",
        event_metadata=json.dumps({"total": total, "satisfied": satisfied, "percentage": pct})
    )
    db.add(audit_log)
    db.commit()

    return TenderComplianceSummary(
        tender_id=tender_id,
        bidder_id=bidder_id,
        total_requirements=total,
        satisfied=satisfied,
        not_satisfied=not_satisfied,
        missing=missing,
        review_required=review_req,
        unable_to_verify=unable_verify,
        not_applicable=not_applicable,
        compliance_percentage=pct,
        disclaimer="Final procurement decision remains with the authorized Procurement Officer.",
        results=[TenderComplianceResultDetail.model_validate(r) for r in results]
    )


# ============================================================================
# PHASE 2: RISK ASSESSMENT API ENDPOINTS
# ============================================================================

@router.post("/{tender_id}/bidders/{bidder_id}/assess-risk")
async def assess_bidder_risk(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Calculate and return risk assessment for bidder.

    Risk calculation is deterministic and based on:
    - Compliance results (eligibility failures, review items, missing docs)
    - Verification results (mismatches, identity issues)

    Returns:
        BidderRiskAssessment with risk_level, risk_score, factors, and summary
    """
    from app.services.tender.risk_evaluator import RiskEvaluator
    from app.models.verification import VerificationResult

    # Get compliance results
    compliance_results = db.query(TenderComplianceResult).filter(
        TenderComplianceResult.tender_id == tender_id,
        TenderComplianceResult.bidder_id == bidder_id
    ).all()

    if not compliance_results:
        raise HTTPException(
            status_code=404,
            detail=f"No compliance evaluation found for tender {tender_id} and bidder {bidder_id}. Run compliance evaluation first."
        )

    # Get verification results
    verification_results = db.query(VerificationResult).filter(
        VerificationResult.bidder_id == bidder_id
    ).all()

    # Calculate risk
    evaluator = RiskEvaluator(db)
    risk_assessment = evaluator.calculate_risk(
        tender_id=tender_id,
        bidder_id=bidder_id,
        compliance_results=compliance_results,
        verification_results=verification_results
    )

    # Delete old risk assessment for this tender+bidder
    db.query(BidderRiskAssessment).filter(
        BidderRiskAssessment.tender_id == tender_id,
        BidderRiskAssessment.bidder_id == bidder_id
    ).delete()

    # Save new risk assessment
    db.add(risk_assessment)
    db.commit()
    db.refresh(risk_assessment)

    # Create RISK_ASSESSED audit event
    audit_log = AuditLog(
        event_type=AuditEvent.RISK_ASSESSED,
        tender_id=tender_id,
        bidder_id=bidder_id,
        action_description=f"Risk assessment completed: {risk_assessment.risk_level.value} ({risk_assessment.risk_score}/100)",
        event_metadata=json.dumps({
            "risk_level": risk_assessment.risk_level.value,
            "risk_score": risk_assessment.risk_score,
            "factor_count": len(risk_assessment.factors)
        })
    )
    db.add(audit_log)
    db.commit()

    return {
        "id": risk_assessment.id,
        "tender_id": risk_assessment.tender_id,
        "bidder_id": risk_assessment.bidder_id,
        "risk_level": risk_assessment.risk_level.value,
        "risk_score": risk_assessment.risk_score,
        "factors": risk_assessment.factors,
        "summary": risk_assessment.summary,
        "calculated_at": risk_assessment.calculated_at.isoformat() if risk_assessment.calculated_at else None
    }


@router.get("/{tender_id}/bidders/{bidder_id}/risk")
async def get_bidder_risk(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk assessment for bidder.

    If no risk assessment exists, automatically calculates it.

    Returns:
        BidderRiskAssessment with risk_level, risk_score, factors, and summary
    """
    # Try to get existing risk assessment
    risk = db.query(BidderRiskAssessment).filter(
        BidderRiskAssessment.tender_id == tender_id,
        BidderRiskAssessment.bidder_id == bidder_id
    ).order_by(BidderRiskAssessment.calculated_at.desc()).first()

    if not risk:
        # Auto-calculate if not exists
        return await assess_bidder_risk(tender_id, bidder_id, db)

    return {
        "id": risk.id,
        "tender_id": risk.tender_id,
        "bidder_id": risk.bidder_id,
        "risk_level": risk.risk_level.value,
        "risk_score": risk.risk_score,
        "factors": risk.factors,
        "summary": risk.summary,
        "calculated_at": risk.calculated_at.isoformat() if risk.calculated_at else None
    }
