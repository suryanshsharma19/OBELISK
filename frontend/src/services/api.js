// Axios API client

import axios from 'axios';
import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// normalise errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
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
