import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { UserCheck, LogIn, LogOut, Shield, User, X } from 'lucide-react';

export default function AuthBar({ onAuthChange }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('attendee');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setCurrentUser(JSON.parse(storedUser));
      } catch (e) {}
    } else {
      // Auto-login as Organizer by default for frictionless out-of-the-box demo experience
      quickLogin('organizer@cloud.edu', 'Password123!');
    }
  }, []);

  const quickLogin = async (username, pwd) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/auth/login', new URLSearchParams({
        username,
        password: pwd
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      setCurrentUser(res.data.user);
      if (onAuthChange) onAuthChange(res.data.user);
    } catch (err) {
      console.warn('Quick login notice:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (isRegister) {
        await api.post('/api/auth/register', {
          email,
          password,
          full_name: fullName,
          role
        });
      }
      // Log in after register or login
      const res = await api.post('/api/auth/login', new URLSearchParams({
        username: email,
        password
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      setCurrentUser(res.data.user);
      setShowModal(false);
      if (onAuthChange) onAuthChange(res.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentUser(null);
    if (onAuthChange) onAuthChange(null);
  };

  return (
    <>
      <div className="bg-slate-900 text-white text-xs px-4 py-2 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {currentUser ? (
            <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
              <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Logged in: <strong className="text-white">{currentUser.full_name}</strong> ({currentUser.role})</span>
            </div>
          ) : (
            <span className="text-slate-400">Not authenticated (Select a role or sign in)</span>
          )}
        </div>

        {/* 1-Click Role Switchers */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 hidden sm:inline">Demo Switcher:</span>
          <button
            onClick={() => quickLogin('organizer@cloud.edu', 'Password123!')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border ${
              currentUser?.role === 'organizer'
                ? 'bg-sky-600 text-white border-sky-500 shadow-sm'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
          >
            ⚡ Organizer (Prof. Cloud)
          </button>
          <button
            onClick={() => quickLogin('attendee@cloud.edu', 'Password123!')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border ${
              currentUser?.role === 'attendee'
                ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
          >
            ⚡ Attendee (Alex Student)
          </button>

          {currentUser ? (
            <button
              onClick={handleLogout}
              className="px-2 py-1 bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800 rounded-md text-[11px] font-medium flex items-center gap-1"
            >
              <LogOut className="w-3 h-3" /> Logout
            </button>
          ) : (
            <button
              onClick={() => { setShowModal(true); setIsRegister(false); }}
              className="px-2.5 py-1 bg-white text-slate-900 rounded-md text-[11px] font-bold hover:bg-slate-100 flex items-center gap-1"
            >
              <LogIn className="w-3 h-3" /> Sign In / Register
            </button>
          )}
        </div>
      </div>

      {/* Modal for Custom Register / Login */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-slate-900">
                {isRegister ? 'Create Cloud Account' : 'Sign in to Cloud Platform'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {error && <div className="p-2.5 mb-3 bg-red-50 text-red-700 rounded-lg text-xs">{error}</div>}

            <form onSubmit={handleCustomAuth} className="space-y-3">
              {isRegister && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                    <input
                      type="text" required
                      value={fullName} onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-3 py-1.5 border rounded-lg text-xs"
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Role</label>
                    <select
                      value={role} onChange={(e) => setRole(e.target.value)}
                      className="w-full px-3 py-1.5 border rounded-lg text-xs"
                    >
                      <option value="attendee">Attendee</option>
                      <option value="organizer">Organizer</option>
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                <input
                  type="email" required
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  placeholder="name@cloud.edu"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                <input
                  type="password" required minLength={6}
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  placeholder="Min 6 characters"
                />
              </div>

              <button
                type="submit" disabled={loading}
                className="w-full py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg text-xs transition"
              >
                {loading ? 'Processing...' : (isRegister ? 'Register & Sign In' : 'Sign In')}
              </button>
            </form>

            <div className="mt-4 pt-3 border-t text-center text-xs text-slate-500">
              {isRegister ? (
                <span>Already have an account? <button onClick={() => setIsRegister(false)} className="text-sky-600 font-semibold underline">Sign in</button></span>
              ) : (
                <span>New here? <button onClick={() => setIsRegister(true)} className="text-sky-600 font-semibold underline">Create account</button></span>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
