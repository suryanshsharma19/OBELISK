/**
 * Authentication helpers.
 *
 * OBELISK v1 uses simple token-based auth.  This module wraps
 * localStorage for token management and provides login/logout stubs
 * for when a full auth backend is wired up.
 */

import { STORAGE_KEYS } from '../utils/constants';

/**
 * Persist a JWT token.
 */
export function setToken(token) {
  localStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

/**
 * Retrieve the stored token (or null).
 */
export function getToken() {
  return localStorage.getItem(STORAGE_KEYS.TOKEN);
}

/**
 * Remove the token — effectively logging the user out.
 */
export function clearToken() {
  localStorage.removeItem(STORAGE_KEYS.TOKEN);
}

/**
 * Quick check: is a token present?
 */
export function isAuthenticated() {
  return !!getToken();
}

/**
 * Placeholder login function.
 * Replace with a real POST /auth/login when the auth service is ready.
 */
export async function login(/* username, password */) {
  // TODO: wire up to backend auth endpoint
  return { token: 'dev-token' };
}

/**
 * Clear session data.
 */
export function logout() {
  clearToken();
}
