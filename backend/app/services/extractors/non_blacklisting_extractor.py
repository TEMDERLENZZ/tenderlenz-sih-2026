"""
Non-Blacklisting Declaration field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import NonBlacklistingDeclarationData


class NonBlacklistingExtractor(BaseExtractor):
    """
    Extract structured data from Non-Blacklisting Declarations / Affidavits.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['bidder_name', 'declaration_date', 'declaration_statement', 'signatory_name', 'signatory_designation']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. Bidder / Company Name
        bidder_name = self.extract_pattern(text, r'(?:we|i)[,\s]+(?:m/s\.?\s+)?([A-Za-z0-9\s.&]+?)[,\s]+(?:hereby|declare)')
        if not bidder_name:
            bidder_name = self.extract_pattern(text, r'(?:company|firm|bidder|name)[:\s]*(?:m/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)')
        trace.append(self.make_trace('bidder_name', bidder_name, 'label_based_regex'))

        # 2. Declaration Date
        declaration_date = self.extract_date(
            text,
            ['dated', 'date', 'declaration date', 'signed on', 'executed on']
        )
        trace.append(self.make_trace('declaration_date', declaration_date, 'extract_date'))

        # 3. Declaration Statement
        statement = None
        match = re.search(
            r'(not\s+been\s+blacklisted[^\n.]{10,200}|have\s+not\s+been\s+debarred[^\n.]{10,200}|never\s+been\s+blacklisted[^\n.]{10,200})',
            text,
            re.IGNORECASE
        )
        if match:
            statement = self.normalize_value(match.group(1))
        trace.append(self.make_trace('declaration_statement', statement, 'statement_regex'))

        # 4. Signatory Name
        signatory_name = self.extract_field_aware(
            text,
            [r'for\s+and\s+on\s+behalf\s+of', r'authorised\s+signatory', r'signatory\s+name', r'name\s+of\s+signatory', r'deponent', r'signature'],
            ['designation', 'date', 'place', 'seal', 'stamp']
        )
        trace.append(self.make_trace('signatory_name', signatory_name, 'field_aware'))

        # 5. Signatory Designation
        signatory_designation = self.extract_field_aware(
            text,
            [r'designation', r'capacity', r'title'],
            ['date', 'place', 'seal', 'stamp', 'signature', 'name']
        )
        trace.append(self.make_trace('signatory_designation', signatory_designation, 'field_aware'))

        result = {
            'bidder_name': bidder_name,
            'declaration_date': declaration_date,
            'declaration_statement': statement,
            'signatory_name': signatory_name,
            'signatory_designation': signatory_designation,
        }
        return result, trace
