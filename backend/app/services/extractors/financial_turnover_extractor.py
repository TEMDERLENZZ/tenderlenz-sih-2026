"""
Financial Turnover Certificate field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import FinancialTurnoverCertificateData

class FinancialTurnoverExtractor(BaseExtractor):
    """Extract structured data from Financial Turnover Certificate"""

    REQUIRED_FIELDS = ['fy_2023_24_turnover', 'fy_2022_23_turnover', 'average_turnover']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract financial turnover fields"""
        trace: List[Dict[str, Any]] = []
        data = FinancialTurnoverCertificateData()

        # Extract bidder/company name
        name_patterns = [
            r'bidder\s*[:\-]?\s*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'company\s+name\s*[:\-]?\s*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'(?:certified that|certify that)[:\s]*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\s+has|\s+having|\n|,|\Z)',
            r'(?:company|firm|enterprise|name)[:\s]*(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)'
        ]
        b_ev = None
        for pattern in name_patterns:
            result, b_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and len(result.strip()) > 2 and result.strip().lower() not in ['financial turnover certificate', 'financial turnover', 'turnover']:
                data.bidder_name = result.strip()
                break
        trace.append(self.make_trace('bidder_name', data.bidder_name, 'bidder_name_regex', evidence=b_ev if data.bidder_name else None))

        # Extract turnover for different financial years
        # FY 2021-22
        fy_21_22 = self.extract_amount(text, [
            r'(?:fy|f\.y\.|financial year)\s*(?:20)?21[-]?22',
            r'2021[-]?22',
            r'2021[-]?2022'
        ])
        if fy_21_22:
            data.fy_2021_22_turnover = fy_21_22
        trace.append(self.make_trace('fy_2021_22_turnover', data.fy_2021_22_turnover, 'amount_extract'))

        # FY 2022-23
        fy_22_23 = self.extract_amount(text, [
            r'(?:fy|f\.y\.|financial year)\s*(?:20)?22[-]?23',
            r'2022[-]?23',
            r'2022[-]?2023'
        ])
        if fy_22_23:
            data.fy_2022_23_turnover = fy_22_23
        trace.append(self.make_trace('fy_2022_23_turnover', data.fy_2022_23_turnover, 'amount_extract'))

        # FY 2023-24
        fy_23_24 = self.extract_amount(text, [
            r'(?:fy|f\.y\.|financial year)\s*(?:20)?23[-]?24',
            r'2023[-]?24',
            r'2023[-]?2024'
        ])
        if fy_23_24:
            data.fy_2023_24_turnover = fy_23_24
        trace.append(self.make_trace('fy_2023_24_turnover', data.fy_2023_24_turnover, 'amount_extract'))

        # FY 2024-25
        fy_24_25 = self.extract_amount(text, [
            r'(?:fy|f\.y\.|financial year)\s*(?:20)?24[-]?25',
            r'2024[-]?25',
            r'2024[-]?2025'
        ])
        if fy_24_25:
            data.fy_2024_25_turnover = fy_24_25
        trace.append(self.make_trace('fy_2024_25_turnover', data.fy_2024_25_turnover, 'amount_extract'))

        # Extract average turnover
        avg_turnover = self.extract_amount(text, [
            r'average\s+turnover',
            r'avg\s+turnover',
            r'average\s+annual\s+turnover'
        ])
        if avg_turnover:
            data.average_turnover = avg_turnover
        trace.append(self.make_trace('average_turnover', data.average_turnover, 'amount_extract'))

        # Extract certificate issuer (CA details)
        issuer_patterns = [
            r'(?:chartered\s+accountant|ca\s+firm|certifying\s+authority|issued\s+by)[:\s]*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'\b(?:M/s\.?\s+)?([A-Za-z0-9\s.&]+?\b(?: chartered accountants| ca & associates))\b'
        ]
        iss_ev = None
        for pat in issuer_patterns:
            res, iss_ev = self.extract_pattern_with_evidence(text, pat, group=1)
            if res and len(res.strip()) > 3 and res.strip().lower() not in ['certificate', 'turnover certificate']:
                data.certificate_issuer = res.strip()
                break
        trace.append(self.make_trace('certificate_issuer', data.certificate_issuer, 'issuer_regex', evidence=iss_ev if data.certificate_issuer else None))

        # Extract CA registration number
        reg_pattern = r'(?:membership|registration|icai)\s+(?:no|number)[:\s]*([\d]+)'
        data.issuer_registration_number = self.extract_pattern(text, reg_pattern)
        trace.append(self.make_trace('issuer_registration_number', data.issuer_registration_number, 'reg_num_regex'))

        # Extract issue date
        data.issue_date = self.extract_date(text, [
            'issue date',
            'certificate date',
            'dated',
            'date'
        ])
        trace.append(self.make_trace('issue_date', data.issue_date, 'extract_date'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

