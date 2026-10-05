"""
Local Content Declaration field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import LocalContentDeclarationData

class LocalContentExtractor(BaseExtractor):
    """Extract structured data from Local Content Declaration"""

    REQUIRED_FIELDS = ['bidder_name', 'local_content_percentage', 'declaration_date']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract local content declaration fields"""
        trace: List[Dict[str, Any]] = []
        data = LocalContentDeclarationData()

        # Extract bidder name
        name_patterns = [
            r'bidder\s*[:\-]?\s*(?:m/s\.?\s+)?([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'(?:we|i)[,\s]+(?:m/s\.?\s+)?([A-Za-z0-9\s.&]+?)[,\s]+(?:hereby|declare)',
            r'(?:company|firm|supplier|contractor)[:\s]*(?:m/s\.?\s+)?([A-Za-z0-9\s.&]+)'
        ]
        b_ev = None
        for pattern in name_patterns:
            result, b_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and len(result.strip()) > 2 and result.strip().lower() not in ['declaration', 'local content']:
                data.bidder_name = result.strip()
                break
        trace.append(self.make_trace('bidder_name', data.bidder_name, 'bidder_name_regex', evidence=b_ev if data.bidder_name else None))

        # Extract local content percentage
        percentage_patterns = [
            r'local\s+content[^\n\d]*?(\d+(?:\.\d+)?)\s*%',
            r'local content[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+(?:of\s+the\s+total|local\s+content)',
            r'local content[:\s]+is[:\s]+(\d+(?:\.\d+)?)'
        ]
        for pattern in percentage_patterns:
            result = self.extract_pattern(text, pattern)
            if result:
                data.local_content_percentage = f"{result}%"
                break
        trace.append(self.make_trace('local_content_percentage', data.local_content_percentage, 'percentage_regex'))

        # Extract product description
        prod_val, prod_ev = self.extract_pattern_with_evidence(text, r'product\s*[:\-]?\s*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)', group=1)
        if prod_val:
            data.product_description = prod_val.strip()
        trace.append(self.make_trace('product_description', data.product_description, 'product_regex', evidence=prod_ev if data.product_description else None))

        # Extract declaration date
        data.declaration_date = self.extract_date(text, [
            'declaration date',
            'dated',
            'date'
        ])
        trace.append(self.make_trace('declaration_date', data.declaration_date, 'extract_date'))

        # Extract category
        if 'class-i' in text.lower() or 'class i' in text.lower():
            data.category = 'Class-I'
        elif 'class-ii' in text.lower() or 'class ii' in text.lower():
            data.category = 'Class-II'
        trace.append(self.make_trace('category', data.category, 'category_keyword'))

        # Extract signatory details
        signatory_pattern = r'(?:authorised signatory|authorized signatory|signature)[:\s\n]*([A-Za-z\s.]+)'
        data.signatory_name = self.extract_pattern(text, signatory_pattern)
        trace.append(self.make_trace('signatory_name', data.signatory_name, 'signatory_name_regex'))

        designation_pattern = r'(?:designation|title)[:\s]*([A-Za-z\s]+)'
        data.signatory_designation = self.extract_pattern(text, designation_pattern)
        trace.append(self.make_trace('signatory_designation', data.signatory_designation, 'designation_regex'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

