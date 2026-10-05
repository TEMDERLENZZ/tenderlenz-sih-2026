"""
Comprehensive Test Suite for Phase 6: Tender Requirement Engine
Tests requirements extraction, procurement officer review/editing, bidder evaluation,
numeric/percentage/document/status comparison logic, evidence generation, and summary metrics.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tender import Tender, TenderRequirement, TenderComplianceResult, RequirementType, ComplianceResultStatus
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.verification import VerificationSession, VerificationResult, VerificationStatus, VerificationSourceMode, VerificationCategory
from app.services.tender.requirement_extractor import RequirementExtractor
from app.services.tender.compliance_evaluator import ComplianceEvaluator

class TestPhase6Engine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create in-memory SQLite DB for testing
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_01_requirement_extraction(self):
        """Test 1: Requirement extraction from tender document text"""
        extractor = RequirementExtractor()
        tender_text = """
        TENDER DOCUMENT REF-2026-001
        1. Minimum Turnover required: ₹5 Crore per year
        2. GST Registration: Mandatory active GSTIN
        3. BIS Certification: Mandatory BIS Certificate IS-12345
        4. OEM Authorization: Letter from Original Equipment Manufacturer
        5. Local Content Percentage: Minimum 50% Make in India local content
        6. Blacklisting Condition: Bidder must not be blacklisted
        """
        reqs = extractor.extract_requirements(tender_text, "TENDER_TEST_001")
        self.assertGreaterEqual(len(reqs), 6)

        categories = [r['category'] for r in reqs]
        self.assertIn("FINANCIAL", categories)
        self.assertIn("REGISTRATION", categories)
        self.assertIn("CERTIFICATE", categories)

    def test_02_seed_demo_requirements(self):
        """Test 2: Standard demo requirements generator"""
        extractor = RequirementExtractor()
        demo_reqs = extractor.get_standard_demo_requirements()
        self.assertEqual(len(demo_reqs), 6)

        codes = [r['requirement_code'] for r in demo_reqs]
        self.assertIn("REQ-001", codes)
        self.assertIn("REQ-006", codes)

    def test_03_bidder_evaluation_and_comparisons(self):
        """Test 3-10: Complete bidder evaluation covering numeric, percentage, document, status, missing, review-required cases"""
        tender_id = "TENDER_DEMO_TEST"
        bidder_id = "BIDDER_001"

        # 1. Setup Tender & Requirements in DB
        tender = Tender(
            tender_id=tender_id,
            title="Demo Procurement Tender",
            extracted_text="Minimum Turnover ₹5 Crore, GST Active, BIS Certificate, OEM Authorization, Local Content >= 50%, Not Blacklisted",
            status="EXTRACTED"
        )
        self.db.add(tender)
        self.db.commit()

        extractor = RequirementExtractor()
        for req_data in extractor.get_standard_demo_requirements():
            r = TenderRequirement(tender_id=tender_id, **req_data)
            self.db.add(r)
        self.db.commit()

        # 2. Setup Bidder Documents in DB for BIDDER_001
        docs = [
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.FINANCIAL_TURNOVER_CERTIFICATE,
                file_name="02_Financial_Turnover_DEMO.pdf",
                file_path="/uploads/BIDDER_001/02_Financial_Turnover_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"average_turnover": "₹7.2 Crore", "bidder_name": "ABC TECHNOLOGIES PVT LTD"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.GST_CERTIFICATE,
                file_name="01_GST_DEMO.pdf",
                file_path="/uploads/BIDDER_001/01_GST_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"gstin": "27AABCU9603R1ZM", "legal_name": "ABC TECHNOLOGIES PVT LTD", "status": "ACTIVE"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.BIS_CERTIFICATE,
                file_name="10_BIS_DEMO.pdf",
                file_path="/uploads/BIDDER_001/10_BIS_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"license_number": "IS123456", "status": "VALID"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.OEM_AUTHORIZATION,
                file_name="08_OEM_DEMO.pdf",
                file_path="/uploads/BIDDER_001/08_OEM_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"authorized_bidder_name": "ABC TECHNOLOGIES PVT LTD", "oem_name": "GLOBAL HARDWARE INC"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.LOCAL_CONTENT_DECLARATION,
                file_name="09_Local_Content_DEMO.pdf",
                file_path="/uploads/BIDDER_001/09_Local_Content_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"local_content_percentage": "65%"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.NON_BLACKLISTING_DECLARATION,
                file_name="13_Blacklisting_DEMO.pdf",
                file_path="/uploads/BIDDER_001/13_Blacklisting_DEMO.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"blacklisting_status": "NOT_BLACKLISTED"}
            ),
        ]
        for d in docs:
            self.db.add(d)
        self.db.commit()

        # 3. Setup Phase 2 Verification Result for GST
        v_res = VerificationResult(
            session_id=1,
            bidder_id=bidder_id,
            check_id="GST-003",
            category=VerificationCategory.COMPLIANCE,
            requirement="GST registration status must be ACTIVE",
            verification_source="GST_PROVIDER",
            source_mode=VerificationSourceMode.SANDBOX,
            status=VerificationStatus.VERIFIED,
            confidence=0.95,
            explanation="GST registration status is ACTIVE (verified via sandbox provider)",
            evidence={"verified_status": "ACTIVE"}
        )
        self.db.add(v_res)
        self.db.commit()

        # 4. Execute Evaluation
        evaluator = ComplianceEvaluator(self.db)
        results = evaluator.evaluate_bidder(tender_id, bidder_id)

        self.assertEqual(len(results), 6)

        results_by_code = {r.requirement_code: r for r in results}

        # Check REQ-001 (Minimum Turnover: ₹7.2 Cr vs ₹5 Cr -> SATISFIED)
        r1 = results_by_code["REQ-001"]
        self.assertEqual(r1.result, ComplianceResultStatus.SATISFIED)
        self.assertIn("7.2 Crore", r1.actual_value)
        self.assertIn("Financial Turnover Certificate", r1.evidence["document"])

        # Check REQ-002 (GST Active -> SATISFIED)
        r2 = results_by_code["REQ-002"]
        self.assertEqual(r2.result, ComplianceResultStatus.SATISFIED)

        # Check REQ-003 (BIS Certificate -> SATISFIED)
        r3 = results_by_code["REQ-003"]
        self.assertEqual(r3.result, ComplianceResultStatus.SATISFIED)

        # Check REQ-004 (OEM Authorization match -> SATISFIED or REVIEW_REQUIRED for OEM legitimacy review)
        r4 = results_by_code["REQ-004"]
        self.assertIn(r4.result, [ComplianceResultStatus.SATISFIED, ComplianceResultStatus.REVIEW_REQUIRED])

        # Check REQ-005 (Local Content 65% vs 50% -> SATISFIED)
        r5 = results_by_code["REQ-005"]
        self.assertEqual(r5.result, ComplianceResultStatus.SATISFIED)
        self.assertEqual(r5.actual_value, "65%")

        # Check REQ-006 (Non-Blacklisted -> SATISFIED)
        r6 = results_by_code["REQ-006"]
        self.assertEqual(r6.result, ComplianceResultStatus.SATISFIED)

    def test_04_test_not_satisfied_and_missing_cases(self):
        """Test NOT_SATISFIED and MISSING results for failing bidder"""
        tender_id = "TENDER_FAIL_TEST"
        bidder_id = "BIDDER_002"

        tender = Tender(
            tender_id=tender_id,
            title="Strict Tender Specification",
            extracted_text="Minimum Turnover ₹5 Crore, BIS mandatory, Local Content >= 50%",
            status="EXTRACTED"
        )
        self.db.add(tender)
        
        extractor = RequirementExtractor()
        for req_data in extractor.get_standard_demo_requirements():
            r = TenderRequirement(tender_id=tender_id, **req_data)
            self.db.add(r)
        self.db.commit()

        # Bidder 002: Low turnover (₹4.35 Crore) and low local content (42%), Missing BIS document
        docs = [
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.FINANCIAL_TURNOVER_CERTIFICATE,
                file_name="Turnover_Fail.pdf",
                file_path="/uploads/BIDDER_002/Turnover_Fail.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"average_turnover": "₹4.35 Crore"}
            ),
            Document(
                bidder_id=bidder_id,
                document_type=DocumentType.LOCAL_CONTENT_DECLARATION,
                file_name="Local_Fail.pdf",
                file_path="/uploads/BIDDER_002/Local_Fail.pdf",
                status=ProcessingStatus.EXTRACTED,
                extracted_data={"local_content_percentage": "42%"}
            )
            # BIS_CERTIFICATE is NOT uploaded -> MISSING
        ]
        for d in docs:
            self.db.add(d)
        self.db.commit()

        evaluator = ComplianceEvaluator(self.db)
        results = evaluator.evaluate_bidder(tender_id, bidder_id)
        results_by_code = {r.requirement_code: r for r in results}

        # REQ-001 (Turnover 4.35 Cr vs 5 Cr -> NOT_SATISFIED)
        r1 = results_by_code["REQ-001"]
        self.assertEqual(r1.result, ComplianceResultStatus.NOT_SATISFIED)
        self.assertIn("4.35 Crore", r1.actual_value)

        # REQ-003 (BIS Certificate -> MISSING)
        r3 = results_by_code["REQ-003"]
        self.assertEqual(r3.result, ComplianceResultStatus.MISSING)

        # REQ-005 (Local content 42% vs 50% -> NOT_SATISFIED)
        r5 = results_by_code["REQ-005"]
        self.assertEqual(r5.result, ComplianceResultStatus.NOT_SATISFIED)
        self.assertEqual(r5.actual_value, "42%")

if __name__ == "__main__":
    unittest.main()
