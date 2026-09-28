import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useEventRealtime } from '../hooks/useEventRealtime';
import LiveCounterCard from '../components/LiveCounterCard';
import EventCreateModal from '../components/EventCreateModal';
import InviteManagerModal from '../components/InviteManagerModal';
import { Users, CheckCircle, HelpCircle, XCircle, Clock, Plus, Wifi, WifiOff, Link, Megaphone, BrainCircuit } from 'lucide-react';

export default function OrganizerDashboard() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [announcementText, setAnnouncementText] = useState('');
  const [aiPrediction, setAiPrediction] = useState(null);
  const { counts, isConnected } = useEventRealtime(selectedEventId);

  const fetchEvents = async () => {
    try {
      const res = await api.get('/api/events');
      setEvents(res.data);
      if (res.data.length > 0 && !selectedEventId) {
        setSelectedEventId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const selectedEvent = events.find((e) => e.id === selectedEventId);

  const handlePostAnnouncement = async (e) => {
    e.preventDefault();
    if (!announcementText || !selectedEventId) return;
    try {
      await api.post(`/api/events/${selectedEventId}/announcements`, {
        title: 'Event Update',
        message: announcementText
      });
      setAnnouncementText('');
      alert('Announcement dispatched to all attendees!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to post announcement');
    }
  };

  const handleRunAiPrediction = async () => {
    if (!selectedEventId) return;
    try {
      const res = await api.post(`/api/events/${selectedEventId}/analytics/predict-attendance`, {
        invited_before: 2,
        rsvp_yes_rate: 0.8,
        day_of_week: 'Friday',
        days_before: 2,
        role: 'student'
      });
      setAiPrediction(res.data);
    } catch (err) {
      console.error('Failed AI prediction:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Organizer Live Operations Hub</h1>
          <p className="text-sm text-slate-500">Real-time attendance telemetry and event operations</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-white border shadow-sm">
            {isConnected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
                <span className="text-emerald-700">Live Sync Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-amber-700">Connecting...</span>
              </>
            )}
          </div>
          <button
            onClick={() => setIsInviteModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-sm"
          >
            <Link className="w-3.5 h-3.5" />
            Invite Links
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow"
          >
            <Plus className="w-4 h-4" />
            Create Event
          </button>
        </div>
      </div>

      {/* Event Selector */}
      <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
        {events.map((evt) => (
          <button
            key={evt.id}
            onClick={() => setSelectedEventId(evt.id)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border ${
              selectedEventId === evt.id
                ? 'bg-slate-900 text-white border-slate-900 shadow'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {evt.title} ({evt.status})
          </button>
        ))}
      </div>

      {/* Live Telemetry Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <LiveCounterCard label="Going (Confirmed)" count={counts.going} colorClass="text-emerald-600" icon={CheckCircle} subtext="Real-time count" />
        <LiveCounterCard label="Maybe" count={counts.maybe} colorClass="text-amber-600" icon={HelpCircle} subtext="Follow-up needed" />
        <LiveCounterCard label="Not Going" count={counts.not_going} colorClass="text-rose-600" icon={XCircle} subtext="Declined" />
        <LiveCounterCard label="Available Seats" count={counts.available_seats} colorClass="text-sky-600" icon={Users} subtext={`Capacity: ${counts.maximum_capacity}`} />
        <LiveCounterCard label="Waitlist (FIFO)" count={counts.waitlist_count} colorClass="text-purple-600" icon={Clock} subtext="Auto-promoting" />
      </div>

      {/* Selected Event Details & Operations */}
      {selectedEvent && (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900">{selectedEvent.title}</h2>
                <p className="text-xs text-slate-500 mt-1">{selectedEvent.venue} • {selectedEvent.event_date} ({selectedEvent.start_time} - {selectedEvent.end_time})</p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase bg-slate-100 text-slate-800">
                {counts.status || selectedEvent.status}
              </span>
            </div>

            {/* Progress bar for capacity */}
            <div className="mb-6">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Capacity Utilization</span>
                <span>{Math.round((counts.going / (counts.maximum_capacity || 1)) * 100)}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-sky-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (counts.going / (counts.maximum_capacity || 1)) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Announcement dispatch */}
            <form onSubmit={handlePostAnnouncement} className="mt-6 border-t pt-4">
              <label className="block text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                <Megaphone className="w-4 h-4 text-sky-600" />
                Dispatch Live Announcement
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Venue moved to Auditorium Room B..."
                  value={announcementText}
                  onChange={(e) => setAnnouncementText(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-xl text-xs"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold"
                >
                  Send
                </button>
              </div>
            </form>
          </div>

          {/* AI Attendance Prediction Widget */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <BrainCircuit className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">AI Attendance Predictor</h3>
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Trained on historical attendee behavior using scikit-learn Logistic Regression pipeline.
              </p>

              {aiPrediction ? (
                <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl mb-4">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-semibold text-indigo-900">Predicted Turnout:</span>
                    <span className="text-sm font-extrabold text-indigo-700">{aiPrediction.attendance_likelihood_pct}%</span>
                  </div>
                  <p className="text-[11px] text-indigo-600">{aiPrediction.recommendation}</p>
                </div>
              ) : (
                <div className="p-4 bg-slate-50 border rounded-xl text-center text-xs text-slate-400 mb-4">
                  Run predictive inference on registered cohort
                </div>
              )}
            </div>

            <button
              onClick={handleRunAiPrediction}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition"
            >
              Run Attendance Scoring
            </button>
          </div>
        </div>
      )}

      <EventCreateModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={fetchEvents}
      />

      <InviteManagerModal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        eventId={selectedEventId}
      />
    </div>
  );
}
