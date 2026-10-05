"""
GST Certificate field extractor — Field-Aware & Evidence-Enabled Edition

Raw text format observed in real GST PDFs (Form GST REG-06):

  1.Legal Name SASIKUMAR
  2.Trade Name, if any VIVID TRADERS
  3.Additional trade names, if any
  4.Constitution of Business Proprietorship
  5.Address of Principal Place of Business Floor No.: 0 ...
  6. Date of Liability
  7. Date of Validity From 22/05/2025 To Not Applicable
  8. Type of Registration Regular

Key extraction rules:
  - Supports Legal Name in formats:
      - 1. Legal Name SASIKUMAR / 1.Legal Name: SASIKUMAR
      - Legal Name SASIKUMAR
      - Legal Name: SASIKUMAR
      - Legal Name - SASIKUMAR
      - Legal Name \n SASIKUMAR
      - Legal Name of Business SASIKUMAR
  - Each extracted field produces full trace: field, value, status, confidence, method, evidence
"""
from typing import Dict, Any, List, Optional, Tuple
import re
from .base_extractor import BaseExtractor
from app.schemas.document_schemas import GSTCertificateData


_ALL_GST_LABELS: List[str] = [
    r'legal\s+name(?:\s+of\s+business)?',
    r'trade\s+name(?:,?\s*if\s+any)?',
    r'additional\s+trade\s+names?(?:,?\s*if\s+any)?',
    r'constitution\s+of\s+business',
    r'address\s+of\s+(?:principal\s+place|business)',
    r'principal\s+place\s+of\s+business',
    r'date\s+of\s+liability',
    r'date\s+of\s+validity',
    r'type\s+of\s+registration',
    r'particulars\s+of\s+approving',
    r'registration\s+(?:number|date)',
    r'date\s+of\s+(?:registration|issue)',
    r'goods\s+and\s+services\s+tax\s+identification',
    r'gstin',
    r'state',
]


