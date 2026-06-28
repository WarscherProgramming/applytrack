import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

import {
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  setAuthTokens,
} from './auth-tokens';

/**
 * Centralised Axios instance — the single entry point for every backend call.
 *
 * Base URL strategy:
 *  - Development: VITE_API_URL (e.g. http://localhost:8000) is set, so the
 *    browser hits the backend container directly. CORS on the API allows
 *    http://localhost:5173.
 *  - Production: VITE_API_URL is unset, so we fall back to a relative `/api/v1`
 *    path which nginx proxies to the backend service.
 *
 * No component should import axios directly; they go through the typed service
 * modules in each feature's `api/` folder, which use this client.
 */
const apiBase = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api/v1`
  : '/api/v1';

export const apiClient = axios.create({
  baseURL: apiBase,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Normalise the HTTP status onto the thrown error so the QueryClient's retry
// policy and UI error handling can read `error.status` uniformly.
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response) {
      (error as AxiosError & { status?: number }).status =
        error.response.status;
    }
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const url = original?.url ?? '';
    const canRefresh =
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !url.includes('/auth/login') &&
      !url.includes('/auth/register') &&
      !url.includes('/auth/refresh');

    if (canRefresh) {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          original._retry = true;
          const response = await apiClient.post('/auth/refresh', {
            refresh_token: refreshToken,
          });
          setAuthTokens(response.data.access_token, response.data.refresh_token);
          original.headers.Authorization = `Bearer ${response.data.access_token}`;
          return apiClient(original);
        } catch {
          clearAuthTokens();
        }
      }
    }
    return Promise.reject(error);
  },
);
