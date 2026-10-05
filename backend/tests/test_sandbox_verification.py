"""
Unit tests for expanded SandboxProvider & BankProvider (Phase 2 Verification Engine)
"""
import pytest
from app.services.verification.verification_providers import (
    SandboxProvider,
    BankProvider,
    GSTProvider,
    PANProvider,
    UdyamProvider,
    MCAProvider
)
from app.models.verification import VerificationSourceMode


def test_sandbox_provider_status():
    provider = SandboxProvider()
    status = provider.get_status()
    assert status['mode'] == 'SANDBOX'
    assert status['available'] is True
    assert 'BANK' in status['supported_checks']
    assert 'BIS' in status['supported_checks']
    assert len(status['supported_checks']) == 14


def test_sandbox_provider_all_14_categories():
    provider = SandboxProvider()

    test_cases = [
        ("GST_CERTIFICATE", "33DEMO1234F1Z5", "ABC Technologies Pvt Ltd"),
        ("PAN_CARD", "DEMOA1234F", "ABC Technologies Pvt Ltd"),
        ("UDYAM_CERTIFICATE", "UDYAM-TN-03-0012345", "ABC Technologies Pvt Ltd"),
        ("COMPANY_INCORPORATION", "U72900TN2021PTC012345", "ABC Technologies Private Limited"),
        ("BANK_CERTIFICATE", "BANK-TN-2024-001", "ABC Technologies Pvt Ltd"),
        ("BIS_CERTIFICATE", "BIS-CERT-2024-12345", "ABC Technologies Pvt Ltd"),
        ("INCOME_TAX_RETURN", "ITR-ACK-2024-001234", "DEMOA1234F"),
        ("STARTUP_CERTIFICATE", "DPIIT-STARTUP-2023-12345", "ABC Technologies Pvt Ltd"),
        ("NSIC_CERTIFICATE", "NSIC-TN-2022-12345", "ABC Technologies Pvt Ltd"),
        ("OEM_AUTHORIZATION", "OEM-AUTH-2024-1234", "ABC Technologies Pvt Ltd"),
        ("FINANCIAL_TURNOVER_CERTIFICATE", "FTC-2024-001234", "ABC Technologies Pvt Ltd"),
        ("NON_BLACKLISTING_DECLARATION", "NBL-DECL-2024-001234", "ABC Technologies Pvt Ltd"),
        ("LOCAL_CONTENT_DECLARATION", "LCD-2024-001234", "ABC Technologies Pvt Ltd"),
        ("COMPLIANCE", "COMP-2024-001", "ABC Technologies Pvt Ltd"),
    ]

    for doc_type, identifier, expected_substring in test_cases:
        res = provider.verify(identifier, doc_type)
        assert res['found'] is True, f"Failed for {doc_type} with identifier {identifier}"
        assert res['data'] is not None
        assert res['mode'] == 'SANDBOX'


def test_bank_provider():
    bank_provider = BankProvider()
    status = bank_provider.get_status()
    assert status['provider_name'] == 'BankProvider'
    assert status['mode'] == 'SANDBOX'

    res = bank_provider.verify("BANK-TN-2024-001", "BANK_CERTIFICATE")
    assert res['found'] is True
    assert res['data']['account_name'] in ["ABC Technologies Pvt Ltd", "SASIKUMAR"]
    assert res['data']['bank_name'] == "State Bank of India"
    assert res['data']['solvency_amount'] in [10000000.0, 50000000.0]


def test_sandbox_provider_not_found():
    provider = SandboxProvider()
    res = provider.verify("NON_EXISTENT_12345", "GST_CERTIFICATE")
    assert res['found'] is False
    assert res['data'] is None
