"""
Test script to validate document classification for all 14 document types
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


from app.services.document_processor import DocumentProcessor
from app.models.document import DocumentType
import os

processor = DocumentProcessor()

# Test documents with expected content
test_cases = [
    {
        "filename": "01_GST_Certificate",
        "expected_type": DocumentType.GST_CERTIFICATE,
        "test_content": """
        GOODS AND SERVICES TAX REGISTRATION CERTIFICATE
        GSTIN: 33AXMPS1015Q2Z2
        Legal Name: SASIKUMAR
        Trade Name: VIVID TRADERS
        """
    },
    {
        "filename": "02_Udyam_Certificate",
        "expected_type": DocumentType.UDYAM_CERTIFICATE,
        "test_content": """
        UDYAM REGISTRATION CERTIFICATE
        Udyam Registration Number: UDYAM-TN-01-0012345
        Enterprise Name: SASIKUMAR
        MSME Certificate
        """
    },
    {
        "filename": "03_PAN_Card",
        "expected_type": DocumentType.PAN_CARD,
        "test_content": """
        PERMANENT ACCOUNT NUMBER CARD
        Income Tax Department
        PAN: AXMPS1015Q
        Name: SASIKUMAR
        """
    },
    {
        "filename": "04_Income_Tax_Return",
        "expected_type": DocumentType.INCOME_TAX_RETURN,
        "test_content": """
        INCOME TAX RETURN ACKNOWLEDGEMENT
        Assessment Year: 2023-24
        PAN: AXMPS1015Q
        Acknowledgement Number: 123456789
        """
    },
    {
        "filename": "05_OEM_Authorization",
        "expected_type": DocumentType.OEM_AUTHORIZATION,
        "test_content": """
        OEM AUTHORIZATION LETTER
        Original Equipment Manufacturer
        OEM Name: TechCorp Industries
        Authorized Bidder: SASIKUMAR
        Authorization Number: OEM-2024-001
        """
    },
    {
        "filename": "06_EPFO_Registration",
        "expected_type": DocumentType.EPFO_REGISTRATION,
        "test_content": """
        EPFO REGISTRATION CERTIFICATE
        Employees Provident Fund Organisation
        Establishment Code: KN/12345
        Establishment Name: SASIKUMAR
        """
    },
    {
        "filename": "07_ESIC_Registration",
        "expected_type": DocumentType.ESIC_REGISTRATION,
        "test_content": """
        ESIC REGISTRATION CERTIFICATE
        Employees State Insurance Corporation
        Employer Name: SASIKUMAR
        ESIC Code: 56001234560001001
        Status: ACTIVE
        """
    },
    {
        "filename": "08_Local_Content_Declaration",
        "expected_type": DocumentType.LOCAL_CONTENT_DECLARATION,
        "test_content": """
        LOCAL CONTENT DECLARATION
        Make in India
        Bidder Name: SASIKUMAR
        Local Content Percentage: 65%
        """
    },
    {
        "filename": "09_BIS_Certificate",
        "expected_type": DocumentType.BIS_CERTIFICATE,
        "test_content": """
        BIS CERTIFICATE
        Bureau of Indian Standards
        License Number: 1234567
        Product: Industrial Equipment
        """
    },
    {
        "filename": "10_Startup_Certificate",
        "expected_type": DocumentType.STARTUP_CERTIFICATE,
        "test_content": """
        STARTUP RECOGNITION CERTIFICATE
        DPIIT Recognition
        Certificate of Recognition
        Startup Name: SASIKUMAR Tech
        """
    },
    {
        "filename": "11_NSIC_Certificate",
        "expected_type": DocumentType.NSIC_CERTIFICATE,
        "test_content": """
        NSIC CERTIFICATE
        National Small Industries Corporation
        Registration Number: NSIC-001
        Performance Certificate
        """
    },
    {
        "filename": "12_Company_Incorporation",
        "expected_type": DocumentType.COMPANY_INCORPORATION,
        "test_content": """
        CERTIFICATE OF INCORPORATION
        Corporate Identity Number: U74999MH2015PTC123456
        Registrar of Companies
        Company Name: SASIKUMAR TECHNOLOGIES PVT LTD
        """
    },
    {
        "filename": "13_Non_Blacklisting",
        "expected_type": DocumentType.NON_BLACKLISTING_DECLARATION,
        "test_content": """
        NON BLACKLISTING DECLARATION
        I declare that I am not blacklisted
        Not debarred by any government authority
        Declaration by bidder
        """
    },
    {
        "filename": "14_Financial_Turnover",
        "expected_type": DocumentType.FINANCIAL_TURNOVER_CERTIFICATE,
        "test_content": """
        FINANCIAL TURNOVER CERTIFICATE
        Chartered Accountant Certificate
        Annual Turnover for FY 2023-24: Rs. 5,00,00,000
        Financial Year turnover statement
        """
    },
]

print("=" * 100)
print("DOCUMENT CLASSIFICATION TEST - ALL 14 DOCUMENT TYPES")
print("=" * 100)
print()
print(f"{'Filename':<35} {'Expected Type':<25} {'Detected Type':<25} {'Conf':<7} {'Status':<8}")
print("-" * 100)

passed = 0
failed = 0

for test in test_cases:
    predicted_type, confidence, details = processor.classify_document(test["test_content"])

    expected = test["expected_type"]
    detected = predicted_type.value if predicted_type else "NONE"
    expected_name = expected.value

    status = "PASS" if predicted_type == expected else "FAIL"

    if status == "PASS":
        passed += 1
    else:
        failed += 1

    print(f"{test['filename']:<35} {expected_name:<25} {detected:<25} {confidence:<7.2f} {status:<8}")

    if status == "FAIL":
        print(f"  [X] Expected: {expected_name}, Got: {detected}")
        print(f"  Scores: {details.get('all_scores', {})}")
        print(f"  Top keywords: {details.get('matched_keywords', {}).get(detected, [])[:3]}")

print("-" * 100)
print(f"\n[RESULTS] {passed} PASSED, {failed} FAILED out of {len(test_cases)} tests")
print(f"Success Rate: {(passed/len(test_cases))*100:.1f}%")
print()

if failed == 0:
    print("[SUCCESS] ALL TESTS PASSED!")
else:
    print(f"[WARNING] {failed} test(s) failed. Review classification keywords.")

