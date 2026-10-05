"""
Automated Phase 1 Test Suite - All 14 Demo PDFs
Tests classification accuracy and extraction success
"""
import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))


from app.services.document_processor import DocumentProcessor
from app.models.document import DocumentType

processor = DocumentProcessor()

# Expected mappings for all 14 demo documents
EXPECTED_MAPPINGS = {
    "01_GST": DocumentType.GST_CERTIFICATE,
    "02_Udyam": DocumentType.UDYAM_CERTIFICATE,
    "03_PAN": DocumentType.PAN_CARD,
    "04_Income_Tax": DocumentType.INCOME_TAX_RETURN,
    "04_ITR": DocumentType.INCOME_TAX_RETURN,
    "05_OEM": DocumentType.OEM_AUTHORIZATION,
    "06_EPFO": DocumentType.EPFO_REGISTRATION,
    "07_ESIC": DocumentType.ESIC_REGISTRATION,
    "08_Local_Content": DocumentType.LOCAL_CONTENT_DECLARATION,
    "09_BIS": DocumentType.BIS_CERTIFICATE,
    "10_Startup": DocumentType.STARTUP_CERTIFICATE,
    "11_NSIC": DocumentType.NSIC_CERTIFICATE,
    "12_Company_Incorporation": DocumentType.COMPANY_INCORPORATION,
    "12_Incorporation": DocumentType.COMPANY_INCORPORATION,
    "13_Non_Blacklisting": DocumentType.NON_BLACKLISTING_DECLARATION,
    "13_Blacklisting": DocumentType.NON_BLACKLISTING_DECLARATION,
    "14_Financial_Turnover": DocumentType.FINANCIAL_TURNOVER_CERTIFICATE,
}

def find_demo_pdfs():
    """Find all demo PDFs in uploads directory"""
    pdf_files = []
    search_dirs = ["demo_fixtures", "uploads", "../backend/demo_fixtures", "../backend/uploads"]
    seen = set()
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for root, dirs, files in os.walk(s_dir):
                for file in files:
                    if file.endswith(".pdf") and "DEMO" in file:
                        full_p = os.path.abspath(os.path.join(root, file))
                        if full_p not in seen:
                            seen.add(full_p)
                            pdf_files.append(full_p)

    return sorted(pdf_files)

def extract_doc_prefix(filename):
    """Extract document prefix (e.g., '01_GST' from '01_GST_Certificate_DEMO.pdf')"""
    basename = os.path.basename(filename)
    # Try to match pattern like "01_GST_Certificate_DEMO.pdf"
    parts = basename.replace("_DEMO.pdf", "").split("_")

    if len(parts) >= 2:
        # Return first two parts (e.g., "01_GST")
        prefix = f"{parts[0]}_{parts[1]}"

        # Special handling for multi-word names
        if prefix in EXPECTED_MAPPINGS:
            return prefix

        # Try three parts
        if len(parts) >= 3:
            prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
            if prefix in EXPECTED_MAPPINGS:
                return prefix

    return None

def test_all_documents():
    """Test classification for all 14 demo documents"""
    print("=" * 100)
    print("PHASE 1 AUTOMATED TEST SUITE - ALL 14 DEMO PDFs")
    print("=" * 100)
    print()

    pdf_files = find_demo_pdfs()

    if not pdf_files:
        print("WARNING: No demo PDFs found in uploads directory")
        print("Please upload documents first via the UI")
        return

    print(f"Found {len(pdf_files)} demo PDF(s)\n")

    results = []

    print(f"{'Document':<40} {'Expected':<30} {'Detected':<30} {'Conf%':<8} {'Status':<10}")
    print("-" * 100)

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        prefix = extract_doc_prefix(filename)

        if not prefix or prefix not in EXPECTED_MAPPINGS:
            print(f"{filename:<40} {'UNKNOWN':<30} {'SKIPPED':<30} {'N/A':<8} {'SKIP':<10}")
            continue

        expected = EXPECTED_MAPPINGS[prefix]

        try:
            # Extract text from PDF
            text = processor.extract_text(pdf_path, "application/pdf")

            if not text or len(text) < 10:
                results.append({
                    'filename': filename,
                    'expected': expected.value,
                    'detected': 'NO_TEXT',
                    'status': 'FAIL',
                    'confidence': 0.0,
                    'error': 'No text extracted'
                })
                print(f"{filename:<40} {expected.value:<30} {'NO_TEXT':<30} {'0.0':<8} {'FAIL':<10}")
                continue

            # Classify document
            predicted, confidence, details = processor.classify_document(text)

            detected = predicted.value if predicted else "NONE"
            status = "PASS" if predicted == expected else "FAIL"
            conf_pct = f"{confidence*100:.1f}"

            results.append({
                'filename': filename,
                'expected': expected.value,
                'detected': detected,
                'status': status,
                'confidence': confidence,
                'error': None if status == 'PASS' else f"Expected {expected.value}, got {detected}"
            })

            # Status display (plain text for Windows console)
            status_display = status

            print(f"{filename:<40} {expected.value:<30} {detected:<30} {conf_pct:<8} {status_display:<10}")

            if status == "FAIL":
                scores = details.get('all_scores', {})
                print(f"  Scores: {dict(list(sorted(scores.items(), key=lambda x: x[1], reverse=True))[:3])}")

        except Exception as e:
            error_msg = str(e)[:50]
            results.append({
                'filename': filename,
                'expected': expected.value,
                'detected': 'ERROR',
                'status': 'ERROR',
                'confidence': 0.0,
                'error': error_msg
            })
            print(f"{filename:<40} {expected.value:<30} {'ERROR':<30} {'0.0':<8} {'ERROR':<10}")
            print(f"  Error: {error_msg}")

    print("-" * 100)

    # Summary
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    total = len(results)

    print(f"\nTEST RESULTS:")
    print(f"   PASSED: {passed}/{total}")
    print(f"   FAILED: {failed}/{total}")
    print(f"   ERRORS: {errors}/{total}")

    if total > 0:
        success_rate = (passed / total) * 100
        print(f"   Success Rate: {success_rate:.1f}%")

    print()

    if passed == total and total >= 14:
        print("ALL PHASE 1 TESTS PASSED - SYSTEM READY FOR PHASE 2")
    elif passed == total and total > 0:
        print(f"All {total} available documents passed")
        print(f"WARNING: Upload remaining documents to complete full test (14 total expected)")
    else:
        print(f"WARNING: {failed + errors} test(s) failed - review classifier and extraction")

        if failed > 0:
            print("\nFailed Documents:")
            for r in results:
                if r['status'] == 'FAIL':
                    print(f"  - {r['filename']}: {r['error']}")

if __name__ == "__main__":
    test_all_documents()
