import { useContext } from 'react';

import { ThemeProviderContext } from '@/components/theme/theme-provider';

/** Access the current theme and a setter. Must be used within <ThemeProvider>. */
export function useTheme() {
  const context = useContext(ThemeProviderContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
