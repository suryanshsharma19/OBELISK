/**
 * Shows the latest 5 alerts with threat badges.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { THREAT_COLORS } from '../../utils/constants';
import { timeAgo, threatLabel } from '../../utils/formatters';

export default function RecentAlerts({ alerts = [] }) {
  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Recent Alerts</h3>
        <Link
          to="/alerts"
          className="text-xs text-emerald-400 hover:underline"
        >
          View all
        </Link>
      </div>

      {alerts.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          No alerts yet
        </p>
      ) : (
        <ul className="space-y-3">
          {alerts.slice(0, 5).map((alert) => (
            <li
              key={alert.id}
              className="flex items-start justify-between gap-2 rounded-lg bg-gray-900 px-3 py-2.5"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">
                  {alert.title}
                </p>
                <p className="text-xs text-gray-500">
                  {timeAgo(alert.created_at)}
                </p>
              </div>
              <span
                className="shrink-0 rounded px-2 py-0.5 text-[10px] font-bold uppercase"
                style={{
                  backgroundColor: `${THREAT_COLORS[alert.threat_level] || '#6b7280'}20`,
                  color: THREAT_COLORS[alert.threat_level] || '#9ca3af',
                }}
              >
                {threatLabel(alert.threat_level)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
