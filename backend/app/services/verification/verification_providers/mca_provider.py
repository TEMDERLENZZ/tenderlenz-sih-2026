"""
MCA (Ministry of Corporate Affairs) Verification Provider (Sandbox Mode)

In production, this would integrate with MCA21 API.
Currently operates in SANDBOX mode with demo data.
"""
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider
from .sandbox_provider import SandboxProvider

class MCAProvider(BaseVerificationProvider):
    """
    MCA Verification Provider

    MODE: SANDBOX (No live MCA API credentials configured)

    In production, this would connect to:
    - MCA21 API (Ministry of Corporate Affairs)
    - Company registration verification
    """

    def __init__(self):
        super().__init__()
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "MCAProvider"
        self.sandbox = SandboxProvider()

    def verify(self, cin: str, document_type: str = "COMPANY_INCORPORATION") -> Dict[str, Any]:
        """
        Verify CIN (Corporate Identification Number).

        Args:
            cin: 21-character CIN
            document_type: Should be COMPANY_INCORPORATION

        Returns:
            Verification result with company details
        """
        if self.mode == VerificationSourceMode.SANDBOX:
            result = self.sandbox.verify(cin, document_type)
            result['provider'] = self.provider_name
            return result

        return {
            'found': False,
            'data': None,
            'mode': self.mode.value,
            'provider': self.provider_name,
            'message': 'Live MCA API not configured'
        }

    def get_status(self) -> Dict[str, Any]:
        """Get MCA provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'MCA company verification provider (SANDBOX MODE - demo data only)',
            'supported_checks': ['MCA-001']
        }
