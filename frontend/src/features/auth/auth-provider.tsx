import type { ReactNode } from 'react';
import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { PageFallback } from '@/components/common/page-fallback';
import { clearAuthTokens, getAccessToken, setAuthTokens } from '@/services/auth-tokens';

import { authApi } from './api';
import type { AuthUser, LoginInput, RegisterInput, UserUpdateInput } from './types';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  updateMe: (input: UserUpdateInput) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadUser() {
      if (!getAccessToken()) {
        setIsLoading(false);
        return;
      }
      try {
        const current = await authApi.me();
        if (mounted) setUser(current);
      } catch {
        clearAuthTokens();
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    void loadUser();
    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      async login(input) {
        const result = await authApi.login(input);
        setAuthTokens(result.access_token, result.refresh_token);
        setUser(result.user);
      },
      async register(input) {
        const result = await authApi.register(input);
        setAuthTokens(result.access_token, result.refresh_token);
        setUser(result.user);
      },
      async logout() {
        try {
          await authApi.logout();
        } finally {
          clearAuthTokens();
          setUser(null);
        }
      },
      async updateMe(input) {
        const updated = await authApi.updateMe(input);
        setUser(updated);
      },
    }),
    [isLoading, user],
  );

  if (isLoading) return <PageFallback />;

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
