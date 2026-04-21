/**
 * Filter controls for alerts — threat level and resolved status.
 */

import React from 'react';
import { THREAT_LEVELS } from '../../utils/constants';
import { capitalise } from '../../utils/formatters';

export default function AlertFilter({ filters, onChange }) {
  const handleChange = (key) => (e) => {
    onChange({ ...filters, [key]: e.target.value });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={filters.threat_level || ''}
        onChange={handleChange('threat_level')}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-neon-500 focus:outline-none"
      >
        <option value="">All Levels</option>
        {THREAT_LEVELS.map((l) => (
          <option key={l} value={l}>{capitalise(l)}</option>
        ))}
      </select>

      <select
        value={filters.is_resolved ?? ''}
        onChange={handleChange('is_resolved')}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-neon-500 focus:outline-none"
      >
        <option value="">All Status</option>
        <option value="false">Active</option>
        <option value="true">Resolved</option>
      </select>
    </div>
  );
}
