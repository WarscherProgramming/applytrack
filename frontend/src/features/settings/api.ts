import { getRefreshToken } from '@/services/auth-tokens';
import { apiClient } from '@/services/api-client';

import type {
  AccountSettingsInput,
  DataExportResponse,
  NotificationSettingsInput,
  PasswordChangeInput,
  PasswordChangeResponse,
  PreferencesInput,
  SessionActionResponse,
  SessionInfo,
  SessionListResponse,
  SettingsCenter,
  UserSettings,
} from './types';

function refreshTokenPayload() {
  const refreshToken = getRefreshToken();
  return refreshToken ? { refresh_token: refreshToken } : null;
}

export const settingsApi = {
  get(): Promise<SettingsCenter> {
    return apiClient.get<SettingsCenter>('/settings/').then((res) => res.data);
  },

  updateAccount(input: AccountSettingsInput): Promise<SettingsCenter> {
    return apiClient
      .patch<SettingsCenter>('/settings/account', input)
      .then((res) => res.data);
  },

  updatePreferences(input: PreferencesInput): Promise<UserSettings> {
    return apiClient
      .patch<UserSettings>('/settings/preferences', input)
      .then((res) => res.data);
  },

  updateNotifications(input: NotificationSettingsInput): Promise<UserSettings> {
    return apiClient
      .patch<UserSettings>('/settings/notifications', input)
      .then((res) => res.data);
  },

  changePassword(input: PasswordChangeInput): Promise<PasswordChangeResponse> {
    return apiClient
      .post<PasswordChangeResponse>('/settings/security/change-password', {
        ...input,
        current_refresh_token: getRefreshToken() ?? undefined,
      })
      .then((res) => res.data);
  },

  sessions(): Promise<SessionListResponse> {
    const payload = refreshTokenPayload();
    if (payload) {
      return apiClient
        .post<SessionListResponse>('/settings/sessions', payload)
        .then((res) => res.data);
    }
    return apiClient.get<SessionListResponse>('/settings/sessions').then((res) => res.data);
  },

  currentSession(): Promise<SessionInfo> {
    const payload = refreshTokenPayload();
    if (!payload) throw new Error('No refresh token found for this session.');
    return apiClient
      .post<SessionInfo>('/settings/sessions/current', payload)
      .then((res) => res.data);
  },

  signOutCurrent(): Promise<SessionActionResponse> {
    const payload = refreshTokenPayload();
    if (!payload) throw new Error('No refresh token found for this session.');
    return apiClient
      .post<SessionActionResponse>('/settings/sessions/logout-current', payload)
      .then((res) => res.data);
  },

  signOutAll(): Promise<SessionActionResponse> {
    return apiClient
      .post<SessionActionResponse>('/settings/sessions/logout-all')
      .then((res) => res.data);
  },

  exportData(): Promise<DataExportResponse> {
    return apiClient.get<DataExportResponse>('/settings/export').then((res) => res.data);
  },
};
