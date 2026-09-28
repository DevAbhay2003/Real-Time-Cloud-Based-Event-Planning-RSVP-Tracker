import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Calendar, MapPin, Users, Check, HelpCircle, X, Bell } from 'lucide-react';

export default function AttendeeEvents() {
  const [events, setEvents] = useState([]);
  const [myRsvps, setMyRsvps] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [eventsRes, rsvpsRes, notifsRes] = await Promise.all([
        api.get('/api/events'),
        api.get('/api/rsvps/me').catch(() => ({ data: [] })),
        api.get('/api/notifications').catch(() => ({ data: [] }))
      ]);
      setEvents(eventsRes.data);
      const rsvpMap = {};
      rsvpsRes.data.forEach((r) => {
        rsvpMap[r.event_id] = r.status;
      });
      setMyRsvps(rsvpMap);
      setNotifications(notifsRes.data);
    } catch (err) {
      console.error('Error fetching attendee data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRSVP = async (eventId, status) => {
    setLoading(true);
    try {
      await api.post(`/api/events/${eventId}/rsvp`, { status, plus_ones: 0 });
      setMyRsvps((prev) => ({ ...prev, [eventId]: status }));
      setFeedback((prev) => ({ ...prev, [eventId]: `RSVP recorded as ${status}!` }));
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit RSVP';
      setFeedback((prev) => ({ ...prev, [eventId]: msg }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Notifications bar */}
      {notifications.length > 0 && (
        <div className="mb-6 p-4 bg-sky-50 border border-sky-100 rounded-2xl flex items-start gap-3">
          <Bell className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-xs font-bold text-sky-900 uppercase tracking-wider mb-1">Recent Announcements & Alerts</h4>
            <div className="space-y-1">
              {notifications.slice(0, 3).map((n) => (
                <p key={n.id} className="text-xs text-sky-800">{n.message}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      <h1 className="text-2xl font-black text-slate-900 mb-2">Discover & RSVP Events</h1>
      <p className="text-sm text-slate-500 mb-6">Select your attendance response with real-time cloud sync</p>

      <div className="grid md:grid-cols-2 gap-6">
        {events.map((evt) => {
          const currentStatus = myRsvps[evt.id];
          return (
            <div key={evt.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-bold text-slate-900">{evt.title}</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    evt.status === 'FULL' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {evt.status}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mb-4">{evt.description || 'No description provided.'}</p>
                <div className="space-y-1.5 text-xs text-slate-500 mb-6">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>{evt.event_date} ({evt.start_time} - {evt.end_time})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    <span>{evt.venue}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-slate-400" />
                    <span>Capacity: {evt.current_going} / {evt.maximum_capacity}</span>
                  </div>
                </div>
              </div>

              {/* RSVP Action Bar */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2">Your Response:</p>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleRSVP(evt.id, 'GOING')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'GOING'
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-emerald-50'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" /> Going
                  </button>
                  <button
                    onClick={() => handleRSVP(evt.id, 'MAYBE')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'MAYBE'
                        ? 'bg-amber-500 text-white border-amber-500'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-amber-50'
                    }`}
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> Maybe
                  </button>
                  <button
                    onClick={() => handleRSVP(evt.id, 'NOT_GOING')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition border ${
                      currentStatus === 'NOT_GOING'
                        ? 'bg-rose-600 text-white border-rose-600'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-rose-50'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" /> Decline
                  </button>
                </div>
                {feedback[evt.id] && (
                  <p className="text-xs text-sky-600 font-medium mt-2">{feedback[evt.id]}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
