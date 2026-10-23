import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.models.all_models import ProofPack, Receipt, ApprovalRequest, UploadOperation, TestExecutionReport
from backend.app.services.tax_rule_service import evaluate_pan_requirement
from backend.app.services.approval_upload_service import (
    create_or_get_approval_request, submit_approval_decision, execute_idempotent_upload, verify_employer_portal_upload
)
from backend.app.services.test_runner_service import execute_tc1

client = TestClient(app)

def setup_module(module):
    Base.metadata.create_all(bind=engine)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# 1. TC1: Exactly 12 receipts, correct month-by-month amounts, payment dates, and source references
def test_tc1_scenario_detailed():
    res = client.post("/api/test-lab/run-tc1")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["receipt_count"] == 12

    db = SessionLocal()
    try:
        receipts = db.query(Receipt).filter(Receipt.proof_pack_id == data["proof_pack_id"]).order_by(Receipt.month_str.asc()).all()
        assert len(receipts) == 12
        for r in receipts:
            assert r.amount == 25000
            assert r.actual_payment_date.startswith("202")
            assert len(r.payment_reference) > 5
            assert r.pdf_sha256 is not None
            assert os.path.exists(r.pdf_path)
            assert os.path.getsize(r.pdf_path) > 1000
    finally:
        db.close()

# 2. TC2: Never generates a receipt for March when evidence is missing
def test_tc2_scenario_march_missing():
    res = client.post("/api/test-lab/run-tc2")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["receipt_count"] == 11
    
    db = SessionLocal()
    try:
        march_rec = db.query(Receipt).filter(
            Receipt.proof_pack_id == data["proof_pack_id"],
            Receipt.month_str == "2026-03"
        ).first()
        assert march_rec is None # Strictly verified that no March receipt exists
    finally:
        db.close()

# 3. TC3: Landlord PAN requirement & boundary testing (80k, 100k, 100k+1)
def test_tc3_pan_threshold_and_boundaries():
    below = evaluate_pan_requirement(annual_rent=80000, landlord_pan=None, threshold=100000)
    assert not below["pan_required"]
    assert below["status"] == "COMPLIANT_BELOW_THRESHOLD"

    at = evaluate_pan_requirement(annual_rent=100000, landlord_pan=None, threshold=100000)
    assert not at["pan_required"]
    assert at["status"] == "COMPLIANT_BELOW_THRESHOLD"

    above = evaluate_pan_requirement(annual_rent=100001, landlord_pan=None, threshold=100000)
    assert above["pan_required"]
    assert above["status"] == "PAN_REQUIRED_BLOCKING"

    res = client.post("/api/test-lab/run-tc3")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["pan_required"] is True
    assert data["submission_blocked"] is True

# 4. TC4: Independently re-reads mock portal and reports PENDING_VERIFICATION
def test_tc4_pending_verification():
    res = client.post("/api/test-lab/run-tc4")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["verified_status"] == "PENDING_VERIFICATION"
    assert data["verified_status"] != "VERIFIED_APPROVED"

# 5. Direct API requests cannot upload without valid approval
def test_unapproved_upload_is_blocked():
    db = SessionLocal()
    try:
        tc1_res = execute_tc1(db)
        app_req = create_or_get_approval_request(db, tc1_res["proof_pack_id"])
        assert app_req.status == "PENDING"
        
        # Direct upload attempt before approval
        res = client.post(f"/api/approval-requests/{app_req.id}/upload")
        assert res.status_code == 400
        assert "Human approval is mandatory" in res.json()["detail"]
    finally:
        db.close()

