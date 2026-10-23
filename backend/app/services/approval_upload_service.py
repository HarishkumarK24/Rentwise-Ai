import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.all_models import (
    ProofPack, Receipt, ApprovalRequest, UploadOperation,
    ApprovalStatus, UploadOperationStatus, MockPortalUpload, MockPortalDeclaration
)
from backend.app.services.audit_service import log_audit_event
from backend.app.services.tax_rule_service import evaluate_pan_requirement

def create_or_get_approval_request(db: Session, proof_pack_id: str) -> ApprovalRequest:
    """
    Creates an approval request for a proof pack.
    Binds the approval to exact receipt file hashes and destination.
    Enforces PAN blocking if required.
    """
    proof_pack = db.query(ProofPack).filter(ProofPack.id == proof_pack_id).first()
    if not proof_pack:
        raise ValueError(f"Proof pack {proof_pack_id} not found")
        
    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == proof_pack_id).all()
    if not receipts:
        raise ValueError("Cannot request approval: No receipts generated yet")

    # Evaluate PAN rules
    total_annual = sum(r.amount for r in receipts)
    pan_eval = evaluate_pan_requirement(
        annual_rent=total_annual,
        landlord_pan=proof_pack.landlord_pan,
        threshold=proof_pack.pan_threshold_applied
    )
    
    if pan_eval["status"] == "PAN_REQUIRED_BLOCKING":
        proof_pack.status = "PAN_REQUIRED"
        db.commit()
        raise ValueError(
            f"Submission Blocked by Statutory Tax Rules: {pan_eval['explanation']}"
        )

    file_hashes = [r.pdf_sha256 for r in receipts]
    hashes_str = json.dumps(sorted(file_hashes))

    # Check if an active pending approval request exists
    existing = db.query(ApprovalRequest).filter(
        ApprovalRequest.proof_pack_id == proof_pack_id,
        ApprovalRequest.proof_pack_version == proof_pack.version,
        ApprovalRequest.status.in_([ApprovalStatus.PENDING.value, ApprovalStatus.APPROVED.value])
    ).first()

    if existing:
        # Check payload integrity: if hashes changed, invalidate prior approval
        if existing.approved_file_hashes != hashes_str:
            existing.status = ApprovalStatus.INVALIDATED.value
            log_audit_event(
                db=db,
                entity_id=existing.id,
                entity_type="APPROVAL",
                event_type="APPROVAL_INVALIDATED",
                reason="Payload contents or receipt hashes changed after prior approval was generated"
            )
        else:
            return existing

    app_req = ApprovalRequest(
        id=f"APP-{uuid.uuid4().hex[:10].upper()}",
        proof_pack_id=proof_pack.id,
        proof_pack_version=proof_pack.version,
        status=ApprovalStatus.PENDING.value,
        total_claimed_rent=total_annual,
        receipt_count=len(receipts),
        approved_file_hashes=hashes_str,
        destination_portal="ACME_CORP_PEOPLE_PORTAL",
        destination_declaration_id="DECL-2025-ACME-001"
    )
    db.add(app_req)
    proof_pack.status = "APPROVAL_REQUESTED"
    db.commit()
    db.refresh(app_req)

    log_audit_event(
        db=db,
        entity_id=app_req.id,
        entity_type="APPROVAL",
        event_type="APPROVAL_REQUEST_CREATED",
        after_state={
            "proof_pack_id": proof_pack.id,
            "receipt_count": len(receipts),
            "total_rent": total_annual,
            "hashes": file_hashes
        },
        reason="Human Approval Gate initiated before mock employer portal submission"
    )

    return app_req

def submit_approval_decision(
    db: Session,
    approval_request_id: str,
    decision: str,
    approver_identity: str,
    reason_notes: str = None
) -> ApprovalRequest:
    """
    Submits user decision: APPROVE, REJECT, or REQUEST_CHANGES
    """
    app_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_request_id).first()
    if not app_req:
        raise ValueError(f"Approval request {approval_request_id} not found")
        
    if app_req.status == ApprovalStatus.INVALIDATED.value:
        raise ValueError("Cannot decide on an invalidated approval request. A newer version exists.")

    proof_pack = db.query(ProofPack).filter(ProofPack.id == app_req.proof_pack_id).first()

    if decision.upper() == "APPROVE":
        app_req.status = ApprovalStatus.APPROVED.value
        proof_pack.status = "APPROVED"
    elif decision.upper() == "REJECT":
        app_req.status = ApprovalStatus.REJECTED.value
        proof_pack.status = "REJECTED"
    elif decision.upper() in ["REQUEST_CHANGES", "CHANGES_REQUESTED"]:
        app_req.status = ApprovalStatus.CHANGES_REQUESTED.value
        proof_pack.status = "CHANGES_REQUESTED"
    else:
        raise ValueError(f"Unsupported decision: {decision}")

    app_req.approver_identity = approver_identity
    app_req.decision_timestamp = datetime.now(timezone.utc)
    app_req.reason_notes = reason_notes
    
    db.commit()

    log_audit_event(
        db=db,
        entity_id=app_req.id,
        entity_type="APPROVAL",
        event_type=f"APPROVAL_{app_req.status}",
        actor_identity=approver_identity,
        reason=reason_notes or f"Explicit human decision recorded: {app_req.status}"
    )

    return app_req

