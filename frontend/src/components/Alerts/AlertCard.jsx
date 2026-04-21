/**
 * Single alert card with threat badge, timestamp, and action buttons.
 */

import React from 'react';
import { useDispatch } from 'react-redux';
import { resolveAlert, markAlertRead } from '../../store/slices/alertsSlice';
import { THREAT_COLORS } from '../../utils/constants';
import { timeAgo, threatLabel } from '../../utils/formatters';
import { Check, Eye } from 'lucide-react';

export default function AlertCard({ alert }) {
  const dispatch = useDispatch();
  const colour = THREAT_COLORS[alert.threat_level] || '#6b7280';

  return (
    <div
      className={`rounded-xl border bg-gray-800 p-4 transition ${
        alert.is_read ? 'border-gray-700' : 'border-neon-700'
      }`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-white">
            {alert.title}
          </p>
          <p className="text-xs text-gray-500">{timeAgo(alert.created_at)}</p>
        </div>
        <span
          className="shrink-0 rounded px-2 py-0.5 text-[10px] font-bold uppercase"
          style={{ color: colour, backgroundColor: `${colour}20` }}
        >
          {threatLabel(alert.threat_level)}
        </span>
      </div>

      {alert.description && (
        <p className="mb-3 text-xs text-gray-400">{alert.description}</p>
      )}

      <div className="flex gap-2">
        {!alert.is_read && (
          <button
            onClick={() => dispatch(markAlertRead(alert.id))}
            className="flex items-center gap-1 rounded-lg bg-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-600"
          >
            <Eye size={14} /> Mark read
          </button>
        )}
        {!alert.is_resolved && (
          <button
            onClick={() => dispatch(resolveAlert(alert.id))}
            className="flex items-center gap-1 rounded-lg bg-neon-700 px-3 py-1.5 text-xs text-white hover:bg-neon-600"
          >
            <Check size={14} /> Resolve
          </button>
        )}
        {alert.is_resolved && (
          <span className="text-xs text-gray-500">Resolved</span>
        )}
      </div>
    </div>
  );
}