# 6. Any change to approved files/hashes invalidates the approval
def test_payload_tamper_invalidates_approval():
    db = SessionLocal()
    try:
        tc1_res = execute_tc1(db)
        app_req = create_or_get_approval_request(db, tc1_res["proof_pack_id"])
        submit_approval_decision(db, app_req.id, "APPROVE", "QA Reviewer")
        assert app_req.status == "APPROVED"

        # Tamper with an approved receipt hash
        first_receipt = db.query(Receipt).filter(Receipt.proof_pack_id == tc1_res["proof_pack_id"]).first()
        first_receipt.pdf_sha256 = "tampered_sha256_hash_value_1234567890"
        db.commit()

        # Attempt upload with tampered receipts
        res = client.post(f"/api/approval-requests/{app_req.id}/upload")
        assert res.status_code == 400
        assert "Receipts or files have changed after approval" in res.json()["detail"]
        
        # Verify approval is now marked INVALIDATED
        db.refresh(app_req)
        assert app_req.status == "INVALIDATED"
    finally:
        db.close()

# 7. Retrying an upload does not create duplicate submissions (Idempotency)
def test_idempotent_upload_no_duplicates():
    db = SessionLocal()
    try:
        tc1_res = execute_tc1(db)
        app_req = create_or_get_approval_request(db, tc1_res["proof_pack_id"])
        submit_approval_decision(db, app_req.id, "APPROVE", "QA Reviewer")

        res1 = client.post(f"/api/approval-requests/{app_req.id}/upload")
        assert res1.status_code == 200
        data1 = res1.json()
        assert not data1.get("is_duplicate_retry", False)
        first_op_id = data1["upload_operation_id"]
        first_ref = data1["portal_upload_ref"]

        # Second upload retry
        res2 = client.post(f"/api/approval-requests/{app_req.id}/upload")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2.get("is_duplicate_retry", False) is True
        assert data2["upload_operation_id"] == first_op_id
        assert data2["portal_upload_ref"] == first_ref
    finally:
        db.close()

# 8. Portal verification failure and honest reporting
def test_verification_failure_honest_reporting():
    db = SessionLocal()
    try:
        tc1_res = execute_tc1(db)
        app_req = create_or_get_approval_request(db, tc1_res["proof_pack_id"])
        submit_approval_decision(db, app_req.id, "APPROVE", "QA Reviewer")
        upload_data = execute_idempotent_upload(db, app_req.id)
        
        # Simulate corrupt/deleted portal upload record
        op = db.query(UploadOperation).filter(UploadOperation.id == upload_data["upload_operation_id"]).first()
        op.portal_upload_ref = "NON_EXISTENT_PORTAL_REF_9999"
        db.commit()

        verif = verify_employer_portal_upload(db, op.id)
        assert verif["status"] == "VERIFICATION_FAILED"
        assert "NOT_FOUND_ON_PORTAL" in verif["verified_status"]
    finally:
        db.close()

# 9. PDF receipts are actually generated, downloadable, and readable
def test_receipt_pdf_download():
    res = client.post("/api/test-lab/run-tc1")
    pack_id = res.json()["proof_pack_id"]
    
    db = SessionLocal()
    try:
        receipt = db.query(Receipt).filter(Receipt.proof_pack_id == pack_id).first()
        assert receipt is not None
        
        # Download single receipt
        dl_res = client.get(f"/api/receipts/{receipt.id}/download")
        assert dl_res.status_code == 200
        assert dl_res.headers["content-type"] == "application/pdf"
        assert dl_res.content.startswith(b"%PDF")
        
        # Download ZIP of all receipts
        zip_res = client.get(f"/api/proof-packs/{pack_id}/download-zip")
        assert zip_res.status_code == 200
        assert zip_res.headers["content-type"] == "application/zip"
        assert len(zip_res.content) > 1000
    finally:
        db.close()

# 10. Demo reset works without corrupting test history
def test_demo_reset_preserves_test_reports():
    # Run test lab
    client.post("/api/test-lab/run-tc1")
    
    db = SessionLocal()
    try:
        count_before = db.query(TestExecutionReport).count()
        assert count_before > 0
    finally:
        db.close()

    # Call reset
    reset_res = client.post("/api/demo/reset")
    assert reset_res.status_code == 200

    db = SessionLocal()
    try:
        count_after = db.query(TestExecutionReport).count()
        assert count_after >= count_before # Preserved
    finally:
        db.close()

def test_run_all_official_tests():
    res = client.post("/api/test-lab/run-all")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    assert data["passed"] == 4
    assert data["failed"] == 0
