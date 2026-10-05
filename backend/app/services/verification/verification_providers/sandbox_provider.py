"""
Sandbox Verification Provider - Realistic Demo Data & External API Integration

Integrates with TenderVerify Sandbox API (http://localhost:8001) if available,
with automatic fallback to local demonstration dataset.
"""
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider

SANDBOX_API_BASE_URL = os.getenv("SANDBOX_API_BASE_URL", "http://localhost:8001")

# ============================================================
# SANDBOX DATA - Realistic sample records for fallback demonstration
# ============================================================

SANDBOX_GST_DATA = {
    "33DEMO1234F1Z5": {
        "gstin": "33DEMO1234F1Z5",
        "legal_name": "ABC Technologies Pvt Ltd",
        "trade_name": "ABC Technologies",
        "status": "ACTIVE",
        "registration_date": "15-Apr-2021",
        "state": "Tamil Nadu",
        "state_code": "33"
    },
    "33AXMPS1015Q2Z2": {
        "gstin": "33AXMPS1015Q2Z2",
        "legal_name": "SASIKUMAR",
        "trade_name": "VIVID TRADERS",
        "status": "ACTIVE",
        "registration_date": "22/05/2025",
        "state": "Tamil Nadu",
        "state_code": "33"
    },
    "27AABCU9603R1ZM": {
        "gstin": "27AABCU9603R1ZM",
        "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "trade_name": "ABC TECH",
        "status": "ACTIVE",
        "registration_date": "01/07/2017",
        "state": "Maharashtra",
        "state_code": "27"
    }
}

SANDBOX_PAN_DATA = {
    "DEMOA1234F": {
        "pan": "DEMOA1234F",
        "name": "ABC Technologies Pvt Ltd",
        "category": "Company",
        "status": "ACTIVE"
    },
    "AXMPS1015Q": {
        "pan": "AXMPS1015Q",
        "name": "SASIKUMAR",
        "category": "Individual",
        "status": "ACTIVE"
    },
    "AABCU9603R": {
        "pan": "AABCU9603R",
        "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "category": "Company",
        "status": "ACTIVE"
    }
}

SANDBOX_UDYAM_DATA = {
    "UDYAM-TN-03-0012345": {
        "udyam_number": "UDYAM-TN-03-0012345",
        "enterprise_name": "ABC Technologies Pvt Ltd",
        "enterprise_type": "Small",
        "status": "ACTIVE",
        "registration_date": "20-May-2021",
        "pan": "DEMOA1234F",
        "state": "Tamil Nadu"
    },
    "UDYAM-TN-01-0012345": {
        "udyam_number": "UDYAM-TN-01-0012345",
        "enterprise_name": "SASIKUMAR",
        "enterprise_type": "Micro",
        "status": "ACTIVE",
        "registration_date": "15/03/2024",
        "pan": "AXMPS1015Q",
        "state": "Tamil Nadu"
    }
}

SANDBOX_MCA_DATA = {
    "U72900TN2021PTC012345": {
        "cin": "U72900TN2021PTC012345",
        "company_name": "ABC Technologies Private Limited",
        "registration_date": "15-Apr-2021",
        "status": "ACTIVE",
        "company_class": "Private",
        "state": "Tamil Nadu"
    },
    "U74999MH2015PTC123456": {
        "cin": "U74999MH2015PTC123456",
        "company_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
        "registration_date": "15/06/2015",
        "status": "ACTIVE",
        "company_class": "Private",
        "state": "Maharashtra"
    }
}

SANDBOX_BANK_DATA = {
    "BANK-TN-2024-001": {
        "identifier": "BANK-TN-2024-001",
        "account_name": "ABC Technologies Pvt Ltd",
        "bank_name": "State Bank of India",
        "ifsc_code": "SBIN0001234",
        "account_type": "CURRENT",
        "solvency_amount": 10000000.0,
        "status": "ACTIVE",
        "verified": True
    },
    "SBIN0001234": {
        "identifier": "BANK-TN-2024-001",
        "account_name": "ABC Technologies Pvt Ltd",
        "bank_name": "State Bank of India",
        "ifsc_code": "SBIN0001234",
        "account_type": "CURRENT",
        "solvency_amount": 10000000.0,
        "status": "ACTIVE",
        "verified": True
    }
}

