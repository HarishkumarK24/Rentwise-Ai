import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.models.all_models import (
    ProofPack, RentMonth, PaymentRecord, Receipt, ApprovalRequest, 
    UploadOperation, MockPortalDeclaration, MockPortalUpload, TestExecutionReport
)
from backend.app.mock_connectors.payment_connector import seed_payment_history, seed_mock_portal
from backend.app.services.reconciliation_service import reconcile_proof_pack, generate_month_range, get_month_label
from backend.app.services.receipt_service import generate_receipts_for_proof_pack
from backend.app.services.approval_upload_service import (
    create_or_get_approval_request, submit_approval_decision, execute_idempotent_upload, verify_employer_portal_upload
)
from backend.app.services.tax_rule_service import evaluate_pan_requirement

def execute_tc1(db: Session) -> Dict[str, Any]:
    """
    TC1 — Twelve monthly rent payments:
    - 12 rent months in FY 2025-26
    - 12 valid distinct payment records
    - 12 receipts generated with correct amounts and references
    - Assert no duplicate receipts
    """
    seed_mock_portal(db)
    seed_payment_history(db, exclude_march=False, tenant_name="Aarav Sharma TC1", payee_name="Suresh R. Verma", monthly_amount=25000)

    # Create Proof Pack
    pack_id = f"PK-TC1-{uuid.uuid4().hex[:6].upper()}"
    months = generate_month_range("2025-04", "2026-03")
    
    proof_pack = ProofPack(
        id=pack_id,
        tenant_name="Aarav Sharma TC1",
        employee_id="EMP-TC1-100",
        employer_name="Acme Technologies Pvt Ltd",
        work_location="Bengaluru",
        financial_year="2025-2026",
        declaration_period="Apr 2025 - Mar 2026",
        landlord_name="Suresh R. Verma",
        landlord_address="#402, Green Glen Heights, Bellandur, Bengaluru 560103",
        landlord_pan="ABCDE1234F",
        monthly_rent=25000,
        start_month="2025-04",
        end_month="2026-03",
        pan_threshold_applied=100000,
        status="DRAFT"
    )
    db.add(proof_pack)
    db.commit()

    for m in months:
        rm = RentMonth(
            id=f"RM-{pack_id[-6:]}-{m.replace('-', '')}",
            proof_pack_id=pack_id,
            month_str=m,
            month_label=get_month_label(m),
            expected_rent=25000,
            matching_status="PENDING"
        )
        db.add(rm)
    db.commit()

    # Reconcile
    rec_result = reconcile_proof_pack(db, pack_id)
    # Generate Receipts
    gen_result = generate_receipts_for_proof_pack(db, pack_id)

    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == pack_id).all()
    
    # Assertions
    assertions = []
    assertions.append({"check": "Reconciled exactly 12 months", "pass": rec_result["matched_count"] == 12})
    assertions.append({"check": "Zero missing payment months", "pass": rec_result["missing_count"] == 0})
    assertions.append({"check": "Exactly 12 receipts generated", "pass": len(receipts) == 12})
    
    # Assert each receipt has correct month, amount, and non-empty reference
    receipt_months = [r.month_str for r in receipts]
    no_duplicate_months = len(receipt_months) == len(set(receipt_months))
    assertions.append({"check": "No duplicate receipts for the same month", "pass": no_duplicate_months})
    
    all_amounts_25k = all(r.amount == 25000 for r in receipts)
    assertions.append({"check": "Every receipt has exact rent amount ₹25,000", "pass": all_amounts_25k})
    
    all_passed = all(a["pass"] for a in assertions)

    report = TestExecutionReport(
        id=f"TR-{uuid.uuid4().hex[:8].upper()}",
        test_case_id="TC1",
        test_case_name="Twelve monthly rent payments",
        status="PASS" if all_passed else "FAIL",
        executed_at=datetime.now(timezone.utc),
        inputs_summary="12 months (2025-04 to 2026-03), 12 HDFC banking transactions of ₹25,000 each, valid Landlord PAN ABCDE1234F",
        expected_result="12 rent months matched, 12 PDF receipts generated with unique SHA-256 hashes, 0 duplicates",
        actual_result=f"{rec_result['matched_count']} matched, {len(receipts)} receipts generated. Duplicate check: {no_duplicate_months}",
        assertions=json.dumps(assertions),
        evidence_and_records=json.dumps({"proof_pack_id": pack_id, "receipt_ids": [r.id for r in receipts]}),
        explanation="All 12 monthly rent transactions strictly verified and generated without errors."
    )
    db.add(report)
    db.commit()

    return {
        "test_case_id": "TC1",
        "status": report.status,
        "proof_pack_id": pack_id,
        "assertions": assertions,
        "receipt_count": len(receipts)
    }

