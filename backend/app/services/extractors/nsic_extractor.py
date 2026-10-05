"""
NSIC Certificate field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import NSICCertificateData


class NSICExtractor(BaseExtractor):
    """
    Extract structured data from NSIC (National Small Industries Corporation) Certificates.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['registration_number', 'enterprise_name', 'validity_from', 'validity_to', 'category']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. Registration Number
        reg_num, r_ev = self.extract_pattern_with_evidence(text, r'(?:certificate\s*no|registration\s*(?:no|number)|nsic\s*(?:no|number))[:\s]*([A-Z0-9\-/]+)', group=1)
        if not reg_num:
            reg_num, r_ev = self.extract_pattern_with_evidence(text, r'\bNSIC-[A-Z0-9\-/]+\b', group=0)
        trace.append(self.make_trace('registration_number', reg_num, 'reg_pattern', evidence=r_ev if reg_num else None))

        # 2. Enterprise Name
        enterprise_name, e_ev = self.extract_pattern_with_evidence(text, r'(?:enterprise|name\s+of\s+(?:the\s+)?unit|name\s+of\s+enterprise|enterprise\s+name|unit\s+name)[:\s]*(?:m/s\.?\s+)?([A-Za-z0-9\s.&,]+?)(?:\n|category|validity|status|\Z)', group=1)
        trace.append(self.make_trace('enterprise_name', enterprise_name.strip() if enterprise_name else None, 'label_based_regex', evidence=e_ev if enterprise_name else None))

        # 3. Validity From
        validity_from = self.extract_date(
            text,
            ['validity from', 'valid from', 'from date', 'date of issue', 'issued on', 'from']
        )
        trace.append(self.make_trace('validity_from', validity_from, 'extract_date'))

        # 4. Validity To
        validity_to = self.extract_date(
            text,
            ['validity to', 'valid upto', 'valid till', 'to date', 'expiry date', 'upto']
        )
        trace.append(self.make_trace('validity_to', validity_to, 'extract_date'))

        # 5. Category (Micro / Small / Medium / Manufacturing / Services)
        category = self.extract_field_aware(
            text,
            [r'category\s+of\s+enterprise', r'category', r'enterprise\s+category'],
            ['registration', 'validity', 'monetary', 'name', 'address']
        )
        if not category:
            text_lower = text.lower()
            if 'micro' in text_lower:
                category = 'Micro'
            elif 'small' in text_lower:
                category = 'Small'
            elif 'medium' in text_lower:
                category = 'Medium'
        trace.append(self.make_trace('category', category, 'category_heuristic'))

        result = {
            'registration_number': reg_num,
            'enterprise_name': enterprise_name,
            'validity_from': validity_from,
            'validity_to': validity_to,
            'category': category,
        }
        return result, trace
