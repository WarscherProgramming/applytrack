import { apiClient } from '@/services/api-client';

import type {
  CalendarConnectResponse,
  CalendarProvider,
  CalendarStatusResponse,
  CalendarSyncSummary,
  ManualSyncInput,
} from './types';

const basePath = '/calendar-integration';

export const calendarIntegrationApi = {
  status(): Promise<CalendarStatusResponse> {
    return apiClient
      .get<CalendarStatusResponse>(`${basePath}/status`)
      .then((res) => res.data);
  },

  connect(provider: CalendarProvider): Promise<CalendarConnectResponse> {
    return apiClient
      .post<CalendarConnectResponse>(`${basePath}/connect/${provider}`)
      .then((res) => res.data);
  },

  disconnect(provider: CalendarProvider): Promise<void> {
    return apiClient
      .post(`${basePath}/disconnect/${provider}`)
      .then(() => undefined);
  },

  sync(input: ManualSyncInput): Promise<CalendarSyncSummary> {
    return apiClient
      .post<CalendarSyncSummary>(`${basePath}/sync`, input)
      .then((res) => res.data);
  },

  syncInterview(
    interviewId: string,
    provider: CalendarProvider,
  ): Promise<CalendarSyncSummary> {
    return apiClient
      .post<CalendarSyncSummary>(`${basePath}/interviews/${interviewId}/sync`, {
        provider,
      })
      .then((res) => res.data);
  },

  icsUrl(): string {
    const base = apiClient.defaults.baseURL ?? '';
    return `${base}${basePath}/ics`;
  },
};
