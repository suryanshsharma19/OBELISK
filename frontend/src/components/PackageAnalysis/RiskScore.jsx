/**
 * Circular risk-score gauge with animated fill and colour gradient.
 */

import React from 'react';
import { THREAT_COLORS } from '../../utils/constants';
import { formatRiskScore, threatLabel } from '../../utils/formatters';

function getColor(score) {
  if (score >= 80) return THREAT_COLORS.critical;
  if (score >= 60) return THREAT_COLORS.high;
  if (score >= 40) return THREAT_COLORS.medium;
  if (score >= 20) return THREAT_COLORS.low;
  return THREAT_COLORS.safe;
}

export default function RiskScore({ score = 0, threatLevel = 'safe' }) {
  const colour = getColor(score);
  // SVG circle constants
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle
          cx="70" cy="70" r={radius}
          fill="none" stroke="#374151" strokeWidth="10"
        />
        <circle
          cx="70" cy="70" r={radius}
          fill="none" stroke={colour} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text
          x="70" y="66" textAnchor="middle"
          className="fill-white text-2xl font-bold"
        >
          {formatRiskScore(score)}
        </text>
        <text
          x="70" y="86" textAnchor="middle"
          className="fill-gray-400 text-xs"
        >
          /100
        </text>
      </svg>

      <span
        className="rounded px-3 py-1 text-xs font-bold uppercase"
        style={{
          color: colour,
          backgroundColor: `${colour}20`,
        }}
      >
        {threatLabel(threatLevel)}
      </span>
    </div>
  );
}
