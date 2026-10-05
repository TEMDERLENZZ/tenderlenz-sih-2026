"""
GST Verification Provider (Sandbox Mode)

In production, this would integrate with the official GST API.
Currently operates in SANDBOX mode with demo data.
"""
from typing import Dict, Any
from app.models.verification import VerificationSourceMode
from .base_provider import BaseVerificationProvider
from .sandbox_provider import SandboxProvider

class GSTProvider(BaseVerificationProvider):
    """
    GST Verification Provider

    MODE: SANDBOX (No live GST API credentials configured)

    In production, this would connect to:
    - GST Portal API (https://api.gst.gov.in)
    - Requires authentication and API key
    """

    def __init__(self):
        super().__init__()
        # Check if LIVE credentials are available
        # For now, always use SANDBOX mode
        self.mode = VerificationSourceMode.SANDBOX
        self.provider_name = "GSTProvider"
        self.sandbox = SandboxProvider()

    def verify(self, gstin: str, document_type: str = "GST_CERTIFICATE") -> Dict[str, Any]:
        """
        Verify GSTIN against GST records.

        Args:
            gstin: 15-character GSTIN
            document_type: Should be GST_CERTIFICATE

        Returns:
            Verification result with GST details
        """
        # In SANDBOX mode, delegate to sandbox provider
        if self.mode == VerificationSourceMode.SANDBOX:
            result = self.sandbox.verify(gstin, document_type)
            result['provider'] = self.provider_name
            return result

        # LIVE mode would go here
        # response = requests.post("https://api.gst.gov.in/verify", ...)
        # return parsed response

        return {
            'found': False,
            'data': None,
            'mode': self.mode.value,
            'provider': self.provider_name,
            'message': 'Live GST API not configured'
        }

    def get_status(self) -> Dict[str, Any]:
        """Get GST provider status"""
        return {
            'provider_name': self.provider_name,
            'mode': self.mode.value,
            'available': True,
            'description': 'GST verification provider (SANDBOX MODE - demo data only)',
            'supported_checks': ['GST-001', 'GST-002', 'GST-003']
        }
