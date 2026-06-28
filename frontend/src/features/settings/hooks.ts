import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { settingsApi } from './api';
import type {
  AccountSettingsInput,
  NotificationSettingsInput,
  PasswordChangeInput,
  PreferencesInput,
} from './types';

export const settingsKeys = {
  all: ['settings'] as const,
  center: () => [...settingsKeys.all, 'center'] as const,
  sessions: () => [...settingsKeys.all, 'sessions'] as const,
};

export function useSettingsCenter() {
  return useQuery({
    queryKey: settingsKeys.center(),
    queryFn: settingsApi.get,
  });
}

export function useSessions() {
  return useQuery({
    queryKey: settingsKeys.sessions(),
    queryFn: settingsApi.sessions,
  });
}

export function useUpdateAccountSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AccountSettingsInput) => settingsApi.updateAccount(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.center() });
    },
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PreferencesInput) => settingsApi.updatePreferences(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.center() });
    },
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: NotificationSettingsInput) => settingsApi.updateNotifications(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.center() });
    },
  });
}

export function useChangePassword() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PasswordChangeInput) => settingsApi.changePassword(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.sessions() });
    },
  });
}

export function useSignOutCurrentSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.signOutCurrent,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.sessions() });
    },
  });
}

export function useSignOutAllSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.signOutAll,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: settingsKeys.sessions() });
    },
  });
}

export function useExportData() {
  return useMutation({
    mutationFn: settingsApi.exportData,
  });
}
