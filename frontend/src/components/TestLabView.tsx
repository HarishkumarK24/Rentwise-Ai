import React, { useEffect, useState } from 'react';
import { 
  FlaskConical, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert, 
  RefreshCw,
  FileCode2,
  ChevronRight
} from 'lucide-react';
import { TestReport } from '../types';

interface Props {
  onLoadPack: (packId: string) => void;
  onNavigate: (tab: string) => void;
}

export const TestLabView: React.FC<Props> = ({ onLoadPack, onNavigate }) => {
  const [reports, setReports] = useState<TestReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [runningAll, setRunningAll] = useState(false);
  const [runningSingle, setRunningSingle] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<TestReport | null>(null);

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/test-lab/reports');
      const data = await res.json();
      setReports(data);
      if (data.length > 0 && !selectedReport) {
        setSelectedReport(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleRunAll = async () => {
    try {
      setRunningAll(true);
      const res = await fetch('/api/test-lab/run-all', { method: 'POST' });
      await res.json();
      await fetchReports();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningAll(false);
    }
  };

  const handleRunSingle = async (endpoint: string, tcId: string) => {
    try {
      setRunningSingle(tcId);
      const res = await fetch(`/api/test-lab/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (data.proof_pack_id) {
        onLoadPack(data.proof_pack_id);
      }
      await fetchReports();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningSingle(null);
    }
  };

  const officialCases = [
    {
      id: 'TC1',
      endpoint: 'run-tc1',
      title: 'TC1 — Twelve Monthly Rent Payments',
      desc: '12 rent months in FY 2025-26, 12 valid bank ledger payments, exact amount & date match. 12 receipts generated with zero duplicates.'
    },
    {
      id: 'TC2',
      endpoint: 'run-tc2',
      title: 'TC2 — No Payment Found for March',
      desc: '12-month period with March payment omitted from ledger. March flagged as MISSING_PAYMENT, 0 March receipt fabricated, 11 receipts generated.'
    },
    {
      id: 'TC3',
      endpoint: 'run-tc3',
      title: 'TC3 — Annual Rent Above Landlord-PAN Threshold',
      desc: 'Annual rent > ₹1,00,000 statutory threshold. Landlord PAN omitted. Asserts PAN requirement flagged, user prompted, submission blocked, and boundary checks (80k, 100k, 100k+1) pass.'
    },
    {
      id: 'TC4',
      endpoint: 'run-tc4',
      title: 'TC4 — Employer Portal Shows Pending Verification',
      desc: 'Human-approved submission sent to mock portal. Agent independently re-reads portal status, asserts PENDING_VERIFICATION, and never prematurely marks as Approved.'
    }
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-sky-600" />
            <h1 className="text-2xl font-bold text-slate-900">Official Test Lab & Verification Bench</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Automated test harness executing the four mandatory hackathon scenarios with live assertions and persistent reports.
          </p>
        </div>

        <button 
          onClick={handleRunAll}
          disabled={runningAll}
          className="flex items-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow cursor-pointer disabled:opacity-50"
        >
          <Play className={`w-4 h-4 ${runningAll ? 'animate-spin' : ''}`} />
          {runningAll ? 'Executing Full Test Suite...' : 'Run All Official Tests (TC1–TC4)'}
        </button>
      </div>

      {/* Official Test Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {officialCases.map((tc) => {
          const latestReport = reports.find(r => r.test_case_id === tc.id);
          const isPassed = latestReport?.status === 'PASS';
          return (
            <div key={tc.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {tc.id}
                  </span>
                  {latestReport && (
                    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full ${
                      isPassed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {isPassed ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {latestReport.status}
                    </span>
                  )}
                </div>
                <h3 className="font-bold text-slate-900 text-sm mt-2">{tc.title}</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{tc.desc}</p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <span className="text-[11px] text-slate-400">
                  {latestReport ? `Last run: ${new Date(latestReport.executed_at).toLocaleTimeString()}` : 'Not run yet'}
                </span>
                <button 
                  onClick={() => handleRunSingle(tc.endpoint, tc.id)}
                  disabled={runningSingle === tc.id}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50"
                >
                  <Play className="w-3 h-3" />
                  {runningSingle === tc.id ? 'Running...' : 'Run Scenario'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Execution Reports & Deep Assertions */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <h2 className="text-base font-bold text-slate-900">Live Test Run Reports & Assertion Logs</h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Run History List */}
          <div className="lg:col-span-1 border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100 max-h-96 overflow-y-auto">
            {reports.map((r) => (
              <div 
                key={r.id}
                onClick={() => setSelectedReport(r)}
                className={`p-3 text-xs cursor-pointer transition ${
                  selectedReport?.id === r.id ? 'bg-sky-50/80 border-l-4 border-sky-600' : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{r.test_case_id}</span>
                  <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                    r.status === 'PASS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                  }`}>
                    {r.status}
                  </span>
                </div>
                <div className="text-slate-600 truncate mt-0.5">{r.test_case_name}</div>
                <div className="text-[10px] text-slate-400 mt-1">{new Date(r.executed_at).toLocaleTimeString()}</div>
              </div>
            ))}
          </div>

          {/* Selected Run Details */}
          <div className="lg:col-span-2 p-5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-4">
            {selectedReport ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div>
                    <span className="font-mono text-slate-400">{selectedReport.id}</span>
                    <h3 className="font-bold text-slate-900 text-sm">{selectedReport.test_case_name}</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    selectedReport.status === 'PASS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                  }`}>
                    {selectedReport.status}
                  </span>
                </div>

                <div className="space-y-2">
                  <div><b>Inputs:</b> {selectedReport.inputs_summary}</div>
                  <div><b>Expected:</b> {selectedReport.expected_result}</div>
                  <div><b>Actual:</b> {selectedReport.actual_result}</div>
                  <div><b>Agent Reasoning:</b> {selectedReport.explanation}</div>
                </div>

                {/* Assertions Table */}
                <div>
                  <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[10px] mb-2">Automated Assertions</h4>
                  <div className="space-y-1.5">
                    {selectedReport.assertions.map((a, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded bg-white border border-slate-200">
                        {a.pass ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        )}
                        <span className={a.pass ? 'text-slate-800' : 'text-rose-700 font-semibold'}>{a.check}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">Select a test run to inspect assertions.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
