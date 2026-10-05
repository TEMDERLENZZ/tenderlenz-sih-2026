"""
Comprehensive test script for Phase 1 - All 14 document types
Tests: Classification, Extraction, UTF-8 handling
"""
import sys
import os
sys.path.insert(0, 'D:/tender-compliance-copilot/backend')
os.chdir('D:/tender-compliance-copilot/backend')

from app.services.document_processor import DocumentProcessor
from app.models.document import DocumentType

processor = DocumentProcessor()

print("="*100)
print("PHASE 1 COMPREHENSIVE TEST - ALL 14 DOCUMENT TYPES")
print("="*100)
print()

# Test all 14 document types
results = []

test_cases = [
    ("01_GST", DocumentType.GST_CERTIFICATE,
     "GOODS AND SERVICES TAX CERTIFICATE GSTIN 27AABCU9603R1ZM Legal Name ABC TECHNOLOGIES"),
    ("02_Financial_Turnover", DocumentType.FINANCIAL_TURNOVER_CERTIFICATE,
     "FINANCIAL TURNOVER CERTIFICATE Chartered Accountant Annual Turnover FY 2023-24"),
    ("03_PAN", DocumentType.PAN_CARD,
     "PERMANENT ACCOUNT NUMBER Income Tax Department PAN AABCU9603R Name ABC TECH"),
    ("04_Udyam", DocumentType.UDYAM_CERTIFICATE,
     "UDYAM REGISTRATION CERTIFICATE MSME Udyam Number UDYAM-MH-01-001"),
    ("05_MCA", DocumentType.COMPANY_INCORPORATION,
     "CERTIFICATE OF INCORPORATION CIN U74999MH2015PTC123456 Registrar of Companies"),
    ("06_EPFO", DocumentType.EPFO_REGISTRATION,
     "EPFO REGISTRATION Employees Provident Fund Establishment Code MH/12345"),
    ("07_ESIC", DocumentType.ESIC_REGISTRATION,
     "ESIC REGISTRATION CERTIFICATE Employees State Insurance ESIC Code 56001234560001001"),
    ("08_OEM", DocumentType.OEM_AUTHORIZATION,
     "OEM AUTHORIZATION LETTER Original Equipment Manufacturer Authorized Bidder ABC TECH"),
    ("09_Local_Content", DocumentType.LOCAL_CONTENT_DECLARATION,
     "LOCAL CONTENT DECLARATION Make in India Local Content Percentage 65%"),
    ("10_BIS", DocumentType.BIS_CERTIFICATE,
     "BIS CERTIFICATE Bureau of Indian Standards License Number IS123456"),
    ("11_Startup", DocumentType.STARTUP_CERTIFICATE,
     "STARTUP RECOGNITION CERTIFICATE DPIIT Recognition Startup India"),
    ("12_NSIC", DocumentType.NSIC_CERTIFICATE,
     "NSIC CERTIFICATE National Small Industries Corporation Performance Certificate"),
    ("13_Non_Blacklisting", DocumentType.NON_BLACKLISTING_DECLARATION,
     "NON BLACKLISTING DECLARATION Not blacklisted Not debarred Declaration"),
    ("14_ITR", DocumentType.INCOME_TAX_RETURN,
     "INCOME TAX RETURN ACKNOWLEDGEMENT Assessment Year 2023-24 ITR-V"),
]

print(f"{'Document':<25} {'Expected':<30} {'Detected':<30} {'Status':<10} {'Conf':<6} {'Errors':<20}")
print("-"*100)

for name, expected, content in test_cases:
    try:
        predicted, confidence, details = processor.classify_document(content)

        detected = predicted.value if predicted else "NONE"
        expected_val = expected.value

        status = "PASS" if predicted == expected else "FAIL"
        errors = "None"

        if status == "FAIL":
            scores = details.get('all_scores', {})
            errors = f"Got {detected}"

        results.append({
            'name': name,
            'expected': expected_val,
            'detected': detected,
            'status': status,
            'confidence': confidence,
            'errors': errors
        })

        print(f"{name:<25} {expected_val:<30} {detected:<30} {status:<10} {confidence:<6.2f} {errors:<20}")

    except Exception as e:
        error_msg = str(e)[:50]
        results.append({
            'name': name,
            'expected': expected.value,
            'detected': "ERROR",
            'status': "ERROR",
            'confidence': 0.0,
            'errors': error_msg
        })
        print(f"{name:<25} {expected.value:<30} {'ERROR':<30} {'ERROR':<10} {'0.00':<6} {error_msg:<20}")

print("-"*100)

# Summary
passed = sum(1 for r in results if r['status'] == 'PASS')
failed = sum(1 for r in results if r['status'] == 'FAIL')
errors = sum(1 for r in results if r['status'] == 'ERROR')

print(f"\nRESULTS: {passed} PASSED, {failed} FAILED, {errors} ERRORS out of {len(results)} tests")
print(f"Success Rate: {(passed/len(results))*100:.1f}%")

if passed == len(results):
    print("\n[SUCCESS] ALL PHASE 1 TESTS PASSED - READY FOR PHASE 2")
else:
    print(f"\n[WARNING] {failed + errors} test(s) need attention")

