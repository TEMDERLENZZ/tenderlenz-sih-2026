"""
Base Verification Provider Interface
All verification providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.verification import VerificationSourceMode

class BaseVerificationProvider(ABC):
    """
    Abstract base class for all verification providers.

    Providers can be:
    - LIVE: Connected to real government APIs
    - SANDBOX: Using realistic demo data
    - DEMO: Using simplified test data
    - UNAVAILABLE: Provider not configured
    """

    def __init__(self):
        self.mode: VerificationSourceMode = VerificationSourceMode.UNAVAILABLE
        self.provider_name: str = "BaseProvider"

    @abstractmethod
    def verify(self, identifier: str, document_type: str) -> Dict[str, Any]:
        """
        Verify an identifier against the external source.

        Args:
            identifier: The value to verify (GSTIN, PAN, etc.)
            document_type: Type of document being verified

        Returns:
            {
                'found': bool,
                'data': dict or None,
                'mode': VerificationSourceMode,
                'provider': str,
                'message': str
            }
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get provider status and availability.

        Returns:
            {
                'provider_name': str,
                'mode': VerificationSourceMode,
                'available': bool,
                'description': str,
                'supported_checks': List[str]
            }
        """
        pass

    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.mode != VerificationSourceMode.UNAVAILABLE
