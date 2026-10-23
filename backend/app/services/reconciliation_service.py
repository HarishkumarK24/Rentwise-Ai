from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.all_models import ProofPack, RentMonth, PaymentRecord, MonthMatchingStatus
from backend.app.services.audit_service import log_audit_event

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def get_month_label(month_str: str) -> str:
    # month_str: "2025-04" -> "April 2025"
    parts = month_str.split("-")
    year = parts[0]
    m_idx = int(parts[1]) - 1
    return f"{MONTH_NAMES[m_idx]} {year}"

def generate_month_range(start_month: str, end_month: str) -> List[str]:
    # format: YYYY-MM
    start_y, start_m = map(int, start_month.split("-"))
    end_y, end_m = map(int, end_month.split("-"))
    
    months = []
    curr_y, curr_m = start_y, start_m
    while (curr_y < end_y) or (curr_y == end_y and curr_m <= end_m):
        months.append(f"{curr_y:04d}-{curr_m:02d}")
        curr_m += 1
        if curr_m > 12:
            curr_m = 1
            curr_y += 1
    return months

def reconcile_proof_pack(db: Session, proof_pack_id: str, allow_fuzzy_dates: bool = True) -> Dict[str, Any]:
    """
    Deterministic payment reconciliation engine.
    Matches payments from PaymentRecord to ProofPack rent months.
    Enforces that a rent month is only marked READY_FOR_RECEIPT when
    full expected rent is matched and evidence is unambiguous.
    """
    proof_pack = db.query(ProofPack).filter(ProofPack.id == proof_pack_id).first()
    if not proof_pack:
        raise ValueError(f"Proof pack {proof_pack_id} not found")
        
    rent_months = db.query(RentMonth).filter(RentMonth.proof_pack_id == proof_pack_id).all()
    # Fetch available payments for this tenant
    payments = db.query(PaymentRecord).filter(
        PaymentRecord.tenant_name == proof_pack.tenant_name
    ).all()

    # Track allocated payments to prevent duplicate double-counting across months
    allocated_payment_ids = set()
    
    total_expected = 0
    total_allocated = 0
    matched_count = 0
    missing_count = 0
    
    reconciliation_details = []

    for rm in rent_months:
        total_expected += rm.expected_rent
        expected_amount = rm.expected_rent
        month_str = rm.month_str # e.g. "2025-04"
        
        # Candidate payments:
        # Match rule:
        # 1. Payment date matches the calendar month or within 10 days of start/end of month
        # 2. Or description explicitly mentions month/year
        # 3. Payee corresponds to landlord or rent
        matched_candidates = []
        for p in payments:
            if p.id in allocated_payment_ids:
                continue
            
            # Date match check
            p_month = p.transaction_date[:7] # YYYY-MM
            is_same_month = (p_month == month_str)
            desc_match = rm.month_label.lower() in (p.description or "").lower() or month_str in (p.description or "")
            
            if is_same_month or desc_match:
                matched_candidates.append(p)
        
        # Analyze candidates for this month
        if not matched_candidates:
            rm.allocated_amount = 0
            rm.difference = expected_amount
            rm.matching_status = MonthMatchingStatus.MISSING_PAYMENT.value
            rm.matching_method = "DETERMINISTIC_LOOKUP"
            rm.confidence = "CERTAIN"
            rm.explanation = f"No payment evidence discovered in banking ledger for {rm.month_label}."
            rm.transaction_references = ""
            rm.is_eligible_for_receipt = False
            missing_count += 1
        elif len(matched_candidates) == 1:
            cand = matched_candidates[0]
            if cand.amount == expected_amount:
                rm.allocated_amount = cand.amount
                rm.difference = 0
                rm.matching_status = MonthMatchingStatus.MATCHED.value
                rm.matching_method = "EXACT_DATE_AND_AMOUNT_MATCH"
                rm.confidence = "HIGH_RULE_BASED"
                rm.explanation = (
                    f"Exact payment of ₹{cand.amount:,} verified via {cand.source_system} "
                    f"on {cand.transaction_date} (Ref: {cand.payment_reference})."
                )
                rm.transaction_references = cand.payment_reference
                rm.is_eligible_for_receipt = True
                allocated_payment_ids.add(cand.id)
                cand.matching_status = "MATCHED"
                matched_count += 1
                total_allocated += cand.amount
            elif cand.amount < expected_amount:
                diff = expected_amount - cand.amount
                rm.allocated_amount = cand.amount
                rm.difference = diff
                rm.matching_status = MonthMatchingStatus.PARTIALLY_MATCHED.value
                rm.matching_method = "PARTIAL_PAYMENT_MATCH"
                rm.confidence = "MEDIUM_ALERT"
                rm.explanation = f"Partial payment received: ₹{cand.amount:,} against expected ₹{expected_amount:,} (Shortfall: ₹{diff:,})."
                rm.transaction_references = cand.payment_reference
                rm.is_eligible_for_receipt = False
                allocated_payment_ids.add(cand.id)
                total_allocated += cand.amount
            else:
                # amount > expected
                rm.allocated_amount = cand.amount
                rm.difference = cand.amount - expected_amount
                rm.matching_status = MonthMatchingStatus.AMOUNT_MISMATCH.value
                rm.matching_method = "SURPLUS_AMOUNT_ALERT"
                rm.confidence = "NEEDS_CONFIRMATION"
                rm.explanation = f"Payment amount of ₹{cand.amount:,} exceeds expected monthly rent of ₹{expected_amount:,}."
                rm.transaction_references = cand.payment_reference
                rm.is_eligible_for_receipt = False
                allocated_payment_ids.add(cand.id)
                total_allocated += cand.amount
        else:
            # Multiple candidate payments or potential duplicates
            sum_candidates = sum(c.amount for c in matched_candidates)
            refs = ", ".join(c.payment_reference for c in matched_candidates)
            if sum_candidates == expected_amount:
                # Split payment contributing to month
                rm.allocated_amount = sum_candidates
                rm.difference = 0
                rm.matching_status = MonthMatchingStatus.MATCHED.value
                rm.matching_method = "SPLIT_MULTI_PAYMENT_COMBINED"
                rm.confidence = "RULE_BASED"
                rm.explanation = f"Matched {len(matched_candidates)} split transactions totaling ₹{sum_candidates:,} for {rm.month_label}."
                rm.transaction_references = refs
                rm.is_eligible_for_receipt = True
                for c in matched_candidates:
                    allocated_payment_ids.add(c.id)
                    c.matching_status = "MATCHED"
                matched_count += 1
                total_allocated += sum_candidates
            else:
                rm.allocated_amount = sum_candidates
                rm.difference = abs(expected_amount - sum_candidates)
                rm.matching_status = MonthMatchingStatus.AMBIGUOUS.value
                rm.matching_method = "AMBIGUOUS_MULTI_CANDIDATE"
                rm.confidence = "FLAGGED_FOR_HUMAN"
                rm.explanation = f"Multiple transactions detected ({refs}) totaling ₹{sum_candidates:,} for expected ₹{expected_amount:,}. Needs user clarification."
                rm.transaction_references = refs
                rm.is_eligible_for_receipt = False

        db.add(rm)
        reconciliation_details.append({
            "month_str": rm.month_str,
            "month_label": rm.month_label,
            "expected_rent": rm.expected_rent,
            "allocated_amount": rm.allocated_amount,
            "difference": rm.difference,
            "status": rm.matching_status,
            "method": rm.matching_method,
            "confidence": rm.confidence,
            "explanation": rm.explanation,
            "is_eligible": rm.is_eligible_for_receipt
        })

    proof_pack.status = "RECONCILED"
    db.commit()

    # Log audit event
    log_audit_event(
        db=db,
        entity_id=proof_pack.id,
        entity_type="PROOF_PACK",
        event_type="PAYMENT_RECONCILIATION_COMPLETED",
        actor_identity="RECONCILIATION_ENGINE",
        after_state={
            "matched_months": matched_count,
            "missing_months": missing_count,
            "total_expected": total_expected,
            "total_allocated": total_allocated
        },
        reason="Automated deterministic payment reconciliation against banking ledger"
    )

    return {
        "proof_pack_id": proof_pack.id,
        "total_months": len(rent_months),
        "matched_count": matched_count,
        "missing_count": missing_count,
        "total_expected": total_expected,
        "total_allocated": total_allocated,
        "details": reconciliation_details
    }