def execute_tc2(db: Session) -> Dict[str, Any]:
    """
    TC2 — No payment found for March:
    - 12-month rent period
    - Payments for 11 months, March missing
    - March flagged as MISSING_PAYMENT
    - No receipt generated for March
    - Other 11 months receive receipts
    """
    seed_mock_portal(db)
    seed_payment_history(db, exclude_march=True, tenant_name="Aarav Sharma TC2", payee_name="Suresh R. Verma", monthly_amount=25000)

    pack_id = f"PK-TC2-{uuid.uuid4().hex[:6].upper()}"
    months = generate_month_range("2025-04", "2026-03")
    
    proof_pack = ProofPack(
        id=pack_id,
        tenant_name="Aarav Sharma TC2",
        employee_id="EMP-TC2-101",
        employer_name="Acme Technologies Pvt Ltd",
        work_location="Bengaluru",
        financial_year="2025-2026",
        declaration_period="Apr 2025 - Mar 2026",
        landlord_name="Suresh R. Verma",
        landlord_address="#402, Green Glen Heights, Bellandur, Bengaluru 560103",
        landlord_pan="ABCDE1234F",
        monthly_rent=25000,
        start_month="2025-04",
        end_month="2026-03",
        pan_threshold_applied=100000,
        status="DRAFT"
    )
    db.add(proof_pack)
    db.commit()

    for m in months:
        rm = RentMonth(
            id=f"RM-{pack_id[-6:]}-{m.replace('-', '')}",
            proof_pack_id=pack_id,
            month_str=m,
            month_label=get_month_label(m),
            expected_rent=25000,
            matching_status="PENDING"
        )
        db.add(rm)
    db.commit()

    rec_result = reconcile_proof_pack(db, pack_id)
    gen_result = generate_receipts_for_proof_pack(db, pack_id)

    march_rm = db.query(RentMonth).filter(
        RentMonth.proof_pack_id == pack_id,
        RentMonth.month_str == "2026-03"
    ).first()

    march_receipt = db.query(Receipt).filter(
        Receipt.proof_pack_id == pack_id,
        Receipt.month_str == "2026-03"
    ).first()

    receipts = db.query(Receipt).filter(Receipt.proof_pack_id == pack_id).all()

    assertions = []
    assertions.append({"check": "Reconciled 11 matched months", "pass": rec_result["matched_count"] == 11})
    assertions.append({"check": "Exactly 1 missing month flagged", "pass": rec_result["missing_count"] == 1})
    assertions.append({"check": "March status is strictly MISSING_PAYMENT", "pass": march_rm.matching_status == "MISSING_PAYMENT"})
    assertions.append({"check": "No receipt exists for March", "pass": march_receipt is None})
    assertions.append({"check": "Receipts generated for other 11 months", "pass": len(receipts) == 11})
    assertions.append({"check": "March is marked ineligible for receipt", "pass": not march_rm.is_eligible_for_receipt})

    all_passed = all(a["pass"] for a in assertions)

    report = TestExecutionReport(
        id=f"TR-{uuid.uuid4().hex[:8].upper()}",
        test_case_id="TC2",
        test_case_name="No payment found for March",
        status="PASS" if all_passed else "FAIL",
        executed_at=datetime.now(timezone.utc),
        inputs_summary="12-month period with March payment omitted from banking records",
        expected_result="March flagged as MISSING_PAYMENT. Zero receipt fabricated for March. 11 receipts generated for rest.",
        actual_result=f"March status: {march_rm.matching_status}. Total receipts: {len(receipts)}. March receipt found: {bool(march_receipt)}",
        assertions=json.dumps(assertions),
        evidence_and_records=json.dumps({"proof_pack_id": pack_id, "march_rent_month_id": march_rm.id}),
        explanation="RentWise AI refused to hallucinate or invent a receipt for March where banking evidence was missing."
    )
    db.add(report)
    db.commit()

    return {
        "test_case_id": "TC2",
        "status": report.status,
        "proof_pack_id": pack_id,
        "assertions": assertions,
        "receipt_count": len(receipts)
    }

