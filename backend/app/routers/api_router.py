import os
import zipfile
import io
import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.all_models import (
    ProofPack, RentMonth, PaymentRecord, Receipt, ApprovalRequest, 
    UploadOperation, MockPortalDeclaration, MockPortalUpload, AuditEvent, TestExecutionReport
)
from backend.app.schemas.schemas import (
    ProofPackCreate, RentMonthUpdate, LandlordPanUpdate, 
    ApprovalDecisionRequest, MockUploadRequest, PortalStatusSimulationUpdate
)
from backend.app.mock_connectors.payment_connector import seed_payment_history, seed_mock_portal
from backend.app.services.reconciliation_service import reconcile_proof_pack, generate_month_range, get_month_label
from backend.app.services.receipt_service import generate_receipts_for_proof_pack
from backend.app.services.tax_rule_service import evaluate_pan_requirement, TaxRuleConfig
from backend.app.services.approval_upload_service import (
    create_or_get_approval_request, submit_approval_decision, execute_idempotent_upload, verify_employer_portal_upload
)
from backend.app.services.audit_service import log_audit_event
from backend.app.services.test_runner_service import (
    execute_tc1, execute_tc2, execute_tc3, execute_tc4, run_all_official_tests
)

router = APIRouter()

# ----------------- 1. Overview & Health -----------------
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RentWise AI — HRA Proof Pack Agent",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/overview/stats")
def get_overview_stats(proof_pack_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Real database-derived metrics for dashboard
    """
    pack = None
    if proof_pack_id:
        pack = db.query(ProofPack).filter(ProofPack.id == proof_pack_id).first()
    if not pack:
        pack = db.query(ProofPack).order_by(ProofPack.created_at.desc()).first()

    if not pack:
        return {
            "has_proof_pack": False,
            "total_rent_months": 0,
            "matched_payment_months": 0,
            "missing_payment_months": 0,
            "receipts_generated": 0,
            "items_awaiting_approval": 0,
            "uploads_awaiting_verification": 0,
            "verified_upload_outcomes": 0,
            "recent_packs": []
        }

    rent_months = db.query(RentMonth).filter(RentMonth.proof_pack_id == pack.id).all()
    matched_count = sum(1 for m in rent_months if m.matching_status == "MATCHED")
    missing_count = sum(1 for m in rent_months if m.matching_status == "MISSING_PAYMENT")
    receipts_count = db.query(Receipt).filter(Receipt.proof_pack_id == pack.id).count()
    awaiting_approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.proof_pack_id == pack.id,
        ApprovalRequest.status == "PENDING"
    ).count()
    awaiting_verification = db.query(UploadOperation).filter(
        UploadOperation.proof_pack_id == pack.id,
        UploadOperation.status.in_(["UPLOAD_SUCCEEDED", "PENDING_VERIFICATION"])
    ).count()
    verified_outcomes = db.query(UploadOperation).filter(
        UploadOperation.proof_pack_id == pack.id,
        UploadOperation.status.in_(["VERIFIED_APPROVED", "VERIFIED_REJECTED"])
    ).count()

    recent_packs = db.query(ProofPack).order_by(ProofPack.created_at.desc()).limit(10).all()

    return {
        "has_proof_pack": True,
        "selected_pack_id": pack.id,
        "tenant_name": pack.tenant_name,
        "financial_year": pack.financial_year,
        "status": pack.status,
        "total_rent_months": len(rent_months),
        "matched_payment_months": matched_count,
        "missing_payment_months": missing_count,
        "receipts_generated": receipts_count,
        "items_awaiting_approval": awaiting_approval,
        "uploads_awaiting_verification": awaiting_verification,
        "verified_upload_outcomes": verified_outcomes,
        "recent_packs": [
            {
                "id": p.id,
                "tenant_name": p.tenant_name,
                "financial_year": p.financial_year,
                "status": p.status,
                "monthly_rent": p.monthly_rent,
                "created_at": p.created_at.isoformat()
            }
            for p in recent_packs
        ]
    }

# ----------------- 2. Proof Pack Management -----------------
@router.post("/proof-packs")
def create_proof_pack(data: ProofPackCreate, db: Session = Depends(get_db)):
    pack_id = f"PK-{uuid.uuid4().hex[:8].upper()}"
    months = generate_month_range(data.start_month, data.end_month)
    
    # Calculate estimated annual rent
    total_months = len(months)
    annual_rent = total_months * data.monthly_rent
    
    pan_eval = evaluate_pan_requirement(annual_rent=annual_rent, landlord_pan=data.landlord_pan)

    pack = ProofPack(
        id=pack_id,
        tenant_name=data.tenant_name,
        employee_id=data.employee_id,
        employer_name=data.employer_name,
        work_location=data.work_location,
        financial_year=data.financial_year,
        declaration_period=data.declaration_period,
        landlord_name=data.landlord_name,
        landlord_address=data.landlord_address,
        landlord_contact=data.landlord_contact,
        landlord_pan=data.landlord_pan,
        monthly_rent=data.monthly_rent,
        deposit_amount=data.deposit_amount or 0,
        rent_agreement_ref=data.rent_agreement_ref,
        start_month=data.start_month,
        end_month=data.end_month,
        pan_threshold_applied=TaxRuleConfig.threshold_amount,
        pan_required=pan_eval["pan_required"],
        pan_rule_source=TaxRuleConfig.source,
        status="DRAFT"
    )
    db.add(pack)
    db.commit()

    # Seed mock payments if bank source is netbanking
    seed_payment_history(db, exclude_march=False, tenant_name=data.tenant_name, payee_name=data.landlord_name, monthly_amount=data.monthly_rent)
    seed_mock_portal(db)

    # Initialize Rent Months
    rent_months = []
    for m in months:
        rm = RentMonth(
            id=f"RM-{pack_id[-6:]}-{m.replace('-', '')}",
            proof_pack_id=pack_id,
            month_str=m,
            month_label=get_month_label(m),
            expected_rent=data.monthly_rent,
            allocated_amount=0,
            difference=data.monthly_rent,
            matching_status="AWAITING_RECONCILIATION",
            explanation="Initial draft. Payment matching pending."
        )
        rent_months.append(rm)
    
    db.add_all(rent_months)
    db.commit()

    log_audit_event(
        db=db,
        entity_id=pack_id,
        entity_type="PROOF_PACK",
        event_type="PROOF_PACK_CREATED",
        actor_identity="TENANT_USER",
        after_state={"tenant": data.tenant_name, "annual_rent": annual_rent, "months": len(months)},
        reason="Proof Pack initialized via guided intake form"
    )

    return {"proof_pack_id": pack_id, "months_created": len(months), "pan_evaluation": pan_eval}

@router.get("/proof-packs/{pack_id}")
def get_proof_pack(pack_id: str, db: Session = Depends(get_db)):
    pack = db.query(ProofPack).filter(ProofPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Proof pack not found")

    rent_months = db.query(RentMonth).filter(RentMonth.proof_pack_id == pack_id).order_by(RentMonth.month_str.asc()).all()
    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == pack_id).all()
    approval_req = db.query(ApprovalRequest).filter(
        ApprovalRequest.proof_pack_id == pack_id,
        ApprovalRequest.proof_pack_version == pack.version
    ).order_by(ApprovalRequest.created_at.desc()).first()
    upload_op = db.query(UploadOperation).filter(UploadOperation.proof_pack_id == pack_id).order_by(UploadOperation.created_at.desc()).first()

    total_expected = sum(m.expected_rent for m in rent_months)
    total_allocated = sum(m.allocated_amount for m in rent_months)
    pan_eval = evaluate_pan_requirement(annual_rent=total_allocated or total_expected, landlord_pan=pack.landlord_pan, threshold=pack.pan_threshold_applied)

    return {
        "proof_pack": {
            "id": pack.id,
            "tenant_name": pack.tenant_name,
            "employee_id": pack.employee_id,
            "employer_name": pack.employer_name,
            "work_location": pack.work_location,
            "financial_year": pack.financial_year,
            "declaration_period": pack.declaration_period,
            "landlord_name": pack.landlord_name,
            "landlord_address": pack.landlord_address,
            "landlord_contact": pack.landlord_contact,
            "landlord_pan": pack.landlord_pan,
            "monthly_rent": pack.monthly_rent,
            "start_month": pack.start_month,
            "end_month": pack.end_month,
            "status": pack.status,
            "version": pack.version,
            "created_at": pack.created_at.isoformat()
        },
        "tax_evaluation": pan_eval,
        "rent_months": [
            {
                "id": m.id,
                "month_str": m.month_str,
                "month_label": m.month_label,
                "expected_rent": m.expected_rent,
                "allocated_amount": m.allocated_amount,
                "difference": m.difference,
                "matching_status": m.matching_status,
                "matching_method": m.matching_method,
                "confidence": m.confidence,
                "explanation": m.explanation,
                "transaction_references": m.transaction_references,
                "is_eligible_for_receipt": m.is_eligible_for_receipt
            }
            for m in rent_months
        ],
        "receipts": [
            {
                "id": r.id,
                "month_str": r.month_str,
                "month_label": r.month_label,
                "amount": r.amount,
                "payment_date": r.actual_payment_date,
                "payment_reference": r.payment_reference,
                "pdf_sha256": r.pdf_sha256,
                "requires_signature": r.requires_landlord_signature
            }
            for r in receipts
        ],
        "approval_request": {
            "id": approval_req.id,
            "status": approval_req.status,
            "total_claimed_rent": approval_req.total_claimed_rent,
            "receipt_count": approval_req.receipt_count,
            "destination_portal": approval_req.destination_portal,
            "approver_identity": approval_req.approver_identity,
            "decision_timestamp": approval_req.decision_timestamp.isoformat() if approval_req.decision_timestamp else None,
            "reason_notes": approval_req.reason_notes
        } if approval_req else None,
        "upload_operation": {
            "id": upload_op.id,
            "status": upload_op.status,
            "portal_upload_ref": upload_op.portal_upload_ref,
            "latest_verified_status": upload_op.latest_verified_status,
            "verification_timestamp": upload_op.verification_timestamp.isoformat() if upload_op.verification_timestamp else None,
            "discrepancy_explanation": upload_op.discrepancy_explanation
        } if upload_op else None
    }

@router.put("/proof-packs/{pack_id}/landlord-pan")
def update_landlord_pan(pack_id: str, data: LandlordPanUpdate, db: Session = Depends(get_db)):
    pack = db.query(ProofPack).filter(ProofPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Proof pack not found")

    old_pan = pack.landlord_pan
    pack.landlord_pan = data.landlord_pan.strip().upper()
    pack.version += 1
    db.commit()

    log_audit_event(
        db=db,
        entity_id=pack.id,
        entity_type="PROOF_PACK",
        event_type="LANDLORD_PAN_UPDATED",
        actor_identity="TENANT_USER",
        before_state={"landlord_pan": old_pan},
        after_state={"landlord_pan": pack.landlord_pan, "new_version": pack.version},
        reason="Landlord PAN supplied to comply with statutory HRA threshold rules"
    )

    return {"message": "Landlord PAN updated", "proof_pack_version": pack.version}

# ----------------- 3. Reconciliation & Receipts -----------------
@router.post("/proof-packs/{pack_id}/reconcile")
def run_reconciliation(pack_id: str, db: Session = Depends(get_db)):
    try:
        res = reconcile_proof_pack(db, pack_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/proof-packs/{pack_id}/generate-receipts")
def generate_receipts(pack_id: str, db: Session = Depends(get_db)):
    try:
        res = generate_receipts_for_proof_pack(db, pack_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receipts/{receipt_id}/download")
def download_receipt(receipt_id: str, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt or not os.path.exists(receipt.pdf_path):
        raise HTTPException(status_code=404, detail="Receipt PDF not found")
    return FileResponse(
        receipt.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(receipt.pdf_path)
    )

@router.get("/proof-packs/{pack_id}/download-zip")
def download_all_receipts_zip(pack_id: str, db: Session = Depends(get_db)):
    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == pack_id).all()
    if not receipts:
        raise HTTPException(status_code=404, detail="No receipts found for this proof pack")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for r in receipts:
            if os.path.exists(r.pdf_path):
                zip_file.write(r.pdf_path, arcname=os.path.basename(r.pdf_path))
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=RentWise_Receipts_{pack_id}.zip"}
    )

# ----------------- 4. Approval Gate -----------------
@router.post("/proof-packs/{pack_id}/approval-request")
def request_approval(pack_id: str, db: Session = Depends(get_db)):
    try:
        app_req = create_or_get_approval_request(db, pack_id)
        return {
            "approval_request_id": app_req.id,
            "status": app_req.status,
            "receipt_count": app_req.receipt_count,
            "total_claimed_rent": app_req.total_claimed_rent,
            "destination_portal": app_req.destination_portal,
            "approved_file_hashes": json.loads(app_req.approved_file_hashes)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/approval-requests/{approval_id}/decision")
def record_approval_decision(approval_id: str, data: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    try:
        res = submit_approval_decision(
            db=db,
            approval_request_id=approval_id,
            decision=data.decision,
            approver_identity=data.approver_identity,
            reason_notes=data.reason_notes
        )
        return {
            "approval_request_id": res.id,
            "status": res.status,
            "approver": res.approver_identity,
            "decision_timestamp": res.decision_timestamp.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- 5. Upload & Verification -----------------
@router.post("/approval-requests/{approval_id}/upload")
def upload_to_employer(approval_id: str, db: Session = Depends(get_db)):
    try:
        res = execute_idempotent_upload(db, approval_id, simulated_portal_status="PENDING_VERIFICATION")
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-operations/{upload_op_id}/verify")
def verify_upload(upload_op_id: str, db: Session = Depends(get_db)):
    try:
        res = verify_employer_portal_upload(db, upload_op_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- 6. Mock Portal Endpoints -----------------
@router.get("/mock-portal/declarations")
def list_mock_declarations(db: Session = Depends(get_db)):
    decls = db.query(MockPortalDeclaration).all()
    return decls

@router.get("/mock-portal/uploads/{upload_id}")
def get_mock_upload_status(upload_id: str, db: Session = Depends(get_db)):
    upl = db.query(MockPortalUpload).filter(MockPortalUpload.id == upload_id).first()
    if not upl:
        raise HTTPException(status_code=404, detail="Upload record not found on Employer Portal")
    return {
        "id": upl.id,
        "declaration_id": upl.declaration_id,
        "status": upl.status,
        "file_count": upl.file_count,
        "payload_hash": upl.payload_hash,
        "submission_timestamp": upl.submission_timestamp.isoformat(),
        "notes": upl.simulated_reviewer_notes
    }

@router.put("/mock-portal/uploads/{upload_id}/simulate-status")
def simulate_employer_status(upload_id: str, data: PortalStatusSimulationUpdate, db: Session = Depends(get_db)):
    upl = db.query(MockPortalUpload).filter(MockPortalUpload.id == upload_id).first()
    if not upl:
        raise HTTPException(status_code=404, detail="Upload record not found")
    
    upl.status = data.status
    if data.status == "VERIFIED_APPROVED":
        upl.simulated_reviewer_notes = "Employer Payroll Audit Completed: All rent receipts verified and approved."
    elif data.status == "VERIFIED_REJECTED":
        upl.simulated_reviewer_notes = "Employer Payroll Audit Rejected: Address proof conflict detected."
    db.commit()
    return {"message": f"Simulated status updated to {data.status}"}

# ----------------- 7. Audit Trail -----------------
@router.get("/audit-events")
def get_audit_trail(entity_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AuditEvent)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    events = query.order_by(AuditEvent.timestamp.desc()).limit(100).all()
    
    return [
        {
            "id": e.id,
            "entity_id": e.entity_id,
            "entity_type": e.entity_type,
            "event_type": e.event_type,
            "actor_identity": e.actor_identity,
            "timestamp": e.timestamp.isoformat(),
            "correlation_id": e.correlation_id,
            "before_state": json.loads(e.before_state) if e.before_state else None,
            "after_state": json.loads(e.after_state) if e.after_state else None,
            "evidence_references": json.loads(e.evidence_references) if e.evidence_references else None,
            "reason": e.reason
        }
        for e in events
    ]

# ----------------- 8. Test Lab & Quick Demos -----------------
@router.post("/test-lab/run-all")
def run_all_tests(db: Session = Depends(get_db)):
    return run_all_official_tests(db)

@router.post("/test-lab/run-tc1")
def run_tc1(db: Session = Depends(get_db)):
    return execute_tc1(db)

@router.post("/test-lab/run-tc2")
def run_tc2(db: Session = Depends(get_db)):
    return execute_tc2(db)

@router.post("/test-lab/run-tc3")
def run_tc3(db: Session = Depends(get_db)):
    return execute_tc3(db)

@router.post("/test-lab/run-tc4")
def run_tc4(db: Session = Depends(get_db)):
    return execute_tc4(db)

@router.get("/test-lab/reports")
def get_test_reports(db: Session = Depends(get_db)):
    reports = db.query(TestExecutionReport).order_by(TestExecutionReport.executed_at.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "test_case_id": r.test_case_id,
            "test_case_name": r.test_case_name,
            "status": r.status,
            "executed_at": r.executed_at.isoformat(),
            "inputs_summary": r.inputs_summary,
            "expected_result": r.expected_result,
            "actual_result": r.actual_result,
            "assertions": json.loads(r.assertions) if r.assertions else [],
            "explanation": r.explanation
        }
        for r in reports
    ]

@router.post("/demo/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    Cleans database and re-initializes fresh baseline demo data.
    """
    db.query(Receipt).delete()
    db.query(RentMonth).delete()
    db.query(UploadOperation).delete()
    db.query(ApprovalRequest).delete()
    db.query(ProofPack).delete()
    db.query(MockPortalUpload).delete()
    db.query(PaymentRecord).delete()
    # Do not delete TestExecutionReport or AuditEvent to preserve auditability & test history
    db.commit()

    seed_mock_portal(db)
    
    # Preload TC1 as initial baseline
    execute_tc1(db)

    return {"message": "Demo data successfully reset to clean baseline with TC1 preloaded."}
