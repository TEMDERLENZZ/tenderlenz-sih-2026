"""
PAN Card field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import PANCardData

class PANExtractor(BaseExtractor):
    """Extract structured data from PAN Card"""

    REQUIRED_FIELDS = ['pan_number', 'name', 'date_of_birth']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract PAN card fields"""
        trace: List[Dict[str, Any]] = []
        data = PANCardData()

        # Extract PAN number (10 characters: e.g., DEMOA1234F or AXMPS1015Q)
        pan_val, pan_ev = self.extract_pattern_with_evidence(text, r'PAN\s*[:\-]?\s*([A-Z0-9]{10})', group=1)
        if not pan_val:
            pan_val, pan_ev = self.extract_pattern_with_evidence(text, r'\b[A-Z0-9]{5}\d{4}[A-Z0-9]{1}\b', group=0)
        data.pan_number = pan_val
        trace.append(self.make_trace('pan_number', data.pan_number, 'pan_regex', evidence=pan_ev))

        # Extract name
        name_patterns = [
            r'name[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|father|entity|dob|\Z)',
            r'holder(?:\s+name)?[:\s]*([A-Za-z0-9\s.&,]+?)(?:\n|father|dob|\Z)',
            r'(?:^|\n)([A-Z][A-Za-z0-9\s.&,]+?)(?:\n|father)'
        ]
        for pattern in name_patterns:
            result, name_ev = self.extract_pattern_with_evidence(text, pattern, group=1)
            if result and len(result.strip()) > 2 and result.strip().lower() not in ['card', 'holder', 'entity']:
                data.name = result.strip()
                break
        trace.append(self.make_trace('name', data.name, 'name_label_regex', evidence=name_ev if data.name else None))

        # Extract father's name
        father_pattern = r"(?:father'?s?\s+name|father)[:\s]*([A-Za-z\s]+)"
        data.father_name = self.extract_pattern(text, father_pattern)
        trace.append(self.make_trace('father_name', data.father_name, 'father_name_regex'))

        # Extract date of birth
        data.date_of_birth = self.extract_date(text, [
            'date of birth',
            'dob',
            'birth'
        ])
        trace.append(self.make_trace('date_of_birth', data.date_of_birth, 'extract_date'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

