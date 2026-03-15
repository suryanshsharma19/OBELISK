// In-memory session state and bootstrap authentication helper.

import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

let accessToken = null;
let loginPromise = null;

function setAccessToken(token) {
  accessToken = token || null;
}

function getAccessToken() {
  return accessToken;
}

function clearAccessToken() {
  accessToken = null;
}

async function loginWithConfiguredCredentials() {
  const username = process.env.REACT_APP_AUTH_USERNAME;
  const password = process.env.REACT_APP_AUTH_PASSWORD;

  if (!username || !password) {
    throw new Error('Missing REACT_APP_AUTH_USERNAME/REACT_APP_AUTH_PASSWORD');
  }

  const response = await axios.post(
    `${API_BASE_URL}/api/auth/login`,
    { username, password },
    { withCredentials: true, timeout: 15_000 },
  );

  const token = response?.data?.access_token;
  if (!token) {
    throw new Error('Login succeeded but no access token was returned');
  }

  setAccessToken(token);
  return token;
}

async function ensureAuthenticated() {
  if (accessToken) return accessToken;

  if (!loginPromise) {
    loginPromise = loginWithConfiguredCredentials().finally(() => {
      loginPromise = null;
    });
  }

  return loginPromise;
}

export {
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  ensureAuthenticated,
};
