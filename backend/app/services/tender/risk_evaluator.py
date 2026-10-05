"""
Risk Evaluator Service

Deterministic and explainable risk calculation based on:
- Compliance results
- Verification results
- Document status

NOT AI-driven. Uses rule-based scoring for transparency.
"""
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.tender import (
    TenderComplianceResult,
    ComplianceResultStatus,
    BidderRiskAssessment,
    RiskLevel
)
from app.models.verification import (
    VerificationResult,
    VerificationStatus,
    VerificationCategory
)


class RiskEvaluator:
    """
    Deterministic risk calculation engine.

    Risk Score Calculation (0-100):
    - Critical eligibility failures: +30 each
    - Non-critical compliance failures: +15 each
    - High-severity verification mismatches: +20 each
    - Medium-severity verification mismatches: +10 each
    - Review required items: +5 each
    - Missing critical documents: +10 each

    Risk Levels:
    - LOW: score < 20
    - MEDIUM: score 20-49
    - HIGH: score >= 50
    """

    # Critical requirements that cause high risk
    CRITICAL_REQUIREMENTS = ['REQ-001', 'REQ-002']

    def __init__(self, db: Session):
        self.db = db

    def calculate_risk(
        self,
        tender_id: str,
        bidder_id: str,
        compliance_results: List[TenderComplianceResult] = None,
        verification_results: List[VerificationResult] = None
    ) -> BidderRiskAssessment:
        """
        Calculate risk assessment for a bidder.

        Args:
            tender_id: Tender identifier
            bidder_id: Bidder identifier
            compliance_results: Optional pre-loaded compliance results
            verification_results: Optional pre-loaded verification results

        Returns:
            BidderRiskAssessment with calculated risk level, score, and factors
        """
        # Load data if not provided
        if compliance_results is None:
            compliance_results = self.db.query(TenderComplianceResult).filter(
                TenderComplianceResult.tender_id == tender_id,
                TenderComplianceResult.bidder_id == bidder_id
            ).all()

        if verification_results is None:
            verification_results = self.db.query(VerificationResult).filter(
                VerificationResult.bidder_id == bidder_id
            ).all()

        # Calculate risk
        factors = []
        risk_score = 0

        # 1. Analyze compliance failures
        compliance_factors, compliance_score = self._analyze_compliance(compliance_results)
        factors.extend(compliance_factors)
        risk_score += compliance_score

        # 2. Analyze verification mismatches
        verification_factors, verification_score = self._analyze_verification(verification_results)
        factors.extend(verification_factors)
        risk_score += verification_score

        # 3. Determine risk level and summary
        risk_level, summary = self._determine_risk_level(risk_score, factors)

        # Cap risk score at 100
        risk_score = min(risk_score, 100)

        # Create risk assessment
        risk_assessment = BidderRiskAssessment(
            tender_id=tender_id,
            bidder_id=bidder_id,
            risk_level=risk_level,
            risk_score=risk_score,
            factors=factors,
            summary=summary
        )

        return risk_assessment

    def _analyze_compliance(
        self,
        results: List[TenderComplianceResult]
    ) -> Tuple[List[dict], float]:
        """
        Analyze compliance results and return risk factors + score.

        Returns:
            (factors, total_score)
        """
        factors = []
        score = 0

        for result in results:
            if result.result == ComplianceResultStatus.NOT_SATISFIED:
                is_critical = result.requirement_code in self.CRITICAL_REQUIREMENTS
                severity = "HIGH" if is_critical else "MEDIUM"
                points = 30 if is_critical else 15

                factors.append({
                    "type": "COMPLIANCE_FAILURE",
                    "severity": severity,
                    "requirement": result.requirement_code,
                    "description": result.explanation,
                    "source": "Compliance Engine",
                    "points": points
                })
                score += points

            elif result.result == ComplianceResultStatus.REVIEW_REQUIRED:
                factors.append({
                    "type": "REVIEW_REQUIRED",
                    "severity": "MEDIUM",
                    "requirement": result.requirement_code,
                    "description": result.explanation,
                    "source": "Compliance Engine",
                    "points": 5
                })
                score += 5

            elif result.result == ComplianceResultStatus.MISSING:
                factors.append({
                    "type": "DOCUMENT_MISSING",
                    "severity": "MEDIUM",
                    "requirement": result.requirement_code,
                    "description": result.explanation,
                    "source": "Document Check",
                    "points": 10
                })
                score += 10

        return factors, score

    def _analyze_verification(
        self,
        results: List[VerificationResult]
    ) -> Tuple[List[dict], float]:
        """
        Analyze verification results and return risk factors + score.

        Returns:
            (factors, total_score)
        """
        factors = []
        score = 0

        for result in results:
            if result.status == VerificationStatus.MISMATCH:
                # Determine severity based on verification category
                is_high_severity = result.category in [
                    VerificationCategory.IDENTITY,
                    VerificationCategory.REGISTRATION
                ]
                severity = "HIGH" if is_high_severity else "MEDIUM"
                points = 20 if is_high_severity else 10

                factors.append({
                    "type": "VERIFICATION_MISMATCH",
                    "severity": severity,
                    "check": result.check_id,
                    "category": result.category.value,
                    "description": result.explanation,
                    "source": result.verification_source,
                    "points": points
                })
                score += points

            elif result.status == VerificationStatus.NOT_VERIFIED:
                factors.append({
                    "type": "VERIFICATION_FAILED",
                    "severity": "MEDIUM",
                    "check": result.check_id,
                    "category": result.category.value,
                    "description": result.explanation,
                    "source": result.verification_source,
                    "points": 5
                })
                score += 5

        return factors, score

    def _determine_risk_level(
        self,
        risk_score: float,
        factors: List[dict]
    ) -> Tuple[RiskLevel, str]:
        """
        Determine risk level and generate summary based on score and factors.

        Returns:
            (risk_level, summary_text)
        """
        # Count high-severity factors
        high_severity_count = sum(1 for f in factors if f.get('severity') == 'HIGH')

        if risk_score >= 50 or high_severity_count >= 2:
            return (
                RiskLevel.HIGH,
                f"HIGH RISK: Critical eligibility failures or multiple serious discrepancies detected. "
                f"Risk score: {risk_score:.1f}/100. {len(factors)} risk factor(s) identified. "
                f"Procurement officer review strongly recommended before proceeding."
            )
        elif risk_score >= 20 or high_severity_count >= 1:
            return (
                RiskLevel.MEDIUM,
                f"MEDIUM RISK: Some non-compliance or verification issues require officer review. "
                f"Risk score: {risk_score:.1f}/100. {len(factors)} risk factor(s) identified. "
                f"Manual verification recommended for flagged items."
            )
        else:
            return (
                RiskLevel.LOW,
                f"LOW RISK: Requirements generally satisfied with minor or no issues. "
                f"Risk score: {risk_score:.1f}/100. {len(factors)} risk factor(s) identified. "
                f"Standard procurement procedures apply."
            )
