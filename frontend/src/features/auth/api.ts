import { getRefreshToken } from '@/services/auth-tokens';
import { apiClient } from '@/services/api-client';

import type {
  AuthResponse,
  AuthUser,
  LoginInput,
  RegisterInput,
  UserUpdateInput,
} from './types';

export const authApi = {
  register(input: RegisterInput): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/register', input).then((res) => res.data);
  },

  login(input: LoginInput): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/login', input).then((res) => res.data);
  },

  me(): Promise<AuthUser> {
    return apiClient.get<AuthUser>('/auth/me').then((res) => res.data);
  },

  refresh(refreshToken: string): Promise<AuthResponse> {
    return apiClient
      .post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken })
      .then((res) => res.data);
  },

  logout(): Promise<void> {
    return apiClient
      .post('/auth/logout', { refresh_token: getRefreshToken() })
      .then(() => undefined);
  },

  updateMe(input: UserUpdateInput): Promise<AuthUser> {
    return apiClient.patch<AuthUser>('/users/me', input).then((res) => res.data);
  },
};
