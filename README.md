# RentWise AI — Intelligent Rent Receipt & HRA Proof Pack Agent

RentWise AI is an autonomous, evidence-driven financial workflow agent designed to solve HRA investment declaration and rent proof preparation for salaried employees.

Unlike simple form-fillers or chatbots, RentWise AI implements:
- **Deterministic Banking Ledger Reconciliation**: Matches rent months against bank transaction ledgers with zero hallucination. If evidence is missing, it refuses to fabricate receipts.
- **Statutory Tax Rule & Landlord PAN Verification**: Enforces CBDT Circular No. 08/2013 and Section 10(13A) rules requiring landlord PAN for annual rents exceeding ₹1,00,000.
- **Verifiable PDF Receipt Generation**: Generates real, tamper-evident PDF receipts using ReportLab stamped with SHA-256 cryptographic hashes.
- **Mandatory Human Approval Gate**: Server-enforced approval gate bound to exact file hashes.
- **Duplicate-Safe Idempotent Uploads**: Employs idempotency keys to ensure safe retries without duplicate portal records.
- **Independent Post-Upload Verification**: Queries the Mock Employer Portal status endpoint after submission to distinguish `Pending Verification` from `Approved`.
- **Append-Only Audit Trail**: Full traceability of all state transitions and policy decisions.
- **Integrated Test Lab**: Instant repeatable execution of official scenarios **TC1, TC2, TC3, and TC4**.

---

## Architecture Overview

```
rentwise-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application setup & lifecycle
│   │   ├── database.py                # SQLite / SQLAlchemy session engine
│   │   ├── models/
│   │   │   └── all_models.py          # Relational schemas & Audit trail
│   │   ├── schemas/
│   │   │   └── schemas.py             # Pydantic request & response models
│   │   ├── mock_connectors/
│   │   │   └── payment_connector.py   # Bank ledger & employer portal seed connectors
│   │   ├── services/
│   │   │   ├── tax_rule_service.py    # Statutory PAN threshold policy & boundary checks
│   │   │   ├── reconciliation_service.py # Deterministic month matching logic
│   │   │   ├── receipt_service.py     # ReportLab PDF receipt generator & SHA-256
│   │   │   ├── approval_upload_service.py # Human approval gate & idempotent upload
│   │   │   ├── audit_service.py       # Append-only audit logger
│   │   │   └── test_runner_service.py # Official test cases execution engine
│   │   └── routers/
│   │       └── api_router.py          # REST API endpoints
│   └── tests/
│       └── test_official_scenarios.py # Pytest test suite for TC1-TC4
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── OverviewView.tsx               # Real database-derived KPI dashboard
│   │   │   ├── CreateProofPackView.tsx        # Guided 4-step intake wizard
│   │   │   ├── PaymentReconciliationView.tsx  # Ledger matching & receipt downloads
│   │   │   ├── ApprovalCenterView.tsx         # Mandatory Human Approval Gate
│   │   │   ├── EmployerPortalView.tsx         # Post-upload status verification
│   │   │   ├── TestLabView.tsx                # Official test scenarios & assertions
│   │   │   └── AuditTrailView.tsx             # Traceable audit event explorer
│   │   ├── App.tsx                    # Main navigation & Judge quick launchers
│   │   └── types/index.ts             # TypeScript definitions
│   └── package.json
└── README.md
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Backend Setup
```bash
# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies (if not already installed)
pip install fastapi uvicorn pydantic sqlalchemy reportlab pytest httpx python-multipart

# Start Backend Server on port 8000
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be live at: `http://localhost:5173`

---

## Official Test Suite (Mandatory Scenarios)

Execute all test cases directly via pytest:
```bash
source backend/venv/bin/activate
PYTHONPATH=. pytest backend/tests/test_official_scenarios.py -v
```

### Official Scenario Coverage:
1. **TC1 — Twelve monthly rent payments**:
   - Reconciles 12 rent months in FY 2025-26.
   - Generates 12 PDF receipts with unique SHA-256 hashes.
   - Asserts zero duplicate receipts.
2. **TC2 — No payment found for March**:
   - Validates 11 months of payment evidence with March omitted from bank ledger.
   - March is strictly flagged as `MISSING_PAYMENT`.
   - Asserts zero receipt fabricated for March; receipts generated only for verified months.
3. **TC3 — Annual rent above landlord-PAN threshold**:
   - Tests statutory threshold ₹1,00,000 under Section 10(13A).
   - Landlord PAN omitted: marks `PAN_REQUIRED` and blocks upload submission.
   - Executes boundary tests: Below (₹80k - Optional), Equal (₹100k - Optional), Above (₹100k+1 - Mandatory).
4. **TC4 — Employer portal shows pending verification**:
   - Approved submission uploaded to Mock Employer Portal.
   - Agent independently re-reads portal status.
   - Asserts state is strictly `PENDING_VERIFICATION` and never mislabeled as `Approved`.

---

## 3-Minute Live Hackathon Demo Walkthrough

1. **Overview Dashboard**:
   - Open `http://localhost:5173`.
   - View real database-derived metrics, reconciliation timeline, and proof pack history.
2. **Quick Scenario TC1**:
   - Click **Load TC1** in the top navigation bar.
   - Inspect the **Payment Reconciliation** screen showing all 12 months matched with banking references and download individual PDF receipts or the full ZIP archive.
3. **Quick Scenario TC2 (Missing March)**:
   - Click **Load TC2**.
   - Notice that March is flagged as `MISSING_PAYMENT`. Zero receipt is fabricated for March, while other 11 months remain eligible.
4. **Quick Scenario TC3 (Statutory PAN Block)**:
   - Click **Load TC3**.
   - Review how RentWise AI refuses to hallucinate a PAN. When clicking into Approval Center, the submission is blocked under statutory CBDT rules until the landlord PAN is provided.
5. **Quick Scenario TC4 (Independent Verification)**:
   - Click **Load TC4**.
   - Navigate to **Employer Portal**.
   - View the upload reference and click **Re-Read Portal Status (Verify)** to verify that the agent records `PENDING_VERIFICATION` without false approval claims.
6. **Audit Trail**:
   - Click **7. Audit Trail** to view tamper-evident records linking every matching decision, hash, and status transition.
