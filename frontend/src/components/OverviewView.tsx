import React, { useEffect, useState } from 'react';
import { OverviewStats } from '../types';
import { 
  FileCheck2, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  UploadCloud, 
  ArrowRight,
  TrendingUp,
  Receipt,
  Building,
  UserCheck
} from 'lucide-react';

interface Props {
  onNavigate: (tab: string) => void;
  selectedPackId: string | null;
  onSelectPack: (packId: string) => void;
}

export const OverviewView: React.FC<Props> = ({ onNavigate, selectedPackId, onSelectPack }) => {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const url = selectedPackId 
        ? `/api/overview/stats?proof_pack_id=${selectedPackId}`
        : '/api/overview/stats';
      const res = await fetch(url);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [selectedPackId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner / Hero */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl p-7 shadow-xl border border-slate-700/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-sky-500/20 text-sky-300 text-xs font-semibold px-2.5 py-1 rounded-full border border-sky-400/30">
              Tax FY 2025-2026 Engine
            </span>
            <span className="bg-emerald-500/20 text-emerald-300 text-xs font-semibold px-2.5 py-1 rounded-full border border-emerald-400/30">
              Deterministic Verification Active
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            RentWise AI — HRA Proof Pack Agent
          </h1>
          <p className="text-slate-300 text-sm mt-1 max-w-2xl">
            Autonomous audit-grade agent for banking evidence reconciliation, statutory landlord PAN threshold validation, tamper-evident PDF receipts, human approval gating, and independent employer portal verification.
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => onNavigate('create')}
            className="flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold rounded-xl shadow-lg transition-all text-sm cursor-pointer"
          >
            Create New Proof Pack
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Selected Proof Pack Context Bar */}
      {stats?.has_proof_pack && (
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-sky-50 text-sky-600 rounded-lg">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Proof Pack</div>
              <div className="font-semibold text-slate-900 text-base flex items-center gap-2">
                {stats.tenant_name} • {stats.financial_year}
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono">
                  {stats.selected_pack_id}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => onNavigate('reconciliation')}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition cursor-pointer"
            >
              View Month Timeline
            </button>
            <button 
              onClick={() => onNavigate('approval')}
              className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
            >
              Approval Center
            </button>
          </div>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div 
          onClick={() => onNavigate('reconciliation')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-sky-300 hover:shadow-md transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Rent Months</span>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{stats?.total_rent_months ?? 0}</span>
            <span className="text-xs text-slate-500 font-medium">months claimed</span>
          </div>
          <div className="mt-2 text-xs text-emerald-600 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{stats?.matched_payment_months ?? 0} verified matched</span>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('reconciliation')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-amber-300 hover:shadow-md transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Missing Evidence</span>
            <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-600">{stats?.missing_payment_months ?? 0}</span>
            <span className="text-xs text-slate-500 font-medium">unresolved months</span>
          </div>
          <div className="mt-2 text-xs text-slate-500 font-medium">
            Receipts blocked until bank proof verified
          </div>
        </div>

        <div 
          onClick={() => onNavigate('approval')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-300 hover:shadow-md transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Receipts & Approval</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{stats?.receipts_generated ?? 0}</span>
            <span className="text-xs text-slate-500 font-medium">PDFs generated</span>
          </div>
          <div className="mt-2 text-xs text-amber-600 flex items-center gap-1 font-medium">
            <Clock className="w-3.5 h-3.5" />
            <span>{stats?.items_awaiting_approval ?? 0} awaiting human approval</span>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('employer')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Employer Upload</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <UploadCloud className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">
              {stats?.uploads_awaiting_verification ? 'Pending' : (stats?.verified_upload_outcomes ? 'Verified' : 'Ready')}
            </span>
            <span className="text-xs text-slate-500 font-medium">portal sync</span>
          </div>
          <div className="mt-2 text-xs text-slate-600 flex items-center gap-1 font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            <span>{stats?.uploads_awaiting_verification ?? 0} pending employer check</span>
          </div>
        </div>
      </div>

      {/* Timeline & Flow Explanation */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 mb-1">Verifiable Evidence Flow Pipeline</h2>
        <p className="text-xs text-slate-500 mb-6">
          Every stage is cryptographically linked with SHA-256 hashes and append-only audit entries.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-sky-600">STAGE 1</div>
            <div className="font-semibold text-slate-800 text-sm mt-1">Tenant & Rent Intake</div>
            <p className="text-xs text-slate-500 mt-1">Collects rent schedule, period, and landlord details with boundary validation.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-sky-600">STAGE 2</div>
            <div className="font-semibold text-slate-800 text-sm mt-1">Bank Reconciliation</div>
            <p className="text-xs text-slate-500 mt-1">Deterministic matching of bank ledger records to rent months. Zero hallucinations.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-sky-600">STAGE 3</div>
            <div className="font-semibold text-slate-800 text-sm mt-1">Statutory PAN Rule</div>
            <p className="text-xs text-slate-500 mt-1">Enforces CBDT ₹1 Lakh threshold. Mandates landlord PAN before upload if rent &gt; ₹1L.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-sky-600">STAGE 4</div>
            <div className="font-semibold text-slate-800 text-sm mt-1">Human Approval Gate</div>
            <p className="text-xs text-slate-500 mt-1">Mandatory human sign-off bound to payload hashes. Blocks unauthorized automatic push.</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-sky-600">STAGE 5</div>
            <div className="font-semibold text-slate-800 text-sm mt-1">Independent Verification</div>
            <p className="text-xs text-slate-500 mt-1">Re-reads mock employer portal status. Distinguishes 'Uploaded' from 'Approved'.</p>
          </div>
        </div>
      </div>

      {/* Recent Proof Packs Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Stored Proof Packs</h2>
            <p className="text-xs text-slate-500">Persistent database records for tenant declarations</p>
          </div>
          <button 
            onClick={() => onNavigate('create')}
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1 cursor-pointer"
          >
            + New Pack
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-700 text-xs uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Proof Pack ID</th>
                <th className="py-3 px-4">Tenant Name</th>
                <th className="py-3 px-4">Financial Year</th>
                <th className="py-3 px-4">Monthly Rent</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats?.recent_packs && stats.recent_packs.length > 0 ? (
                stats.recent_packs.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-mono text-xs font-semibold text-slate-900">{p.id}</td>
                    <td className="py-3 px-4 font-medium text-slate-800">{p.tenant_name}</td>
                    <td className="py-3 px-4">{p.financial_year}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">₹{p.monthly_rent.toLocaleString()}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        p.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' :
                        p.status === 'PAN_REQUIRED' ? 'bg-amber-100 text-amber-800' :
                        p.status === 'RECEIPTS_GENERATED' ? 'bg-indigo-100 text-indigo-800' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button 
                        onClick={() => {
                          onSelectPack(p.id);
                          onNavigate('reconciliation');
                        }}
                        className="text-xs font-semibold text-sky-600 hover:text-sky-800 cursor-pointer"
                      >
                        Inspect &rarr;
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No proof packs created yet. Use Quick Demos in the top bar or Create New Proof Pack.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
