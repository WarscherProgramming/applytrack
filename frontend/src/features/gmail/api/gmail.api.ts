import { apiClient } from '@/services/api-client';

import type {
  EmailListParams,
  EmailListResponse,
  GmailConnectResponse,
  GmailStatus,
  GmailSyncResponse,
  TimelineEvent,
} from '../types';

/**
 * Typed wrappers around the /gmail endpoints. All Gmail network access lives
 * here — components and hooks never touch URLs, and no Gmail/OAuth logic leaks
 * into React.
 */
export const gmailApi = {
  status(): Promise<GmailStatus> {
    return apiClient.get<GmailStatus>('/gmail/status').then((r) => r.data);
  },

  connect(): Promise<GmailConnectResponse> {
    return apiClient
      .post<GmailConnectResponse>('/gmail/connect')
      .then((r) => r.data);
  },

  disconnect(): Promise<void> {
    return apiClient.post('/gmail/disconnect').then(() => undefined);
  },

  sync(): Promise<GmailSyncResponse> {
    return apiClient.post<GmailSyncResponse>('/gmail/sync').then((r) => r.data);
  },

  listEmails(params: EmailListParams = {}): Promise<EmailListResponse> {
    return apiClient
      .get<EmailListResponse>('/gmail/emails', { params })
      .then((r) => r.data);
  },

  timeline(applicationId: string): Promise<{ items: TimelineEvent[] }> {
    return apiClient
      .get<{ items: TimelineEvent[] }>('/gmail/timeline', {
        params: { application_id: applicationId },
      })
      .then((r) => r.data);
  },
};
