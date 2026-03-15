/**
 * Four summary stat cards displayed at the top of the dashboard.
 * Total Packages · Malicious Detected · Active Alerts · 24h Scans
 */

import React from 'react';
import { Package, ShieldAlert, Bell, Activity } from 'lucide-react';
import { formatCount } from '../../utils/formatters';

const CARDS = [
  { key: 'total_packages', label: 'Total Packages', icon: Package, color: 'text-blue-400' },
  { key: 'malicious_packages', label: 'Malicious Detected', icon: ShieldAlert, color: 'text-red-400' },
  { key: 'active_alerts', label: 'Active Alerts', icon: Bell, color: 'text-amber-400' },
  { key: 'scans_24h', label: '24h Scans', icon: Activity, color: 'text-emerald-400' },
];

export default function StatsCards({ stats = {} }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {CARDS.map(({ key, label, icon: Icon, color }) => (
        <div
          key={key}
          className="flex items-center gap-4 rounded-xl border border-gray-700 bg-gray-800 p-5"
        >
          <div className={`rounded-lg bg-gray-900 p-3 ${color}`}>
            <Icon size={24} />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">
              {formatCount(stats[key])}
            </p>
            <p className="text-xs text-gray-400">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
