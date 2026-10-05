"""
BIS Certificate field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import BISCertificateData


class BISExtractor(BaseExtractor):
    """
    Extract structured data from BIS (Bureau of Indian Standards) Certificates.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['license_number', 'licensee_name', 'product_name', 'is_standard', 'date_of_grant', 'valid_upto', 'status']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. License / Registration Number (e.g. CM/L-1234567 or BIS-DEMO-2026-00125)
        lic_num, lic_ev = self.extract_pattern_with_evidence(text, r'(?:certificate\s+no|licence|license|registration)\s*(?:no|number)?[:\s]*([A-Z0-9\-/]+)', group=1)
        if not lic_num:
            lic_num, lic_ev = self.extract_pattern_with_evidence(text, r'\b(?:CM/L|R|BIS-DEMO)-[A-Z0-9\-/]+\b', group=0)
        trace.append(self.make_trace('license_number', lic_num, 'license_pattern', evidence=lic_ev if lic_num else None))

        # 2. Licensee Name
        licensee_name, l_ev = self.extract_pattern_with_evidence(text, r'(?:manufacturer|name\s+of\s+licensee|licensee\s+name|granted\s+to)[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|product|standard|date|\Z)', group=1)
        trace.append(self.make_trace('licensee_name', licensee_name, 'label_based_regex', evidence=l_ev if licensee_name else None))

        # 3. Product Name
        product_name = self.extract_pattern(text, r'(?:product\s+name|name\s+of\s+product|product|commodity)[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|is\s+standard|standard|date|\Z)')
        trace.append(self.make_trace('product_name', product_name, 'label_based_regex'))

        # 4. IS Standard (e.g., IS 13252:2010 or IS/IEC 60950-1)
        is_std = self.extract_pattern(text, r'\bIS\s*[\d\-/:]+(?:\s*:\s*\d{4})?\b', group=0)
        if not is_std:
            is_std = self.extract_pattern(text, r'(?:indian\s+standard|is\s+number|standard)[:\s]*([A-Z0-9\s/:-]+)')
        trace.append(self.make_trace('is_standard', is_std, 'is_standard_pattern'))

        # 5. Date of Grant
        date_of_grant = self.extract_date(
            text,
            ['date of grant', 'granted on', 'issue date', 'date of issue', 'valid from', 'from']
        )
        trace.append(self.make_trace('date_of_grant', date_of_grant, 'extract_date'))

        # 6. Valid Upto
        valid_upto = self.extract_date(
            text,
            ['valid upto', 'validity upto', 'expiry date', 'valid till', 'upto', 'to']
        )
        trace.append(self.make_trace('valid_upto', valid_upto, 'extract_date'))

        # 7. Status
        status = None
        text_lower = text.lower()
        if 'operative' in text_lower or 'valid' in text_lower or 'active' in text_lower:
            status = 'VALID'
        elif 'expired' in text_lower or 'cancelled' in text_lower or 'suspended' in text_lower:
            status = 'EXPIRED'
        elif valid_upto:
            status = 'VALID'
        trace.append(self.make_trace('status', status, 'status_heuristic'))

        result = {
            'license_number': lic_num,
            'licensee_name': licensee_name,
            'product_name': product_name,
            'is_standard': is_std,
            'date_of_grant': date_of_grant,
            'valid_upto': valid_upto,
            'status': status,
        }
        return result, trace