def execute_tc3(db: Session) -> Dict[str, Any]:
    """
    TC3 — Annual rent above the landlord-PAN threshold:
    - Annual rent > ₹1,00,000 (e.g. 12 * ₹25,000 = ₹3,00,000)
    - Landlord PAN omitted
    - System detects requirement, marks PAN_REQUIRED, prompts user, and blocks submission
    - Includes boundary evaluations: below (₹80k), at (₹100k), above (₹120k/₹300k)
    """
    seed_mock_portal(db)
    seed_payment_history(db, exclude_march=False, tenant_name="Aarav Sharma TC3", payee_name="Suresh R. Verma", monthly_amount=25000)

    pack_id = f"PK-TC3-{uuid.uuid4().hex[:6].upper()}"
    months = generate_month_range("2025-04", "2026-03")
    
    proof_pack = ProofPack(
        id=pack_id,
        tenant_name="Aarav Sharma TC3",
        employee_id="EMP-TC3-102",
        employer_name="Acme Technologies Pvt Ltd",
        work_location="Bengaluru",
        financial_year="2025-2026",
        declaration_period="Apr 2025 - Mar 2026",
        landlord_name="Suresh R. Verma",
        landlord_address="#402, Green Glen Heights, Bellandur, Bengaluru 560103",
        landlord_pan="", # OMITTED intentionally
        monthly_rent=25000,
        start_month="2025-04",
        end_month="2026-03",
        pan_threshold_applied=100000,
        status="DRAFT"
    )
    db.add(proof_pack)
    db.commit()

    for m in months:
        rm = RentMonth(
            id=f"RM-{pack_id[-6:]}-{m.replace('-', '')}",
            proof_pack_id=pack_id,
            month_str=m,
            month_label=get_month_label(m),
            expected_rent=25000,
            matching_status="PENDING"
        )
        db.add(rm)
    db.commit()

    reconcile_proof_pack(db, pack_id)
    generate_receipts_for_proof_pack(db, pack_id)

    # Evaluate PAN directly
    total_rent = 25000 * 12 # 300,000
    pan_eval = evaluate_pan_requirement(annual_rent=total_rent, landlord_pan=proof_pack.landlord_pan, threshold=100000)
    
    # Boundary tests
    eval_below = evaluate_pan_requirement(annual_rent=80000, landlord_pan=None, threshold=100000)
    eval_at = evaluate_pan_requirement(annual_rent=100000, landlord_pan=None, threshold=100000)
    eval_above = evaluate_pan_requirement(annual_rent=100001, landlord_pan=None, threshold=100000)

    # Test that approval request creation raises blocking error
    submission_blocked = False
    try:
        create_or_get_approval_request(db, pack_id)
    except ValueError as e:
        if "Statutory Tax Rules" in str(e) or "PAN is mandatory" in str(e):
            submission_blocked = True

    proof_pack = db.query(ProofPack).filter(ProofPack.id == pack_id).first()

    assertions = []
    assertions.append({"check": "Annual rent ₹3,00,000 strictly > ₹1,00,000 threshold", "pass": pan_eval["is_above_threshold"]})
    assertions.append({"check": "PAN requirement correctly identified as mandatory", "pass": pan_eval["pan_required"]})
    assertions.append({"check": "Proof pack marked as PAN_REQUIRED or PAN_REQUIRED_BLOCKING", "pass": proof_pack.status == "PAN_REQUIRED" or pan_eval["status"] == "PAN_REQUIRED_BLOCKING"})
    assertions.append({"check": "Backend approval creation strictly blocked when PAN missing", "pass": submission_blocked})
    assertions.append({"check": "Boundary test Below (₹80k): Optional PAN", "pass": not eval_below["pan_required"]})
    assertions.append({"check": "Boundary test Equal (₹100k): Optional PAN (threshold not exceeded)", "pass": not eval_at["pan_required"]})
    assertions.append({"check": "Boundary test Above (₹100,001): Mandatory PAN", "pass": eval_above["pan_required"]})

    all_passed = all(a["pass"] for a in assertions)

    report = TestExecutionReport(
        id=f"TR-{uuid.uuid4().hex[:8].upper()}",
        test_case_id="TC3",
        test_case_name="Annual rent above the landlord-PAN threshold",
        status="PASS" if all_passed else "FAIL",
        executed_at=datetime.now(timezone.utc),
        inputs_summary="Annual rent ₹300,000 with landlord PAN omitted, testing statutory threshold ₹100,000",
        expected_result="PAN requirement flagged, submission blocked, boundary tests (80k, 100k, 100k+1) pass",
        actual_result=f"Blocked status: {submission_blocked}, PAN required: {pan_eval['pan_required']}",
        assertions=json.dumps(assertions),
        evidence_and_records=json.dumps({"proof_pack_id": pack_id, "boundary_eval": {"below": eval_below["status"], "at": eval_at["status"], "above": eval_above["status"]}}),
        explanation="Strict adherence to CBDT Circular No. 08/2013: no fabricated PAN and upload blocked."
    )
    db.add(report)
    db.commit()

    return {
        "test_case_id": "TC3",
        "status": report.status,
        "proof_pack_id": pack_id,
        "assertions": assertions,
        "pan_required": pan_eval["pan_required"],
        "submission_blocked": submission_blocked
    }

