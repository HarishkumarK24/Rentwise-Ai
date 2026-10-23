import React, { useEffect, useState } from 'react';
import { History, ShieldCheck, Search, Filter } from 'lucide-react';
import { AuditEvent } from '../types';

export const AuditTrailView: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/audit-events');
      const data = await res.json();
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const filteredEvents = events.filter((e) => {
    const matchesFilter = filterType === 'ALL' || e.entity_type === filterType;
    const matchesSearch = 
      e.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.reason && e.reason.toLowerCase().includes(searchTerm.toLowerCase())) ||
      e.actor_identity.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-7 max-w-6xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <History className="w-6 h-6 text-sky-600" />
          <h1 className="text-2xl font-bold text-slate-900">Append-Only Application Audit Trail</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Cryptographically traceable event log recording all state transitions, matching decisions, tax evaluations, human approvals, and upload attempts.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select 
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white outline-none focus:border-sky-500"
          >
            <option value="ALL">All Event Entities</option>
            <option value="PROOF_PACK">Proof Pack</option>
            <option value="APPROVAL">Approval Gate</option>
            <option value="UPLOAD">Employer Upload</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search event ID, type, actor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 w-64 outline-none focus:border-sky-500"
          />
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold uppercase border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Entity Type</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Audit Reason & State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEvents.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{e.id}</td>
                  <td className="py-3 px-4 text-slate-500">{new Date(e.timestamp).toLocaleString()}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-100 font-medium text-slate-700">
                      {e.entity_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-800">{e.event_type}</td>
                  <td className="py-3 px-4 font-medium text-slate-600">{e.actor_identity}</td>
                  <td className="py-3 px-4 max-w-sm text-slate-600">
                    <div>{e.reason || 'N/A'}</div>
                    {e.after_state && (
                      <div className="font-mono text-[10px] text-slate-400 mt-0.5 truncate">
                        {JSON.stringify(e.after_state)}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
