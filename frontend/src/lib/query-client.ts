import { QueryClient } from '@tanstack/react-query';

/**
 * A single shared QueryClient for the app.
 *
 * Defaults chosen for a CRM-style dashboard: data is treated as fresh for a
 * short window to avoid refetch storms when navigating between pages, and we
 * don't retry 4xx responses (they won't succeed on retry).
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        const status = (error as { status?: number })?.status;
        if (status && status >= 400 && status < 500) return false;
        return failureCount < 2;
      },
    },
  },
});
