/**
 * Line chart showing scans and threats over the last N days.
 * Powered by Recharts.
 */

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export default function ThreatChart({ trend = [] }) {
  if (!trend.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-500">
        No trend data available
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-5">
      <h3 className="mb-4 text-sm font-semibold text-gray-300">Detection Trend</h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={trend}>
          <defs>
            <linearGradient id="gradScanned" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradThreats" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: 8,
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="scanned"
            stroke="#3b82f6"
            fill="url(#gradScanned)"
            name="Scanned"
          />
          <Area
            type="monotone"
            dataKey="threats"
            stroke="#ef4444"
            fill="url(#gradThreats)"
            name="Threats"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
