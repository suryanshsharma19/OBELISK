/**
 * Filter controls for the package & alert listings.
 * Provides threat-level dropdown, registry filter, and sort select.
 */

import React from 'react';
import { THREAT_LEVELS, REGISTRIES, SORT_OPTIONS } from '../../utils/constants';
import { capitalise } from '../../utils/formatters';

export default function FilterBar({ filters, onChange }) {
  const handleChange = (key) => (e) => {
    onChange({ ...filters, [key]: e.target.value });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Threat level */}
      <select
        value={filters.threat_level || ''}
        onChange={handleChange('threat_level')}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-emerald-500 focus:outline-none"
      >
        <option value="">All Levels</option>
        {THREAT_LEVELS.map((l) => (
          <option key={l} value={l}>{capitalise(l)}</option>
        ))}
      </select>

      {/* Registry */}
      <select
        value={filters.registry || ''}
        onChange={handleChange('registry')}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-emerald-500 focus:outline-none"
      >
        <option value="">All Registries</option>
        {REGISTRIES.map((r) => (
          <option key={r} value={r}>{r}</option>
        ))}
      </select>

      {/* Sort */}
      <select
        value={filters.sort || 'risk_score_desc'}
        onChange={handleChange('sort')}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-emerald-500 focus:outline-none"
      >
        {SORT_OPTIONS.map(({ value, label }) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>
    </div>
  );
}
