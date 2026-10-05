"""
ESIC Registration field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import ESICRegistrationData


class ESICExtractor(BaseExtractor):
    """
    Extract structured data from ESIC Registration Certificates.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['esic_registration_number', 'establishment_name', 'registration_date', 'address', 'status']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. ESIC Registration Number (usually 17 digits)
        esic_num = self.extract_pattern(text, r'\b\d{17}\b', group=0)
        if not esic_num:
            esic_num = self.extract_pattern(text, r'(?:esic\s*(?:registration|code|number|no)?[:\s]*)([A-Z0-9\-/]{10,20})')
        trace.append(self.make_trace('esic_registration_number', esic_num, 'esic_pattern'))

        # 2. Establishment Name
        establishment_name = self.extract_pattern(text, r'(?:establishment\s+name|name\s+of\s+establishment|employer\s+name|unit\s+name)[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|address|date|status|\Z)')
        trace.append(self.make_trace('establishment_name', establishment_name, 'label_based_regex'))

        # 3. Registration Date
        reg_date = self.extract_date(
            text,
            ['date of registration', 'registration date', 'date of coverage', 'coverage date', 'effective date', 'date']
        )
        trace.append(self.make_trace('registration_date', reg_date, 'extract_date'))

        # 4. Address
        address = self.extract_field_aware(
            text,
            [r'address\s+of\s+establishment', r'establishment\s+address', r'address'],
            ['esic', 'code', 'date', 'status', 'registration', 'name', 'phone', 'email']
        )
        trace.append(self.make_trace('address', address, 'field_aware'))

        # 5. Status
        status = None
        text_lower = text.lower()
        if 'active' in text_lower or 'covered' in text_lower or 'registered' in text_lower:
            status = 'ACTIVE'
        elif 'cancelled' in text_lower or 'in-active' in text_lower:
            status = 'INACTIVE'
        trace.append(self.make_trace('status', status, 'status_heuristic'))

        result = {
            'esic_registration_number': esic_num,
            'establishment_name': establishment_name,
            'registration_date': reg_date,
            'address': address,
            'status': status,
        }
        return result, trace
