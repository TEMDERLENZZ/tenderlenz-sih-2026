"""
Bank / Financial Solvency Verification Provider (Sandbox Mode)

Integrates with TenderVerify Sandbox Provider for Bank Account & Solvency verification.
"""
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider
from .sandbox_provider import SandboxProvider

class BankProvider(BaseVerificationProvider):
    """
    Bank Verification Provider
    MODE: SANDBOX (TenderVerify Sandbox Provider)
    """

    def __init__(self):
        super().__init__()
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "BankProvider"
        self.sandbox = SandboxProvider()

    def verify(self, identifier: str, document_type: str = "BANK_CERTIFICATE") -> Dict[str, Any]:
        """
        Verify Bank details / Solvency certificate reference.
        """
        result = self.sandbox.verify(identifier, document_type)
        result['provider'] = self.provider_name
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get Bank provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'Bank / Financial Solvency provider (SANDBOX MODE)',
            'supported_checks': ['BANK-001', 'BANK-002']
        }
