"""
EPFO Registration field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import EPFORegistrationData


class EPFOExtractor(BaseExtractor):
    """Extract structured data from EPFO Registration Certificate"""

    REQUIRED_FIELDS = ['establishment_id', 'establishment_name', 'registration_date']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract EPFO registration fields"""
        trace: List[Dict[str, Any]] = []

        data = EPFORegistrationData()

        # Extract Establishment ID (PF code format: XX/XXXXX/NNN or similar)
        est_id_val = self.extract_pattern(text, r'\b[A-Z]{2}/[A-Z]+/\d+(?:/\d+)?\b', group=0)
        if not est_id_val:
            est_id_val = self.extract_pattern(text, r'establishment\s+(?:id|code|number)\s*[:\-]?\s*([\w/]+)', group=1)
        if est_id_val:
            data.establishment_id = est_id_val
        trace.append(self.make_trace('establishment_id', data.establishment_id, 'establishment_id_regex'))

        # Extract establishment name
        name_patterns = [
            r'(?:establishment\s+name|name\s+of\s+establishment|employer\s+name)[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|address|date|\Z)',
            r'(?:m/s\.?|name)[:\s]*([A-Za-z0-9\s.&]+?)(?:\n|pvt|private|limited)',
        ]
        for pat in name_patterns:
            val = self.extract_pattern(text, pat)
            if val and len(val) > 3:
                data.establishment_name = val
                break
        trace.append(self.make_trace('establishment_name', data.establishment_name, 'label_based_regex'))

        # Extract registration date
        data.registration_date = self.extract_date(text, [
            'date of registration',
            'registration date',
            'coverage date',
            'date of coverage',
            'effective date',
        ])
        trace.append(self.make_trace('registration_date', data.registration_date, 'extract_date'))

        # Extract address
        addr_pat = r'(?:address|registered\s+address)[:\s]*([^\n]+(?:\n[^\n]+){0,3}?)(?:\n\n|state|pin|$)'
        val = self.extract_pattern(text, addr_pat)
        if val:
            data.address = self.normalize_value(re.sub(r'\s*\n\s*', ', ', val))
        trace.append(self.make_trace('address', data.address, 'address_block'))

        # Status
        text_lower = text.lower()
        if 'active' in text_lower or 'compliant' in text_lower:
            data.status = 'ACTIVE'
        elif 'inactive' in text_lower or 'deregistered' in text_lower:
            data.status = 'INACTIVE'
        trace.append(self.make_trace('status', data.status, 'keyword_status'))

        result = {k: v for k, v in data.model_dump().items()}
        return result, trace

