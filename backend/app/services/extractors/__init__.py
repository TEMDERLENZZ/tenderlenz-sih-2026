"""
Document extractors package
Maps document types to their extractors
"""
from .base_extractor import BaseExtractor
from .gst_extractor import GSTExtractor
from .financial_turnover_extractor import FinancialTurnoverExtractor
from .oem_extractor import OEMExtractor
from .pan_extractor import PANExtractor
from .udyam_extractor import UdyamExtractor
from .company_incorporation_extractor import CompanyIncorporationExtractor
from .local_content_extractor import LocalContentExtractor
from .epfo_extractor import EPFOExtractor
from .esic_extractor import ESICExtractor
from .bis_extractor import BISExtractor
from .startup_extractor import StartupExtractor
from .nsic_extractor import NSICExtractor
from .non_blacklisting_extractor import NonBlacklistingExtractor
from .itr_extractor import ITRExtractor

from app.models.document import DocumentType

# Map document types to extractor classes
EXTRACTOR_MAP = {
    DocumentType.GST_CERTIFICATE: GSTExtractor,
    DocumentType.FINANCIAL_TURNOVER_CERTIFICATE: FinancialTurnoverExtractor,
    DocumentType.OEM_AUTHORIZATION: OEMExtractor,
    DocumentType.PAN_CARD: PANExtractor,
    DocumentType.UDYAM_CERTIFICATE: UdyamExtractor,
    DocumentType.COMPANY_INCORPORATION: CompanyIncorporationExtractor,
    DocumentType.LOCAL_CONTENT_DECLARATION: LocalContentExtractor,
    DocumentType.EPFO_REGISTRATION: EPFOExtractor,
    DocumentType.ESIC_REGISTRATION: ESICExtractor,
    DocumentType.BIS_CERTIFICATE: BISExtractor,
    DocumentType.STARTUP_CERTIFICATE: StartupExtractor,
    DocumentType.NSIC_CERTIFICATE: NSICExtractor,
    DocumentType.NON_BLACKLISTING_DECLARATION: NonBlacklistingExtractor,
    DocumentType.INCOME_TAX_RETURN: ITRExtractor,
}

def get_extractor(document_type: DocumentType) -> BaseExtractor:
    """
    Get appropriate extractor for document type

    Args:
        document_type: Type of document

    Returns:
        Instance of extractor class

    Raises:
        NotImplementedError: If extractor not yet implemented
    """
    extractor_class = EXTRACTOR_MAP.get(document_type)

    if extractor_class is None:
        raise NotImplementedError(f"Extractor for {document_type.value} not yet implemented")

    return extractor_class()
