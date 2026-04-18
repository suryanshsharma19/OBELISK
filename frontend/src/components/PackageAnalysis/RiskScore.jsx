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

const SIZE_PRESETS = {
  small: {
    diameter: 96,
    radius: 36,
    center: 48,
    valueFontSize: 18,
    denomFontSize: 10,
    badgeClass: 'text-[10px] px-2 py-0.5',
  },
  medium: {
    diameter: 120,
    radius: 46,
    center: 60,
    valueFontSize: 22,
    denomFontSize: 11,
    badgeClass: 'text-[11px] px-2.5 py-0.5',
  },
  large: {
    diameter: 140,
    radius: 54,
    center: 70,
    valueFontSize: 24,
    denomFontSize: 12,
    badgeClass: 'text-xs px-3 py-1',
  },
};

export default function RiskScore({ score = 0, threatLevel = 'safe', size = 'medium' }) {
  const colour = getColor(score);
  const preset = SIZE_PRESETS[size] || SIZE_PRESETS.medium;

  // SVG circle constants
  const radius = preset.radius;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(score, 100));
  const offset = circumference - (clampedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={preset.diameter} height={preset.diameter} viewBox={`0 0 ${preset.diameter} ${preset.diameter}`}>
        <circle
          cx={preset.center} cy={preset.center} r={radius}
          fill="none" stroke="#374151" strokeWidth="10"
        />
        <circle
          cx={preset.center} cy={preset.center} r={radius}
          fill="none" stroke={colour} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${preset.center} ${preset.center})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text
          x={preset.center} y={preset.center - 4} textAnchor="middle"
          className="fill-white font-bold"
          style={{ fontSize: preset.valueFontSize }}
        >
          {formatRiskScore(clampedScore)}
        </text>
        <text
          x={preset.center} y={preset.center + 16} textAnchor="middle"
          className="fill-gray-400"
          style={{ fontSize: preset.denomFontSize }}
        >
          /100
        </text>
      </svg>

      <span
        className={`rounded font-bold uppercase ${preset.badgeClass}`}
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
