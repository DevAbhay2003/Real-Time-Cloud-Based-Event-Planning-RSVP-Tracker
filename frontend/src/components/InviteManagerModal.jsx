import React, { useState } from 'react';
import api from '../services/api';
import { X, UserPlus, Link, Copy, Check } from 'lucide-react';

export default function InviteManagerModal({ isOpen, onClose, eventId }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [generatedInvites, setGeneratedInvites] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!name || !email) return;
    setLoading(true);
    try {
      const res = await api.post(`/api/events/${eventId}/invites`, {
        invitees: [{ name, email, plus_ones_allowed: 0 }]
      });
      setGeneratedInvites([...res.data.invites, ...generatedInvites]);
      setName('');
      setEmail('');
    } catch (err) {
      console.error('Failed to generate invite:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (url, index) => {
    const fullUrl = `${window.location.origin}${url}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-slate-900">Manage VIP Invite Links & Tokens</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleGenerate} className="flex gap-2 mb-6">
          <input
            type="text" placeholder="Invitee Name" required
            value={name} onChange={(e) => setName(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-xl text-xs"
          />
          <input
            type="email" placeholder="Email Address" required
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-xl text-xs"
          />
          <button
            type="submit" disabled={loading}
            className="px-4 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold hover:bg-sky-700 flex items-center gap-1"
          >
            <UserPlus className="w-3.5 h-3.5" />
            Generate
          </button>
        </form>

        <div className="space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Generated Links ({generatedInvites.length})</p>
          {generatedInvites.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-4 text-center">No links generated in this session yet.</p>
          ) : (
            generatedInvites.map((inv, idx) => (
              <div key={idx} className="p-3 bg-slate-50 border rounded-xl flex items-center justify-between text-xs">
                <div>
                  <p className="font-bold text-slate-800">{inv.name}</p>
                  <p className="text-[11px] text-slate-500">{inv.email} • Token: <span className="font-mono text-sky-600">{inv.token.slice(0, 10)}...</span></p>
                </div>
                <button
                  onClick={() => copyToClipboard(inv.rsvp_url, idx)}
                  className="px-2.5 py-1.5 bg-white border rounded-lg text-slate-600 hover:bg-slate-100 flex items-center gap-1 font-medium shadow-sm"
                >
                  {copiedIndex === idx ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-600" />
                      <span className="text-emerald-700">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy RSVP URL</span>
                    </>
                  )}
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
