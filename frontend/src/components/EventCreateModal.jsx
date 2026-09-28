import React, { useState } from 'react';
import api from '../services/api';
import { X } from 'lucide-react';

export default function EventCreateModal({ isOpen, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'hybrid',
    event_date: '',
    start_time: '10:00',
    end_time: '16:00',
    venue: '',
    online_link: '',
    maximum_capacity: 100,
    registration_deadline: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...formData,
        maximum_capacity: parseInt(formData.maximum_capacity, 10),
        registration_deadline: formData.registration_deadline.replace('T', ' ') + ':00'
      };
      await api.post('/api/events', payload);
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-slate-900">Create New Cloud Event</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        {error && <div className="p-3 mb-4 rounded bg-red-50 text-red-700 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Event Title</label>
            <input
              type="text" required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-sky-500"
              placeholder="Cloud Native DevOps Summit"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
              placeholder="Workshop description..."
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Event Date</label>
              <input
                type="date" required
                value={formData.event_date}
                onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Capacity</label>
              <input
                type="number" min="1" required
                value={formData.maximum_capacity}
                onChange={(e) => setFormData({ ...formData, maximum_capacity: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Start Time</label>
              <input
                type="time" required
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">End Time</label>
              <input
                type="time" required
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Venue</label>
            <input
              type="text" required
              value={formData.venue}
              onChange={(e) => setFormData({ ...formData, venue: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
              placeholder="Engineering Hall Room 301"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Registration Deadline</label>
            <input
              type="datetime-local" required
              value={formData.registration_deadline}
              onChange={(e) => setFormData({ ...formData, registration_deadline: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">Cancel</button>
            <button type="submit" disabled={loading} className="px-5 py-2 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50">
              {loading ? 'Creating...' : 'Publish Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
