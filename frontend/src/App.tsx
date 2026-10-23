import React, { useState, useEffect } from 'react';
import { 
  FileCheck2, 
  Receipt, 
  CheckCircle, 
  Building2, 
  FlaskConical, 
  History, 
  ShieldCheck, 
  RotateCcw,
  Sparkles,
  ExternalLink
} from 'lucide-react';

import { OverviewView } from './components/OverviewView';
import { CreateProofPackView } from './components/CreateProofPackView';
import { PaymentReconciliationView } from './components/PaymentReconciliationView';
import { ApprovalCenterView } from './components/ApprovalCenterView';
import { EmployerPortalView } from './components/EmployerPortalView';
import { TestLabView } from './components/TestLabView';
import { AuditTrailView } from './components/AuditTrailView';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [selectedPackId, setSelectedPackId] = useState<string | null>(null);
  const [demoBannerMessage, setDemoBannerMessage] = useState<string | null>(null);

  // Initialize with latest pack or TC1
  useEffect(() => {
    fetch('/api/overview/stats')
      .then(res => res.json())
      .then(data => {
        if (data.selected_pack_id) {
          setSelectedPackId(data.selected_pack_id);
        }
      })
      .catch(console.error);
  }, []);

  const handleQuickDemo = async (endpoint: string, label: string, targetTab: string) => {
    try {
      setDemoBannerMessage(`Loading ${label}...`);
      const res = await fetch(`/api/test-lab/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (data.proof_pack_id) {
        setSelectedPackId(data.proof_pack_id);
      }
      setActiveTab(targetTab);
      setDemoBannerMessage(`Loaded ${label}. Real deterministic execution completed.`);
      setTimeout(() => setDemoBannerMessage(null), 4000);
    } catch (err: any) {
      setDemoBannerMessage(`Error loading demo: ${err.message}`);
    }
  };

  const handleResetData = async () => {
    if (!confirm('Reset all demo data back to a clean baseline with TC1 preloaded?')) return;
    try {
      setDemoBannerMessage('Resetting demo environment...');
      const res = await fetch('/api/demo/reset', { method: 'POST' });
      await res.json();
      const statsRes = await fetch('/api/overview/stats');
      const statsData = await statsRes.json();
      if (statsData.selected_pack_id) {
        setSelectedPackId(statsData.selected_pack_id);
      }
      setActiveTab('overview');
      setDemoBannerMessage('Demo environment clean reset successfully.');
      setTimeout(() => setDemoBannerMessage(null), 3500);
    } catch (err: any) {
      setDemoBannerMessage(`Reset error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* Top Judge Quick Actions Header */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 font-bold tracking-tight text-white text-sm">
              <div className="w-6 h-6 rounded-lg bg-sky-500 flex items-center justify-center text-slate-950 font-black">
                R
              </div>
              RentWise AI
            </div>
            <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
              Hackathon Judge Mode
            </span>
          </div>

          {/* Quick Scenario Launchers */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-400 font-medium mr-1 hidden md:inline">Quick Scenarios:</span>
            <button 
              onClick={() => handleQuickDemo('run-tc1', 'TC1 (12 Months)', 'reconciliation')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium transition cursor-pointer"
            >
              Load TC1
            </button>
            <button 
              onClick={() => handleQuickDemo('run-tc2', 'TC2 (Missing March)', 'reconciliation')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium transition cursor-pointer"
            >
              Load TC2
            </button>
            <button 
              onClick={() => handleQuickDemo('run-tc3', 'TC3 (PAN Blocked)', 'reconciliation')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium transition cursor-pointer"
            >
              Load TC3
            </button>
            <button 
              onClick={() => handleQuickDemo('run-tc4', 'TC4 (Verification)', 'employer')}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium transition cursor-pointer"
            >
              Load TC4
            </button>
            <button 
              onClick={() => {
                setActiveTab('testlab');
                handleQuickDemo('run-all', 'All Official Tests', 'testlab');
              }}
              className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded font-semibold transition cursor-pointer"
            >
              Run All Tests
            </button>
            <button 
              onClick={handleResetData}
              title="Reset Demo Data"
              className="p-1 hover:bg-slate-800 text-slate-400 hover:text-rose-400 rounded transition cursor-pointer ml-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Navigation Bar */}
      <nav className="bg-white border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-1 overflow-x-auto text-xs font-semibold py-1">
          {[
            { id: 'overview', label: '1. Overview', icon: Building2 },
            { id: 'create', label: '2. Create Proof Pack', icon: FileCheck2 },
            { id: 'reconciliation', label: '3. Payment Reconciliation', icon: Receipt },
            { id: 'approval', label: '4. Approval Center', icon: ShieldCheck },
            { id: 'employer', label: '5. Employer Portal', icon: Building2 },
            { id: 'testlab', label: '6. Test Lab', icon: FlaskConical },
            { id: 'audit', label: '7. Audit Trail', icon: History }
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3.5 py-2.5 rounded-lg transition whitespace-nowrap cursor-pointer ${
                  isActive 
                    ? 'text-sky-600 bg-sky-50 font-bold border-b-2 border-sky-600 rounded-b-none' 
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Demo Notification Toast */}
      {demoBannerMessage && (
        <div className="bg-indigo-900 text-white text-xs py-2 px-4 text-center font-medium shadow-inner animate-pulse">
          {demoBannerMessage}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'overview' && (
          <OverviewView 
            onNavigate={setActiveTab} 
            selectedPackId={selectedPackId}
            onSelectPack={(id) => setSelectedPackId(id)}
          />
        )}
        {activeTab === 'create' && (
          <CreateProofPackView 
            onSuccess={(newPackId) => {
              setSelectedPackId(newPackId);
              setActiveTab('reconciliation');
            }} 
          />
        )}
        {activeTab === 'reconciliation' && (
          <PaymentReconciliationView 
            proofPackId={selectedPackId || ''} 
            onNavigate={setActiveTab} 
          />
        )}
        {activeTab === 'approval' && (
          <ApprovalCenterView 
            proofPackId={selectedPackId || ''} 
            onNavigate={setActiveTab} 
          />
        )}
        {activeTab === 'employer' && (
          <EmployerPortalView 
            proofPackId={selectedPackId || ''} 
          />
        )}
        {activeTab === 'testlab' && (
          <TestLabView 
            onLoadPack={(packId) => setSelectedPackId(packId)}
            onNavigate={setActiveTab}
          />
        )}
        {activeTab === 'audit' && (
          <AuditTrailView />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        RentWise AI Agent • Income Tax Act Section 10(13A) • Demonstrator tool for Hackathon Evaluation
      </footer>
    </div>
  );
}

export default App;
