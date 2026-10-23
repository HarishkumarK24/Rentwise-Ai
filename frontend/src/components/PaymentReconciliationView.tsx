import React, { useEffect, useState } from 'react';
import { RentMonth, Receipt, TaxEvaluation } from '../types';
import { 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  RefreshCw, 
  FileText, 
  Download, 
  FileCheck,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

interface Props {
  proofPackId: string;
  onNavigate: (tab: string) => void;
}

export const PaymentReconciliationView: React.FC<Props> = ({ proofPackId, onNavigate }) => {
  const [loading, setLoading] = useState(true);
  const [reconciling, setReconciling] = useState(false);
  const [generating, setGenerating] = useState(false);
  
  const [pack, setPack] = useState<any>(null);
  const [rentMonths, setRentMonths] = useState<RentMonth[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [taxEval, setTaxEval] = useState<TaxEvaluation | null>(null);
  const [panInput, setPanInput] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/proof-packs/${proofPackId}`);
      if (!res.ok) throw new Error('Failed to load proof pack');
      const data = await res.json();
      setPack(data.proof_pack);
      setRentMonths(data.rent_months);
      setReceipts(data.receipts);
      setTaxEval(data.tax_evaluation);
      if (data.proof_pack.landlord_pan) {
        setPanInput(data.proof_pack.landlord_pan);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (proofPackId) {
      fetchData();
    }
  }, [proofPackId]);

  const handleReconcile = async () => {
    try {
      setReconciling(true);
      setMessage(null);
      const res = await fetch(`/api/proof-packs/${proofPackId}/reconcile`, { method: 'POST' });
      const data = await res.json();
      setMessage(`Reconciliation Complete: ${data.matched_count} months matched, ${data.missing_count} missing payment months detected.`);
      await fetchData();
    } catch (err: any) {
      setMessage(`Reconciliation Error: ${err.message}`);
    } finally {
      setReconciling(false);
    }
  };

  const handleGenerateReceipts = async () => {
    try {
      setGenerating(true);
      setMessage(null);
      const res = await fetch(`/api/proof-packs/${proofPackId}/generate-receipts`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to generate receipts');
      setMessage(`Successfully generated ${data.receipts_count} tamper-evident PDF receipts with SHA-256 hashes.`);
      await fetchData();
    } catch (err: any) {
      setMessage(`Receipt Generation Error: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdatePan = async () => {
    try {
      setMessage(null);
      const res = await fetch(`/api/proof-packs/${proofPackId}/landlord-pan`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ landlord_pan: panInput })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update PAN');
      setMessage(`Landlord PAN updated and version incremented.`);
      await fetchData();
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

  const matchedCount = rentMonths.filter(m => m.matching_status === 'MATCHED').length;
  const missingCount = rentMonths.filter(m => m.matching_status === 'MISSING_PAYMENT').length;

  return (
    <div className="space-y-7 max-w-7xl mx-auto">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900">Payment Evidence & Reconciliation</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono">
              {pack?.id}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic matching of bank ledger transactions to each rent month. Never hallucinates missing evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={handleReconcile}
            disabled={reconciling}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold shadow transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? 'animate-spin' : ''}`} />
            {reconciling ? 'Matching Ledger...' : 'Run Reconciliation'}
          </button>
          
          <button 
            onClick={handleGenerateReceipts}
            disabled={generating || matchedCount === 0}
            className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow transition cursor-pointer disabled:opacity-50"
          >
            <FileText className="w-3.5 h-3.5" />
            {generating ? 'Generating PDFs...' : 'Generate PDF Receipts'}
          </button>

          {receipts.length > 0 && (
            <a 
              href={`/api/proof-packs/${proofPackId}/download-zip`}
              download
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download All (ZIP)
            </a>
          )}
        </div>
      </div>

      {message && (
        <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs font-medium flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-blue-500 hover:text-blue-800">✕</button>
        </div>
      )}

      {/* Tax & Landlord PAN Assessment Card */}
      {taxEval && (
        <div className={`p-5 rounded-xl border ${
          taxEval.status === 'PAN_REQUIRED_BLOCKING' 
            ? 'bg-amber-50/70 border-amber-300 text-amber-900' 
            : 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
        }`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                Statutory Tax Rule Status: {taxEval.status}
              </div>
              <p className="text-xs max-w-3xl leading-relaxed">
                {taxEval.explanation}
              </p>
              <div className="text-[11px] text-slate-500 font-mono mt-1">
                Source: {taxEval.policy_source} • Threshold: ₹{taxEval.threshold.toLocaleString()}/year
              </div>
            </div>

            {taxEval.status === 'PAN_REQUIRED_BLOCKING' && (
              <div className="flex items-center gap-2 bg-white p-2 rounded-lg border border-amber-300 shadow-xs">
                <input 
                  type="text" 
                  value={panInput}
                  onChange={(e) => setPanInput(e.target.value.toUpperCase())}
                  placeholder="Enter Landlord PAN"
                  className="px-2.5 py-1.5 text-xs border border-slate-300 rounded font-mono uppercase outline-none focus:border-sky-500"
                />
                <button 
                  onClick={handleUpdatePan}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold cursor-pointer"
                >
                  Save PAN
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reconciliation Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Month Ledger Reconciliation</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
              {matchedCount} Matched
            </span>
            {missingCount > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-medium">
                {missingCount} Missing Payment
              </span>
            )}
          </div>
          <span className="text-xs text-slate-500">
            Expected: ₹{(pack?.monthly_rent * rentMonths.length).toLocaleString()}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-700 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Rent Month</th>
                <th className="py-3 px-4">Expected Rent</th>
                <th className="py-3 px-4">Allocated Bank Payment</th>
                <th className="py-3 px-4">Difference</th>
                <th className="py-3 px-4">Ledger Status</th>
                <th className="py-3 px-4">Evidence & Transaction Reference</th>
                <th className="py-3 px-4 text-center">Receipt Eligibility</th>
                <th className="py-3 px-4 text-right">PDF Receipt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rentMonths.map((rm) => {
                const rec = receipts.find(r => r.month_str === rm.month_str);
                return (
                  <tr key={rm.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-semibold text-slate-900">{rm.month_label}</td>
                    <td className="py-3 px-4 font-mono">₹{rm.expected_rent.toLocaleString()}</td>
                    <td className="py-3 px-4 font-mono font-medium text-slate-800">
                      ₹{rm.allocated_amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500">
                      {rm.difference === 0 ? '₹0' : `₹${rm.difference.toLocaleString()}`}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        rm.matching_status === 'MATCHED' ? 'bg-emerald-100 text-emerald-800' :
                        rm.matching_status === 'MISSING_PAYMENT' ? 'bg-rose-100 text-rose-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {rm.matching_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate font-mono text-slate-600">
                      {rm.transaction_references || (
                        <span className="text-rose-500 italic">No bank ledger transaction found</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {rm.is_eligible_for_receipt ? (
                        <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Eligible
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-500 font-semibold">
                          <AlertCircle className="w-3.5 h-3.5" /> Ineligible
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {rec ? (
                        <a 
                          href={`/api/receipts/${rec.id}/download`} 
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-800 font-semibold cursor-pointer"
                        >
                          <Download className="w-3.5 h-3.5" /> View PDF
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">Not generated</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Next Step Navigation */}
      <div className="flex justify-end pt-2">
        <button 
          onClick={() => onNavigate('approval')}
          className="flex items-center gap-2 px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-xl shadow-md text-xs transition cursor-pointer"
        >
          Proceed to Human Approval Gate <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
