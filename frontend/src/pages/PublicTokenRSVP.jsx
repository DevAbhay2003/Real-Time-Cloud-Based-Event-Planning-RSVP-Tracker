import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { Check, HelpCircle, X, QrCode } from 'lucide-react';

export default function PublicTokenRSVP() {
  const [searchParams] = useSearchParams();
  const eventId = searchParams.get('e');
  const token = searchParams.get('t');

  const [event, setEvent] = useState(null);
  const [qrUrl, setQrUrl] = useState('');
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (eventId) {
      api.get(`/api/events/${eventId}`).then((res) => setEvent(res.data)).catch(console.error);
    }
    if (eventId && token) {
      api.get(`/api/events/${eventId}/checkin/qr/${token}`)
        .then((res) => setQrUrl(res.data.qr_data_url))
        .catch(console.error);
    }
  }, [eventId, token]);

  const respond = async (answer) => {
    setLoading(true);
    setMessage('');
    try {
      await api.post('/api/rsvp/public', {
        token,
        status: answer,
        plus_ones: 0
      });
      setStatus(answer);
      setMessage(`Thank you! Your RSVP has been confirmed as ${answer}.`);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Error recording RSVP');
    } finally {
      setLoading(false);
    }
  };

  if (!token || !eventId) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-white rounded-2xl border text-center">
        <h2 className="text-xl font-bold text-slate-800">Invalid Invite Link</h2>
        <p className="text-sm text-slate-500 mt-2">Missing event ID or token parameter.</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-white rounded-3xl border border-slate-200 shadow-xl text-center">
      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700">VIP Digital Invitation</span>
      <h2 className="text-2xl font-black text-slate-900 mt-3">{event?.title || 'Loading Event...'}</h2>
      <p className="text-xs text-slate-500 mt-1">{event?.venue} • {event?.event_date}</p>

      {/* QR Code Attendee Pass */}
      {qrUrl && (
        <div className="my-6 flex flex-col items-center">
          <div className="p-3 bg-white border rounded-2xl shadow-sm">
            <img src={qrUrl} alt="Invite QR Pass" className="w-48 h-48" />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">Present this QR code for instant venue check-in</p>
        </div>
      )}

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <button
          onClick={() => respond('GOING')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'GOING' ? 'bg-emerald-600 text-white' : 'bg-slate-100 hover:bg-emerald-100 text-slate-700'
          }`}
        >
          <Check className="w-4 h-4" /> Going
        </button>
        <button
          onClick={() => respond('MAYBE')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'MAYBE' ? 'bg-amber-500 text-white' : 'bg-slate-100 hover:bg-amber-100 text-slate-700'
          }`}
        >
          <HelpCircle className="w-4 h-4" /> Maybe
        </button>
        <button
          onClick={() => respond('NOT_GOING')}
          disabled={loading}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
            status === 'NOT_GOING' ? 'bg-rose-600 text-white' : 'bg-slate-100 hover:bg-rose-100 text-slate-700'
          }`}
        >
          <X className="w-4 h-4" /> Decline
        </button>
      </div>

      {message && <p className="text-xs font-semibold text-sky-700 mt-4 bg-sky-50 py-2 rounded-lg">{message}</p>}
    </div>
  );
}
