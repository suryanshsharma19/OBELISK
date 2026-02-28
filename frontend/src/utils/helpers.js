/**
 * General-purpose helper functions.
 */

/**
 * Clamp a number between min and max.
 */
export function clamp(value, min = 0, max = 100) {
  return Math.min(Math.max(value, min), max);
}

/**
 * Shallow-merge query parameters into a URL string.
 */
export function buildQueryString(params = {}) {
  const cleaned = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  return cleaned.length ? `?${cleaned.join('&')}` : '';
}

/**
 * Sleep for `ms` milliseconds (useful for debounced retries).
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Truncate a string to `len` characters, appending '…' if cut.
 */
export function truncate(str = '', len = 80) {
  if (str.length <= len) return str;
  return str.slice(0, len) + '…';
}

/**
 * Generate a deterministic-ish colour from a string (for avatars etc.).
 */
export function stringToColor(str = '') {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 60%, 50%)`;
}

/**
 * Deep-clone a plain object (JSON-safe only).
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}
