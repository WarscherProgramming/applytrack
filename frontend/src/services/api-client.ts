import axios, { AxiosError } from 'axios';

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

// Normalise the HTTP status onto the thrown error so the QueryClient's retry
// policy and UI error handling can read `error.status` uniformly.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      (error as AxiosError & { status?: number }).status =
        error.response.status;
    }
    return Promise.reject(error);
  },
);
