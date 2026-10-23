import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class MonthMatchingStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MISSING_PAYMENT = "MISSING_PAYMENT"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    DUPLICATE_SUSPECTED = "DUPLICATE_SUSPECTED"
    AMBIGUOUS = "AMBIGUOUS"
    READY_FOR_RECEIPT = "READY_FOR_RECEIPT"

class ProofPackStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RECONCILED = "RECONCILED"
    PAN_REQUIRED = "PAN_REQUIRED"
    RECEIPTS_GENERATED = "RECEIPTS_GENERATED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UPLOAD_QUEUED = "UPLOAD_QUEUED"
    UPLOAD_SUCCEEDED = "UPLOAD_SUCCEEDED"
    UPLOAD_FAILED = "UPLOAD_FAILED"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    INVALIDATED = "INVALIDATED"

class UploadOperationStatus(str, enum.Enum):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    UPLOAD_QUEUED = "UPLOAD_QUEUED"
    UPLOAD_SUCCEEDED = "UPLOAD_SUCCEEDED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED_APPROVED = "VERIFIED_APPROVED"
    VERIFIED_REJECTED = "VERIFIED_REJECTED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

class ProofPack(Base):
    __tablename__ = "proof_packs"

    id = Column(String, primary_key=True, index=True)
    tenant_name = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    employer_name = Column(String, nullable=False)
    work_location = Column(String, nullable=True)
    financial_year = Column(String, nullable=False) # e.g. "2025-2026"
    declaration_period = Column(String, nullable=False) # e.g. "Apr 2025 - Mar 2026"
    
    # Landlord
    landlord_name = Column(String, nullable=False)
    landlord_address = Column(String, nullable=False)
    landlord_contact = Column(String, nullable=True)
    landlord_pan = Column(String, nullable=True)
    monthly_rent = Column(Integer, nullable=False) # in minor units (paise/cents) or direct rupees
    deposit_amount = Column(Integer, default=0)
    rent_agreement_ref = Column(String, nullable=True)
    
    # Timeline
    start_month = Column(String, nullable=False) # YYYY-MM
    end_month = Column(String, nullable=False)   # YYYY-MM
    
    # Policy / Tax info
    pan_threshold_applied = Column(Integer, default=100000)
    pan_required = Column(Boolean, default=False)
    pan_rule_source = Column(String, default="Indian Income Tax Act Section 10(13A) / CBDT Circular (configured demonstration policy)")
    
    status = Column(String, default=ProofPackStatus.DRAFT.value)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    rent_months = relationship("RentMonth", back_populates="proof_pack", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="proof_pack", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="proof_pack", cascade="all, delete-orphan")
    upload_operations = relationship("UploadOperation", back_populates="proof_pack", cascade="all, delete-orphan")

class RentMonth(Base):
    __tablename__ = "rent_months"

    id = Column(String, primary_key=True, index=True)
    proof_pack_id = Column(String, ForeignKey("proof_packs.id"), nullable=False, index=True)
    month_str = Column(String, nullable=False) # "2025-04"
    month_label = Column(String, nullable=False) # "April 2025"
    expected_rent = Column(Integer, nullable=False) # in Rupees
    allocated_amount = Column(Integer, default=0)
    difference = Column(Integer, default=0)
    
    matching_status = Column(String, default=MonthMatchingStatus.MISSING_PAYMENT.value)
    matching_method = Column(String, default="RULE_EXACT_OR_WINDOW")
    confidence = Column(String, default="CERTAIN")
    explanation = Column(Text, default="Awaiting payment reconciliation")
    
    transaction_references = Column(Text, default="") # comma-separated
    is_eligible_for_receipt = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    proof_pack = relationship("ProofPack", back_populates="rent_months")
    receipt = relationship("Receipt", back_populates="rent_month", uselist=False)

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(String, primary_key=True, index=True)
    source_system = Column(String, nullable=False) # e.g. "HDFC_NETBANKING", "UPI_LOG"
    source_record_id = Column(String, nullable=False)
    tenant_name = Column(String, nullable=False)
    payee_name = Column(String, nullable=False)
    transaction_date = Column(String, nullable=False) # YYYY-MM-DD
    amount = Column(Integer, nullable=False) # in Rupees
    payment_reference = Column(String, nullable=False, unique=True, index=True)
    payment_method = Column(String, default="NET_BANKING")
    description = Column(String, nullable=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=utcnow)
    evidence_reference = Column(String, nullable=True) # doc/hash/statement ref
    matching_status = Column(String, default="UNMATCHED") # UNMATCHED, MATCHED, DUPLICATE_SUSPECTED

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String, primary_key=True, index=True)
    proof_pack_id = Column(String, ForeignKey("proof_packs.id"), nullable=False, index=True)
    rent_month_id = Column(String, ForeignKey("rent_months.id"), nullable=False, unique=True, index=True)
    
    tenant_name = Column(String, nullable=False)
    landlord_name = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    landlord_pan = Column(String, nullable=True)
    
    month_label = Column(String, nullable=False)
    month_str = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    actual_payment_date = Column(String, nullable=False)
    payment_reference = Column(String, nullable=False)
    payment_method = Column(String, default="NET_BANKING")
    
    pdf_path = Column(String, nullable=False)
    pdf_sha256 = Column(String, nullable=False)
    requires_landlord_signature = Column(Boolean, default=True)
    is_draft = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    proof_pack = relationship("ProofPack", back_populates="receipts")
    rent_month = relationship("RentMonth", back_populates="receipt")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, index=True)
    proof_pack_id = Column(String, ForeignKey("proof_packs.id"), nullable=False, index=True)
    proof_pack_version = Column(Integer, nullable=False)
    status = Column(String, default=ApprovalStatus.PENDING.value)
    
    total_claimed_rent = Column(Integer, nullable=False)
    receipt_count = Column(Integer, nullable=False)
    approved_file_hashes = Column(Text, nullable=False) # JSON or comma-separated SHA-256
    destination_portal = Column(String, nullable=False) # e.g. "ACME_CORP_PEOPLE_PORTAL"
    destination_declaration_id = Column(String, nullable=False)
    
    approver_identity = Column(String, nullable=True)
    decision_timestamp = Column(DateTime(timezone=True), nullable=True)
    reason_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    proof_pack = relationship("ProofPack", back_populates="approval_requests")
    upload_operation = relationship("UploadOperation", back_populates="approval_request", uselist=False)

