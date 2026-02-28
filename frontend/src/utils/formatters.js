/**
 * Formatting utilities for dates, numbers, and display strings.
 */

/**
 * Format an ISO timestamp to a human-friendly relative string.
 * e.g. "2 hours ago", "just now"
 */
export function timeAgo(isoString) {
  if (!isoString) return '—';
  const date = new Date(isoString);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

/**
 * Format an ISO timestamp to a local date-time string.
 */
export function formatDateTime(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleString();
}

/**
 * Format a risk score (0-100) to a fixed string like "42.5".
 */
export function formatRiskScore(score) {
  if (score == null) return '—';
  return Number(score).toFixed(1);
}

/**
 * Format a large number with K/M suffixes.
 */
export function formatCount(n) {
  if (n == null) return '0';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

/**
 * Capitalise the first letter of a string.
 */
export function capitalise(str = '') {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Map a threat level to a human-readable label.
 */
export function threatLabel(level) {
  const labels = {
    safe: 'Safe',
    low: 'Low Risk',
    medium: 'Medium Risk',
    high: 'High Risk',
    critical: 'Critical',
  };
  return labels[level] || capitalise(level);
}
