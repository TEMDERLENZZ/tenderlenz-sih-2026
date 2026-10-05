"""
Income Tax Return (ITR) field extractor
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import IncomeTaxReturnData


class ITRExtractor(BaseExtractor):
    """
    Extract structured data from Income Tax Return (ITR-V / Acknowledgement) documents.
    Returns: (data_dict, trace_list)
    """

    REQUIRED_FIELDS = ['pan', 'name', 'assessment_year', 'financial_year', 'total_income', 'total_tax_paid', 'filing_date', 'acknowledgement_number']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []

        # 1. PAN (10 chars regex: 5 alpha, 4 numeric, 1 alpha)
        pan = self.extract_pattern(text, r'\b[A-Z]{5}\d{4}[A-Z]{1}\b', group=0)
        trace.append(self.make_trace('pan', pan, 'pan_regex'))

        # 2. Name
        name = self.extract_pattern(text, r'(?:name\s+of\s+taxpayer|assessee\s+name|name\s+of\s+assessee|taxpayer\s+name|name)[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|assessment|pan|financial|\Z)')
        trace.append(self.make_trace('name', name, 'label_based_regex'))

        # 3. Assessment Year (e.g. 2024-25 or 2024-2025)
        ay = self.extract_pattern(text, r'(?:assessment\s+year|ay)[:\s]*(\d{4}[-\s]*\d{2,4})')
        if not ay:
            ay = self.extract_pattern(text, r'\b20\d{2}[-\s]*20?\d{2}\b', group=0)
        trace.append(self.make_trace('assessment_year', ay, 'ay_pattern'))

        # 4. Financial Year (e.g. 2023-24)
        fy = self.extract_pattern(text, r'(?:financial\s+year|previous\s+year|fy)[:\s]*(\d{4}[-\s]*\d{2,4})')
        trace.append(self.make_trace('financial_year', fy, 'fy_pattern'))

        # 5. Total Income
        total_income = self.extract_amount(text, ['total income', 'gross total income', 'total income / gross total income', 'income'])
        trace.append(self.make_trace('total_income', total_income, 'extract_amount'))

        # 6. Total Tax Paid
        total_tax = self.extract_amount(text, ['total tax paid', 'tax paid', 'total tax payable', 'net tax payable', 'taxes paid'])
        trace.append(self.make_trace('total_tax_paid', total_tax, 'extract_amount'))

        # 7. Filing Date
        filing_date = self.extract_date(
            text,
            ['filing date', 'date of filing', 'e-filed on', 'filed on', 'date']
        )
        trace.append(self.make_trace('filing_date', filing_date, 'extract_date'))

        # 8. Acknowledgement Number (15 digits usually)
        ack_num = self.extract_pattern(text, r'\b\d{15}\b', group=0)
        if not ack_num:
            ack_num = self.extract_pattern(text, r'(?:acknowledgement\s*(?:number|no|#)?|ack\s*(?:no|number)?)[:\s]*(\d{10,20})')
        trace.append(self.make_trace('acknowledgement_number', ack_num, 'ack_pattern'))

        result = {
            'pan': pan,
            'name': name,
            'assessment_year': ay,
            'financial_year': fy,
            'total_income': total_income,
            'total_tax_paid': total_tax,
            'filing_date': filing_date,
            'acknowledgement_number': ack_num,
        }
        return result, trace
