"""
AI Tender Compliance Copilot - Phase 1: Document Intelligence
FastAPI backend for document upload, processing, and extraction
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

from app.database import engine, Base
from app.api.routes import documents, verification, tenders, decisions, auth
from sqlalchemy import inspect, text

# Create database tables
Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite schema if new columns are missing
with engine.connect() as conn:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if 'documents' in table_names:
        columns = [c['name'] for c in inspector.get_columns('documents')]
        if 'file_hash' not in columns:
            conn.execute(text("ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64)"))
            conn.commit()
        if 'extraction_trace' not in columns:
            conn.execute(text("ALTER TABLE documents ADD COLUMN extraction_trace JSON"))
            conn.commit()
        if 'extraction_confidence' not in columns:
            conn.execute(text("ALTER TABLE documents ADD COLUMN extraction_confidence REAL"))
            conn.commit()

    if 'verification_sessions' in table_names:
        columns = [c['name'] for c in inspector.get_columns('verification_sessions')]
        if 'meta_data' not in columns:
            conn.execute(text("ALTER TABLE verification_sessions ADD COLUMN meta_data JSON"))
            conn.commit()

    if 'verification_results' in table_names:
        columns = [c['name'] for c in inspector.get_columns('verification_results')]
        if 'meta_data' not in columns:
            conn.execute(text("ALTER TABLE verification_results ADD COLUMN meta_data JSON"))
            conn.commit()

# Startup schema verification check
def verify_schema():
    from app.models.document import Document
    from app.models.verification import VerificationSession, VerificationResult
    from app.models.tender import Tender, TenderRequirement, TenderComplianceResult, BidderRiskAssessment
    from app.models.decision import OfficerDecision, AuditLog
    from app.models.user import User

    inspector = inspect(engine)
    models_to_check = [
        (Document, 'documents'),
        (VerificationSession, 'verification_sessions'),
        (VerificationResult, 'verification_results'),
        (Tender, 'tenders'),
        (TenderRequirement, 'tender_requirements'),
        (TenderComplianceResult, 'tender_compliance_results'),
        (BidderRiskAssessment, 'bidder_risk_assessments'),
        (OfficerDecision, 'officer_decisions'),
        (AuditLog, 'audit_logs'),
        (User, 'users')
    ]

    missing_schema = []
    for model, table_name in models_to_check:
        if table_name not in inspector.get_table_names():
            missing_schema.append(f"Table '{table_name}' does not exist in database")
            continue

        db_columns = {c['name'] for c in inspector.get_columns(table_name)}
        model_mapper = inspect(model)
        for col_attr in model_mapper.columns:
            if col_attr.name not in db_columns:
                missing_schema.append(f"Table '{table_name}' missing column '{col_attr.name}'")

    if missing_schema:
        error_msg = f"DATABASE SCHEMA MIGRATION ERROR: {'; '.join(missing_schema)}"
        print(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)

verify_schema()

# Seed demo users for Phase 7
def seed_demo_users_on_startup():
    """Create demo users if they don't exist"""
    from app.database import SessionLocal
    from app.services.auth.seed import seed_demo_users

    db = SessionLocal()
    try:
        seed_demo_users(db)
    except Exception as e:
        print(f"[WARNING] Failed to seed demo users: {e}")
    finally:
        db.close()

# Run seed after schema verification (skip during test collection)
import sys
if "pytest" not in sys.modules:
    seed_demo_users_on_startup()


app = FastAPI(
    title="Tender Compliance Copilot - Phase 1, 2 & 6",
    description="Document Intelligence & Tender Requirement Compliance Engine",
    version="1.0.0"
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5176",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5200",
        "http://localhost:3000",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5200",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):(517[0-9]|5200|3000)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(verification.router, prefix="/api/verification", tags=["verification"])
app.include_router(tenders.router, prefix="/api/tenders", tags=["tenders"])
app.include_router(decisions.router, prefix="/api/tenders", tags=["decisions"])

@app.get("/")
async def root():
    return {
        "message": "Tender Compliance Copilot API - Phase 1, 2 & 6",
        "phase_1": "Document Intelligence (Complete)",
        "phase_2": "Verification Engine (Active)",
        "phase_6": "Tender Requirement Engine (Active)",
        "supported_documents": 14,
        "verification_mode": "SANDBOX"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "phase": "6", "verification_mode": "SANDBOX"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
