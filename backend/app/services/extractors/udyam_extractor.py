"""
Udyam/MSME Certificate field extractor
"""
from typing import Dict, Any, List, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import UdyamCertificateData

class UdyamExtractor(BaseExtractor):
    """Extract structured data from Udyam/MSME Certificate"""

    REQUIRED_FIELDS = ['udyam_registration_number', 'enterprise_name', 'enterprise_type']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extract Udyam certificate fields"""
        trace: List[Dict[str, Any]] = []
        data = UdyamCertificateData()

        # Extract Udyam registration number
        udyam_pattern = r'UDYAM-[A-Z]{2}-\d{2}-\d{7}'
        data.udyam_registration_number = self.extract_pattern(text, udyam_pattern, group=0)
        trace.append(self.make_trace('udyam_registration_number', data.udyam_registration_number, 'udyam_regex'))

        # Extract enterprise name
        name_patterns = [
            r'(?:name of enterprise|enterprise name)[:\s]*([A-Za-z0-9\s.&]+?)(?:\n|,|\Z)',
            r'(?:organization name|unit name)[:\s]*([A-Za-z0-9\s.&]+)'
        ]
        for pattern in name_patterns:
            result = self.extract_pattern(text, pattern)
            if result:
                data.enterprise_name = result
                break
        trace.append(self.make_trace('enterprise_name', data.enterprise_name, 'label_based_regex'))

        # Extract enterprise type
        if 'micro' in text.lower():
            data.enterprise_type = 'Micro'
        elif 'small' in text.lower():
            data.enterprise_type = 'Small'
        elif 'medium' in text.lower():
            data.enterprise_type = 'Medium'
        trace.append(self.make_trace('enterprise_type', data.enterprise_type, 'keyword_classification'))

        # Extract dates
        data.date_of_incorporation = self.extract_date(text, [
            'date of incorporation',
            'date of commencement'
        ])
        trace.append(self.make_trace('date_of_incorporation', data.date_of_incorporation, 'extract_date'))

        data.date_of_udyam_registration = self.extract_date(text, [
            'date of registration',
            'registration date',
            'date of udyam registration'
        ])
        trace.append(self.make_trace('date_of_udyam_registration', data.date_of_udyam_registration, 'extract_date'))

        # Extract major activity
        activity_pattern = r'(?:major activity|type of organization)[:\s]*([A-Za-z\s]+)'
        data.major_activity = self.extract_pattern(text, activity_pattern)
        trace.append(self.make_trace('major_activity', data.major_activity, 'regex_label'))

        # Extract PAN
        pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'
        data.pan = self.extract_pattern(text, pan_pattern, group=0)
        trace.append(self.make_trace('pan', data.pan, 'pan_regex'))

        result = data.model_dump()
        return {k: v for k, v in result.items()}, trace

