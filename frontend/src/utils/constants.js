// App-wide constants

export const API_BASE_URL =
  process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const WS_BASE_URL =
  process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

// Threat-level colour palette (matches Tailwind classes)
export const THREAT_COLORS = {
  safe: '#10b981',     // neon-500
  low: '#3b82f6',      // blue-500
  medium: '#f59e0b',   // amber-500
  high: '#f97316',     // orange-500
  critical: '#ef4444', // red-500
};

export const THREAT_LEVELS = ['safe', 'low', 'medium', 'high', 'critical'];

export const REGISTRIES = ['npm', 'pypi'];

// Dashboard refresh interval (ms)
export const POLL_INTERVAL = 30_000;

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Local-storage keys
export const STORAGE_KEYS = {
  THEME: 'obelisk_theme',
  NOTIFICATIONS: 'obelisk_notifications',
};

// Sort options used in the package list
export const SORT_OPTIONS = [
  { value: 'risk_score_desc', label: 'Highest risk' },
  { value: 'risk_score_asc', label: 'Lowest risk' },
  { value: 'analyzed_at_desc', label: 'Newest first' },
  { value: 'analyzed_at_asc', label: 'Oldest first' },
];
