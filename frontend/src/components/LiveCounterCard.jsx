import React from 'react';

export default function LiveCounterCard({ label, count, colorClass, icon: Icon, subtext }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex items-center justify-between transition-all hover:shadow-md">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
        <h3 className={`text-3xl font-extrabold ${colorClass}`}>{count}</h3>
        {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
      </div>
      {Icon && (
        <div className={`p-3 rounded-lg bg-slate-50 text-slate-600`}>
          <Icon className="w-6 h-6" />
        </div>
      )}
    </div>
  );
}
