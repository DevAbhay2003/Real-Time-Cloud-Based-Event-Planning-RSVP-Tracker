import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';
import { Cloud, Lock, Mail, ArrowRight, UserCheck } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/auth/login', new URLSearchParams({
        username: email,
        password: password
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));

      // Redirect to origin or appropriate portal based on role
      const from = location.state?.from?.pathname;
      if (from) {
        navigate(from, { replace: true });
      } else if (res.data.user.role === 'organizer' || res.data.user.role === 'admin') {
        navigate('/organizer', { replace: true });
      } else {
        navigate('/attendee', { replace: true });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  // Helper chips to fill credentials without auto-logging in
  const fillCredentials = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-3xl border border-slate-200 p-8 shadow-xl">
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-sky-50 text-sky-600 mb-3">
            <Cloud className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Sign in to CloudRSVP</h1>
          <p className="text-xs text-slate-500 mt-1">Real-time cloud event planning & RSVP tracking</p>
        </div>

        {error && (
          <div className="p-3 mb-4 rounded-xl bg-red-50 text-red-700 text-xs font-medium border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="name@cloud.edu"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password" required
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit" disabled={loading}
            className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Account Helpers */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 text-center">
            Demo Accounts (Click to Pre-fill)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillCredentials('organizer@cloud.edu', 'Password123!')}
              className="p-2.5 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded-xl text-left transition"
            >
              <p className="text-[11px] font-bold text-slate-800">👨‍💼 Organizer</p>
              <p className="text-[10px] text-slate-500 truncate">organizer@cloud.edu</p>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('attendee@cloud.edu', 'Password123!')}
              className="p-2.5 bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-200 rounded-xl text-left transition"
            >
              <p className="text-[11px] font-bold text-slate-800">👩‍🎓 Attendee</p>
              <p className="text-[10px] text-slate-500 truncate">attendee@cloud.edu</p>
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-sky-600 font-bold hover:underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}
