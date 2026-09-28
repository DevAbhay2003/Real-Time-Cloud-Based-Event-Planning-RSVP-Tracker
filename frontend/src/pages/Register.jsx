import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Cloud, Lock, Mail, User, Shield, ArrowRight } from 'lucide-react';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('attendee');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // 1. Register user
      await api.post('/api/auth/register', {
        email,
        password,
        full_name: fullName,
        role
      });

      // 2. Automatically log in to retrieve JWT token
      const res = await api.post('/api/auth/login', new URLSearchParams({
        username: email,
        password: password
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));

      if (res.data.user.role === 'organizer' || res.data.user.role === 'admin') {
        navigate('/organizer', { replace: true });
      } else {
        navigate('/attendee', { replace: true });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-3xl border border-slate-200 p-8 shadow-xl">
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-sky-50 text-sky-600 mb-3">
            <Cloud className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Create Cloud Account</h1>
          <p className="text-xs text-slate-500 mt-1">Join as an Event Organizer or Attendee</p>
        </div>

        {error && (
          <div className="p-3 mb-4 rounded-xl bg-red-50 text-red-700 text-xs font-medium border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text" required
                value={fullName} onChange={(e) => setFullName(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="Jane Doe"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="name@university.edu"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password" required minLength={6}
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="Minimum 6 characters"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Account Role</label>
            <div className="relative">
              <Shield className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={role} onChange={(e) => setRole(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white"
              >
                <option value="attendee">Attendee (Discover & RSVP Events)</option>
                <option value="organizer">Organizer (Create & Manage Events)</option>
              </select>
            </div>
          </div>

          <button
            type="submit" disabled={loading}
            className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Register Account'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-sky-600 font-bold hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