def _extract_legal_name_with_evidence(text: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extract Legal Name from GST document text and return (value, source_evidence, method).

    Supports variations:
      - 1. Legal Name SASIKUMAR / 1.Legal Name: SASIKUMAR
      - Legal Name SASIKUMAR
      - Legal Name: SASIKUMAR
      - Legal Name - SASIKUMAR
      - Legal Name \n SASIKUMAR
      - Legal Name of Business SASIKUMAR
      - Legal Name of Registered Person SASIKUMAR
      - Name of Taxpayer SASIKUMAR
    """
    patterns = [
        # Pattern 1: Numbered format e.g. "1. Legal Name SASIKUMAR" or "1.Legal Name: SASIKUMAR"
        (
            r'\b1\s*[.\)]?\s*legal\s+name(?:\s+(?:of|/)\s+(?:the\s+)?(?:business|registered\s+person|taxpayer))?\s*[:\-]?\s*\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:\n\s*2\s*[.\)]|\s+2\s*[.\)]|\n\s*trade\s+name|\s+trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\n\n|$))',
            'numbered_label_field_1'
        ),
        # Pattern 2: Label with explicit separator e.g. "Legal Name: SASIKUMAR", "Legal Name - SASIKUMAR"
        (
            r'legal\s+name(?:\s+(?:of|/)\s+(?:the\s+)?(?:business|registered\s+person|taxpayer))?\s*[:\-=]\s*\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\d+\s*[.\)]|\n\n|$))',
            'legal_name_label'
        ),
        # Pattern 3: Label followed by space or newline e.g. "Legal Name SASIKUMAR", "Legal Name\nSASIKUMAR"
        (
            r'legal\s+name(?:\s+(?:of|/)\s+(?:the\s+)?(?:business|registered\s+person|taxpayer))?\s+\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\d+\s*[.\)]|\n\n|$))',
            'legal_name_label'
        ),
        # Pattern 4: Name of Taxpayer / Legal Name of Business
        (
            r'(?:name\s+of\s+(?:the\s+)?taxpayer|legal\s+name\s*/\s*name\s+of\s+business)\s*[:\-]?\s*\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\d+\s*[.\)]|\n\n|$))',
            'legal_name_label'
        ),
    ]

    for pat, method in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            raw_val = m.group(1).strip()
            # Stop if value bleeds into next field label
            val = re.split(
                r'\s+(?:trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|particulars|\d+\s*[.\)])',
                raw_val,
                flags=re.IGNORECASE
            )[0].strip()
            val = re.sub(r'^[:\-\s]+', '', val).strip()
            val = re.sub(r'[:\-\s]+$', '', val).strip()

            # Reject common labels mistakenly captured as value
            if val and len(val) > 1 and val.lower() not in ['of business', 'of the business', 'of registered person', 'if any']:
                full_match = m.group(0).strip()
                # Stop evidence before trailing next field label if present
                evidence_clean = re.split(
                    r'\s+(?:2\s*[.\)]|trade\s+name|additional\s+trade|constitution|address|date\s+of|type\s+of)',
                    full_match,
                    flags=re.IGNORECASE
                )[0].strip()
                evidence = re.sub(r'[\r\n\t]+', ' ', evidence_clean)
                evidence = re.sub(r' {2,}', ' ', evidence).strip()
                return val, evidence, method

    return None, None, 'not_found'


def _extract_trade_name_with_evidence(text: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extract Trade Name from GST document text and return (value, source_evidence, method).
    """
    patterns = [
        (
            r'\b2\s*[.\)]?\s*trade\s+name(?:,?\s*if\s+any)?\s*[:\-]?\s*\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:\n\s*3\s*[.\)]|\s+3\s*[.\)]|\n\s*additional\s+trade|\s*\n\s*constitution|\n\n|$))',
            'numbered_label_field_2'
        ),
        (
            r'trade\s+name(?:,?\s*if\s+any)?\s*[:\-=]\s*\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\d+\s*[.\)]|\n\n|$))',
            'plain_label_colon'
        ),
        (
            r'trade\s+name(?:,?\s*if\s+any)?\s+\n?\s*([A-Za-z0-9\s.&,/\'\"()\-\&]+?)(?=\s*(?:additional\s+trade|constitution|address|date\s+of|type\s+of|gstin|state|\d+\s*[.\)]|\n\n|$))',
            'plain_label_colon'
        ),
    ]

    for pat, method in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            raw_val = m.group(1).strip()
            val = re.split(r'\s+(?:additional\s+trade|constitution|address|date|type|\d+[.\)])', raw_val, flags=re.IGNORECASE)[0].strip()
            val = re.sub(r'^[:\-\s]+', '', val).strip()
            val = re.sub(r'[:\-\s]+$', '', val).strip()
            if val and len(val) > 1 and val.lower() not in ['if any', 'if any 3']:
                full_match = m.group(0).strip()
                evidence_clean = re.split(
                    r'\s+(?:3\s*[.\)]|additional\s+trade|constitution|address|date\s+of|type\s+of)',
                    full_match,
                    flags=re.IGNORECASE
                )[0].strip()
                evidence = re.sub(r'[\r\n\t]+', ' ', evidence_clean)
                evidence = re.sub(r' {2,}', ' ', evidence).strip()
                return val, evidence, method

    return None, None, 'not_found'


class GSTExtractor(BaseExtractor):
    """
    Extract structured data from GST Certificate (Form GST REG-06).

    Returns a tuple: (extracted_data_dict, extraction_trace_list)
    """

    REQUIRED_FIELDS = ['gstin', 'legal_name', 'trade_name', 'registration_date', 'status', 'address']

    def extract(self, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract GST certificate fields with full extraction trace and evidence.
        """
        # Normalize text: collapse whitespace, handle newlines
        normalized_text = re.sub(r'\s+', ' ', text)
        text_with_newlines = text  # Keep original for some patterns

        trace: List[Dict[str, Any]] = []

        # ------------------------------------------------------------------
        # 1. GSTIN — Enhanced pattern with multiple label variations
        # ------------------------------------------------------------------
        gstin = None
        gstin_ev = None

        # Pattern: Standard 15-character GSTIN format or synthetic GSTIN format
        gstin_pattern = r'\b\d{2}[A-Z0-9]{10,13}\b'

        # Try multiple label variations
        label_patterns = [
            rf'(?:gstin|gstin/uin|goods\s+and\s+services\s+tax\s+identification\s+number|registration\s+number)\s*[:\-]?\s*({gstin_pattern})',
            rf'({gstin_pattern})',  # Standalone GSTIN
        ]

        for pattern in label_patterns:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                # Extract the GSTIN (last group)
                gstin = match.group(match.lastindex) if match.lastindex else match.group(1)
                # Get evidence
                evidence_start = max(0, match.start() - 30)
                evidence_end = min(len(normalized_text), match.end() + 30)
                gstin_ev = normalized_text[evidence_start:evidence_end].strip()
                break

        trace.append(self.make_trace('gstin', gstin, 'gstin_multi_label_regex', evidence=gstin_ev))

        # ------------------------------------------------------------------
        # 2. LEGAL NAME — multi-pattern with evidence
        # ------------------------------------------------------------------
        legal_name, legal_name_ev, legal_method = _extract_legal_name_with_evidence(text)
        trace.append(self.make_trace('legal_name', legal_name, legal_method, evidence=legal_name_ev))

        # ------------------------------------------------------------------
        # 3. TRADE NAME — multi-pattern with evidence
        # ------------------------------------------------------------------
        trade_name, trade_name_ev, trade_method = _extract_trade_name_with_evidence(text)
        trace.append(self.make_trace('trade_name', trade_name, trade_method, evidence=trade_name_ev))

        # ------------------------------------------------------------------
        # 4. REGISTRATION DATE — with evidence
        # ------------------------------------------------------------------
        registration_date = None
        reg_ev = None
        method = 'not_found'

        date_pats = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
        ]
        date_group = '(' + '|'.join(date_pats) + ')'

        # a) "Date of Validity From DATE"
        val, ev = self.extract_pattern_with_evidence(text, rf'date\s+of\s+validity\s+from\s+{date_group}', group=1)
        if val:
            registration_date = val
            reg_ev = ev
            method = 'date_of_validity_from'

        # b) "granted on DATE"
        if not registration_date:
            val, ev = self.extract_pattern_with_evidence(text, rf'granted\s+on\s+{date_group}', group=1)
            if val:
                registration_date = val
                reg_ev = ev
                method = 'granted_on'

        # c) "Date of issue of Certificate DATE"
        if not registration_date:
            val, ev = self.extract_pattern_with_evidence(text, rf'date\s+of\s+issue\s+of\s+certificate\s+{date_group}', group=1)
            if val:
                registration_date = val
                reg_ev = ev
                method = 'date_of_issue_certificate'

        # d) "registration date / date of registration"
        if not registration_date:
            val, ev = self.extract_pattern_with_evidence(text, rf'(?:registration\s+date|date\s+of\s+registration|effective\s+date)\s*[:\-]?\s*{date_group}', group=1)
            if val:
                registration_date = val
                reg_ev = ev
                method = 'registration_date_keyword'

        trace.append(self.make_trace('registration_date', registration_date, method, evidence=reg_ev))

        # ------------------------------------------------------------------
        # 5. STATUS — with evidence
        # ------------------------------------------------------------------
        status = None
        status_ev = None
        method = 'not_found'

        text_lower = text.lower()
        if 'cancelled' in text_lower or 'canceled' in text_lower:
            status = 'CANCELLED'
            _, status_ev = self.extract_pattern_with_evidence(text, r'.{0,30}(?:cancelled|canceled).{0,30}', group=0)
            method = 'keyword_cancelled'
        elif 'suspended' in text_lower:
            status = 'SUSPENDED'
            _, status_ev = self.extract_pattern_with_evidence(text, r'.{0,30}suspended.{0,30}', group=0)
            method = 'keyword_suspended'
        elif 'inactive' in text_lower:
            status = 'INACTIVE'
            _, status_ev = self.extract_pattern_with_evidence(text, r'.{0,30}inactive.{0,30}', group=0)
            method = 'keyword_inactive'
        elif re.search(r'\bactive\b', text_lower):
            status = 'ACTIVE'
            _, status_ev = self.extract_pattern_with_evidence(text, r'.{0,30}\bactive\b.{0,30}', group=0)
            method = 'keyword_active'
        elif re.search(r'type\s+of\s+registration\s*:?\s*regular', text_lower):
            status = 'ACTIVE'
            _, status_ev = self.extract_pattern_with_evidence(text, r'type\s+of\s+registration\s*:?\s*regular', group=0)
            method = 'type_of_registration_regular'
        elif re.search(r'registration\s+certificate', text_lower):
            if gstin:
                status = 'ACTIVE'
                _, status_ev = self.extract_pattern_with_evidence(text, r'.{0,30}registration\s+certificate.{0,30}', group=0)
                method = 'registration_certificate_present'

        trace.append(self.make_trace('status', status, method, evidence=status_ev))

        # ------------------------------------------------------------------
        # 6. ADDRESS — with evidence
        # ------------------------------------------------------------------
        address = None
        addr_ev = None
        method = 'not_found'

        addr_block_pat = (
            r'(?:5\s*[.\)]\s*)?'
            r'address\s+of\s+(?:principal\s+place\s+of\s+)?business'
            r'(?:[^\n]*?\n)?'
            r'((?:(?!6\s*[.\)]|\d+\s*[.\)]\s*date|type\s+of|particulars).)+?)'
            r'(?=\s*6\s*[.\)]|\s*\n\s*\d+\s*[.\)]|$)'
        )
        m = re.search(addr_block_pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw_addr = m.group(1)
            raw_addr = re.sub(r'\s*\n\s*', ', ', raw_addr)
            raw_addr = re.sub(r',\s*,', ',', raw_addr)
            raw_addr = re.sub(r'\s{2,}', ' ', raw_addr)

            sub_labels = [
                r'Floor\s+No\.?',
                r'Building\s+No\.?/Flat\s+No\.?',
                r'Name\s+Of\s+Premises/Building',
                r'Road/Street',
                r'Locality/Sub\s+Locality',
                r'City/Town/Village',
                r'District',
                r'State',
                r'PIN\s+Code',
            ]
            for lbl in sub_labels:
                raw_addr = re.sub(rf'\b{lbl}\b\s*:?\s*', ' ', raw_addr, flags=re.IGNORECASE)

            raw_addr = re.sub(r'(?<!\d)\b0\b(?!\d)', '', raw_addr)
            raw_addr = re.sub(r',\s*,', ',', raw_addr)
            raw_addr = re.sub(r'^\s*,\s*', '', raw_addr)
            raw_addr = re.sub(r'\s{2,}', ' ', raw_addr).strip()

            if raw_addr and len(raw_addr) > 5:
                address = raw_addr
                addr_ev = self.normalize_value(m.group(0)[:150])
                method = 'numbered_block_5_reconstruction'

        if not address:
            val, ev = self.extract_pattern_with_evidence(text, r'(?:principal\s+place\s+of\s+)?address[:\s]+([^\n]+)', group=1)
            if val and len(val) > 5:
                address = val
                addr_ev = ev
                method = 'plain_address_label'

        if not address:
            city_m = re.search(r'(?:city|town|village)\s*[:/]?\s*([A-Za-z\s]+?)(?:\n|District|State)', text, re.IGNORECASE)
            state_m = re.search(r'\bState\s*[:/]?\s*([A-Za-z\s]+?)(?:\n|PIN|$)', text, re.IGNORECASE)
            pin_m = re.search(r'PIN\s*(?:Code)?\s*[:/]?\s*(\d{6})', text, re.IGNORECASE)
            parts = []
            if city_m:
                parts.append(city_m.group(1).strip())
            if state_m:
                parts.append(state_m.group(1).strip())
            if pin_m:
                parts.append(f'PIN {pin_m.group(1)}')
            if parts:
                address = ', '.join(parts)
                addr_ev = address
                method = 'city_state_pin_reconstruction'

        trace.append(self.make_trace('address', address, method, evidence=addr_ev))

        # ------------------------------------------------------------------
        # 7. STATE (bonus field)
        # ------------------------------------------------------------------
        state = None
        state_ev = None
        val, ev = self.extract_pattern_with_evidence(text, r'\bState\s*[:/]?\s*([A-Za-z][A-Za-z\s]+?)(?:\n|PIN|$)', group=1)
        if val:
            state = re.split(r'\s+PIN', val)[0].strip()
            state_ev = ev
        elif address:
            # Try to infer state from address
            state_map = {
                'TN': 'Tamil Nadu', 'TAMIL NADU': 'Tamil Nadu',
                'MH': 'Maharashtra', 'MAHARASHTRA': 'Maharashtra',
                'DL': 'Delhi', 'DELHI': 'Delhi',
                'KA': 'Karnataka', 'KARNATAKA': 'Karnataka',
                'WB': 'West Bengal', 'WEST BENGAL': 'West Bengal'
            }
            for kw, sname in state_map.items():
                if kw in address.upper():
                    state = sname
                    state_ev = f"Inferred from address: {address}"
                    break
        if not state and gstin and len(gstin) >= 2:
            code_map = {'33': 'Tamil Nadu', '27': 'Maharashtra', '29': 'Karnataka', '07': 'Delhi', '19': 'West Bengal'}
            if gstin[:2] in code_map:
                state = code_map[gstin[:2]]
                state_ev = f"Derived from GSTIN prefix: {gstin[:2]}"

        trace.append(self.make_trace('state', state, 'state_label', evidence=state_ev))

        # ------------------------------------------------------------------
        # BUILD RESULT
        # ------------------------------------------------------------------
        result: Dict[str, Any] = {
            'gstin': gstin,
            'legal_name': legal_name,
            'trade_name': trade_name,
            'registration_date': registration_date,
            'status': status,
            'address': address,
        }

        if state:
            result['state'] = state

        return result, trace

