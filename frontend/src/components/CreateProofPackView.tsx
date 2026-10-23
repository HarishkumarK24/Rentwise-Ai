import React, { useState } from 'react';
import { Building2, User, Calendar, DollarSign, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-react';

interface Props {
  onSuccess: (packId: string) => void;
}

export const CreateProofPackView: React.FC<Props> = ({ onSuccess }) => {
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    tenant_name: 'Aarav Sharma',
    employee_id: 'EMP-8921',
    employer_name: 'Acme Technologies Pvt Ltd',
    work_location: 'Bengaluru',
    financial_year: '2025-2026',
    declaration_period: 'Apr 2025 - Mar 2026',
    
    landlord_name: 'Suresh R. Verma',
    landlord_address: '#402, Green Glen Heights, Bellandur, Bengaluru 560103',
    landlord_contact: '+91-9876543210',
    landlord_pan: 'ABCDE1234F',
    monthly_rent: 25000,
    deposit_amount: 50000,
    rent_agreement_ref: 'AGR-BLR-2025-99',
    
    start_month: '2025-04',
    end_month: '2026-03',
    payment_source: 'HDFC_NETBANKING'
  });

  const estimatedAnnual = formData.monthly_rent * 12;
  const isPanRequired = estimatedAnnual > 100000;

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/proof-packs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to create proof pack');
      }
      onSuccess(data.proof_pack_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Create HRA Rent Proof Pack</h1>
        <p className="text-sm text-slate-500 mt-1">
          Guided 4-step wizard to collect tenancy parameters, validate statutory rules, and prepare ledger matching.
        </p>
      </div>

      {/* Stepper Progress */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        {[
          { num: 1, title: 'Tenant Details' },
          { num: 2, title: 'Landlord & Property' },
          { num: 3, title: 'Rent Schedule' },
          { num: 4, title: 'Review & Verify' }
        ].map((s) => (
          <div 
            key={s.num} 
            onClick={() => setStep(s.num)}
            className={`flex items-center gap-2 cursor-pointer ${
              step === s.num ? 'text-sky-600 font-bold' : step > s.num ? 'text-emerald-600 font-medium' : 'text-slate-400'
            }`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
              step === s.num ? 'bg-sky-600 text-white' : step > s.num ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
            }`}>
              {step > s.num ? '✓' : s.num}
            </div>
            <span className="text-xs hidden sm:inline">{s.title}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Step 1: Tenant Details */}
      {step === 1 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <User className="w-4 h-4 text-sky-600" />
            Step A: Salaried Tenant & Employer Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Tenant Full Name *</label>
              <input 
                type="text" 
                value={formData.tenant_name} 
                onChange={(e) => setFormData({...formData, tenant_name: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Employee ID *</label>
              <input 
                type="text" 
                value={formData.employee_id} 
                onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Employer Name *</label>
              <input 
                type="text" 
                value={formData.employer_name} 
                onChange={(e) => setFormData({...formData, employer_name: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Work Location / City</label>
              <input 
                type="text" 
                value={formData.work_location} 
                onChange={(e) => setFormData({...formData, work_location: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Financial Year</label>
              <input 
                type="text" 
                value={formData.financial_year} 
                onChange={(e) => setFormData({...formData, financial_year: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Declaration Period</label>
              <input 
                type="text" 
                value={formData.declaration_period} 
                onChange={(e) => setFormData({...formData, declaration_period: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
          </div>
          <div className="flex justify-end pt-3">
            <button 
              onClick={() => setStep(2)}
              className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-lg text-sm flex items-center gap-2 cursor-pointer"
            >
              Next: Landlord Details <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Landlord Details */}
      {step === 2 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-sky-600" />
            Step B: Landlord & Leased Property Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Landlord Full Name *</label>
              <input 
                type="text" 
                value={formData.landlord_name} 
                onChange={(e) => setFormData({...formData, landlord_name: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Landlord PAN {isPanRequired ? '(Statutorily Required)' : '(Optional below ₹1L)'}
              </label>
              <input 
                type="text" 
                value={formData.landlord_pan} 
                onChange={(e) => setFormData({...formData, landlord_pan: e.target.value.toUpperCase()})}
                placeholder="e.g. ABCDE1234F"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none font-mono uppercase"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Rented Property Address *</label>
              <input 
                type="text" 
                value={formData.landlord_address} 
                onChange={(e) => setFormData({...formData, landlord_address: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone</label>
              <input 
                type="text" 
                value={formData.landlord_contact} 
                onChange={(e) => setFormData({...formData, landlord_contact: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Rent Agreement Reference</label>
              <input 
                type="text" 
                value={formData.rent_agreement_ref} 
                onChange={(e) => setFormData({...formData, rent_agreement_ref: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-between pt-3">
            <button 
              onClick={() => setStep(1)}
              className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm cursor-pointer"
            >
              Back
            </button>
            <button 
              onClick={() => setStep(3)}
              className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-lg text-sm flex items-center gap-2 cursor-pointer"
            >
              Next: Rent Schedule <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Rent Schedule */}
      {step === 3 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-sky-600" />
            Step C: Rent Schedule & Payment Source
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Monthly Rent Amount (₹) *</label>
              <input 
                type="number" 
                value={formData.monthly_rent} 
                onChange={(e) => setFormData({...formData, monthly_rent: parseInt(e.target.value) || 0})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none font-semibold text-slate-900"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Security Deposit (₹)</label>
              <input 
                type="number" 
                value={formData.deposit_amount} 
                onChange={(e) => setFormData({...formData, deposit_amount: parseInt(e.target.value) || 0})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Start Month (YYYY-MM)</label>
              <input 
                type="text" 
                value={formData.start_month} 
                onChange={(e) => setFormData({...formData, start_month: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">End Month (YYYY-MM)</label>
              <input 
                type="text" 
                value={formData.end_month} 
                onChange={(e) => setFormData({...formData, end_month: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none font-mono"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Payment History Source</label>
              <select 
                value={formData.payment_source}
                onChange={(e) => setFormData({...formData, payment_source: e.target.value})}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 outline-none bg-white"
              >
                <option value="HDFC_NETBANKING">HDFC Bank Direct NetBanking Connector (Synthetic Feed)</option>
                <option value="ICICI_UPI">ICICI Bank UPI Statement Connector</option>
                <option value="MANUAL_LEDGER">Manual Ledger Verification</option>
              </select>
            </div>
          </div>

          <div className="flex justify-between pt-3">
            <button 
              onClick={() => setStep(2)}
              className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm cursor-pointer"
            >
              Back
            </button>
            <button 
              onClick={() => setStep(4)}
              className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-lg text-sm flex items-center gap-2 cursor-pointer"
            >
              Next: Review & Validation <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Review & Validation */}
      {step === 4 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Step D: Pre-Reconciliation Review & Tax Threshold Audit
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-2">
              <div className="text-slate-400 font-semibold uppercase tracking-wider">Tenant & Tenancy</div>
              <div><b>Tenant:</b> {formData.tenant_name} ({formData.employee_id})</div>
              <div><b>Employer:</b> {formData.employer_name}</div>
              <div><b>Financial Year:</b> {formData.financial_year}</div>
              <div><b>Period:</b> {formData.start_month} to {formData.end_month} (12 Months)</div>
              <div><b>Monthly Rent:</b> ₹{formData.monthly_rent.toLocaleString()}</div>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-2">
              <div className="text-slate-400 font-semibold uppercase tracking-wider">Landlord & PAN Rule</div>
              <div><b>Landlord:</b> {formData.landlord_name}</div>
              <div><b>Address:</b> {formData.landlord_address}</div>
              <div><b>Landlord PAN:</b> {formData.landlord_pan || 'NOT PROVIDED'}</div>
              <div><b>Projected Annual Rent:</b> ₹{estimatedAnnual.toLocaleString()}</div>
              <div>
                <b>Statutory Threshold:</b> ₹1,00,000 / year
              </div>
            </div>
          </div>

          {/* Tax Rule Notification Card */}
          <div className={`p-4 rounded-xl border text-xs ${
            isPanRequired 
              ? (formData.landlord_pan ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-amber-50 border-amber-200 text-amber-800')
              : 'bg-blue-50 border-blue-200 text-blue-800'
          }`}>
            <div className="font-bold flex items-center gap-2 mb-1">
              <ShieldAlert className="w-4 h-4" />
              Applicable Tax Policy Rule: Section 10(13A) / CBDT Circular No. 08/2013
            </div>
            <p>
              {isPanRequired 
                ? (formData.landlord_pan 
                    ? `Annual rent (₹${estimatedAnnual.toLocaleString()}) exceeds ₹1,00,000 threshold. Landlord PAN '${formData.landlord_pan}' provided and will be verified for receipt inclusion.`
                    : `⚠️ Annual rent (₹${estimatedAnnual.toLocaleString()}) strictly exceeds ₹1,00,000 threshold. Landlord PAN is required under statutory rules. Final portal submission will be blocked until PAN is supplied.`)
                : `Annual rent (₹${estimatedAnnual.toLocaleString()}) is below the ₹1,00,000 threshold. Landlord PAN is optional under statutory guidelines.`
              }
            </p>
          </div>

          <div className="flex justify-between pt-3">
            <button 
              onClick={() => setStep(3)}
              className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm cursor-pointer"
            >
              Back
            </button>
            <button 
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-lg text-sm flex items-center gap-2 shadow-md cursor-pointer disabled:opacity-50"
            >
              {loading ? 'Creating Proof Pack...' : 'Initialize & Connect Bank Ledger →'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
