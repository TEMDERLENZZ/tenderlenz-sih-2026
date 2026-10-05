"""
Base extractor class that all document extractors inherit from.

Key capabilities:
- extract_labeled_value(): handles "Label: value" and "N.Label value" numbered formats
- extract_field_aware(): captures value between a label and a set of stop patterns
- normalize_value(): trims, collapses whitespace, removes accidental label bleed-over
- extract_date(): supports DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD-MMM-YYYY
- extract_amount(): handles ₹1,23,456.78 / Rs. 123456 / 1,23,456/-
- make_trace(): produces {field, value, confidence, status, evidence, method}
- compute_document_status(): EXTRACTED / PARTIALLY_EXTRACTED / EXTRACTION_FAILED
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import re


class BaseExtractor(ABC):
    """Abstract base class for document field extraction"""

    # Subclasses must define these lists for auto-status computation
    REQUIRED_FIELDS: List[str] = []
    OPTIONAL_FIELDS: List[str] = []

    @abstractmethod
    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract structured data from document text.

        Returns:
            (data_dict, trace_list)
            data_dict  : all schema fields present; missing fields explicitly set to None
            trace_list : [{field, value, confidence, status, evidence, method}] for every field

        Never invent values — return None when a field cannot be found.
        Never raise exceptions for missing fields.
        """
        pass

    # ------------------------------------------------------------------
    # Text normalisation
    # ------------------------------------------------------------------

    def normalize_value(self, value: Optional[str]) -> Optional[str]:
        """
        Normalize an extracted string value:
        - strip leading/trailing whitespace
        - collapse internal repeated whitespace to a single space
        - remove lone punctuation artifacts at the start/end
        Returns None for empty / whitespace-only strings.
        """
        if not value:
            return None
        # Collapse newlines and tabs into spaces
        value = re.sub(r'[\r\n\t]+', ' ', value)
        # Collapse multiple spaces
        value = re.sub(r' {2,}', ' ', value)
        value = value.strip()
        # Reject values that are only punctuation or single chars
        if len(value) <= 1:
            return None
        return value if value else None

    def clean_text(self, text: str) -> str:
        """Remove extra whitespace and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # ------------------------------------------------------------------
    # Core pattern extraction
    # ------------------------------------------------------------------

    def extract_pattern(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """
        Extract text matching a regex pattern.

        Args:
            text: Text to search
            pattern: Regex pattern (use capturing groups)
            group: Capture group index to return (0 = full match)

        Returns:
            Matched text (normalized) or None
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return self.normalize_value(match.group(group))
        return None

    def extract_pattern_with_evidence(
        self, text: str, pattern: str, group: int = 1
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Like extract_pattern but also returns the full matching line as evidence.

        Returns:
            (value, evidence_line) — both may be None
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = self.normalize_value(match.group(group))
            # Find the full line containing the match
            start = text.rfind('\n', 0, match.start()) + 1
            end = text.find('\n', match.end())
            evidence = text[start: end if end != -1 else len(text)].strip()
            return value, evidence
        return None, None

    def extract_labeled_value(
        self,
        text: str,
        label_patterns: List[str],
        stop_patterns: Optional[List[str]] = None,
        multiline: bool = False,
    ) -> Optional[str]:
        """
        Extract the value associated with a label in either of these formats:
          - "Legal Name: ABC Corp"        (colon-separated)
          - "1.Legal Name ABC Corp"       (GST numbered label, no colon)
          - "  2.Trade Name, if any ABC"  (GST with qualifier phrase)

        The value terminates at:
          1. Any pattern in stop_patterns (e.g. the next numbered label or field keyword)
          2. End of line (if multiline=False)
          3. Double newline
        """
        stop_patterns = stop_patterns or []
        stop_group = '|'.join(stop_patterns) if stop_patterns else r'$'

        for label_pat in label_patterns:
            if multiline:
                full_pattern = (
                    rf'(?:{label_pat})'
                    rf'(?:[,\s][^:\n]{0,30}?)?'
                    rf'[:\s]+'
                    rf'(.+?)'
                    rf'(?:{stop_group}|\n\n|$)'
                )
            else:
                full_pattern = (
                    rf'(?:{label_pat})'
                    rf'(?:[,\s][^:\n]{0,30}?)?'
                    rf'[:\s]+'
                    rf'([^\n]+?)'
                    rf'(?:{stop_group}|\n|$)'
                )

            match = re.search(full_pattern, text, re.IGNORECASE | re.DOTALL if multiline else re.IGNORECASE)
            if match:
                val = self.normalize_value(match.group(1))
                if val:
                    return val

        return None

    def extract_labeled_value_with_evidence(
        self,
        text: str,
        label_patterns: List[str],
        stop_patterns: Optional[List[str]] = None,
        multiline: bool = False,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Like extract_labeled_value but also returns evidence line."""
        stop_patterns = stop_patterns or []
        stop_group = '|'.join(stop_patterns) if stop_patterns else r'$'

        for label_pat in label_patterns:
            if multiline:
                full_pattern = (
                    rf'(?:{label_pat})'
                    rf'(?:[,\s][^:\n]{0,30}?)?'
                    rf'[:\s]+'
                    rf'(.+?)'
                    rf'(?:{stop_group}|\n\n|$)'
                )
            else:
                full_pattern = (
                    rf'(?:{label_pat})'
                    rf'(?:[,\s][^:\n]{0,30}?)?'
                    rf'[:\s]+'
                    rf'([^\n]+?)'
                    rf'(?:{stop_group}|\n|$)'
                )

            match = re.search(full_pattern, text, re.IGNORECASE | re.DOTALL if multiline else re.IGNORECASE)
            if match:
                val = self.normalize_value(match.group(1))
                if val:
                    start = text.rfind('\n', 0, match.start()) + 1
                    end = text.find('\n', match.end())
                    evidence = text[start: end if end != -1 else len(text)].strip()
                    return val, evidence

        return None, None

    def extract_field_aware(
        self,
        text: str,
        label_patterns: List[str],
        all_field_labels: List[str],
        multiline: bool = False,
    ) -> Optional[str]:
        """
        Convenience wrapper around extract_labeled_value that auto-builds
        stop_patterns from all_field_labels.
        """
        numbered_stop = r'\d+\s*\.'
        keyword_stops = [rf'(?:{lp})' for lp in all_field_labels if lp not in label_patterns]
        stop_patterns = [numbered_stop] + keyword_stops
        return self.extract_labeled_value(text, label_patterns, stop_patterns, multiline=multiline)

    def extract_field_aware_with_evidence(
        self,
        text: str,
        label_patterns: List[str],
        all_field_labels: List[str],
        multiline: bool = False,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Like extract_field_aware but returns (value, evidence)."""
        numbered_stop = r'\d+\s*\.'
        keyword_stops = [rf'(?:{lp})' for lp in all_field_labels if lp not in label_patterns]
        stop_patterns = [numbered_stop] + keyword_stops
        return self.extract_labeled_value_with_evidence(text, label_patterns, stop_patterns, multiline=multiline)

    # ------------------------------------------------------------------
    # Specialised extractors
    # ------------------------------------------------------------------

    def extract_date(self, text: str, keywords: List[str]) -> Optional[str]:
        """
        Extract a date near given keywords.

        Supported date formats:
          - DD/MM/YYYY  (e.g. 12/06/2025)
          - DD-MM-YYYY  (e.g. 12-06-2025)
          - YYYY-MM-DD  (e.g. 2025-06-12)
          - DD-MMM-YYYY (e.g. 15-Apr-2021)
          - DD MMM YYYY (e.g. 15 Apr 2021)
          - "granted on DATE"
        """
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
        ]
        date_group = '(' + '|'.join(date_patterns) + ')'

        for keyword in keywords:
            pattern = rf'{keyword}[:\s]*{date_group}'
            result = self.extract_pattern(text, pattern)
            if result:
                return result

        return None

    def extract_date_with_evidence(
        self, text: str, keywords: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Like extract_date but returns (value, evidence)."""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
        ]
        date_group = '(' + '|'.join(date_patterns) + ')'
        for keyword in keywords:
            pattern = rf'{keyword}[:\s]*{date_group}'
            value, evidence = self.extract_pattern_with_evidence(text, pattern, group=1)
            if value:
                return value, evidence
        return None, None

    def extract_amount(self, text: str, keywords: List[str]) -> Optional[str]:
        """
        Extract a monetary amount near given keywords.
        Handles: ₹1,23,456.78 / Rs. 123456 / 1,23,456/- / FY 2023-24 Turnover: INR 3,90,00,000
        """
        for keyword in keywords:
            pattern = rf'{keyword}(?:\s+turnover|\s+amount|\s+of|\s+value)?[:\s]*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{{2}})?)'
            result = self.extract_pattern(text, pattern, group=1)
            if result:
                return result
        return None

    def extract_amount_with_evidence(
        self, text: str, keywords: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Like extract_amount but returns (value, evidence)."""
        for keyword in keywords:
            pattern = rf'{keyword}(?:\s+turnover|\s+amount|\s+of|\s+value)?[:\s]*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{{2}})?)'
            value, evidence = self.extract_pattern_with_evidence(text, pattern, group=1)
            if value:
                return value, evidence
        return None, None

    # ------------------------------------------------------------------
    # Confidence helpers
    # ------------------------------------------------------------------

    @staticmethod
    def confidence_for_method(method: str, value: Optional[str]) -> float:
        """
        Return a confidence score based on extraction method and whether a value was found.
        """
        if value is None:
            return 0.0
        confidence_map = {
            'gstin_regex': 0.97,
            'pan_regex': 0.97,
            'udyam_regex': 0.97,
            'cin_regex': 0.97,
            'esic_pattern': 0.92,
            'license_pattern': 0.92,
            'reg_pattern': 0.92,
            'numbered_label_field_1': 0.95,
            'legal_name_label': 0.95,
            'numbered_label_field_2': 0.88,
            'date_of_validity_from': 0.92,
            'granted_on': 0.88,
            'date_of_issue_certificate': 0.88,
            'field_aware': 0.82,
            'label_based_regex': 0.80,
            'extract_date': 0.82,
            'extract_amount': 0.82,
            'ay_pattern': 0.88,
            'fy_pattern': 0.85,
            'ack_pattern': 0.90,
            'cert_pattern': 0.88,
            'dpiit_pattern': 0.95,
            'is_standard_pattern': 0.88,
            'numbered_block_5_reconstruction': 0.75,
            'plain_label_colon': 0.80,
            'plain_address_label': 0.72,
            'city_state_pin_reconstruction': 0.60,
            'state_label': 0.72,
            'keyword_cancelled': 0.90,
            'keyword_suspended': 0.90,
            'keyword_inactive': 0.90,
            'keyword_active': 0.85,
            'keyword_status': 0.78,
            'type_of_registration_regular': 0.80,
            'registration_certificate_present': 0.70,
            'status_heuristic': 0.70,
            'establishment_id_regex': 0.88,
            'address_block': 0.72,
            'registration_date_keyword': 0.80,
            'statement_regex': 0.78,
            'category_heuristic': 0.72,
            'not_found': 0.0,
        }
        return confidence_map.get(method, 0.75)

    @staticmethod
    def field_validation_status(field: str, value: Optional[str]) -> str:
        """
        Return VALID, PARTIAL, NOT_FOUND, or INVALID for a field.
        Applies format validation where applicable.
        """
        if value is None:
            return 'NOT_FOUND'

        validators = {
            'gstin': r'^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$',
            'pan': r'^[A-Z]{5}\d{4}[A-Z]$',
            'pan_number': r'^[A-Z]{5}\d{4}[A-Z]$',
            'udyam_registration_number': r'^UDYAM-[A-Z]{2}-\d{2}-\d{7}$',
            'cin': r'^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$',
            'acknowledgement_number': r'^\d{15}$',
            'esic_registration_number': r'^\d{17}$',
        }
        if field in validators:
            if re.match(validators[field], value.strip(), re.IGNORECASE):
                return 'VALID'
            else:
                return 'INVALID'

        # Generic: non-empty means VALID
        return 'VALID' if value.strip() else 'NOT_FOUND'

    # ------------------------------------------------------------------
    # Trace builder
    # ------------------------------------------------------------------

    @staticmethod
    def make_trace(
        field: str,
        value: Optional[str],
        method: str,
        confidence: float = None,
        evidence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a single extraction trace entry with confidence and evidence.

        Args:
            field: Field name
            value: Extracted value (None if not found)
            method: Extraction method identifier string
            confidence: Override confidence (if None, computed from method)
            evidence: The raw text line(s) used for extraction
        """
        if confidence is None:
            from app.services.extractors.base_extractor import BaseExtractor
            confidence = BaseExtractor.confidence_for_method(method, value)

        status = BaseExtractor.field_validation_status(field, value)

        return {
            "field": field,
            "value": value,
            "confidence": round(confidence, 3),
            "status": status,
            "extraction_method": method,
            "method": method,
            "source_evidence": evidence,
            "evidence": evidence,
        }

    # ------------------------------------------------------------------
    # Document-level status computation
    # ------------------------------------------------------------------

    def compute_document_status(self, trace: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Compute overall document extraction status and confidence.

        Returns:
            (status_string, overall_confidence_float)
        """
        if not self.REQUIRED_FIELDS:
            # No required fields defined — just check if anything was extracted
            found = [t for t in trace if t.get('value') is not None]
            if not found:
                return 'EXTRACTION_FAILED', 0.0
            conf = sum(t.get('confidence', 0) for t in found) / max(len(found), 1)
            return ('EXTRACTED' if conf >= 0.5 else 'PARTIALLY_EXTRACTED'), round(conf, 3)

        # Score required fields
        required_trace = [t for t in trace if t.get('field') in self.REQUIRED_FIELDS]
        found_required = [t for t in required_trace if t.get('value') is not None]
        missing_required = len(self.REQUIRED_FIELDS) - len(found_required)

        total_conf = sum(t.get('confidence', 0) for t in required_trace)
        overall_conf = total_conf / len(self.REQUIRED_FIELDS)

        if overall_conf < 0.30 or (missing_required == len(self.REQUIRED_FIELDS)):
            return 'EXTRACTION_FAILED', round(overall_conf, 3)
        elif missing_required > 0 or overall_conf < 0.70:
            return 'PARTIALLY_EXTRACTED', round(overall_conf, 3)
        else:
            return 'EXTRACTED', round(overall_conf, 3)
