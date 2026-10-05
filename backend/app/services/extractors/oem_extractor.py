"""
OEM Authorization field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import OEMAuthorizationData

class OEMExtractor(BaseExtractor):
    """Extract structured data from OEM Authorization"""

    REQUIRED_FIELDS = ['oem_name', 'authorized_bidder_name', 'expiry_date']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract OEM authorization fields"""
        trace: List[Dict[str, Any]] = []
        data = OEMAuthorizationData()

        # Extract OEM name
        oem_patterns = [
            r'oem\s+name\s*[:\-]?\s*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'manufacturer\s+name\s*[:\-]?\s*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'name\s+of\s+(?:oem|manufacturer)\s*[:\-]?\s*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'(?:we|hereby)[,\s]+([A-Za-z0-9\s.&]+?)[,\s]+(?:hereby\s+)?authorize'
        ]
        for pattern in oem_patterns:
            result, oem_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and len(result.strip()) > 2 and result.strip().lower() not in ['authorization', 'authorization letter']:
                data.oem_name = result.strip()
                break
        trace.append(self.make_trace('oem_name', data.oem_name, 'oem_name_regex', evidence=oem_ev if data.oem_name else None))

        # Extract authorized bidder
        bidder_patterns = [
            r'authorized\s+bidder\s*[:\-]?\s*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'bidder\s*[:\-]?\s*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'(?:authorize|authorized)\s+(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\s+to|\n|,|\Z)',
            r'(?:authorized dealer|authorized partner)[:\s]*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+)'
        ]
        bidder_ev = None
        for pattern in bidder_patterns:
            result, bidder_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and result.strip().lower() != (data.oem_name or '').lower() and len(result.strip()) > 2:
                data.authorized_bidder_name = result.strip()
                break
        trace.append(self.make_trace('authorized_bidder_name', data.authorized_bidder_name, 'bidder_name_regex', evidence=bidder_ev if data.authorized_bidder_name else None))

        # Extract product name
        product_patterns = [
            r'(?:supply|supplying|sale)\s+of\s+([A-Za-z0-9\s.&]+?)(?:\.|\n|,|\Z)',
            r'(?:product|products|equipment)[:\s]*([A-Za-z0-9\s.&\d]+?)(?:\n|,|\Z)'
        ]
        for pattern in product_patterns:
            result = self.extract_pattern(text, pattern)
            if result:
                data.product_name = result
                break
        trace.append(self.make_trace('product_name', data.product_name, 'product_name_regex'))

        # Extract authorization date
        data.authorization_date = self.extract_date(text, [
            'authorization date',
            'date of authorization',
            'issued on',
            'dated',
            'issue date'
        ])
        trace.append(self.make_trace('authorization_date', data.authorization_date, 'extract_date'))

        # Extract expiry date
        data.expiry_date = self.extract_date(text, [
            'valid till',
            'valid upto',
            'expiry date',
            'expires on'
        ])
        trace.append(self.make_trace('expiry_date', data.expiry_date, 'extract_date'))

        # Extract authorization number
        auth_num_pattern = r'(?:authorization|certificate|letter)\s+(?:no|number|code)?[:\s]*([\w/-]+)'
        data.authorization_number = self.extract_pattern(text, auth_num_pattern)
        trace.append(self.make_trace('authorization_number', data.authorization_number, 'auth_num_regex'))

        # Determine status
        if data.expiry_date or 'valid' in text.lower():
            if 'expired' in text.lower():
                data.status = 'EXPIRED'
            else:
                data.status = 'VALID'
        trace.append(self.make_trace('status', data.status, 'status_keyword'))

        # Extract scope
        scope_pattern = r'(?:scope|purpose)[:\s]*(.{50,200}?)(?:\n\n|$)'
        data.scope = self.extract_pattern(text, scope_pattern)
        trace.append(self.make_trace('scope', data.scope, 'scope_regex'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

