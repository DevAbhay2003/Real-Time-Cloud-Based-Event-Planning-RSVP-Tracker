import React, { useState, useEffect } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import api from '../services/api';
import { QrCode, CheckCircle, AlertTriangle } from 'lucide-react';

export default function CheckinKiosk() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [manualToken, setManualToken] = useState('');

  useEffect(() => {
    api.get('/api/events').then((res) => {
      setEvents(res.data);
      if (res.data.length > 0) setSelectedEventId(res.data[0].id);
    });
  }, []);

  const handleScanSuccess = async (decodedText) => {
    let token = decodedText;
    if (decodedText.includes('t=')) {
      const parts = decodedText.split('t=');
      token = parts[1].split('&')[0];
    }
    processCheckin(token);
  };

  const processCheckin = async (token) => {
    if (!selectedEventId || !token) return;
    try {
      const res = await api.post(`/api/events/${selectedEventId}/checkin`, { token });
      setScanResult(res.data);
    } catch (err) {
      setScanResult({
        status: 'ERROR',
        message: err.response?.data?.detail || 'Check-in failed'
      });
    }
  };

  useEffect(() => {
    // Only mount camera scanner if DOM element exists
    try {
      const scanner = new Html5QrcodeScanner(
        'reader',
        { fps: 10, qrbox: { width: 250, height: 250 } },
        false
      );
      scanner.render(handleScanSuccess, () => {});
      return () => {
        try {
          scanner.clear();
        } catch (e) {}
      };
    } catch (err) {
      console.warn('Scanner init notice:', err);
    }
  }, [selectedEventId]);

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xl text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <QrCode className="w-6 h-6 text-sky-600" />
          <h2 className="text-xl font-bold text-slate-900">On-Site QR Check-in Station</h2>
        </div>
        <p className="text-xs text-slate-500 mb-6">Scan attendee digital ticket or badge QR code</p>

        {/* Event selector */}
        <select
          value={selectedEventId}
          onChange={(e) => setSelectedEventId(e.target.value)}
          className="w-full px-3 py-2 border rounded-xl text-xs font-medium mb-6 bg-slate-50"
        >
          {events.map((e) => (
            <option key={e.id} value={e.id}>{e.title}</option>
          ))}
        </select>

        {/* Camera Scanner Viewport */}
        <div id="reader" className="overflow-hidden rounded-2xl border mb-6 bg-slate-50 min-h-[250px]"></div>

        {/* Manual Token Fallback */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Or enter ticket token manually..."
            value={manualToken}
            onChange={(e) => setManualToken(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-xl text-xs"
          />
          <button
            onClick={() => processCheckin(manualToken)}
            className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800"
          >
            Check In
          </button>
        </div>

        {/* Scan Result Feedback */}
        {scanResult && (
          <div className={`mt-6 p-4 rounded-xl flex items-center gap-3 text-left ${
            scanResult.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'
          }`}>
            {scanResult.status === 'SUCCESS' ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            )}
            <div>
              <p className="text-sm font-bold">{scanResult.message}</p>
              {scanResult.attendee_name && (
                <p className="text-xs font-medium mt-0.5">Attendee: {scanResult.attendee_name}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
