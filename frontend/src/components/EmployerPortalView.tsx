import React, { useEffect, useState } from 'react';
import { 
  Building, 
  UploadCloud, 
  ShieldCheck, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ExternalLink,
  FileText
} from 'lucide-react';
import { UploadOperation } from '../types';

interface Props {
  proofPackId: string;
}

export const EmployerPortalView: React.FC<Props> = ({ proofPackId }) => {
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [declarations, setDeclarations] = useState<any[]>([]);
  const [uploadOp, setUploadOp] = useState<UploadOperation | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchPortalData = async () => {
    try {
      setLoading(true);
      const declRes = await fetch('/api/mock-portal/declarations');
      const declData = await declRes.json();
      setDeclarations(declData);

      if (proofPackId) {
        const packRes = await fetch(`/api/proof-packs/${proofPackId}`);
        const packData = await packRes.json();
        setUploadOp(packData.upload_operation);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, [proofPackId]);

  const handleVerify = async () => {
    if (!uploadOp) return;
    try {
      setVerifying(true);
      setMessage(null);
      const res = await fetch(`/api/upload-operations/${uploadOp.id}/verify`, { method: 'POST' });
      const data = await res.json();
      setMessage(`Independent Verification Completed: Portal reported status is '${data.portal_status}'. Verified State: '${data.verified_status}'.`);
      await fetchPortalData();
    } catch (err: any) {
      setMessage(`Verification Error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateStatus = async (status: string) => {
    if (!uploadOp?.portal_upload_ref) return;
    try {
      await fetch(`/api/mock-portal/uploads/${uploadOp.portal_upload_ref}/simulate-status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      setMessage(`Employer Portal reviewer status updated to '${status}'. Click 'Re-Read Portal Status' to verify.`);
      await fetchPortalData();
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-7 max-w-5xl mx-auto">
      {/* Top Banner */}
      <div>
        <div className="flex items-center gap-2">
          <Building className="w-6 h-6 text-indigo-600" />
          <h1 className="text-2xl font-bold text-slate-900">Mock Employer Investment Portal</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Simulated Acme Technologies Enterprise HRMS. Uploads are strictly verified by independently querying the portal status endpoint after submission.
        </p>
      </div>

      {message && (
        <div className="p-4 bg-sky-50 border border-sky-200 text-sky-900 rounded-xl text-xs flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-sky-700 font-bold">✕</button>
        </div>
      )}

      {/* Upload & Verification Status Card */}
      {uploadOp ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Portal Upload Reference</span>
              <div className="font-mono text-base font-bold text-slate-900">{uploadOp.portal_upload_ref}</div>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Independent Verified State</span>
              <div>
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                  uploadOp.status === 'PENDING_VERIFICATION' ? 'bg-amber-100 text-amber-800' :
                  uploadOp.status === 'VERIFIED_APPROVED' ? 'bg-emerald-100 text-emerald-800' :
                  uploadOp.status === 'VERIFIED_REJECTED' ? 'bg-rose-100 text-rose-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {uploadOp.status === 'PENDING_VERIFICATION' && <Clock className="w-3.5 h-3.5" />}
                  {uploadOp.status === 'VERIFIED_APPROVED' && <CheckCircle2 className="w-3.5 h-3.5" />}
                  {uploadOp.status === 'VERIFIED_REJECTED' && <AlertCircle className="w-3.5 h-3.5" />}
                  {uploadOp.status}
                </span>
              </div>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Last Verified At</span>
              <div className="text-xs text-slate-700">
                {uploadOp.verification_timestamp ? new Date(uploadOp.verification_timestamp).toLocaleString() : 'Not verified yet'}
              </div>
            </div>
          </div>

          {/* Action / Re-read status */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Post-Upload Verification Requirement</h3>
              <p className="text-xs text-slate-500 max-w-lg mt-0.5">
                The agent does NOT assume 'Uploaded' means 'Approved'. It polls the employer status endpoint to capture actual HR payroll review state.
              </p>
            </div>

            <button 
              onClick={handleVerify}
              disabled={verifying}
              className="flex items-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
              {verifying ? 'Querying Portal...' : 'Re-Read Portal Status (Verify)'}
            </button>
          </div>

          {/* Simulation Controls for Hackathon Testing */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Mock Employer Reviewer Simulator (For Hackathon Demonstration)
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <button 
                onClick={() => handleSimulateStatus('PENDING_VERIFICATION')}
                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-medium cursor-pointer"
              >
                Set Portal to: Pending Verification (TC4)
              </button>
              <button 
                onClick={() => handleSimulateStatus('VERIFIED_APPROVED')}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium cursor-pointer"
              >
                Set Portal to: Verified Approved
              </button>
              <button 
                onClick={() => handleSimulateStatus('VERIFIED_REJECTED')}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-medium cursor-pointer"
              >
                Set Portal to: Verified Rejected
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl border border-slate-200 text-center text-slate-500 text-xs shadow-sm">
          No submission executed yet for the active proof pack. Complete the Human Approval Gate first.
        </div>
      )}

      {/* Mock Employer Declaration Ledger */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-900">Employer Declaration Records (Mock Database)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold uppercase border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Declaration ID</th>
                <th className="py-2.5 px-4">Employee</th>
                <th className="py-2.5 px-4">Component</th>
                <th className="py-2.5 px-4">Portal Status</th>
                <th className="py-2.5 px-4">Receipts Received</th>
                <th className="py-2.5 px-4">Last Upload Ref</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {declarations.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">{d.id}</td>
                  <td className="py-2.5 px-4">{d.tenant_name} ({d.employee_id})</td>
                  <td className="py-2.5 px-4 font-medium text-slate-700">{d.component}</td>
                  <td className="py-2.5 px-4">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      d.status === 'VERIFIED_APPROVED' ? 'bg-emerald-100 text-emerald-800' :
                      d.status === 'PENDING_VERIFICATION' ? 'bg-amber-100 text-amber-800' :
                      d.status === 'VERIFIED_REJECTED' ? 'bg-rose-100 text-rose-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-bold">{d.uploaded_files_count} files</td>
                  <td className="py-2.5 px-4 font-mono text-slate-500">{d.last_upload_ref || 'None'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