def execute_idempotent_upload(
    db: Session,
    approval_request_id: str,
    simulated_portal_status: str = "PENDING_VERIFICATION"
) -> Dict[str, Any]:
    """
    Executes an idempotent upload to the Mock Employer Portal.
    Guarantees:
    1. Must have explicit human approval.
    2. Stable idempotency key: duplicate calls return existing operation without re-creating.
    3. Persists upload in mock portal database.
    4. Distinguishes UPLOAD_SUCCEEDED from subsequent verification.
    """
    app_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_request_id).first()
    if not app_req:
        raise ValueError(f"Approval request {approval_request_id} not found")
        
    if app_req.status != ApprovalStatus.APPROVED.value:
        raise ValueError(f"Upload Rejected: Human approval is mandatory. Current status is {app_req.status}")

    proof_pack = db.query(ProofPack).filter(ProofPack.id == app_req.proof_pack_id).first()
    
    # Check if files changed since approval
    receipts_current = db.query(Receipt).filter(Receipt.proof_pack_id == proof_pack.id).all()
    current_hashes = json.dumps(sorted([r.pdf_sha256 for r in receipts_current]))
    if current_hashes != app_req.approved_file_hashes:
        app_req.status = ApprovalStatus.INVALIDATED.value
        db.commit()
        raise ValueError("Upload Rejected: Receipts or files have changed after approval was granted. Approval is now invalidated.")
    
    # Stable idempotency key tied to proof pack ID, version, and portal destination
    payload_raw = f"{proof_pack.id}-v{app_req.proof_pack_version}-{app_req.destination_portal}-{app_req.approved_file_hashes}"
    payload_hash = hashlib.sha256(payload_raw.encode("utf-8")).hexdigest()
    idempotency_key = f"IDEMP-{hashlib.sha256((proof_pack.id + str(app_req.proof_pack_version)).encode('utf-8')).hexdigest()[:16].upper()}"

    # Check for existing upload operation with this idempotency key
    existing_op = db.query(UploadOperation).filter(UploadOperation.idempotency_key == idempotency_key).first()
    if existing_op:
        log_audit_event(
            db=db,
            entity_id=existing_op.id,
            entity_type="UPLOAD",
            event_type="UPLOAD_IDEMPOTENT_RETRY_DETECTED",
            reason=f"Idempotent upload invoked again. Returned existing upload reference: {existing_op.portal_upload_ref}"
        )
        return {
            "upload_operation_id": existing_op.id,
            "idempotency_key": existing_op.idempotency_key,
            "portal_upload_ref": existing_op.portal_upload_ref,
            "status": existing_op.status,
            "is_duplicate_retry": True,
            "message": "Existing upload operation returned safely without duplicate portal submission."
        }

    # First time submission: Register upload in Mock Employer Portal
    upload_ref = f"UPL-ACME-{uuid.uuid4().hex[:8].upper()}"
    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == proof_pack.id).all()

    mock_upload = MockPortalUpload(
        id=upload_ref,
        idempotency_key=idempotency_key,
        declaration_id=app_req.destination_declaration_id,
        proof_pack_id=proof_pack.id,
        payload_hash=payload_hash,
        file_hashes=app_req.approved_file_hashes,
        file_count=len(receipts),
        status=simulated_portal_status, # Default is PENDING_VERIFICATION as in TC4
        submission_timestamp=datetime.now(timezone.utc),
        simulated_reviewer_notes="Declaration received into employer processing queue. HR Operations verification in progress."
    )
    db.add(mock_upload)

    # Update Mock Declaration
    declaration = db.query(MockPortalDeclaration).filter(
        MockPortalDeclaration.id == app_req.destination_declaration_id
    ).first()
    if declaration:
        declaration.status = simulated_portal_status
        declaration.uploaded_files_count = len(receipts)
        declaration.last_upload_ref = upload_ref
        declaration.uploaded_files_summary = json.dumps([r.month_label for r in receipts])
        db.add(declaration)

    upload_op = UploadOperation(
        id=f"UPL-OP-{uuid.uuid4().hex[:10].upper()}",
        proof_pack_id=proof_pack.id,
        approval_request_id=app_req.id,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        destination_portal=app_req.destination_portal,
        destination_declaration_id=app_req.destination_declaration_id,
        status=UploadOperationStatus.UPLOAD_SUCCEEDED.value,
        portal_upload_ref=upload_ref,
        portal_initial_response=json.dumps({
            "status": "ACCEPTED",
            "upload_ref": upload_ref,
            "declaration_id": app_req.destination_declaration_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    )
    db.add(upload_op)
    proof_pack.status = "UPLOAD_SUCCEEDED"
    db.commit()
    db.refresh(upload_op)

    log_audit_event(
        db=db,
        entity_id=upload_op.id,
        entity_type="UPLOAD",
        event_type="UPLOAD_EXECUTED_TO_PORTAL",
        after_state={
            "portal_upload_ref": upload_ref,
            "status": upload_op.status,
            "file_count": len(receipts)
        },
        reason="Uploaded approved proof pack to Mock Employer Portal"
    )

    return {
        "upload_operation_id": upload_op.id,
        "idempotency_key": upload_op.idempotency_key,
        "portal_upload_ref": upload_ref,
        "status": upload_op.status,
        "is_duplicate_retry": False,
        "message": "Proof pack successfully submitted to Employer Portal. Verification required."
    }

def verify_employer_portal_upload(db: Session, upload_operation_id: str) -> Dict[str, Any]:
    """
    Independent post-upload verification.
    Re-reads the actual state from the mock employer portal endpoint/table.
    Compares payload hash, files count, and distinguishes PENDING_VERIFICATION from APPROVED.
    """
    upload_op = db.query(UploadOperation).filter(UploadOperation.id == upload_operation_id).first()
    if not upload_op:
        raise ValueError(f"Upload operation {upload_operation_id} not found")

    portal_upload = db.query(MockPortalUpload).filter(
        MockPortalUpload.id == upload_op.portal_upload_ref
    ).first()

    if not portal_upload:
        upload_op.status = UploadOperationStatus.VERIFICATION_FAILED.value
        upload_op.latest_verified_status = "NOT_FOUND_ON_PORTAL"
        upload_op.verification_timestamp = datetime.now(timezone.utc)
        upload_op.discrepancy_explanation = "Re-reading employer portal returned 404: Upload reference not found."
        db.commit()
        return {
            "status": "VERIFICATION_FAILED",
            "verified_status": "NOT_FOUND_ON_PORTAL",
            "message": upload_op.discrepancy_explanation
        }

    # Compare payload integrity
    hashes_match = (portal_upload.payload_hash == upload_op.payload_hash)
    
    # Map portal state to verifiable upload state
    if portal_upload.status == "PENDING_VERIFICATION":
        verified_state = UploadOperationStatus.PENDING_VERIFICATION.value
    elif portal_upload.status == "VERIFIED_APPROVED":
        verified_state = UploadOperationStatus.VERIFIED_APPROVED.value
    elif portal_upload.status == "VERIFIED_REJECTED":
        verified_state = UploadOperationStatus.VERIFIED_REJECTED.value
    else:
        verified_state = "UNKNOWN_STATE"

    upload_op.status = verified_state
    upload_op.latest_verified_status = portal_upload.status
    upload_op.verification_timestamp = datetime.now(timezone.utc)
    upload_op.verification_raw_response = json.dumps({
        "portal_ref": portal_upload.id,
        "declaration_id": portal_upload.declaration_id,
        "portal_status": portal_upload.status,
        "file_count": portal_upload.file_count,
        "reviewer_notes": portal_upload.simulated_reviewer_notes,
        "hashes_intact": hashes_match
    })
    
    if not hashes_match:
        upload_op.status = UploadOperationStatus.VERIFICATION_FAILED.value
        upload_op.discrepancy_explanation = "Security Alert: Payload hash in employer portal does not match approved payload hash."

    db.commit()

    log_audit_event(
        db=db,
        entity_id=upload_op.id,
        entity_type="UPLOAD",
        event_type="INDEPENDENT_PORTAL_VERIFICATION",
        after_state={
            "verified_status": upload_op.status,
            "portal_status": portal_upload.status,
            "hashes_match": hashes_match
        },
        reason=f"Agent independently re-read Employer Portal status: {portal_upload.status}"
    )

    return {
        "upload_operation_id": upload_op.id,
        "portal_upload_ref": upload_op.portal_upload_ref,
        "verified_status": upload_op.status,
        "portal_status": portal_upload.status,
        "hashes_match": hashes_match,
        "notes": portal_upload.simulated_reviewer_notes,
        "verification_timestamp": upload_op.verification_timestamp.isoformat()
    }
