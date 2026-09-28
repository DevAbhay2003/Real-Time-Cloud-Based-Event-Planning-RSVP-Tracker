import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Cloud, Calendar, LayoutDashboard, QrCode, LogOut, LogIn, UserPlus, User } from 'lucide-react';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');
  let user = null;

  if (token && storedUser) {
    try {
      user = JSON.parse(storedUser);
    } catch (e) {
      user = null;
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-sky-600 font-extrabold text-lg">
          <Cloud className="w-6 h-6" />
          <span className="text-slate-900 tracking-tight">CloudRSVP</span>
        </Link>

        {/* Dynamic Nav Links */}
        <nav className="flex items-center gap-6 text-xs font-bold uppercase tracking-wider">
          {user ? (
            <>
              {(user.role === 'organizer' || user.role === 'admin') && (
                <Link
                  to="/organizer"
                  className={`flex items-center gap-1.5 transition ${
                    isActive('/organizer') ? 'text-sky-600 font-extrabold' : 'text-slate-600 hover:text-sky-600'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" /> Organizer Hub
                </Link>
              )}

              <Link
                to="/attendee"
                className={`flex items-center gap-1.5 transition ${
                  isActive('/attendee') ? 'text-sky-600 font-extrabold' : 'text-slate-600 hover:text-sky-600'
                }`}
              >
                <Calendar className="w-4 h-4" /> Attendee Portal
              </Link>

              {(user.role === 'organizer' || user.role === 'admin') && (
                <Link
                  to="/checkin"
                  className={`flex items-center gap-1.5 transition ${
                    isActive('/checkin') ? 'text-sky-600 font-extrabold' : 'text-slate-600 hover:text-sky-600'
                  }`}
                >
                  <QrCode className="w-4 h-4" /> Check-in Kiosk
                </Link>
              )}

              {/* User badge and logout */}
              <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
                <div className="flex items-center gap-1.5 text-slate-700 normal-case font-medium">
                  <div className="w-7 h-7 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs">
                    {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
                  </div>
                  <div className="hidden sm:block text-left">
                    <p className="text-xs font-bold leading-tight">{user.full_name}</p>
                    <p className="text-[10px] text-slate-400 capitalize">{user.role}</p>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="px-2.5 py-1.5 bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-600 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="flex items-center gap-1 px-3.5 py-1.5 text-slate-700 hover:text-sky-600 font-semibold text-xs"
              >
                <LogIn className="w-3.5 h-3.5" /> Sign In
              </Link>
              <Link
                to="/register"
                className="flex items-center gap-1 px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold text-xs transition shadow-sm"
              >
                <UserPlus className="w-3.5 h-3.5" /> Register
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