SANDBOX_BIS_DATA = {
    "BIS-CERT-2024-12345": {
        "certificate_number": "BIS-CERT-2024-12345",
        "license_number": "CM/L-1234567",
        "grantee_name": "ABC Technologies Pvt Ltd",
        "status": "ACTIVE",
        "verified": True
    }
}

SANDBOX_ITR_DATA = {
    "ITR-ACK-2024-001234": {
        "acknowledgement_number": "ITR-ACK-2024-001234",
        "pan": "DEMOA1234F",
        "assessment_year": "2024-25",
        "status": "FILED",
        "verified": True
    },
    "DEMOA1234F": {
        "acknowledgement_number": "ITR-ACK-2024-001234",
        "pan": "DEMOA1234F",
        "assessment_year": "2024-25",
        "status": "FILED",
        "verified": True
    }
}

SANDBOX_STARTUP_DATA = {
    "DPIIT-STARTUP-2023-12345": {
        "certificate_number": "DPIIT-STARTUP-2023-12345",
        "entity_name": "ABC Technologies Pvt Ltd",
        "recognition_number": "DPIIT12345",
        "status": "RECOGNIZED",
        "verified": True
    }
}

SANDBOX_NSIC_DATA = {
    "NSIC-TN-2022-12345": {
        "registration_number": "NSIC-TN-2022-12345",
        "unit_name": "ABC Technologies Pvt Ltd",
        "status": "ACTIVE",
        "verified": True
    }
}

SANDBOX_OEM_DATA = {
    "OEM-AUTH-2024-1234": {
        "authorization_number": "OEM-AUTH-2024-1234",
        "oem_name": "Global Tech Corp",
        "authorized_bidder": "ABC Technologies Pvt Ltd",
        "status": "VALID",
        "verified": True
    }
}

SANDBOX_TURNOVER_DATA = {
    "FTC-2024-001234": {
        "certificate_number": "FTC-2024-001234",
        "bidder_name": "ABC Technologies Pvt Ltd",
        "average_turnover": 50000000.0,
        "status": "VERIFIED",
        "verified": True
    }
}

SANDBOX_NON_BLACKLISTING_DATA = {
    "NBL-DECL-2024-001234": {
        "declaration_number": "NBL-DECL-2024-001234",
        "bidder_name": "ABC Technologies Pvt Ltd",
        "blacklisted": False,
        "status": "CLEAN",
        "verified": True
    }
}

SANDBOX_LOCAL_CONTENT_DATA = {
    "LCD-2024-001234": {
        "declaration_number": "LCD-2024-001234",
        "bidder_name": "ABC Technologies Pvt Ltd",
        "local_content_percentage": 65.0,
        "status": "COMPLIANT",
        "verified": True
    }
}

SANDBOX_COMPLIANCE_DATA = {
    "COMP-2024-001": {
        "identifier": "COMP-2024-001",
        "bidder_name": "ABC Technologies Pvt Ltd",
        "status": "COMPLIANT",
        "verified": True
    }
}

ENDPOINT_ROUTE_MAP = {
    "GST": "/api/gst/",
    "PAN": "/api/pan/",
    "UDYAM": "/api/udyam/",
    "MCA": "/api/mca/",
    "BANK": "/api/bank/",
    "BIS": "/api/bis/",
    "ITR": "/api/itr/",
    "STARTUP": "/api/startup/",
    "NSIC": "/api/nsic/",
    "OEM": "/api/oem/",
    "TURNOVER": "/api/turnover/",
    "NON_BLACKLISTING": "/api/non-blacklisting/",
    "LOCAL_CONTENT": "/api/local-content/",
    "COMPLIANCE": "/api/compliance/"
}


