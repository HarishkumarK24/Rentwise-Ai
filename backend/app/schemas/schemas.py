from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Tenant and Declaration Inputs
class ProofPackCreate(BaseModel):
    tenant_name: str = Field(..., example="Aarav Sharma")
    employee_id: str = Field(..., example="EMP-8921")
    employer_name: str = Field(..., example="Acme Technologies Pvt Ltd")
    work_location: Optional[str] = Field("Bengaluru", example="Bengaluru")
    financial_year: str = Field("2025-2026", example="2025-2026")
    declaration_period: str = Field("Apr 2025 - Mar 2026", example="Apr 2025 - Mar 2026")
    
    landlord_name: str = Field(..., example="Suresh R. Verma")
    landlord_address: str = Field(..., example="#402, Green Glen Heights, Bellandur, Bengaluru 560103")
    landlord_contact: Optional[str] = Field("+91-9876543210")
    landlord_pan: Optional[str] = Field(None, example="ABCDE1234F")
    monthly_rent: int = Field(..., gt=0, example=25000) # Monthly rent in Rupees
    deposit_amount: Optional[int] = Field(0, ge=0)
    rent_agreement_ref: Optional[str] = Field("AGR-BLR-2025-99")
    
    start_month: str = Field("2025-04", example="2025-04")
    end_month: str = Field("2026-03", example="2026-03")
    payment_source: Optional[str] = Field("HDFC_NETBANKING")

class RentMonthUpdate(BaseModel):
    allocated_amount: Optional[int] = None
    matching_status: Optional[str] = None
    explanation: Optional[str] = None

class LandlordPanUpdate(BaseModel):
    landlord_pan: str

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., example="APPROVE") # APPROVE, REJECT, REQUEST_CHANGES
    approver_identity: str = Field(..., example="Aarav Sharma (Employee)")
    reason_notes: Optional[str] = Field(None)

class MockUploadRequest(BaseModel):
    idempotency_key: str
    proof_pack_id: str
    approval_request_id: str
    destination_portal: str
    destination_declaration_id: str
    file_hashes: List[str]

class PortalStatusSimulationUpdate(BaseModel):
    status: str # PENDING_VERIFICATION, VERIFIED_APPROVED, VERIFIED_REJECTED

class AuditEventRead(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    event_type: str
    actor_identity: str
    timestamp: datetime
    correlation_id: Optional[str]
    before_state: Optional[str]
    after_state: Optional[str]
    evidence_references: Optional[str]
    reason: Optional[str]
