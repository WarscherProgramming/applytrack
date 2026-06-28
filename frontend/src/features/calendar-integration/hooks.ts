import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { calendarIntegrationApi } from './api';
import type { CalendarProvider, ManualSyncInput } from './types';

export const calendarIntegrationKeys = {
  all: ['calendar-integration'] as const,
  status: () => [...calendarIntegrationKeys.all, 'status'] as const,
};

export function useCalendarIntegrationStatus() {
  return useQuery({
    queryKey: calendarIntegrationKeys.status(),
    queryFn: calendarIntegrationApi.status,
  });
}

export function useConnectCalendar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: CalendarProvider) =>
      calendarIntegrationApi.connect(provider),
    onSuccess: (result) => {
      if (result.authorization_url) {
        window.location.href = result.authorization_url;
        return;
      }
      void queryClient.invalidateQueries({
        queryKey: calendarIntegrationKeys.status(),
      });
    },
  });
}

export function useDisconnectCalendar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: CalendarProvider) =>
      calendarIntegrationApi.disconnect(provider),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: calendarIntegrationKeys.status(),
      });
    },
  });
}

export function useSyncCalendar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ManualSyncInput) => calendarIntegrationApi.sync(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: calendarIntegrationKeys.status(),
      });
    },
  });
}

export function useSyncInterviewToCalendar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      interviewId,
      provider,
    }: {
      interviewId: string;
      provider: CalendarProvider;
    }) => calendarIntegrationApi.syncInterview(interviewId, provider),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: calendarIntegrationKeys.status(),
      });
    },
  });
}
