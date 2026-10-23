import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.all_models import PaymentRecord, MockPortalDeclaration

DEFAULT_MOCK_PAYMENTS: List[Dict[str, Any]] = [
    # 12 standard monthly payments for FY 2025-26 (Apr 2025 - Mar 2026)
    {"date": "2025-04-05", "amount": 25000, "ref": "TXN-HDFC-20250405-9011", "desc": "Rent for Apr 2025 to Suresh Verma"},
    {"date": "2025-05-04", "amount": 25000, "ref": "TXN-HDFC-20250504-9022", "desc": "Rent for May 2025 Suresh Verma"},
    {"date": "2025-06-05", "amount": 25000, "ref": "TXN-HDFC-20250605-9033", "desc": "Rent June 2025 - Bellandur Flat"},
    {"date": "2025-07-06", "amount": 25000, "ref": "TXN-HDFC-20250706-9044", "desc": "House Rent July 2025"},
    {"date": "2025-08-05", "amount": 25000, "ref": "TXN-HDFC-20250805-9055", "desc": "Rent payment Aug 2025"},
    {"date": "2025-09-07", "amount": 25000, "ref": "TXN-HDFC-20250907-9066", "desc": "Sep 2025 House Rent"},
    {"date": "2025-10-04", "amount": 25000, "ref": "TXN-HDFC-20251004-9077", "desc": "October 2025 rent Suresh Verma"},
    {"date": "2025-11-05", "amount": 25000, "ref": "TXN-HDFC-20251105-9088", "desc": "Nov 2025 Rent payment"},
    {"date": "2025-12-05", "amount": 25000, "ref": "TXN-HDFC-20251205-9099", "desc": "Dec 2025 Flat 402 Rent"},
    {"date": "2026-01-06", "amount": 25000, "ref": "TXN-HDFC-20260106-9110", "desc": "Jan 2026 Rent Suresh Verma"},
    {"date": "2026-02-05", "amount": 25000, "ref": "TXN-HDFC-20260205-9121", "desc": "Feb 2026 Rent Bellandur"},
    {"date": "2026-03-05", "amount": 25000, "ref": "TXN-HDFC-20260305-9132", "desc": "March 2026 Rent Suresh Verma"},
]

def seed_payment_history(db: Session, exclude_march: bool = False, tenant_name: str = "Aarav Sharma", payee_name: str = "Suresh R. Verma", monthly_amount: int = 25000):
    """
    Seeds mock payment history records cleanly.
    """
    # Delete existing payment records for this tenant to keep test repeatable
    db.query(PaymentRecord).filter(PaymentRecord.tenant_name == tenant_name).delete()
    db.commit()

    payments_to_seed = []
    run_suffix = uuid.uuid4().hex[:6].upper()
    for item in DEFAULT_MOCK_PAYMENTS:
        if exclude_march and "2026-03" in item["date"]:
            continue # Exclude March payment for TC2
        
        pref = f"{item['ref']}-{run_suffix}"
        pr = PaymentRecord(
            id=f"PAY-{uuid.uuid4().hex[:10].upper()}",
            source_system="HDFC_NETBANKING",
            source_record_id=f"SRC-{uuid.uuid4().hex[:8].upper()}",
            tenant_name=tenant_name,
            payee_name=payee_name,
            transaction_date=item["date"],
            amount=monthly_amount,
            payment_reference=pref,
            payment_method="NET_BANKING",
            description=item["desc"],
            retrieval_timestamp=datetime.now(timezone.utc),
            evidence_reference=f"HDFC-STMT-{item['ref'][-4:]}",
            matching_status="UNMATCHED"
        )
        payments_to_seed.append(pr)
    
    db.add_all(payments_to_seed)
    db.commit()
    return len(payments_to_seed)

def seed_mock_portal(db: Session):
    """
    Ensures default mock employer declaration exists.
    """
    existing = db.query(MockPortalDeclaration).filter(MockPortalDeclaration.id == "DECL-2025-ACME-001").first()
    if not existing:
        decl = MockPortalDeclaration(
            id="DECL-2025-ACME-001",
            tenant_name="Aarav Sharma",
            employee_id="EMP-8921",
            financial_year="2025-2026",
            component="HOUSE_RENT_ALLOWANCE",
            status="PENDING_SUBMISSION",
            uploaded_files_count=0,
            uploaded_files_summary="[]"
        )
        db.add(decl)
        db.commit()
