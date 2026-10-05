"""
Document API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.decision import AuditLog, AuditEvent
from app.schemas.document_schemas import (
    DocumentUploadResponse,
    DocumentExtractionResponse,
    BatchUploadResponse,
    BatchDocumentItem
)
from app.services.document_processor import DocumentProcessor
from app.services.extractors import get_extractor
from app.services.auth.dependencies import get_current_user, get_current_officer
from app.models.user import User
from typing import Optional
import json

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def detect_expected_type_from_filename(filename: str) -> Optional[DocumentType]:
    """Helper to detect expected document type from filename keywords"""
    fn = filename.lower()
    mapping = [
        ("gst", DocumentType.GST_CERTIFICATE),
        ("turnover", DocumentType.FINANCIAL_TURNOVER_CERTIFICATE),
        ("financial", DocumentType.FINANCIAL_TURNOVER_CERTIFICATE),
        ("oem", DocumentType.OEM_AUTHORIZATION),
        ("pan", DocumentType.PAN_CARD),
        ("udyam", DocumentType.UDYAM_CERTIFICATE),
        ("msme", DocumentType.UDYAM_CERTIFICATE),
        ("incorporation", DocumentType.COMPANY_INCORPORATION),
        ("mca", DocumentType.COMPANY_INCORPORATION),
        ("local_content", DocumentType.LOCAL_CONTENT_DECLARATION),
        ("epfo", DocumentType.EPFO_REGISTRATION),
        ("esic", DocumentType.ESIC_REGISTRATION),
        ("bis", DocumentType.BIS_CERTIFICATE),
        ("startup", DocumentType.STARTUP_CERTIFICATE),
        ("nsic", DocumentType.NSIC_CERTIFICATE),
        ("blacklisting", DocumentType.NON_BLACKLISTING_DECLARATION),
        ("itr", DocumentType.INCOME_TAX_RETURN),
        ("income_tax", DocumentType.INCOME_TAX_RETURN),
    ]
    for kw, doc_type in mapping:
        if kw in fn:
            return doc_type
    return None



@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    bidder_id: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process a document.

    Phase 1: Extract and structure document data.
    Returns 409 Conflict if the same file (same SHA-256 hash) has already
    been uploaded for this bidder — preventing silent duplicates.
    """

    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Use PDF or image files."
        )

    # Read file bytes (needed for hash and saving)
    file_bytes = await file.read()

    # --- DUPLICATE DETECTION ---
    file_hash = compute_file_hash(file_bytes)

    existing = db.query(Document).filter(
        Document.bidder_id == bidder_id,
        Document.file_hash == file_hash
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Duplicate document detected. This exact file has already been uploaded.",
                "existing_document_id": existing.id,
                "existing_document_type": existing.document_type.value,
                "existing_file_name": existing.file_name,
                "existing_status": existing.status.value,
                "hint": "Use POST /api/documents/reprocess/{document_id} to re-extract this document."
            }
        )

    # Create bidder-specific directory
    bidder_dir = UPLOAD_DIR / bidder_id
    bidder_dir.mkdir(exist_ok=True)

    # Save file (use a unique name if file already exists on disk)
    file_path = bidder_dir / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Get file size
    file_size = len(file_bytes)

    # Create database record
    db_document = Document(
        bidder_id=bidder_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        file_hash=file_hash,
        status=ProcessingStatus.UPLOADED
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # Create BIDDER_DOCUMENTS_UPLOADED audit event
    audit_log = AuditLog(
        event_type=AuditEvent.BIDDER_DOCUMENTS_UPLOADED,
        bidder_id=bidder_id,
        action_description=f"Document uploaded: {file.filename} ({document_type.value})",
        event_metadata=json.dumps({
            "document_id": db_document.id,
            "document_type": document_type.value,
            "file_name": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type
        })
    )
    db.add(audit_log)
    db.commit()

    # Process document (synchronously for Phase 1)
    try:
        await process_document(db_document.id, db)
    except Exception as e:
        # Update status to failed
        db_document.status = ProcessingStatus.FAILED
        db_document.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    return db_document


@router.post("/upload-batch", response_model=BatchUploadResponse)
async def upload_batch_documents(
    bidder_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch upload up to 14 bidder documents in a single action.
    Performs content-based classification, mismatch detection, duplicate detection,
    and structured field extraction.
    """
    if len(files) > 14:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum 14 files allowed per batch upload. Received {len(files)} files."
        )

    processed_items = []
    successful_count = 0
    partially_count = 0
    failed_count = 0
    needs_review_count = 0
    duplicate_count = 0

    processor = DocumentProcessor()
    bidder_dir = UPLOAD_DIR / bidder_id
    bidder_dir.mkdir(exist_ok=True)

    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]

    for file in files:
        if file.content_type not in allowed_types:
            item = BatchDocumentItem(
                file_name=file.filename,
                document_type="UNKNOWN",
                status="FAILED",
                error_message=f"Unsupported file type {file.content_type}. Use PDF or images.",
                message=f"Unsupported file type {file.content_type}"
            )
            processed_items.append(item)
            failed_count += 1
            continue

        file_bytes = await file.read()
        file_hash = compute_file_hash(file_bytes)

        # Duplicate check
        existing = db.query(Document).filter(
            Document.bidder_id == bidder_id,
            Document.file_hash == file_hash
        ).first()

        if existing:
            item = BatchDocumentItem(
                id=existing.id,
                file_name=file.filename,
                document_type=existing.document_type.value,
                detected_type=existing.document_type.value,
                status="DUPLICATE",
                is_duplicate=True,
                extraction_confidence=existing.extraction_confidence,
                message="Duplicate document (same file content already exists)",
                extracted_data=existing.extracted_data
            )
            processed_items.append(item)
            duplicate_count += 1
            continue

        # Save file to disk
        file_path = bidder_dir / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        # Extract text & classify
        raw_text = processor.extract_text(str(file_path), file.content_type)
        predicted_type, confidence, classification_details = processor.classify_document(raw_text)

        expected_type = detect_expected_type_from_filename(file.filename)
        classification_mismatch = False
        status_str = "EXTRACTED"
        msg = None

        if expected_type and predicted_type and predicted_type != expected_type:
            classification_mismatch = True
            status_str = "NEEDS_REVIEW"
            needs_review_count += 1
            msg = f"Expected: {expected_type.value}, Detected: {predicted_type.value}, Confidence: {confidence*100:.1f}%, Status: NEEDS REVIEW"
        elif not predicted_type or confidence < 0.35 or classification_details.get("is_ambiguous"):
            status_str = "CLASSIFICATION_UNCERTAIN"
            needs_review_count += 1
            msg = f"Classification uncertain (Confidence: {confidence*100:.1f}%). Please review."

        final_doc_type = predicted_type or expected_type or DocumentType.GST_CERTIFICATE

        # Create Document DB record
        db_document = Document(
            bidder_id=bidder_id,
            document_type=final_doc_type,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=len(file_bytes),
            mime_type=file.content_type,
            file_hash=file_hash,
            raw_text=raw_text,
            status=ProcessingStatus.PROCESSING
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Extract structured fields
        try:
            extractor = get_extractor(final_doc_type)
            result = extractor.extract(raw_text)

            if isinstance(result, tuple):
                extracted_data, trace = result
            else:
                extracted_data = result
                trace = []

            db_document.extracted_data = extracted_data
            db_document.extraction_trace = trace

            if hasattr(extractor, 'compute_document_status') and trace:
                doc_status_str, doc_conf = extractor.compute_document_status(trace)
                db_document.extraction_confidence = doc_conf
                if doc_status_str == 'PARTIALLY_EXTRACTED':
                    db_document.status = ProcessingStatus.PARTIALLY_EXTRACTED
                    if status_str not in ["NEEDS_REVIEW", "CLASSIFICATION_UNCERTAIN"]:
                        status_str = "PARTIALLY_EXTRACTED"
                        partially_count += 1
                elif doc_status_str == 'EXTRACTION_FAILED':
                    db_document.status = ProcessingStatus.FAILED
                    status_str = "FAILED"
                    failed_count += 1
                else:
                    db_document.status = ProcessingStatus.EXTRACTED
                    if status_str not in ["NEEDS_REVIEW", "CLASSIFICATION_UNCERTAIN"]:
                        successful_count += 1
            else:
                db_document.status = ProcessingStatus.EXTRACTED
                db_document.extraction_confidence = 1.0 if trace else 0.5
                if status_str not in ["NEEDS_REVIEW", "CLASSIFICATION_UNCERTAIN"]:
                    successful_count += 1

            db_document.processing_completed_at = datetime.utcnow()
            db.commit()

            item = BatchDocumentItem(
                id=db_document.id,
                file_name=file.filename,
                document_type=final_doc_type.value,
                detected_type=predicted_type.value if predicted_type else None,
                expected_type=expected_type.value if expected_type else None,
                classification_confidence=round(confidence, 2),
                status=status_str,
                extraction_confidence=db_document.extraction_confidence,
                is_duplicate=False,
                classification_mismatch=classification_mismatch,
                message=msg,
                extracted_data=extracted_data
            )
            processed_items.append(item)

        except Exception as e:
            db_document.status = ProcessingStatus.FAILED
            db_document.error_message = str(e)
            db.commit()

            item = BatchDocumentItem(
                id=db_document.id,
                file_name=file.filename,
                document_type=final_doc_type.value,
                status="FAILED",
                error_message=str(e),
                message=f"Extraction failed: {str(e)}"
            )
            processed_items.append(item)
            failed_count += 1

    return BatchUploadResponse(
        bidder_id=bidder_id,
        total_files=len(files),
        processed=len(processed_items),
        successful=successful_count,
        partially_extracted=partially_count,
        failed=failed_count,
        needs_review=needs_review_count,
        duplicates=duplicate_count,
        documents=processed_items
    )


@router.post("/reprocess/{document_id}", response_model=DocumentExtractionResponse)
async def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Explicitly re-process an already-uploaded document.
    This is the only way to re-extract a duplicate document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        await process_document(document_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

    db.refresh(document)
    return document


async def process_document(document_id: int, db: Session):
    """
    Process uploaded document: extract text, classify, extract fields.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update status
    document.status = ProcessingStatus.PROCESSING
    document.processing_started_at = datetime.utcnow()
    db.commit()

    processor = DocumentProcessor()

    # Step 1: Extract text
    raw_text = processor.extract_text(document.file_path, document.mime_type)
    document.raw_text = raw_text

    # Step 2: Classify document
    predicted_type, confidence, classification_details = processor.classify_document(raw_text)

    # Log classification details (UTF-8 safe)
    try:
        print(f"\n=== CLASSIFICATION DEBUG ===")
        print(f"Selected document type: {document.document_type.value}")
        print(f"Detected document type: {predicted_type.value if predicted_type else 'None'}")
        print(f"Confidence: {confidence:.2f}")
        print(f"All scores: {classification_details.get('all_scores', {})}")
        # Safely log matched keywords without Unicode errors
        matched = classification_details.get('matched_keywords', {})
        for key, value in matched.items():
            print(f"  {key}: {len(value)} matches")
        text_preview = classification_details.get('text_preview', '')[:100]
        safe_preview = text_preview.encode('utf-8', errors='replace').decode('utf-8')
        print(f"Text preview: {safe_preview}")
        print(f"=== END DEBUG ===\n")
    except Exception as e:
        print(f"Debug logging error (non-critical): {str(e)}")

    # Step 3: Validate classification
    if predicted_type:
        is_valid, error_msg = processor.validate_classification(
            predicted_type,
            document.document_type,
            confidence,
            classification_details
        )
        if not is_valid:
            document.status = ProcessingStatus.FAILED
            document.error_message = error_msg
            db.commit()
            raise ValueError(error_msg)

    # Step 4: Extract structured fields
    try:
        extractor = get_extractor(document.document_type)
        result = extractor.extract(raw_text)

        # Extractors return a tuple (extracted_data, trace) or just a dict
        if isinstance(result, tuple):
            extracted_data, trace = result
        else:
            extracted_data = result
            trace = []

        document.extracted_data = extracted_data
        document.extraction_trace = trace

        # Dynamically compute document status and overall extraction confidence
        if hasattr(extractor, 'compute_document_status') and trace:
            doc_status_str, doc_conf = extractor.compute_document_status(trace)
            document.extraction_confidence = doc_conf
            if doc_status_str == 'PARTIALLY_EXTRACTED':
                document.status = ProcessingStatus.PARTIALLY_EXTRACTED
            elif doc_status_str == 'EXTRACTION_FAILED':
                document.status = ProcessingStatus.FAILED
            else:
                document.status = ProcessingStatus.EXTRACTED
        else:
            document.status = ProcessingStatus.EXTRACTED
            document.extraction_confidence = 1.0 if trace else 0.5

    except NotImplementedError as e:
        # Extractor not yet implemented — store raw text only
        document.extracted_data = {"note": str(e)}
        document.extraction_trace = []
        document.status = ProcessingStatus.FAILED

    document.processing_completed_at = datetime.utcnow()
    db.commit()


@router.get("/bidder/{bidder_id}", response_model=List[DocumentExtractionResponse])
async def get_bidder_documents(
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents for a bidder with extracted data (all statuses).
    """
    documents = db.query(Document).filter(
        Document.bidder_id == bidder_id
    ).all()

    return documents


@router.get("/{document_id}", response_model=DocumentExtractionResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get single document with extracted data.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/bidder/{bidder_id}/summary")
async def get_bidder_summary(
    bidder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary of all documents uploaded by bidder.
    Shows which of the 14 document types have been uploaded.

    BIDDER ISOLATION: Only counts documents belonging to this specific bidder_id.
    UNIQUE-TYPE COUNTING: For each of the 14 document types, only the most recent
    document record is considered — duplicate uploads don't inflate the count.
    total_documents reflects unique document types present (max 14), not raw DB rows.
    """
    all_docs = db.query(Document).filter(Document.bidder_id == bidder_id).all()

    # Keep only the most-recent record per document type (prevent 28/14 style inflation)
    latest_by_type: dict = {}
    for doc in all_docs:
        key = doc.document_type.value
        existing = latest_by_type.get(key)
        if existing is None:
            latest_by_type[key] = doc
        else:
            # Prefer the record with the later upload timestamp
            existing_ts = existing.uploaded_at or existing.processing_completed_at
            doc_ts = doc.uploaded_at or doc.processing_completed_at
            if doc_ts and (existing_ts is None or doc_ts > existing_ts):
                latest_by_type[key] = doc

    # Build per-type status from the deduplicated set
    # A type is "uploaded/verified" if its latest record has a non-failed status
    GOOD_STATUSES = {ProcessingStatus.EXTRACTED, ProcessingStatus.PARTIALLY_EXTRACTED}
    uploaded_types = [
        doc_type for doc_type, doc in latest_by_type.items()
        if doc.status in GOOD_STATUSES
    ]
    missing_types = [dt.value for dt in DocumentType if dt.value not in uploaded_types]

    # document_counts: 0 or 1 per type (unique presence)
    doc_counts = {dt.value: (1 if dt.value in latest_by_type else 0) for dt in DocumentType}

    return {
        "bidder_id": bidder_id,
        # total_documents = unique types present (max 14), NOT raw row count
        "total_documents": len(latest_by_type),
        "uploaded_document_types": uploaded_types,
        "missing_document_types": missing_types,
        "document_counts": doc_counts,
        "completion_percentage": (len(uploaded_types) / 14) * 100
    }


@router.delete("/clear-all")
async def clear_all_documents(
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Clear all document records from database and delete all uploaded files.
    """
    try:
        deleted_count = db.query(Document).delete()
        db.commit()

        # Remove uploaded files
        if UPLOAD_DIR.exists():
            for item in UPLOAD_DIR.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                elif item.is_file():
                    item.unlink(missing_ok=True)

        return {"message": "All document data cleared successfully", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.delete("/bidder/{bidder_id}/clear")
async def clear_bidder_documents(
    bidder_id: str,
    db: Session = Depends(get_db),
    current_officer: User = Depends(get_current_officer)
):
    """
    Clear all document records for a specific bidder.
    """
    try:
        deleted_count = db.query(Document).filter(Document.bidder_id == bidder_id).delete()
        db.commit()

        # Remove bidder uploaded files
        bidder_dir = UPLOAD_DIR / bidder_id
        if bidder_dir.exists():
            shutil.rmtree(bidder_dir, ignore_errors=True)

        return {"message": f"Data for bidder '{bidder_id}' cleared successfully", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear bidder data: {str(e)}")


@router.get("/classify-test/{document_id}")
async def classify_test(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Diagnostic endpoint to test document classification.

    Returns detailed classification results including:
    - Detected document type
    - Confidence score
    - Top 3 candidates with scores
    - Matched keywords for each type
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.raw_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    processor = DocumentProcessor()
    predicted_type, confidence, classification_details = processor.classify_document(document.raw_text)

    # Get top 3 candidates
    all_scores = classification_details.get("all_scores", {})
    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    top_candidates = [
        {
            "type": doc_type,
            "score": score,
            "confidence_pct": round((score / max(all_scores.values()) * 100) if all_scores else 0, 1)
        }
        for doc_type, score in sorted_scores
    ]

    # Get matched keywords for top candidates
    matched_keywords_detail = {}
    all_matched = classification_details.get("matched_keywords", {})

    for doc_type, score in sorted_scores:
        keywords = all_matched.get(doc_type, [])
        matched_keywords_detail[doc_type] = [
            {"keyword": kw, "weight": wt} for kw, wt in keywords
        ]

    return {
        "document_id": document_id,
        "file_name": document.file_name,
        "selected_type": document.document_type.value,
        "detected_type": predicted_type.value if predicted_type else None,
        "confidence": round(confidence * 100, 1),
        "top_candidates": top_candidates,
        "matched_keywords": matched_keywords_detail,
        "all_scores": all_scores,
        "is_ambiguous": classification_details.get("is_ambiguous", False),
        "text_preview": classification_details.get("text_preview", "")[:200]
    }
