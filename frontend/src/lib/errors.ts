import { AxiosError } from 'axios';

/** Shape of the backend's error responses (see app/exceptions/handlers.py). */
interface ApiErrorBody {
  detail?: string | { msg?: string }[];
}

/**
 * Normalise any thrown value into a human-readable message.
 * Handles Axios errors (pulling FastAPI's `detail`), native Errors, and
 * plain strings, with a safe fallback.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorBody | undefined;
    const detail = body?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (error.message) return error.message;
    return 'Network request failed';
  }
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'An unexpected error occurred';
}