class UploadOperation(Base):
    __tablename__ = "upload_operations"

    id = Column(String, primary_key=True, index=True)
    proof_pack_id = Column(String, ForeignKey("proof_packs.id"), nullable=False, index=True)
    approval_request_id = Column(String, ForeignKey("approval_requests.id"), nullable=False, index=True)
    
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    payload_hash = Column(String, nullable=False)
    destination_portal = Column(String, nullable=False)
    destination_declaration_id = Column(String, nullable=False)
    
    status = Column(String, default=UploadOperationStatus.APPROVAL_REQUIRED.value)
    portal_upload_ref = Column(String, nullable=True, index=True)
    portal_initial_response = Column(Text, nullable=True)
    
    # Verification details
    latest_verified_status = Column(String, nullable=True)
    verification_timestamp = Column(DateTime(timezone=True), nullable=True)
    verification_raw_response = Column(Text, nullable=True)
    discrepancy_explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    proof_pack = relationship("ProofPack", back_populates="upload_operations")
    approval_request = relationship("ApprovalRequest", back_populates="upload_operation")

class MockPortalDeclaration(Base):
    __tablename__ = "mock_portal_declarations"

    id = Column(String, primary_key=True, index=True) # e.g. "DECL-2025-ACME-001"
    tenant_name = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    financial_year = Column(String, nullable=False)
    component = Column(String, default="HOUSE_RENT_ALLOWANCE")
    status = Column(String, default="PENDING_SUBMISSION") # PENDING_SUBMISSION, PENDING_VERIFICATION, APPROVED, REJECTED
    uploaded_files_count = Column(Integer, default=0)
    uploaded_files_summary = Column(Text, default="[]")
    last_upload_ref = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class MockPortalUpload(Base):
    __tablename__ = "mock_portal_uploads"

    id = Column(String, primary_key=True, index=True) # e.g. "UPL-MOCK-98213"
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    declaration_id = Column(String, nullable=False, index=True)
    proof_pack_id = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    file_hashes = Column(Text, nullable=False)
    file_count = Column(Integer, nullable=False)
    status = Column(String, default="PENDING_VERIFICATION") # PENDING_VERIFICATION, VERIFIED_APPROVED, VERIFIED_REJECTED
    submission_timestamp = Column(DateTime(timezone=True), default=utcnow)
    simulated_reviewer_notes = Column(Text, nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True)
    entity_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False) # PROOF_PACK, APPROVAL, UPLOAD, TEST_RUN
    event_type = Column(String, nullable=False)
    actor_identity = Column(String, nullable=False, default="AGENT_SYSTEM")
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
    correlation_id = Column(String, nullable=True, index=True)
    before_state = Column(Text, nullable=True)
    after_state = Column(Text, nullable=True)
    evidence_references = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

class TestExecutionReport(Base):
    __tablename__ = "test_execution_reports"

    id = Column(String, primary_key=True, index=True)
    test_case_id = Column(String, nullable=False)
    test_case_name = Column(String, nullable=False)
    status = Column(String, nullable=False) # PASS, FAIL, BLOCKED
    executed_at = Column(DateTime(timezone=True), default=utcnow)
    inputs_summary = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    actual_result = Column(Text, nullable=False)
    assertions = Column(Text, nullable=False) # JSON list of assertion checks
    evidence_and_records = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
