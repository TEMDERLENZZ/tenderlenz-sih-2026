"""
PAN Verification Provider (Sandbox Mode)

In production, this would integrate with Income Tax Department PAN verification API.
Currently operates in SANDBOX mode with demo data.
"""
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider
from .sandbox_provider import SandboxProvider

class PANProvider(BaseVerificationProvider):
    """
    PAN Verification Provider

    MODE: SANDBOX (No live PAN API credentials configured)

    In production, this would connect to:
    - Income Tax Department PAN Verification API
    - NSDL PAN Verification Service
    """

    def __init__(self):
        super().__init__()
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "PANProvider"
        self.sandbox = SandboxProvider()

    def verify(self, pan: str, document_type: str = "PAN_CARD") -> Dict[str, Any]:
        """
        Verify PAN against Income Tax records.

        Args:
            pan: 10-character PAN
            document_type: Should be PAN_CARD

        Returns:
            Verification result with PAN details
        """
        if self.mode == VerificationSourceMode.SANDBOX:
            result = self.sandbox.verify(pan, document_type)
            result['provider'] = self.provider_name
            return result

        return {
            'found': False,
            'data': None,
            'mode': self.mode.value,
            'provider': self.provider_name,
            'message': 'Live PAN API not configured'
        }

    def get_status(self) -> Dict[str, Any]:
        """Get PAN provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'PAN verification provider (SANDBOX MODE - demo data only)',
            'supported_checks': ['PAN-001']
        }
