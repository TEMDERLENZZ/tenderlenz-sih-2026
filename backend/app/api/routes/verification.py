"""
Phase 2 Verification API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.verification import (
    VerificationSession,
    VerificationResult,
    VerificationSessionType,
    VerificationSourceMode
)
from app.models.decision import AuditLog, AuditEvent
from app.schemas.verification_schemas import (
    VerificationSessionCreate,
    VerificationSessionSummary,
    VerificationResultDetail,
    VerificationRunResponse,
    VerificationResultsResponse,
    ProvidersStatusResponse,
    ProviderStatus
)
from app.services.verification.verification_engine import VerificationEngine
from app.services.verification.verification_providers import (
    GSTProvider,
    PANProvider,
    UdyamProvider,
    MCAProvider
)
from app.services.auth.dependencies import get_current_user, get_current_officer
from app.models.user import User
import json

router = APIRouter()

@router.post("/run/{bidder_id}", response_model=VerificationRunResponse)
async def run_verification(
    bidder_id: str,
    session_type: VerificationSessionType = VerificationSessionType.FULL_VERIFICATION,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Run complete verification for a bidder.

    Performs:
    1. Document-to-document cross-checks
    2. External source verification (SANDBOX mode)
    3. Verification rule application

    Returns verification session with summary.
    """
    try:
        engine = VerificationEngine(db)
        session = engine.run_verification(bidder_id, session_type)

        # Create VERIFICATION_COMPLETED audit event
        audit_log = AuditLog(
            event_type=AuditEvent.VERIFICATION_COMPLETED,
            bidder_id=bidder_id,
            action_description=f"Verification completed: {session.checks_passed}/{session.total_checks} checks passed",
            event_metadata=json.dumps({
                "session_id": session.id,
                "total_checks": session.total_checks,
                "checks_passed": session.checks_passed,
                "checks_failed": session.checks_failed,
                "checks_review_required": session.checks_review_required
            })
        )
        db.add(audit_log)
        db.commit()

        return VerificationRunResponse(
            session_id=session.id,
            bidder_id=session.bidder_id,
            status=session.status,
            message=f"Verification completed with {session.total_checks} checks performed",
            summary=VerificationSessionSummary.from_orm(session)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/session/{session_id}", response_model=VerificationSessionSummary)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get verification session status and summary.
    """
    session = db.query(VerificationSession).filter(
        VerificationSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    return VerificationSessionSummary.from_orm(session)


@router.get("/session/{session_id}/results", response_model=VerificationResultsResponse)
async def get_session_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed verification results for a session.
    """
    session = db.query(VerificationSession).filter(
        VerificationSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    results = db.query(VerificationResult).filter(
        VerificationResult.session_id == session_id
    ).all()

    # Group results by category
    grouped: Dict[str, List[VerificationResultDetail]] = {}
    for result in results:
        category = result.category.value
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(VerificationResultDetail.from_orm(result))

    return VerificationResultsResponse(
        session=VerificationSessionSummary.from_orm(session),
        results=[VerificationResultDetail.from_orm(r) for r in results],
        grouped_by_category=grouped
    )


@router.get("/bidder/{bidder_id}/latest", response_model=VerificationSessionSummary)
async def get_latest_session(
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest verification session for a bidder.
    """
    session = db.query(VerificationSession).filter(
        VerificationSession.bidder_id == bidder_id
    ).order_by(VerificationSession.started_at.desc()).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"No verification session found for bidder {bidder_id}"
        )

    return VerificationSessionSummary.from_orm(session)


@router.get("/providers/status", response_model=ProvidersStatusResponse)
async def get_providers_status(current_user: User = Depends(get_current_user)):
    """
    Get status of all verification providers.

    Shows whether providers are in LIVE or SANDBOX mode.
    """
    providers = [
        GSTProvider(),
        PANProvider(),
        UdyamProvider(),
        MCAProvider()
    ]

    provider_statuses = [
        ProviderStatus(**provider.get_status())
        for provider in providers
    ]

    # Check if any provider is in SANDBOX mode
    sandbox_active = any(
        p.mode == VerificationSourceMode.SANDBOX
        for p in providers
    )

    warning = ""
    if sandbox_active:
        warning = (
            "⚠️ SANDBOX MODE ACTIVE: External verification is using demonstration data, "
            "NOT live government sources. Results are for prototype testing only."
        )

    return ProvidersStatusResponse(
        providers=provider_statuses,
        sandbox_mode_active=sandbox_active,
        warning=warning
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Delete a verification session and all its results.
    """
    session = db.query(VerificationSession).filter(
        VerificationSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    # Delete all results
    db.query(VerificationResult).filter(
        VerificationResult.session_id == session_id
    ).delete()

    # Delete session
    db.delete(session)
    db.commit()

    return {"message": f"Verification session {session_id} deleted successfully"}


@router.delete("/bidder/{bidder_id}/clear")
async def clear_bidder_verifications(
    bidder_id: str,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Clear all verification sessions for a bidder.
    """
    sessions = db.query(VerificationSession).filter(
        VerificationSession.bidder_id == bidder_id
    ).all()

    if not sessions:
        return {"message": f"No verification sessions found for bidder {bidder_id}", "deleted_count": 0}

    # Delete all results for all sessions
    for session in sessions:
        db.query(VerificationResult).filter(
            VerificationResult.session_id == session.id
        ).delete()

    # Delete all sessions
    deleted_count = db.query(VerificationSession).filter(
        VerificationSession.bidder_id == bidder_id
    ).delete()

    db.commit()

    return {
        "message": f"All verification data for bidder {bidder_id} cleared successfully",
        "deleted_count": deleted_count
    }
