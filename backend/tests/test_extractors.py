"""
Extraction Validation Test Framework
Phase 1A — Tests for all 14 document extractors

Tests each extractor against:
1. Valid document (realistic text)
2. Missing required fields
3. OCR-degraded text
4. Different field layouts
5. Invalid/empty document
6. Wrong document type text

Run: python -m pytest backend/tests/test_extractors.py -v
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.services.extractors.gst_extractor import GSTExtractor
from app.services.extractors.pan_extractor import PANExtractor
from app.services.extractors.udyam_extractor import UdyamExtractor
from app.services.extractors.financial_turnover_extractor import FinancialTurnoverExtractor
from app.services.extractors.oem_extractor import OEMExtractor
from app.services.extractors.epfo_extractor import EPFOExtractor
from app.services.extractors.esic_extractor import ESICExtractor
from app.services.extractors.local_content_extractor import LocalContentExtractor
from app.services.extractors.bis_extractor import BISExtractor
from app.services.extractors.startup_extractor import StartupExtractor
from app.services.extractors.nsic_extractor import NSICExtractor
from app.services.extractors.company_incorporation_extractor import CompanyIncorporationExtractor
from app.services.extractors.non_blacklisting_extractor import NonBlacklistingExtractor
from app.services.extractors.itr_extractor import ITRExtractor


# ============================================================
# HELPER: normalize extractor output to (data, trace)
# ============================================================
def normalize_result(result):
    """Ensure result is always (data_dict, trace_list)."""
    if isinstance(result, tuple):
        return result[0], result[1]
    else:
        return result, []


# ============================================================
# 1. GST CERTIFICATE TESTS
# ============================================================
class TestGSTExtractor:
    extractor = GSTExtractor()

    VALID_GST_TEXT = """
    GOODS AND SERVICES TAX IDENTIFICATION NUMBER (GSTIN)
    Registered in accordance with the Central Goods and Services Tax Act 2017.
    GSTIN: 27AABCT1332L1ZF
    1.Legal Name ACME TECHNOLOGIES PRIVATE LIMITED
    2.Trade Name, if any ACME TECH
    4.Constitution of Business Private Limited Company
    5.Address of Principal Place of Business Floor No.: 3 Building: Tech Park Road: MG Road
    City/Town/Village: MUMBAI District: MUMBAI City State: MAHARASHTRA PIN Code: 400001
    6.Date of Liability 01/04/2019
    7.Date of Validity From 22/05/2019 To Not Applicable
    8.Type of Registration Regular
    """

    MISSING_GSTIN_TEXT = """
    GOODS AND SERVICES TAX
    1.Legal Name SOME COMPANY
    2.Trade Name SOME TRADE
    8.Type of Registration Regular
    """

    OCR_DEGRADED_TEXT = """
    G00DS AND SERV1CES TAX
    GST1N: 27AABCT1332L1ZF
    1.Leg@l N@me ACME TECH PVT LTD
    7.D@te 0f V@l1d1ty Fr0m 22/05/2019
    8.Type 0f Reg1str@t10n Regul@r
    """

    EMPTY_TEXT = ""

    WRONG_DOCUMENT_TEXT = """
    This is a PAN card document.
    PERMANENT ACCOUNT NUMBER
    Name: JOHN DOE
    PAN: ABCDE1234F
    """

    def test_valid_document_extracts_gstin(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_GST_TEXT))
        assert data.get('gstin') == '27AABCT1332L1ZF', f"Expected GSTIN, got: {data.get('gstin')}"

    def test_valid_document_extracts_legal_name(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_GST_TEXT))
        assert data.get('legal_name') is not None, "legal_name should be extracted"
        assert len(data.get('legal_name', '')) > 3

    def test_valid_document_extracts_status(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_GST_TEXT))
        assert data.get('status') in ('ACTIVE', 'CANCELLED', 'SUSPENDED', 'INACTIVE'), \
            f"Unexpected status: {data.get('status')}"

    def test_valid_document_extracts_registration_date(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_GST_TEXT))
        assert data.get('registration_date') is not None, "registration_date should be extracted"

    def test_missing_gstin_returns_none_not_error(self):
        data, trace = normalize_result(self.extractor.extract(self.MISSING_GSTIN_TEXT))
        assert data.get('gstin') is None, "Should return None for missing GSTIN, not raise"
        assert data.get('legal_name') is not None, "legal_name should still be found"

    def test_ocr_degraded_still_finds_gstin(self):
        data, trace = normalize_result(self.extractor.extract(self.OCR_DEGRADED_TEXT))
        # Even with OCR noise, GSTIN regex should work
        assert data.get('gstin') == '27AABCT1332L1ZF', \
            f"Should extract GSTIN from OCR text, got: {data.get('gstin')}"

    def test_empty_text_returns_all_none(self):
        data, trace = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('gstin') is None
        assert data.get('legal_name') is None

    def test_wrong_document_returns_no_gstin(self):
        data, trace = normalize_result(self.extractor.extract(self.WRONG_DOCUMENT_TEXT))
        assert data.get('gstin') is None, "PAN card text should not yield a GSTIN"

    def test_returns_tuple_with_trace(self):
        result = self.extractor.extract(self.VALID_GST_TEXT)
        assert isinstance(result, tuple), "GSTExtractor must return (data, trace) tuple"
        data, trace = result
        assert isinstance(trace, list), "Trace must be a list"
        assert len(trace) > 0, "Trace should have at least one entry"

    def test_trace_has_required_keys(self):
        _, trace = normalize_result(self.extractor.extract(self.VALID_GST_TEXT))
        for entry in trace:
            assert 'field' in entry
            assert 'value' in entry
            assert 'confidence' in entry
            assert 'status' in entry
            assert 'method' in entry
            assert 'evidence' in entry

    def test_legal_name_plain_format(self):
        text = "GSTIN: 27AABCT1332L1ZF\nLegal Name SASIKUMAR\nTrade Name VIVID TRADERS"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'SASIKUMAR'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert legal_trace['value'] == 'SASIKUMAR'
        assert legal_trace['status'] == 'VALID'
        assert legal_trace['confidence'] >= 0.9
        assert legal_trace['source_evidence'] == 'Legal Name SASIKUMAR'
        assert legal_trace['extraction_method'] == 'legal_name_label'

    def test_legal_name_colon_format(self):
        text = "GSTIN: 27AABCT1332L1ZF\nLegal Name: SASIKUMAR\nTrade Name: VIVID TRADERS"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'SASIKUMAR'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert legal_trace['source_evidence'] == 'Legal Name: SASIKUMAR'

    def test_legal_name_dash_format(self):
        text = "GSTIN: 27AABCT1332L1ZF\nLegal Name - SASIKUMAR\nTrade Name - VIVID TRADERS"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'SASIKUMAR'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert 'SASIKUMAR' in legal_trace['source_evidence']

    def test_legal_name_newline_format(self):
        text = "GSTIN: 27AABCT1332L1ZF\nLegal Name\nSASIKUMAR\nTrade Name\nVIVID TRADERS"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'SASIKUMAR'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert legal_trace['value'] == 'SASIKUMAR'
        assert 'SASIKUMAR' in legal_trace['source_evidence']

    def test_legal_name_numbered_format(self):
        text = "GSTIN: 27AABCT1332L1ZF\n1.Legal Name SASIKUMAR\n2.Trade Name VIVID TRADERS"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'SASIKUMAR'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert legal_trace['source_evidence'] == '1.Legal Name SASIKUMAR'
        assert legal_trace['extraction_method'] == 'numbered_label_field_1'

    def test_legal_name_different_company(self):
        text = "GSTIN: 27AABCT1332L1ZF\nLegal Name: BHARAT ENTERPRISES PVT LTD\nTrade Name: BHARAT TECH"
        data, trace = self.extractor.extract(text)
        assert data.get('legal_name') == 'BHARAT ENTERPRISES PVT LTD'
        legal_trace = next(t for t in trace if t['field'] == 'legal_name')
        assert legal_trace['source_evidence'] == 'Legal Name: BHARAT ENTERPRISES PVT LTD'




# ============================================================
# 2. PAN CARD TESTS
# ============================================================
class TestPANExtractor:
    extractor = PANExtractor()

    VALID_PAN_TEXT = """
    INCOME TAX DEPARTMENT
    PERMANENT ACCOUNT NUMBER CARD
    Name: RAJESH KUMAR SHARMA
    Father's Name: RAMESH KUMAR SHARMA
    Date of Birth: 15/08/1985
    PAN: ABCDE1234F
    """

    COMPANY_PAN_TEXT = """
    INCOME TAX DEPARTMENT
    Permanent Account Number
    Name: ACME TECHNOLOGIES PVT LTD
    PAN: AABCT1332L
    """

    EMPTY_TEXT = ""

    def test_valid_individual_pan_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_PAN_TEXT))
        assert data.get('pan_number') == 'ABCDE1234F', f"Got: {data.get('pan_number')}"

    def test_company_pan_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.COMPANY_PAN_TEXT))
        assert data.get('pan_number') is not None, "Company PAN should be extracted"

    def test_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_PAN_TEXT))
        assert data.get('name') is not None, "Name should be extracted from PAN card"

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('pan_number') is None

    def test_pan_format_validation(self):
        """PAN must be exactly 10 chars: 5 alpha + 4 digit + 1 alpha"""
        data, _ = normalize_result(self.extractor.extract(self.VALID_PAN_TEXT))
        pan = data.get('pan_number')
        if pan:
            import re
            assert re.match(r'^[A-Z]{5}\d{4}[A-Z]$', pan), f"Invalid PAN format: {pan}"


# ============================================================
# 3. UDYAM CERTIFICATE TESTS
# ============================================================
class TestUdyamExtractor:
    extractor = UdyamExtractor()

    VALID_UDYAM_TEXT = """
    UDYAM REGISTRATION CERTIFICATE
    Ministry of Micro, Small & Medium Enterprises
    Udyam Registration Number: UDYAM-MH-33-0012345
    Name of Enterprise: ACME TECHNOLOGIES PRIVATE LIMITED
    Type of Organisation: Private Limited Company
    Major Activity: Manufacturing
    Enterprise Category: Small
    Date of Registration: 15/06/2021
    """

    MISSING_URN_TEXT = """
    MSME Certificate
    Name of Enterprise: SOME COMPANY
    Category: Micro Enterprise
    """

    EMPTY_TEXT = ""

    def test_valid_urnum_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_UDYAM_TEXT))
        assert data.get('udyam_registration_number') == 'UDYAM-MH-33-0012345', \
            f"Got: {data.get('udyam_registration_number')}"

    def test_enterprise_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_UDYAM_TEXT))
        assert data.get('enterprise_name') is not None

    def test_enterprise_type_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_UDYAM_TEXT))
        assert data.get('enterprise_type') in ('Micro', 'Small', 'Medium'), \
            f"Got: {data.get('enterprise_type')}"

    def test_missing_urn_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.MISSING_URN_TEXT))
        assert data.get('udyam_registration_number') is None

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('udyam_registration_number') is None

    def test_udyam_format(self):
        """URN must match UDYAM-XX-00-0000000"""
        data, _ = normalize_result(self.extractor.extract(self.VALID_UDYAM_TEXT))
        urn = data.get('udyam_registration_number')
        if urn:
            import re
            assert re.match(r'^UDYAM-[A-Z]{2}-\d{2}-\d{7}$', urn), f"Invalid URN: {urn}"


# ============================================================
# 4. FINANCIAL TURNOVER TESTS
# ============================================================
class TestFinancialTurnoverExtractor:
    extractor = FinancialTurnoverExtractor()

    VALID_TURNOVER_TEXT = """
    CHARTERED ACCOUNTANT CERTIFICATE
    This is to certify that M/s ACME Technologies Pvt. Ltd. has achieved the following turnover:
    Financial Year 2021-22: Rs. 1,50,00,000/-
    Financial Year 2022-23: Rs. 1,75,00,000/-
    Financial Year 2023-24: Rs. 2,00,00,000/-
    Average Turnover: Rs. 1,75,00,000/-
    Chartered Accountant: CA Ramesh Gupta
    Membership No: 123456
    Date: 15/04/2025
    """

    MISSING_TURNOVER_TEXT = """
    TURNOVER CERTIFICATE
    Company: Some Company
    This certificate is issued for tender purposes.
    """

    EMPTY_TEXT = ""

    def test_bidder_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_TURNOVER_TEXT))
        assert data.get('bidder_name') is not None, "bidder_name should be extracted"

    def test_fy_2023_24_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_TURNOVER_TEXT))
        assert data.get('fy_2023_24_turnover') is not None, "2023-24 turnover should be extracted"

    def test_fy_2021_22_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_TURNOVER_TEXT))
        assert data.get('fy_2021_22_turnover') is not None

    def test_average_turnover_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_TURNOVER_TEXT))
        assert data.get('average_turnover') is not None

    def test_missing_turnover_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.MISSING_TURNOVER_TEXT))
        assert data.get('fy_2023_24_turnover') is None

    def test_empty_returns_no_turnover(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('fy_2023_24_turnover') is None


# ============================================================
# 5. OEM AUTHORIZATION TESTS
# ============================================================
class TestOEMExtractor:
    extractor = OEMExtractor()

    VALID_OEM_TEXT = """
    OEM AUTHORIZATION LETTER
    We, SAMSUNG ELECTRONICS CO. LTD., hereby authorize M/s ACME TECHNOLOGIES PVT. LTD.
    to participate in tenders for the supply of LED Televisions and Smart Displays.
    This authorization is valid till 31/03/2026.
    Authorization No: SAMSUNG/AUTH/2024/001
    Issued on: 01/04/2024
    """

    MISSING_BIDDER_TEXT = """
    OEM AUTHORIZATION
    We, ABC Manufacturing, hereby authorize for supply of products.
    """

    EMPTY_TEXT = ""

    def test_oem_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_OEM_TEXT))
        assert data.get('oem_name') is not None, "OEM name should be extracted"

    def test_authorized_bidder_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_OEM_TEXT))
        assert data.get('authorized_bidder_name') is not None

    def test_product_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_OEM_TEXT))
        assert data.get('product_name') is not None

    def test_expiry_date_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_OEM_TEXT))
        assert data.get('expiry_date') is not None

    def test_empty_returns_all_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('oem_name') is None


# ============================================================
# 6. EPFO REGISTRATION TESTS
# ============================================================
class TestEPFOExtractor:
    extractor = EPFOExtractor()

    VALID_EPFO_TEXT = """
    EMPLOYEES PROVIDENT FUND ORGANISATION
    REGISTRATION CERTIFICATE
    Establishment Code (PF Code): MH/BAN/12345/678
    Establishment Name: ACME TECHNOLOGIES PRIVATE LIMITED
    Address: 3rd Floor, Tech Park, MG Road, Bengaluru - 560001
    Date of Registration: 01/06/2018
    Status: Active
    """

    MISSING_ID_TEXT = """
    EPFO Registration
    Name: Some Company
    Address: Some address
    """

    EMPTY_TEXT = ""

    def test_establishment_id_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_EPFO_TEXT))
        assert data.get('establishment_id') is not None, "Establishment ID should be extracted"

    def test_establishment_name_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_EPFO_TEXT))
        assert data.get('establishment_name') is not None

    def test_registration_date_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_EPFO_TEXT))
        assert data.get('registration_date') is not None

    def test_status_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_EPFO_TEXT))
        assert data.get('status') in ('ACTIVE', 'INACTIVE', None)

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_EPFO_TEXT)
        assert isinstance(result, tuple), "EPFOExtractor must return tuple"

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('establishment_id') is None


# ============================================================
# 7. ESIC REGISTRATION TESTS
# ============================================================
class TestESICExtractor:
    extractor = ESICExtractor()

    VALID_ESIC_TEXT = """
    EMPLOYEES STATE INSURANCE CORPORATION
    CERTIFICATE OF REGISTRATION
    ESIC Registration Number: 31000123456789012
    Establishment Name: ACME TECHNOLOGIES PRIVATE LIMITED
    Address of Establishment: 3rd Floor, Tech Park, MG Road, Bangalore - 560001
    Date of Registration: 15/03/2018
    Status: Active / Covered
    """

    MISSING_REG_TEXT = """
    ESIC Registration
    Establishment: Some Company
    """

    EMPTY_TEXT = ""

    def test_esic_number_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_ESIC_TEXT))
        assert data.get('esic_registration_number') is not None, "ESIC reg number should be extracted"

    def test_esic_number_format(self):
        """ESIC number should be 17 digits"""
        data, _ = normalize_result(self.extractor.extract(self.VALID_ESIC_TEXT))
        num = data.get('esic_registration_number')
        if num:
            assert len(num.replace(' ', '')) == 17, f"ESIC number should be 17 digits, got: {num}"

    def test_establishment_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ESIC_TEXT))
        assert data.get('establishment_name') is not None

    def test_registration_date_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ESIC_TEXT))
        assert data.get('registration_date') is not None

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_ESIC_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('esic_registration_number') is None


# ============================================================
# 8. LOCAL CONTENT DECLARATION TESTS
# ============================================================
class TestLocalContentExtractor:
    extractor = LocalContentExtractor()

    VALID_LC_TEXT = """
    DECLARATION OF LOCAL CONTENT
    We, M/s ACME TECHNOLOGIES PRIVATE LIMITED, hereby declare that the local content
    of the items offered in this tender is 65% of the total value.
    This product qualifies as Class-I local content as per PPP-MII Order.
    Authorised Signatory: Rajesh Kumar
    Designation: Managing Director
    Date: 15/04/2025
    """

    MISSING_PERCENTAGE_TEXT = """
    LOCAL CONTENT DECLARATION
    We declare that our product has high local content.
    Date: 01/01/2025
    """

    EMPTY_TEXT = ""

    def test_bidder_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_LC_TEXT))
        assert data.get('bidder_name') is not None

    def test_local_content_percentage_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_LC_TEXT))
        assert data.get('local_content_percentage') is not None, \
            "local_content_percentage should be extracted"

    def test_category_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_LC_TEXT))
        assert data.get('category') == 'Class-I'

    def test_declaration_date_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_LC_TEXT))
        assert data.get('declaration_date') is not None

    def test_missing_percentage_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.MISSING_PERCENTAGE_TEXT))
        assert data.get('local_content_percentage') is None

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('bidder_name') is None


# ============================================================
# 9. BIS CERTIFICATE TESTS
# ============================================================
class TestBISExtractor:
    extractor = BISExtractor()

    VALID_BIS_TEXT = """
    BUREAU OF INDIAN STANDARDS
    LICENCE No. CM/L-1234567
    Name of Licensee: ACME TECHNOLOGIES PRIVATE LIMITED
    Product Name: LED Lamps
    IS Standard: IS 16102:2012
    Date of Grant: 01/07/2020
    Valid Upto: 30/06/2025
    Status: Operative
    """

    MISSING_LICENSE_TEXT = """
    BIS Certificate
    Product: Some product
    Standard: IS 123:2020
    """

    EMPTY_TEXT = ""

    def test_license_number_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('license_number') is not None, "License number should be extracted"

    def test_licensee_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('licensee_name') is not None

    def test_product_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('product_name') is not None

    def test_is_standard_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('is_standard') is not None
        assert 'IS' in data.get('is_standard', '')

    def test_date_of_grant_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('date_of_grant') is not None

    def test_valid_upto_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_BIS_TEXT))
        assert data.get('valid_upto') is not None

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_BIS_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('license_number') is None


# ============================================================
# 10. STARTUP CERTIFICATE TESTS
# ============================================================
class TestStartupExtractor:
    extractor = StartupExtractor()

    VALID_STARTUP_TEXT = """
    DEPARTMENT FOR PROMOTION OF INDUSTRY AND INTERNAL TRADE
    CERTIFICATE OF RECOGNITION
    Certificate No: DIPP12345
    This is to certify that ACME TECHNOLOGIES PRIVATE LIMITED
    has been recognized as a Startup by DPIIT.
    Date of Incorporation: 15/03/2018
    Date of Recognition: 01/07/2021
    Valid Upto: 14/03/2028
    """

    MISSING_DPIIT_TEXT = """
    STARTUP INDIA Certificate
    Name: Some Company
    Date: 01/01/2022
    """

    EMPTY_TEXT = ""

    def test_certificate_number_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_STARTUP_TEXT))
        assert data.get('certificate_number') is not None

    def test_dpiit_number_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_STARTUP_TEXT))
        assert data.get('dpiit_number') is not None

    def test_startup_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_STARTUP_TEXT))
        assert data.get('startup_name') is not None

    def test_recognition_date_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_STARTUP_TEXT))
        assert data.get('recognition_date') is not None

    def test_valid_upto_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_STARTUP_TEXT))
        assert data.get('valid_upto') is not None

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_STARTUP_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('certificate_number') is None


# ============================================================
# 11. NSIC CERTIFICATE TESTS
# ============================================================
class TestNSICExtractor:
    extractor = NSICExtractor()

    VALID_NSIC_TEXT = """
    NATIONAL SMALL INDUSTRIES CORPORATION LIMITED
    CERTIFICATE OF REGISTRATION
    Registration No: NSIC/MH/20-21/12345/MM
    Name of the Unit: ACME TECHNOLOGIES PRIVATE LIMITED
    Enterprise Category: Small
    Validity From: 01/04/2021
    Validity To: 31/03/2024
    """

    MISSING_REG_TEXT = """
    NSIC Certificate
    Name: Some Company
    Valid till: 31/03/2024
    """

    EMPTY_TEXT = ""

    def test_registration_number_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_NSIC_TEXT))
        assert data.get('registration_number') is not None

    def test_enterprise_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_NSIC_TEXT))
        assert data.get('enterprise_name') is not None

    def test_validity_to_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_NSIC_TEXT))
        assert data.get('validity_to') is not None

    def test_category_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_NSIC_TEXT))
        assert data.get('category') in ('Micro', 'Small', 'Medium', None)

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_NSIC_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('registration_number') is None


# ============================================================
# 12. COMPANY INCORPORATION TESTS
# ============================================================
class TestCompanyIncorporationExtractor:
    extractor = CompanyIncorporationExtractor()

    VALID_INC_TEXT = """
    MINISTRY OF CORPORATE AFFAIRS
    CERTIFICATE OF INCORPORATION
    This is to certify that ACME TECHNOLOGIES PRIVATE LIMITED
    CIN: U72200MH2015PTC123456
    is duly incorporated on 15/03/2015
    Company Category: Company Limited by Shares
    Company Sub Category: Indian Non-Government Company
    """

    MISSING_CIN_TEXT = """
    Certificate of Incorporation
    Company: Some Company Private Limited
    Incorporated on: 01/01/2020
    """

    EMPTY_TEXT = ""

    def test_cin_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_INC_TEXT))
        assert data.get('cin') is not None, "CIN should be extracted"

    def test_cin_format(self):
        import re
        data, _ = normalize_result(self.extractor.extract(self.VALID_INC_TEXT))
        cin = data.get('cin')
        if cin:
            assert re.match(r'^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$', cin), f"Invalid CIN: {cin}"

    def test_company_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_INC_TEXT))
        assert data.get('company_name') is not None

    def test_date_of_incorporation_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_INC_TEXT))
        assert data.get('date_of_incorporation') is not None

    def test_missing_cin_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.MISSING_CIN_TEXT))
        assert data.get('cin') is None

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('cin') is None


# ============================================================
# 13. NON-BLACKLISTING DECLARATION TESTS
# ============================================================
class TestNonBlacklistingExtractor:
    extractor = NonBlacklistingExtractor()

    VALID_NB_TEXT = """
    DECLARATION
    We, M/s ACME TECHNOLOGIES PRIVATE LIMITED, hereby declare that our company
    has not been blacklisted or debarred by any Government Department/PSU/Authority
    in India or abroad during the last 3 years.
    Authorized Signatory: Rajesh Kumar
    Designation: Managing Director
    Date: 15/04/2025
    """

    MISSING_STATEMENT_TEXT = """
    Declaration
    Company: Some Company
    Date: 01/01/2025
    """

    EMPTY_TEXT = ""

    def test_bidder_name_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_NB_TEXT))
        assert data.get('bidder_name') is not None

    def test_declaration_date_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_NB_TEXT))
        assert data.get('declaration_date') is not None

    def test_declaration_statement_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_NB_TEXT))
        assert data.get('declaration_statement') is not None
        # Must come from actual document text, not a hardcoded string
        stmt = data.get('declaration_statement', '')
        assert 'blacklisted' in stmt.lower() or 'debarred' in stmt.lower(), \
            "Statement must contain actual declaration language"

    def test_declaration_statement_not_hardcoded(self):
        """Statement for missing-keyword doc must be None, not a canned string"""
        data, _ = normalize_result(self.extractor.extract(self.MISSING_STATEMENT_TEXT))
        stmt = data.get('declaration_statement')
        # The canned fallback "Declared not blacklisted..." is NOT acceptable
        if stmt:
            assert stmt != "Declared not blacklisted or debarred by any government/PSU entity.", \
                "FAIL: Hardcoded fallback statement detected — must return None when not found"

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_NB_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('bidder_name') is None


# ============================================================
# 14. ITR TESTS
# ============================================================
class TestITRExtractor:
    extractor = ITRExtractor()

    VALID_ITR_TEXT = """
    INCOME TAX DEPARTMENT - ITR-V ACKNOWLEDGEMENT
    PAN: ABCDE1234F
    Name of Taxpayer: ACME TECHNOLOGIES PRIVATE LIMITED
    Assessment Year: 2024-25
    Financial Year: 2023-24
    Total Income: 50,00,000
    Total Tax Paid: 15,60,000
    Date of Filing: 31/07/2024
    Acknowledgement Number: 123456789012345
    """

    MISSING_ACK_TEXT = """
    Income Tax Return
    PAN: ABCDE1234F
    Name: Some Taxpayer
    Assessment Year: 2024-25
    """

    EMPTY_TEXT = ""

    def test_pan_extracted(self):
        data, trace = normalize_result(self.extractor.extract(self.VALID_ITR_TEXT))
        assert data.get('pan') == 'ABCDE1234F', f"Got: {data.get('pan')}"

    def test_name_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ITR_TEXT))
        assert data.get('name') is not None

    def test_assessment_year_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ITR_TEXT))
        assert data.get('assessment_year') is not None

    def test_acknowledgement_number_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ITR_TEXT))
        ack = data.get('acknowledgement_number')
        assert ack is not None, "Acknowledgement number should be extracted"
        assert len(ack.replace(' ', '')) == 15, f"ACK number should be 15 digits, got: {ack}"

    def test_total_income_extracted(self):
        data, _ = normalize_result(self.extractor.extract(self.VALID_ITR_TEXT))
        assert data.get('total_income') is not None

    def test_missing_ack_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.MISSING_ACK_TEXT))
        assert data.get('acknowledgement_number') is None

    def test_returns_tuple(self):
        result = self.extractor.extract(self.VALID_ITR_TEXT)
        assert isinstance(result, tuple)

    def test_empty_returns_none(self):
        data, _ = normalize_result(self.extractor.extract(self.EMPTY_TEXT))
        assert data.get('pan') is None


# ============================================================
# CONFORMANCE TESTS — all extractors must return tuple + trace
# ============================================================
class TestExtractorConformance:
    """All 14 extractors must return (data_dict, trace_list) tuple"""

    SAMPLE_TEXT = "Sample text for conformance check. No meaningful content."

    def test_gst_returns_tuple(self):
        assert isinstance(GSTExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_pan_returns_tuple(self):
        result = PANExtractor().extract(self.SAMPLE_TEXT)
        # Currently returns dict — this test will FAIL and highlight the bug
        assert isinstance(result, tuple), "PANExtractor MUST return (data, trace) tuple"

    def test_udyam_returns_tuple(self):
        result = UdyamExtractor().extract(self.SAMPLE_TEXT)
        assert isinstance(result, tuple), "UdyamExtractor MUST return (data, trace) tuple"

    def test_turnover_returns_tuple(self):
        result = FinancialTurnoverExtractor().extract(self.SAMPLE_TEXT)
        assert isinstance(result, tuple), "FinancialTurnoverExtractor MUST return (data, trace) tuple"

    def test_oem_returns_tuple(self):
        result = OEMExtractor().extract(self.SAMPLE_TEXT)
        assert isinstance(result, tuple), "OEMExtractor MUST return (data, trace) tuple"

    def test_epfo_returns_tuple(self):
        assert isinstance(EPFOExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_esic_returns_tuple(self):
        assert isinstance(ESICExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_local_content_returns_tuple(self):
        result = LocalContentExtractor().extract(self.SAMPLE_TEXT)
        assert isinstance(result, tuple), "LocalContentExtractor MUST return (data, trace) tuple"

    def test_bis_returns_tuple(self):
        assert isinstance(BISExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_startup_returns_tuple(self):
        assert isinstance(StartupExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_nsic_returns_tuple(self):
        assert isinstance(NSICExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_company_inc_returns_tuple(self):
        result = CompanyIncorporationExtractor().extract(self.SAMPLE_TEXT)
        assert isinstance(result, tuple), "CompanyIncorporationExtractor MUST return (data, trace) tuple"

    def test_non_blacklisting_returns_tuple(self):
        assert isinstance(NonBlacklistingExtractor().extract(self.SAMPLE_TEXT), tuple)

    def test_itr_returns_tuple(self):
        assert isinstance(ITRExtractor().extract(self.SAMPLE_TEXT), tuple)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
