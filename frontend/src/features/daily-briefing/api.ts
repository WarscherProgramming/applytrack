import { apiClient } from '@/services/api-client';

import type {
  DailyBriefingResponse,
  NotificationItem,
  NotificationListResponse,
  NotificationUpdate,
} from './types';

export const dailyBriefingApi = {
  get(): Promise<DailyBriefingResponse> {
    return apiClient
      .get<DailyBriefingResponse>('/daily-briefing/')
      .then((res) => res.data);
  },

  refresh(): Promise<DailyBriefingResponse> {
    return apiClient
      .post<DailyBriefingResponse>('/daily-briefing/refresh')
      .then((res) => res.data);
  },

  notifications(): Promise<NotificationListResponse> {
    return apiClient
      .get<NotificationListResponse>('/daily-briefing/notifications')
      .then((res) => res.data);
  },

  updateNotification(
    id: string,
    input: NotificationUpdate,
  ): Promise<NotificationItem> {
    return apiClient
      .patch<NotificationItem>(`/daily-briefing/notifications/${id}`, input)
      .then((res) => res.data);
  },
};
