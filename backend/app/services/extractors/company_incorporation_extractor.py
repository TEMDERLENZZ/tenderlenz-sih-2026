"""
Company Incorporation / MCA Certificate field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import CompanyIncorporationData

class CompanyIncorporationExtractor(BaseExtractor):
    """Extract structured data from Company Incorporation Certificate"""

    REQUIRED_FIELDS = ['cin', 'company_name', 'date_of_incorporation']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract company incorporation fields"""
        trace: List[Dict[str, Any]] = []
        data = CompanyIncorporationData()

        # Extract CIN (Corporate Identity Number)
        cin_pattern = r'\b[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b'
        data.cin = self.extract_pattern(text, cin_pattern, group=0)
        trace.append(self.make_trace('cin', data.cin, 'cin_regex'))

        # Extract company name
        name_patterns = [
            r'(?:company\s+name|name\s+of\s+(?:the\s+)?company)\s*[:\-]?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:\n|cin|date|category|status|$))',
            r'(?:certify\s+that|certifying\s+that)\s*[:\-]?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?(?:pvt|private|public)?\s*(?:ltd|limited))',
            r'certificate\s+of\s+incorporation\s*[:\-\s\n]+([A-Za-z0-9\s.&,/\'\"()\-\&]+?(?:pvt|private|public)?\s*(?:ltd|limited))'
        ]
        c_ev = None
        for pattern in name_patterns:
            result, c_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and len(result.strip()) > 2 and result.strip().lower() not in ['company incorporation / mca', 'company incorporation', 'mca']:
                data.company_name = result.strip()
                break
        trace.append(self.make_trace('company_name', data.company_name, 'company_name_regex', evidence=c_ev if data.company_name else None))

        # Extract date of incorporation
        data.date_of_incorporation = self.extract_date(text, [
            'date of incorporation',
            'incorporated on',
            'incorporation date'
        ])
        trace.append(self.make_trace('date_of_incorporation', data.date_of_incorporation, 'extract_date'))

        # Extract company category
        if 'private' in text.lower():
            data.company_category = 'Private'
        elif 'public' in text.lower():
            data.company_category = 'Public'
        trace.append(self.make_trace('company_category', data.company_category, 'category_keyword'))

        # Extract authorized capital
        auth_capital = self.extract_amount(text, [
            'authorized capital',
            'authorised capital'
        ])
        if auth_capital:
            data.authorized_capital = auth_capital
        trace.append(self.make_trace('authorized_capital', data.authorized_capital, 'amount_extract'))

        # Extract paid-up capital
        paid_capital = self.extract_amount(text, [
            'paid up capital',
            'paid-up capital'
        ])
        if paid_capital:
            data.paid_up_capital = paid_capital
        trace.append(self.make_trace('paid_up_capital', data.paid_up_capital, 'amount_extract'))

        # Extract status
        if 'active' in text.lower() or 'incorporated' in text.lower():
            data.status = 'ACTIVE'
        trace.append(self.make_trace('status', data.status, 'status_keyword'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

