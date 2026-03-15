/**
 * Horizontal bar chart showing the breakdown by threat level.
 */

import React from 'react';
import { THREAT_COLORS, THREAT_LEVELS } from '../../utils/constants';
import { capitalise } from '../../utils/formatters';

export default function ThreatDistribution({ distribution = {} }) {
  const total = THREAT_LEVELS.reduce((sum, l) => sum + (distribution[l] || 0), 0);

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-5">
      <h3 className="mb-4 text-sm font-semibold text-gray-300">
        Threat Distribution
      </h3>

      {total === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          No packages analyzed yet
        </p>
      ) : (
        <div className="space-y-3">
          {THREAT_LEVELS.map((level) => {
            const count = distribution[level] || 0;
            const pct = total ? Math.round((count / total) * 100) : 0;
            return (
              <div key={level}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-gray-400">{capitalise(level)}</span>
                  <span className="font-medium text-gray-300">
                    {count} ({pct}%)
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-gray-700">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: THREAT_COLORS[level],
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
