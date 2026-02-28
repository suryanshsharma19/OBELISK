/**
 * Card showing evidence from a single detector.
 * Displays detector name, score bar, confidence, and evidence list.
 */

import React from 'react';
import { THREAT_COLORS } from '../../utils/constants';

function scoreColor(score) {
  if (score >= 80) return THREAT_COLORS.critical;
  if (score >= 50) return THREAT_COLORS.high;
  if (score >= 25) return THREAT_COLORS.medium;
  return THREAT_COLORS.safe;
}

export default function EvidenceCard({ detector = '', result = {} }) {
  const { score = 0, confidence = 0, evidence = {} } = result;
  const colour = scoreColor(score);

  // Flatten evidence into displayable items
  const items = Object.entries(evidence).map(([key, val]) => {
    const display = Array.isArray(val) ? val.join(', ') : String(val);
    return { key, display };
  });

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-4">
      {/* Header row */}
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold capitalize text-white">
          {detector.replace(/_/g, ' ')}
        </h4>
        <span className="text-xs text-gray-400">
          Confidence: {Math.round(confidence * 100)}%
        </span>
      </div>

      {/* Score bar */}
      <div className="mb-3">
        <div className="mb-1 flex justify-between text-xs">
          <span className="text-gray-400">Score</span>
          <span style={{ color: colour }} className="font-medium">
            {score.toFixed(1)}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-gray-700">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${Math.min(score, 100)}%`, backgroundColor: colour }}
          />
        </div>
      </div>

      {/* Evidence items */}
      {items.length > 0 && (
        <ul className="space-y-1">
          {items.map(({ key, display }) => (
            <li key={key} className="flex text-xs">
              <span className="w-28 shrink-0 text-gray-500">{key}</span>
              <span className="text-gray-300">{display}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
