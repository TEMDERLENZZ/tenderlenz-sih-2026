"""
Document processor: OCR, classification, and orchestration

CLASSIFICATION FIX: Uses weighted scoring with document-specific strong signals
"""
import os
import mimetypes
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import PyPDF2
import pytesseract
from PIL import Image
import io
import re

from app.models.document import DocumentType

class DocumentProcessor:
    """Handles document text extraction and classification"""

    # Weighted keywords for document classification
    # Format: {DocumentType: [(keyword, weight), ...]}
    # Higher weight = stronger signal for that document type
    CLASSIFICATION_KEYWORDS_WEIGHTED = {
        DocumentType.GST_CERTIFICATE: [
            ("gstin", 10),
            ("goods and services tax", 8),
            ("gst certificate", 10),
            ("gst registration", 8),
            ("registration certificate", 3),
        ],
        DocumentType.UDYAM_CERTIFICATE: [
            ("udyam registration", 10),
            ("udyam certificate", 10),
            ("udyam", 5),
            ("msme", 5),
            ("micro small medium enterprise", 7),
        ],
        DocumentType.PAN_CARD: [
            ("permanent account number", 10),
            ("income tax department", 8),
            ("pan card", 10),
            ("pan", 3),  # Low weight - too generic
        ],
        DocumentType.INCOME_TAX_RETURN: [
            ("income tax return", 10),
            ("itr acknowledgement", 10),
            ("assessment year", 8),
            ("acknowledgement number", 5),
            ("total income", 3),
        ],
        DocumentType.OEM_AUTHORIZATION: [
            ("oem authorization letter", 15),
            ("oem authorization", 12),
            ("oem authorisation", 12),
            ("original equipment manufacturer", 12),
            ("oem name", 10),
            ("authorized bidder", 10),
            ("authorised bidder", 10),
            ("authorization date", 8),
            ("expiry date", 6),
            ("authorization number", 6),
            ("manufacturer authorization", 8),
            ("oem", 2),  # Low weight - too generic
        ],
        DocumentType.EPFO_REGISTRATION: [
            ("epfo registration", 10),
            ("epfo certificate", 10),
            ("employees provident fund", 10),
            ("establishment code", 8),
            ("provident fund", 5),
            ("epfo", 3),  # Low weight - could appear elsewhere
        ],
        DocumentType.ESIC_REGISTRATION: [
            ("esic registration certificate", 15),
            ("esic registration", 12),
            ("employer code", 10),
            ("employer name", 8),
            ("employees state insurance", 10),
            ("esic code", 10),
            ("registration status", 6),
            ("state insurance corporation", 8),
            ("esic", 3),  # Low weight - too generic alone
        ],
        DocumentType.LOCAL_CONTENT_DECLARATION: [
            ("local content declaration", 10),
            ("local content", 8),
            ("make in india", 8),
            ("indigenous content", 7),
            ("local content percentage", 8),
        ],
        DocumentType.BIS_CERTIFICATE: [
            ("bis certificate", 10),
            ("bureau of indian standards", 10),
            ("bis license", 10),
            ("license number", 5),
            ("bis", 2),  # Low weight - too generic
        ],
        DocumentType.STARTUP_CERTIFICATE: [
            ("startup recognition", 10),
            ("startup certificate", 10),
            ("dpiit recognition", 10),
            ("certificate of recognition", 5),
            ("startup", 3),  # Low weight - too generic
        ],
        DocumentType.NSIC_CERTIFICATE: [
            ("nsic certificate", 10),
            ("national small industries corporation", 10),
            ("nsic registration", 10),
            ("performance certificate", 5),
            ("nsic", 3),  # Low weight
        ],
        DocumentType.COMPANY_INCORPORATION: [
            ("certificate of incorporation", 10),
            ("corporate identity number", 10),
            ("company incorporation", 10),
            ("cin", 5),
            ("registrar of companies", 8),
            ("company registration", 7),
        ],
        DocumentType.NON_BLACKLISTING_DECLARATION: [
            ("non blacklisting declaration", 10),
            ("blacklist declaration", 8),
            ("not blacklisted", 8),
            ("not debarred", 8),
            ("debarred", 4),
            ("blacklist", 3),  # Low weight - could appear in many contexts
        ],
        DocumentType.FINANCIAL_TURNOVER_CERTIFICATE: [
            ("turnover certificate", 10),
            ("financial turnover", 10),
            ("chartered accountant", 8),
            ("annual turnover", 8),
            ("financial year", 5),
            ("turnover", 2),  # Low weight - too generic
        ],
    }

    def __init__(self):
        # Configure tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass

    def extract_text(self, file_path: str, mime_type: str) -> str:
        """
        Extract text from document using appropriate method
        UTF-8 safe with robust error handling

        Args:
            file_path: Path to uploaded file
            mime_type: MIME type of file

        Returns:
            Extracted text content (UTF-8 sanitized)
        """
        try:
            if mime_type == "application/pdf":
                text = self._extract_from_pdf(file_path)
            elif mime_type.startswith("image/"):
                text = self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")

            # Sanitize extracted text for UTF-8 safety
            return self._sanitize_text(text)

        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print(f"Text extraction error: {error_msg}")
            return ""

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text to ensure UTF-8 compatibility
        Remove control characters that may cause encoding issues
        """
        if not text:
            return ""

        # Normalize Unicode
        import unicodedata
        text = unicodedata.normalize('NFKC', text)

        # Remove control characters except newline, tab, carriage return
        sanitized = ''.join(
            char for char in text
            if char in '\n\r\t' or not unicodedata.category(char).startswith('C')
        )

        # Ensure valid UTF-8 encoding
        sanitized = sanitized.encode('utf-8', errors='replace').decode('utf-8')

        return sanitized

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2 first, fall back to OCR"""
        text = ""

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        # Ensure text is properly encoded as UTF-8
                        text += page_text + "\n"

            # If PDF text extraction yielded too little content, try OCR
            if len(text.strip()) < 50:
                text = self._ocr_pdf(file_path)

        except Exception as e:
            # Use safe Unicode logging
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print(f"PDF extraction error: {error_msg}")
            # Fall back to OCR
            text = self._ocr_pdf(file_path)

        return text

    def _ocr_pdf(self, file_path: str) -> str:
        """Convert PDF pages to images and OCR them using pdf2image and pytesseract"""
        ocr_text = ""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path)
            for img in images:
                page_text = pytesseract.image_to_string(img)
                if page_text:
                    ocr_text += page_text + "\n"
        except Exception as e:
            # Use safe Unicode logging
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print(f"OCR PDF conversion warning: {error_msg}")
        return ocr_text

    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using Tesseract OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            # Use safe Unicode logging
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print(f"Image OCR error: {error_msg}")
            return ""

    def classify_document(self, text: str) -> Tuple[Optional[DocumentType], float, Dict[str, Any]]:
        """
        Classify document type based on content using weighted scoring.

        Args:
            text: Extracted text content

        Returns:
            Tuple of (predicted_type, confidence_score, classification_details)
        """
        text_lower = text.lower()

        # Calculate weighted scores for each document type
        scores = {}
        matched_keywords = {}

        for doc_type, weighted_keywords in self.CLASSIFICATION_KEYWORDS_WEIGHTED.items():
            total_score = 0
            matches = []

            for keyword, weight in weighted_keywords:
                if keyword in text_lower:
                    total_score += weight
                    matches.append((keyword, weight))

            if total_score > 0:
                scores[doc_type] = total_score
                matched_keywords[doc_type] = matches

        # No matches found
        if not scores:
            return None, 0.0, {"matched_keywords": {}, "scores": {}}

        # Get top prediction
        predicted_type = max(scores, key=scores.get)
        max_score = scores[predicted_type]

        # Calculate confidence (normalize against maximum possible score for this type)
        max_possible = sum(weight for _, weight in self.CLASSIFICATION_KEYWORDS_WEIGHTED[predicted_type])
        confidence = min(max_score / max_possible, 1.0) if max_possible > 0 else 0.0

        # Get second-best score for ambiguity check
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        second_best_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

        # Check if classification is ambiguous (top two scores are too close)
        ambiguity_ratio = second_best_score / max_score if max_score > 0 else 0
        is_ambiguous = ambiguity_ratio > 0.7  # If second-best is within 70% of best

        classification_details = {
            "predicted_type": predicted_type.value if predicted_type else None,
            "confidence": confidence,
            "max_score": max_score,
            "all_scores": {dt.value: score for dt, score in scores.items()},
            "matched_keywords": {dt.value: matches for dt, matches in matched_keywords.items()},
            "is_ambiguous": is_ambiguous,
            "ambiguity_ratio": ambiguity_ratio,
            "text_preview": text_lower[:200] + "..." if len(text_lower) > 200 else text_lower
        }

        return predicted_type, confidence, classification_details

    def validate_classification(self, predicted_type: Optional[DocumentType],
                               expected_type: DocumentType,
                               confidence: float,
                               classification_details: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that classification matches expected type.

        Enhanced validation with detailed mismatch reporting.

        Returns:
            (is_valid, error_message)
        """
        # No prediction at all
        if predicted_type is None:
            return False, f"Could not classify document. Expected {expected_type.value} but found no matching keywords."

        # Perfect match
        if predicted_type == expected_type:
            return True, None

        # Mismatch - provide detailed diagnostic information
        all_scores = classification_details.get("all_scores", {})
        predicted_score = all_scores.get(predicted_type.value, 0)
        expected_score = all_scores.get(expected_type.value, 0)

        # Get top 3 candidates
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_candidates = [f"{doc_type} (score: {score})" for doc_type, score in sorted_scores]

        # Check if expected type scored reasonably (within 40% of predicted)
        if expected_score > 0 and expected_score >= (predicted_score * 0.4):
            # Accept with warning - scores are close enough
            print(f"⚠️ Classification ambiguous but acceptable:")
            print(f"   Predicted: {predicted_type.value} (score: {predicted_score})")
            print(f"   Expected: {expected_type.value} (score: {expected_score})")
            return True, None

        # Clear mismatch - provide diagnostic info
        error_message = (
            f"Document classification mismatch:\n"
            f"  Expected: {expected_type.value} (score: {expected_score})\n"
            f"  Detected: {predicted_type.value} (score: {predicted_score})\n"
            f"  Confidence: {confidence:.1%}\n"
            f"  Top 3 candidates: {', '.join(top_candidates)}\n"
            f"  Suggestion: Verify uploaded document matches selected type"
        )

        return False, error_message
