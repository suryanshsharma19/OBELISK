// Auth helpers for token lifecycle and credential-based login.

import api from './api';
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from './session';

const DEFAULT_AUTH_ENDPOINT = '/api/auth/login';

export function setToken(token) {
  setAccessToken(token);
}

export function getToken() {
  return getAccessToken();
}

export function clearToken() {
  clearAccessToken();
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export async function login(username, password) {
  if (!username || !password) {
    throw new Error('Username and password are required');
  }

  const endpoint = process.env.REACT_APP_AUTH_ENDPOINT || DEFAULT_AUTH_ENDPOINT;
  const payload = { username, password };

  const response = await api.post(endpoint, payload);
  const responseData = response?.data || {};
  const token = responseData.access_token || responseData.token || responseData?.data?.token;

  if (!token) {
    throw new Error('Authentication succeeded but no token was returned');
  }

  setToken(token);

  return {
    token,
    user: responseData.user || responseData?.data?.user || null,
    expiresIn: responseData.expires_in || responseData?.data?.expires_in || null,
  };
}

export async function logout() {
  try {
    await api.post('/api/auth/logout');
  } catch {
    // no-op on logout failure; local state should still be cleared
  }
  clearToken();
}

export async function getCurrentUser() {
  const response = await api.get('/api/auth/me');
  return response.data;
}
