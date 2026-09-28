import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

export default function ProtectedRoute({ children, allowedRoles }) {
  const location = useLocation();
  const token = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');

  if (!token || !storedUser) {
    // Redirect to login, preserving destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  try {
    const user = JSON.parse(storedUser);
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      // Role not authorized for this specific route
      return (
        <div className="max-w-md mx-auto mt-16 p-6 bg-white rounded-2xl border text-center">
          <h2 className="text-lg font-bold text-rose-600">Access Restricted</h2>
          <p className="text-xs text-slate-500 mt-2">
            This portal is restricted to {allowedRoles.join(' or ')} roles. Your account role is <strong>{user.role}</strong>.
          </p>
          <button
            onClick={() => window.location.href = user.role === 'organizer' ? '/organizer' : '/attendee'}
            className="mt-4 px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold"
          >
            Go to Your Dashboard
          </button>
        </div>
      );
    }
  } catch (e) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return <Navigate to="/login" replace />;
  }

  return children;
}
