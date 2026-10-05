"""
Udyam Verification Provider (Sandbox Mode)

In production, this would integrate with Udyam Registration Portal API.
Currently operates in SANDBOX mode with demo data.
"""
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider
from .sandbox_provider import SandboxProvider

class UdyamProvider(BaseVerificationProvider):
    """
    Udyam (MSME) Verification Provider

    MODE: SANDBOX (No live Udyam API credentials configured)

    In production, this would connect to:
    - Udyam Registration Portal (https://udyamregistration.gov.in)
    """

    def __init__(self):
        super().__init__()
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "UdyamProvider"
        self.sandbox = SandboxProvider()

    def verify(self, udyam_number: str, document_type: str = "UDYAM_CERTIFICATE") -> Dict[str, Any]:
        """
        Verify Udyam registration number.

        Args:
            udyam_number: Udyam registration number
            document_type: Should be UDYAM_CERTIFICATE

        Returns:
            Verification result with Udyam details
        """
        if self.mode == VerificationSourceMode.SANDBOX:
            result = self.sandbox.verify(udyam_number, document_type)
            result['provider'] = self.provider_name
            return result

        return {
            'found': False,
            'data': None,
            'mode': self.mode.value,
            'provider': self.provider_name,
            'message': 'Live Udyam API not configured'
        }

    def get_status(self) -> Dict[str, Any]:
        """Get Udyam provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'Udyam/MSME verification provider (SANDBOX MODE - demo data only)',
            'supported_checks': ['UDYAM-001']
        }
