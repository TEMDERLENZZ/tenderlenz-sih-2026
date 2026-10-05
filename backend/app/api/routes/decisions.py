"""
Officer Decision API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from app.database import get_db
from app.models.decision import OfficerDecision, DecisionStatus, AuditLog, AuditEvent
from app.models.tender import Tender, TenderComplianceResult
from app.models.user import User
from app.services.auth.dependencies import get_current_user, get_current_officer

router = APIRouter()


class OfficerDecisionCreate(BaseModel):
    """
    Request schema for creating officer decision.

    PHASE 7 CHANGE: officer_id is now IGNORED (kept for backward compatibility).
    The authenticated officer's identity from JWT token is used as source of truth.
    """
    decision: DecisionStatus
    officer_id: Optional[str] = None  # IGNORED - kept for backward compatibility
    officer_name: Optional[str] = None  # IGNORED - kept for backward compatibility
    remarks: Optional[str] = None


class OfficerDecisionResponse(BaseModel):
    """Response schema for officer decision"""
    id: int
    tender_id: str
    bidder_id: str
    decision: str
    officer_id: str
    officer_name: Optional[str]
    remarks: Optional[str]
    decided_at: str

    class Config:
        from_attributes = True


@router.post("/{tender_id}/bidders/{bidder_id}/decision", response_model=OfficerDecisionResponse)
async def record_officer_decision(
    tender_id: str,
    bidder_id: str,
    decision_data: OfficerDecisionCreate,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)  # PHASE 7: Require authenticated OFFICER
):
    """
    Record procurement officer's final decision.

    PHASE 7 SECURITY:
    - Requires valid JWT token with OFFICER role
    - officer_id comes from authenticated token (NOT from request body)
    - Prevents officer impersonation attacks

    Flow:
    1. Validate tender exists
    2. Validate compliance evaluation exists
    3. Check for duplicate decision
    4. Save decision to database (use authenticated officer identity)
    5. Create DECISION_MADE audit event (use authenticated officer identity)
    6. Return decision with timestamp
    """
    # 1. Validate tender exists
    tender = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not tender:
        raise HTTPException(
            status_code=404,
            detail=f"Tender '{tender_id}' not found. Cannot record decision for non-existent tender."
        )

    # 2. Validate compliance evaluation exists
    compliance_results = db.query(TenderComplianceResult).filter(
        TenderComplianceResult.tender_id == tender_id,
        TenderComplianceResult.bidder_id == bidder_id
    ).first()

    if not compliance_results:
        raise HTTPException(
            status_code=400,
            detail=f"No compliance evaluation found for tender '{tender_id}' and bidder '{bidder_id}'. Run compliance evaluation before recording decision."
        )

    # 3. Check for duplicate decision (prevent conflicting decisions)
    existing_decision = db.query(OfficerDecision).filter(
        OfficerDecision.tender_id == tender_id,
        OfficerDecision.bidder_id == bidder_id
    ).first()

    if existing_decision:
        raise HTTPException(
            status_code=409,
            detail=f"Decision already exists for tender '{tender_id}' and bidder '{bidder_id}'. "
                   f"Existing decision: {existing_decision.decision.value} by {existing_decision.officer_name or existing_decision.officer_id}. "
                   f"Decision history/updates not supported in current architecture."
        )

    # 4. Save decision to database
    # PHASE 7: Use authenticated officer identity (NOT from request body)
    officer_decision = OfficerDecision(
        tender_id=tender_id,
        bidder_id=bidder_id,
        decision=decision_data.decision,
        officer_id=str(current_officer.id),  # From authenticated token
        officer_name=current_officer.username,  # From authenticated token
        remarks=decision_data.remarks
    )

    db.add(officer_decision)
    db.commit()
    db.refresh(officer_decision)

    # 5. Create DECISION_MADE audit event
    # PHASE 7: Use authenticated officer identity (NOT from request body)
    audit_metadata = {
        "decision": decision_data.decision.value,
        "has_remarks": decision_data.remarks is not None and len(decision_data.remarks) > 0
    }

    audit_log = AuditLog(
        event_type=AuditEvent.DECISION_MADE,
        tender_id=tender_id,
        bidder_id=bidder_id,
        user_id=str(current_officer.id),  # From authenticated token
        user_name=current_officer.username,  # From authenticated token
        action_description=f"Procurement officer recorded decision: {decision_data.decision.value}",
        event_metadata=json.dumps(audit_metadata)
    )

    db.add(audit_log)
    db.commit()

    # 6. Return decision
    return OfficerDecisionResponse(
        id=officer_decision.id,
        tender_id=officer_decision.tender_id,
        bidder_id=officer_decision.bidder_id,
        decision=officer_decision.decision.value,
        officer_id=officer_decision.officer_id,
        officer_name=officer_decision.officer_name,
        remarks=officer_decision.remarks,
        decided_at=officer_decision.decided_at.isoformat() if officer_decision.decided_at else None
    )


@router.get("/{tender_id}/bidders/{bidder_id}/decision", response_model=OfficerDecisionResponse)
async def get_officer_decision(
    tender_id: str,
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve existing officer decision for tender-bidder pair.
    Returns 404 if no decision recorded yet.
    """
    decision = db.query(OfficerDecision).filter(
        OfficerDecision.tender_id == tender_id,
        OfficerDecision.bidder_id == bidder_id
    ).first()

    if not decision:
        raise HTTPException(
            status_code=404,
            detail=f"No decision found for tender '{tender_id}' and bidder '{bidder_id}'."
        )

    return OfficerDecisionResponse(
        id=decision.id,
        tender_id=decision.tender_id,
        bidder_id=decision.bidder_id,
        decision=decision.decision.value,
        officer_id=decision.officer_id,
        officer_name=decision.officer_name,
        remarks=decision.remarks,
        decided_at=decision.decided_at.isoformat() if decision.decided_at else None
    )


@router.get("/audit-logs", response_model=list)
async def get_audit_logs(
    tender_id: Optional[str] = None,
    bidder_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Retrieve audit logs with optional filters.
    Returns most recent events first.
    """
    query = db.query(AuditLog)

    if tender_id:
        query = query.filter(AuditLog.tender_id == tender_id)
    if bidder_id:
        query = query.filter(AuditLog.bidder_id == bidder_id)
    if event_type:
        try:
            query = query.filter(AuditLog.event_type == AuditEvent[event_type])
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "event_type": log.event_type.value,
            "tender_id": log.tender_id,
            "bidder_id": log.bidder_id,
            "user_id": log.user_id,
            "user_name": log.user_name,
            "action_description": log.action_description,
            "metadata": log.event_metadata,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in logs
    ]
