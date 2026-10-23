export interface ProofPack {
  id: string;
  tenant_name: string;
  employee_id: string;
  employer_name: string;
  work_location?: string;
  financial_year: string;
  declaration_period: string;
  landlord_name: string;
  landlord_address: string;
  landlord_contact?: string;
  landlord_pan?: string;
  monthly_rent: number;
  start_month: string;
  end_month: string;
  status: string;
  version: number;
  created_at: string;
}

export interface RentMonth {
  id: string;
  month_str: string;
  month_label: string;
  expected_rent: number;
  allocated_amount: number;
  difference: number;
  matching_status: string;
  matching_method: string;
  confidence: string;
  explanation: string;
  transaction_references: string;
  is_eligible_for_receipt: boolean;
}

export interface Receipt {
  id: string;
  month_str: string;
  month_label: string;
  amount: number;
  payment_date: string;
  payment_reference: string;
  pdf_sha256: string;
  requires_signature: boolean;
}

export interface TaxEvaluation {
  annual_rent: number;
  threshold: number;
  is_above_threshold: boolean;
  is_at_threshold: boolean;
  pan_required: boolean;
  pan_provided: boolean;
  pan_valid_format: boolean;
  status: string;
  explanation: string;
  policy_source: string;
  effective_date: string;
  policy_type: string;
}

export interface ApprovalRequest {
  id: string;
  status: string;
  total_claimed_rent: number;
  receipt_count: number;
  destination_portal: string;
  approver_identity?: string;
  decision_timestamp?: string;
  reason_notes?: string;
}

export interface UploadOperation {
  id: string;
  status: string;
  portal_upload_ref?: string;
  latest_verified_status?: string;
  verification_timestamp?: string;
  discrepancy_explanation?: string;
}

export interface OverviewStats {
  has_proof_pack: boolean;
  selected_pack_id?: string;
  tenant_name?: string;
  financial_year?: string;
  status?: string;
  total_rent_months: number;
  matched_payment_months: number;
  missing_payment_months: number;
  receipts_generated: number;
  items_awaiting_approval: number;
  uploads_awaiting_verification: number;
  verified_upload_outcomes: number;
  recent_packs: Array<{
    id: string;
    tenant_name: string;
    financial_year: string;
    status: string;
    monthly_rent: number;
    created_at: string;
  }>;
}

export interface AuditEvent {
  id: string;
  entity_id: string;
  entity_type: string;
  event_type: string;
  actor_identity: string;
  timestamp: string;
  correlation_id?: string;
  before_state?: any;
  after_state?: any;
  evidence_references?: any;
  reason?: string;
}

export interface TestReport {
  id: string;
  test_case_id: string;
  test_case_name: string;
  status: string;
  executed_at: string;
  inputs_summary: string;
  expected_result: string;
  actual_result: string;
  assertions: Array<{ check: string; pass: boolean }>;
  explanation: string;
}
