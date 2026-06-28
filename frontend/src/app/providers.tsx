import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { ReactNode } from 'react';

import { ThemeProvider } from '@/components/theme/theme-provider';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AuthProvider } from '@/features/auth/auth-provider';
import { queryClient } from '@/lib/query-client';

/**
 * Wraps the app in every cross-cutting provider:
 * theme (dark mode), server-state cache, tooltips, and toast notifications.
 * Kept separate from routing so providers can be reused (e.g. in tests).
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <TooltipProvider delayDuration={200}>
            {children}
            <Toaster />
          </TooltipProvider>
        </ThemeProvider>
      </AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
    </QueryClientProvider>
  );
}
