import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  UploadCloud, 
  FileCheck2, 
  Lock,
  ArrowRight
} from 'lucide-react';
import { ApprovalRequest, Receipt } from '../types';

interface Props {
  proofPackId: string;
  onNavigate: (tab: string) => void;
}

export const ApprovalCenterView: React.FC<Props> = ({ proofPackId, onNavigate }) => {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  const [approvalReq, setApprovalReq] = useState<ApprovalRequest | null>(null);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [pack, setPack] = useState<any>(null);
  const [taxEval, setTaxEval] = useState<any>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [decisionNotes, setDecisionNotes] = useState('All 12 receipts reconciled against HDFC bank ledger. Verified accurate for HRA tax exemption.');
  const [approverName, setApproverName] = useState('Aarav Sharma (Salaried Tenant)');

  const fetchApprovalState = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`/api/proof-packs/${proofPackId}`);
      if (!res.ok) throw new Error('Failed to load proof pack');
      const data = await res.json();
      setPack(data.proof_pack);
      setReceipts(data.receipts);
      setTaxEval(data.tax_evaluation);
      setApprovalReq(data.approval_request);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (proofPackId) {
      fetchApprovalState();
    }
  }, [proofPackId]);

  const handleInitApprovalRequest = async () => {
    try {
      setSubmitting(true);
      setError(null);
      const res = await fetch(`/api/proof-packs/${proofPackId}/approval-request`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to initialize approval request');
      setMessage('Approval Request successfully initialized. Review payload details below.');
      await fetchApprovalState();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRecordDecision = async (decision: 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES') => {
    if (!approvalReq) return;
    try {
      setSubmitting(true);
      setError(null);
      const res = await fetch(`/api/approval-requests/${approvalReq.id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          approver_identity: approverName,
          reason_notes: decisionNotes
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Decision submission failed');
      setMessage(`Decision recorded: ${decision}`);
      await fetchApprovalState();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExecuteUpload = async () => {
    if (!approvalReq) return;
    try {
      setUploading(true);
      setError(null);
      const res = await fetch(`/api/approval-requests/${approvalReq.id}/upload`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setMessage(data.message);
      onNavigate('employer');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  const isApproved = approvalReq?.status === 'APPROVED';

  return (
    <div className="space-y-7 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-sky-600" />
          <h1 className="text-2xl font-bold text-slate-900">Mandatory Human Approval Gate</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Server-enforced verification lock. The agent is strictly prohibited from uploading receipts to employer systems without explicit human confirmation.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-300 rounded-xl text-rose-800 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <div>
            <div className="font-bold">Approval Gate Blocked</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {message && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-800 text-xs flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-emerald-700 font-bold">✕</button>
        </div>
      )}

      {!approvalReq ? (
        <div className="bg-white p-8 rounded-xl border border-slate-200 text-center space-y-4 shadow-sm">
          <Lock className="w-10 h-10 text-slate-400 mx-auto" />
          <h2 className="text-base font-bold text-slate-800">No Active Approval Request</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Ready to initiate formal review for {receipts.length} receipts totaling ₹{(pack?.monthly_rent * receipts.length).toLocaleString()}.
          </p>
          <button 
            onClick={handleInitApprovalRequest}
            disabled={submitting || receipts.length === 0}
            className="px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow cursor-pointer disabled:opacity-50"
          >
            {submitting ? 'Initializing Gate...' : 'Generate Approval Gate Request'}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Approval Details Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Approval Request ID</span>
                <div className="font-mono text-sm font-bold text-slate-900">{approvalReq.id}</div>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Gate Status</span>
                <div>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${
                    isApproved ? 'bg-emerald-100 text-emerald-800' :
                    approvalReq.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                    'bg-amber-100 text-amber-800'
                  }`}>
                    {approvalReq.status}
                  </span>
                </div>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Target Destination</span>
                <div className="text-xs font-semibold text-slate-800">{approvalReq.destination_portal}</div>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Claimed Rent</span>
                <div className="text-sm font-extrabold text-slate-900">₹{approvalReq.total_claimed_rent.toLocaleString()}</div>
              </div>
            </div>

            {/* Evidence & Hash Integrity */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Cryptographic Payload Integrity</h3>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-600 font-mono space-y-1">
                <div>Receipt Count: {approvalReq.receipt_count} PDFs verified</div>
                <div>Hash Binding: Bound to exact SHA-256 digest of generated PDFs. Any modification invalidates this approval automatically.</div>
              </div>
            </div>

            {/* Decision Controls */}
            {!isApproved ? (
              <div className="space-y-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Approver Identity *</label>
                  <input 
                    type="text" 
                    value={approverName}
                    onChange={(e) => setApproverName(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Review Notes & Consequence Confirmation *</label>
                  <textarea 
                    rows={2}
                    value={decisionNotes}
                    onChange={(e) => setDecisionNotes(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button 
                    onClick={() => handleRecordDecision('APPROVE')}
                    disabled={submitting}
                    className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow cursor-pointer disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Approve and Authorize Upload
                  </button>
                  <button 
                    onClick={() => handleRecordDecision('REJECT')}
                    disabled={submitting}
                    className="flex items-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" /> Reject Proof Pack
                  </button>
                  <button 
                    onClick={() => handleRecordDecision('REQUEST_CHANGES')}
                    disabled={submitting}
                    className="px-4 py-2.5 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 cursor-pointer"
                  >
                    Request Changes
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Human Approval Recorded: Approved by {approvalReq.approver_identity}
                </div>
                <p className="text-xs">
                  Payload is locked and verified. You may now execute the idempotent submission to the Mock Employer Portal.
                </p>
                <button 
                  onClick={handleExecuteUpload}
                  disabled={uploading}
                  className="flex items-center gap-2 px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow cursor-pointer disabled:opacity-50"
                >
                  <UploadCloud className="w-4 h-4" />
                  {uploading ? 'Submitting to Portal...' : 'Execute Submission to Mock Employer Portal →'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