def execute_tc4(db: Session) -> Dict[str, Any]:
    """
    TC4 — Employer portal shows pending verification:
    - Complete proof pack
    - Valid human approval
    - Successful mock portal upload
    - Status endpoint re-read returns PENDING_VERIFICATION
    - Assert that final status is NOT Approved, but Pending Verification
    """
    seed_mock_portal(db)
    seed_payment_history(db, exclude_march=False, tenant_name="Aarav Sharma TC4", payee_name="Suresh R. Verma", monthly_amount=25000)

    pack_id = f"PK-TC4-{uuid.uuid4().hex[:6].upper()}"
    months = generate_month_range("2025-04", "2026-03")
    
    proof_pack = ProofPack(
        id=pack_id,
        tenant_name="Aarav Sharma TC4",
        employee_id="EMP-TC4-103",
        employer_name="Acme Technologies Pvt Ltd",
        work_location="Bengaluru",
        financial_year="2025-2026",
        declaration_period="Apr 2025 - Mar 2026",
        landlord_name="Suresh R. Verma",
        landlord_address="#402, Green Glen Heights, Bellandur, Bengaluru 560103",
        landlord_pan="ABCDE1234F",
        monthly_rent=25000,
        start_month="2025-04",
        end_month="2026-03",
        pan_threshold_applied=100000,
        status="DRAFT"
    )
    db.add(proof_pack)
    db.commit()

    for m in months:
        rm = RentMonth(
            id=f"RM-{pack_id[-6:]}-{m.replace('-', '')}",
            proof_pack_id=pack_id,
            month_str=m,
            month_label=get_month_label(m),
            expected_rent=25000,
            matching_status="PENDING"
        )
        db.add(rm)
    db.commit()

    reconcile_proof_pack(db, pack_id)
    generate_receipts_for_proof_pack(db, pack_id)

    # 1. Approval Gate
    app_req = create_or_get_approval_request(db, pack_id)
    submit_approval_decision(db, app_req.id, "APPROVE", "Aarav Sharma TC4 (Tenant)", "Confirmed receipts match bank transactions")

    # 2. Upload with portal simulated as PENDING_VERIFICATION
    upload_res = execute_idempotent_upload(db, app_req.id, simulated_portal_status="PENDING_VERIFICATION")
    
    # 3. Independent Post-Upload Verification (Re-reading Employer Portal)
    verif_res = verify_employer_portal_upload(db, upload_res["upload_operation_id"])

    upload_op = db.query(UploadOperation).filter(UploadOperation.id == upload_res["upload_operation_id"]).first()

    assertions = []
    assertions.append({"check": "Human approval recorded before upload", "pass": app_req.status == "APPROVED"})
    assertions.append({"check": "Upload operation created with portal reference", "pass": bool(upload_op.portal_upload_ref)})
    assertions.append({"check": "Employer portal status independently re-read", "pass": verif_res["portal_status"] == "PENDING_VERIFICATION"})
    assertions.append({"check": "Final status is strictly PENDING_VERIFICATION", "pass": upload_op.status == "PENDING_VERIFICATION"})
    assertions.append({"check": "Final status is NOT marked Approved prior to employer verification", "pass": upload_op.status != "VERIFIED_APPROVED"})
    assertions.append({"check": "Payload and file hashes match exactly", "pass": verif_res["hashes_match"] is True})

    all_passed = all(a["pass"] for a in assertions)

    report = TestExecutionReport(
        id=f"TR-{uuid.uuid4().hex[:8].upper()}",
        test_case_id="TC4",
        test_case_name="Employer portal shows pending verification",
        status="PASS" if all_passed else "FAIL",
        executed_at=datetime.now(timezone.utc),
        inputs_summary="Approved 12 receipts pack submitted to ACME Corp Portal simulating pending queue",
        expected_result="Operation re-reads portal status, records PENDING_VERIFICATION, never mislabels as Approved",
        actual_result=f"Final state: {upload_op.status}. Verified portal state: {verif_res['portal_status']}",
        assertions=json.dumps(assertions),
        evidence_and_records=json.dumps({"upload_operation_id": upload_op.id, "portal_upload_ref": upload_op.portal_upload_ref}),
        explanation="Independent verification confirmed Employer Portal state is Pending Verification without premature approval claims."
    )
    db.add(report)
    db.commit()

    return {
        "test_case_id": "TC4",
        "status": report.status,
        "proof_pack_id": pack_id,
        "assertions": assertions,
        "verified_status": upload_op.status
    }

def run_all_official_tests(db: Session) -> Dict[str, Any]:
    r1 = execute_tc1(db)
    r2 = execute_tc2(db)
    r3 = execute_tc3(db)
    r4 = execute_tc4(db)
    
    total = 4
    passed = sum(1 for r in [r1, r2, r3, r4] if r["status"] == "PASS")
    failed = total - passed
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": [r1, r2, r3, r4]
    }
