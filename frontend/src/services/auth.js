// Auth helpers - token management and login/logout stubs

import { STORAGE_KEYS } from '../utils/constants';

export function setToken(token) {
  localStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

export function getToken() {
  return localStorage.getItem(STORAGE_KEYS.TOKEN);
}

export function clearToken() {
  localStorage.removeItem(STORAGE_KEYS.TOKEN);
}

export function isAuthenticated() {
  return !!getToken();
}

export async function login(/* username, password */) {
  // TODO: wire up to backend auth endpoint
  return { token: 'dev-token' };
}

export function logout() {
  clearToken();
}
