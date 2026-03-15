// Axios API client

import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';
import {
  clearAccessToken,
  ensureAuthenticated,
  getAccessToken,
} from './session';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.request.use(async (config) => {
  if (!config.url?.includes('/api/auth/login')) {
    await ensureAuthenticated();
  }

  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// normalise errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAccessToken();
    }

    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    return Promise.reject(new Error(message));
  },
);

export const analyzePackage = (payload) =>
  api.post('/api/packages/analyze', payload).then((r) => r.data);

export const getPackages = (params = {}) =>
  api.get('/api/packages/list', { params }).then((r) => r.data);

export const getPackageDetail = (id) =>
  api.get(`/api/packages/${id}`).then((r) => r.data);

export const getStatsOverview = () =>
  api.get('/api/stats/overview').then((r) => r.data);

export const getStatsTrend = (days = 7) =>
  api.get('/api/stats/trend', { params: { days } }).then((r) => r.data);

export const getAlerts = (params = {}) =>
  api.get('/api/alerts/', { params }).then((r) => r.data);

export const getAlertDetail = (id) =>
  api.get(`/api/alerts/${id}`).then((r) => r.data);

export const updateAlert = (id, data) =>
  api.put(`/api/alerts/${id}`, null, { params: data }).then((r) => r.data);

export const bulkAlertAction = (alertIds, action) =>
  api.post(`/api/alerts/bulk?action=${action}`, alertIds).then((r) => r.data);

export const getCrawlerStatus = () =>
  api.get('/api/crawler/status').then((r) => r.data);

export const startCrawler = (config = {}) =>
  api.post('/api/crawler/start', config).then((r) => r.data);

export const stopCrawler = () =>
  api.post('/api/crawler/stop').then((r) => r.data);


export const healthCheck = () =>
  api.get('/health').then((r) => r.data);

export default api;
