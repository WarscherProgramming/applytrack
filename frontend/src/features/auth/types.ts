import type { BaseEntity } from '@/types/api';

export interface AuthUser extends BaseEntity {
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: AuthUser;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput extends LoginInput {
  full_name?: string | null;
}

export interface UserUpdateInput {
  email?: string;
  full_name?: string | null;
}
