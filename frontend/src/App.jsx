import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import OrganizerDashboard from './pages/OrganizerDashboard';
import AttendeeEvents from './pages/AttendeeEvents';
import PublicTokenRSVP from './pages/PublicTokenRSVP';
import CheckinKiosk from './pages/CheckinKiosk';

function HomeRedirect() {
  const token = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');

  if (!token || !storedUser) {
    return <Navigate to="/login" replace />;
  }

  try {
    const user = JSON.parse(storedUser);
    if (user.role === 'organizer' || user.role === 'admin') {
      return <Navigate to="/organizer" replace />;
    }
    return <Navigate to="/attendee" replace />;
  } catch (e) {
    return <Navigate to="/login" replace />;
  }
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        {/* Navigation Bar */}
        <Navbar />

        {/* Routes */}
        <main className="flex-1">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/rsvp" element={<PublicTokenRSVP />} />

            {/* Root Redirect */}
            <Route path="/" element={<HomeRedirect />} />

            {/* Protected Routes */}
            <Route
              path="/organizer"
              element={
                <ProtectedRoute allowedRoles={['organizer', 'admin']}>
                  <OrganizerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/attendee"
              element={
                <ProtectedRoute allowedRoles={['attendee', 'organizer', 'admin']}>
                  <AttendeeEvents />
                </ProtectedRoute>
              }
            />
            <Route
              path="/checkin"
              element={
                <ProtectedRoute allowedRoles={['organizer', 'admin']}>
                  <CheckinKiosk />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
