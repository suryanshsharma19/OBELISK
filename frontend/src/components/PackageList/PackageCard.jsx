/**
 * Single package summary card used in the package listing.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { THREAT_COLORS } from '../../utils/constants';
import { formatRiskScore, timeAgo, threatLabel } from '../../utils/formatters';
import { truncate } from '../../utils/helpers';

export default function PackageCard({ pkg }) {
  const colour = THREAT_COLORS[pkg.threat_level] || '#6b7280';

  return (
    <Link
      to={`/packages/${pkg.id}`}
      className="group block rounded-xl border border-gray-700 bg-gray-800 p-4 transition hover:border-gray-600"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white group-hover:text-emerald-400">
            {pkg.name}
          </p>
          <p className="text-xs text-gray-500">
            {pkg.version} · {pkg.registry}
          </p>
        </div>

        <span
          className="shrink-0 rounded px-2 py-0.5 text-[10px] font-bold uppercase"
          style={{ color: colour, backgroundColor: `${colour}20` }}
        >
          {threatLabel(pkg.threat_level)}
        </span>
      </div>

      {pkg.description && (
        <p className="mb-2 text-xs text-gray-400">
          {truncate(pkg.description, 100)}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Risk: {formatRiskScore(pkg.risk_score)}</span>
        <span>{timeAgo(pkg.analyzed_at)}</span>
      </div>
    </Link>
  );
}
