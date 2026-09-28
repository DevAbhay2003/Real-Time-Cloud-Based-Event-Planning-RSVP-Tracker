import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import OrganizerDashboard from './pages/OrganizerDashboard';
import AttendeeEvents from './pages/AttendeeEvents';
import PublicTokenRSVP from './pages/PublicTokenRSVP';
import CheckinKiosk from './pages/CheckinKiosk';
import AuthBar from './components/AuthBar';
import { Cloud, Calendar, LayoutDashboard, QrCode } from 'lucide-react';

export default function App() {
  const [authKey, setAuthKey] = useState(0);

  const handleAuthChange = () => {
    // Force re-render of active components when user switches role
    setAuthKey((prev) => prev + 1);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        {/* Top 1-Click Role Switcher & Auth Bar */}
        <AuthBar onAuthChange={handleAuthChange} />

        {/* Navigation Bar */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-sky-600 font-extrabold text-lg">
              <Cloud className="w-6 h-6" />
              <span className="text-slate-900 tracking-tight">CloudRSVP</span>
            </Link>
            <nav className="flex items-center gap-5 text-xs font-bold uppercase tracking-wider">
              <Link to="/organizer" className="flex items-center gap-1.5 text-slate-600 hover:text-sky-600 transition">
                <LayoutDashboard className="w-4 h-4" /> Organizer Hub
              </Link>
              <Link to="/attendee" className="flex items-center gap-1.5 text-slate-600 hover:text-sky-600 transition">
                <Calendar className="w-4 h-4" /> Attendee Portal
              </Link>
              <Link to="/checkin" className="flex items-center gap-1.5 text-slate-600 hover:text-sky-600 transition">
                <QrCode className="w-4 h-4" /> Check-in Kiosk
              </Link>
            </nav>
          </div>
        </header>

        {/* Content View */}
        <main className="flex-1" key={authKey}>
          <Routes>
            <Route path="/" element={<OrganizerDashboard />} />
            <Route path="/organizer" element={<OrganizerDashboard />} />
            <Route path="/attendee" element={<AttendeeEvents />} />
            <Route path="/rsvp" element={<PublicTokenRSVP />} />
            <Route path="/checkin" element={<CheckinKiosk />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
