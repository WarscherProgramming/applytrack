import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { gmailApi } from '../api/gmail.api';
import type { EmailListParams } from '../types';

export const gmailKeys = {
  all: ['gmail'] as const,
  status: () => [...gmailKeys.all, 'status'] as const,
  emails: (params: EmailListParams) =>
    [...gmailKeys.all, 'emails', params] as const,
  timeline: (applicationId: string) =>
    [...gmailKeys.all, 'timeline', applicationId] as const,
};

export function useGmailStatus() {
  return useQuery({
    queryKey: gmailKeys.status(),
    queryFn: gmailApi.status,
  });
}

export function useConnectGmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gmailApi.connect,
    onSuccess: (result) => {
      // Real OAuth: hand off to Google. Simulation: just refresh status.
      if (result.authorization_url) {
        window.location.href = result.authorization_url;
        return;
      }
      queryClient.invalidateQueries({ queryKey: gmailKeys.status() });
    },
  });
}

export function useDisconnectGmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gmailApi.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gmailKeys.all });
    },
  });
}

export function useSyncGmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gmailApi.sync,
    onSuccess: () => {
      // New emails + updated counts/last-sync.
      queryClient.invalidateQueries({ queryKey: gmailKeys.all });
    },
  });
}

export function useEmails(params: EmailListParams) {
  return useQuery({
    queryKey: gmailKeys.emails(params),
    queryFn: () => gmailApi.listEmails(params),
    placeholderData: keepPreviousData,
  });
}
