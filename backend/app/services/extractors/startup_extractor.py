"""
Startup Certificate field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import StartupCertificateData


class StartupExtractor(BaseExtractor):
    """
    Extract structured data from DPIIT Startup Recognition Certificates.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['certificate_number', 'startup_name', 'date_of_incorporation', 'recognition_date', 'valid_upto', 'dpiit_number']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. Certificate Number / DPIIT Recognition Number (e.g. DIPP12345 or DIPP-DEMO-2021-12345)
        dpiit_num, d_ev = self.extract_pattern_with_evidence(text, r'(?:recognition\s*no|certificate\s*no|dpiit\s*no)[:\s]*([A-Z0-9\-/]+)', group=1)
        if not dpiit_num:
            dpiit_num, d_ev = self.extract_pattern_with_evidence(text, r'\b(?:DIPP|DPIIT)[\s/\-]?[A-Z0-9\-/]+\b', group=0)
        cert_num = dpiit_num
        trace.append(self.make_trace('certificate_number', cert_num, 'cert_pattern', evidence=d_ev if cert_num else None))
        trace.append(self.make_trace('dpiit_number', dpiit_num, 'dpiit_pattern', evidence=d_ev if dpiit_num else None))

        # 2. Startup Name
        startup_name, s_ev = self.extract_pattern_with_evidence(text, r'(?:entity|startup\s+name|name\s+of\s+startup|entity\s+name|certify\s+that|certified\s+that|certifying\s+that)[:\s]*([A-Za-z0-9\s.&,]+?)(?=\s*(?:\s+has|\s+is|\n|date|\Z))', group=1)
        if startup_name and startup_name.strip():
            startup_name = startup_name.strip()
        else:
            startup_name = None
        trace.append(self.make_trace('startup_name', startup_name, 'label_based_regex', evidence=s_ev if startup_name else None))

        # 3. Date of Incorporation
        date_inc = self.extract_date(
            text,
            ['date of incorporation', 'incorporated on', 'date of registration', 'incorporation date']
        )
        trace.append(self.make_trace('date_of_incorporation', date_inc, 'extract_date'))

        # 4. Recognition Date
        date_rec = self.extract_date(
            text,
            ['date of recognition', 'recognized on', 'date of issue', 'issue date', 'recognition date', 'dated']
        )
        trace.append(self.make_trace('recognition_date', date_rec, 'extract_date'))

        # 5. Valid Upto
        valid_upto = self.extract_date(
            text,
            ['valid upto', 'validity upto', 'valid till', 'expiry date', 'valid up to']
        )
        trace.append(self.make_trace('valid_upto', valid_upto, 'extract_date'))

        result = {
            'certificate_number': cert_num,
            'startup_name': startup_name,
            'date_of_incorporation': date_inc,
            'recognition_date': date_rec,
            'valid_upto': valid_upto,
            'dpiit_number': dpiit_num or cert_num,
        }
        return result, trace
