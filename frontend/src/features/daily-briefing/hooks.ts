import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { dailyBriefingApi } from './api';
import type { NotificationUpdate } from './types';

export const dailyBriefingKeys = {
  all: ['daily-briefing'] as const,
  briefing: () => [...dailyBriefingKeys.all, 'briefing'] as const,
  notifications: () => [...dailyBriefingKeys.all, 'notifications'] as const,
};

export function useDailyBriefing() {
  return useQuery({
    queryKey: dailyBriefingKeys.briefing(),
    queryFn: () => dailyBriefingApi.get(),
  });
}

export function useRefreshDailyBriefing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => dailyBriefingApi.refresh(),
    onSuccess: (data) => {
      queryClient.setQueryData(dailyBriefingKeys.briefing(), data);
      void queryClient.invalidateQueries({
        queryKey: dailyBriefingKeys.notifications(),
      });
    },
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: dailyBriefingKeys.notifications(),
    queryFn: () => dailyBriefingApi.notifications(),
  });
}

export function useUpdateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: NotificationUpdate }) =>
      dailyBriefingApi.updateNotification(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: dailyBriefingKeys.all });
    },
  });
}