class SandboxProvider(BaseVerificationProvider):
    """
    Sandbox provider with TenderVerify API integration and local dataset fallback.
    Supports all 14 verification categories.
    """

    def __init__(self):
        super().__init__()
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "SandboxProvider"
        self.api_base_url = SANDBOX_API_BASE_URL.rstrip('/')
        self.data_sources = {
            "GST": SANDBOX_GST_DATA,
            "PAN": SANDBOX_PAN_DATA,
            "UDYAM": SANDBOX_UDYAM_DATA,
            "MCA": SANDBOX_MCA_DATA,
            "BANK": SANDBOX_BANK_DATA,
            "BIS": SANDBOX_BIS_DATA,
            "ITR": SANDBOX_ITR_DATA,
            "STARTUP": SANDBOX_STARTUP_DATA,
            "NSIC": SANDBOX_NSIC_DATA,
            "OEM": SANDBOX_OEM_DATA,
            "TURNOVER": SANDBOX_TURNOVER_DATA,
            "NON_BLACKLISTING": SANDBOX_NON_BLACKLISTING_DATA,
            "LOCAL_CONTENT": SANDBOX_LOCAL_CONTENT_DATA,
            "COMPLIANCE": SANDBOX_COMPLIANCE_DATA
        }

    def _query_external_sandbox_api(self, source: str, identifier: str) -> Dict[str, Any] | None:
        """Attempt to fetch verification result from TenderVerify Sandbox REST API"""
        route = ENDPOINT_ROUTE_MAP.get(source)
        if not route:
            return None

        url = f"{self.api_base_url}{route}{identifier}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TenderComplianceCopilot/1.0'})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode('utf-8'))
                    if payload.get("success") and payload.get("data"):
                        return payload.get("data")
        except Exception:
            # Fall back to local mock dictionary silently if API is offline/unreachable
            pass
        return None

    def verify(self, identifier: str, document_type: str) -> Dict[str, Any]:
        """
        Verify identifier against TenderVerify Sandbox API or fallback local dataset.

        Args:
            identifier: Primary key / identifier string
            document_type: Category of document

        Returns:
            Verification result standard structure
        """
        identifier = identifier.strip().upper() if identifier else ""

        source_map = {
            "GST_CERTIFICATE": "GST",
            "PAN_CARD": "PAN",
            "UDYAM_CERTIFICATE": "UDYAM",
            "COMPANY_INCORPORATION": "MCA",
            "BANK_CERTIFICATE": "BANK",
            "BANK_SOLVENCY": "BANK",
            "BANK": "BANK",
            "BIS_CERTIFICATE": "BIS",
            "INCOME_TAX_RETURN": "ITR",
            "STARTUP_CERTIFICATE": "STARTUP",
            "NSIC_CERTIFICATE": "NSIC",
            "OEM_AUTHORIZATION": "OEM",
            "FINANCIAL_TURNOVER_CERTIFICATE": "TURNOVER",
            "NON_BLACKLISTING_DECLARATION": "NON_BLACKLISTING",
            "LOCAL_CONTENT_DECLARATION": "LOCAL_CONTENT",
            "COMPLIANCE": "COMPLIANCE"
        }

        source = source_map.get(document_type, document_type.upper())
        if source not in self.data_sources:
            return {
                'found': False,
                'data': None,
                'mode': self.mode.value,
                'provider': self.provider_name,
                'message': f"Document type {document_type} not supported by sandbox"
            }

        # 1. Try Live TenderVerify REST API first
        api_record = self._query_external_sandbox_api(source, identifier)
        if api_record:
            return {
                'found': True,
                'data': api_record,
                'mode': self.mode.value,
                'provider': "TenderVerify Sandbox API",
                'message': f"Record verified via TenderVerify Sandbox API ({source})"
            }

        # 2. Fallback to local dataset
        data_source = self.data_sources.get(source, {})
        record = data_source.get(identifier)

        if not record:
            # Fuzzy fallback matching for company name or partial identifiers in dataset
            for key, rec in data_source.items():
                if identifier in key or key in identifier:
                    record = rec
                    break

        if record:
            return {
                'found': True,
                'data': record,
                'mode': self.mode.value,
                'provider': self.provider_name,
                'message': f"Record found in local sandbox dataset ({source})"
            }
        else:
            return {
                'found': False,
                'data': None,
                'mode': self.mode.value,
                'provider': self.provider_name,
                'message': f"Identifier '{identifier}' not found in sandbox data"
            }

    def get_status(self) -> Dict[str, Any]:
        """Get sandbox provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'TenderVerify Sandbox Provider (External REST API & local dataset)',
            'supported_checks': list(ENDPOINT_ROUTE_MAP.keys())
        }
