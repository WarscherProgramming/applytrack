import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { resumeMatchApi } from './api';
import type { ResumeMatchListParams, ResumeMatchRunInput } from './types';

/** Query-key factory — keeps caching consistent and invalidation precise. */
export const resumeMatchKeys = {
  all: ['resume-match'] as const,
  lists: () => [...resumeMatchKeys.all, 'list'] as const,
  list: (params: ResumeMatchListParams) =>
    [...resumeMatchKeys.lists(), params] as const,
  details: () => [...resumeMatchKeys.all, 'detail'] as const,
  detail: (id: string) => [...resumeMatchKeys.details(), id] as const,
};

export function useMatchHistory(params: ResumeMatchListParams = {}) {
  return useQuery({
    queryKey: resumeMatchKeys.list(params),
    queryFn: () => resumeMatchApi.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useMatch(id: string | null) {
  return useQuery({
    queryKey: resumeMatchKeys.detail(id ?? 'none'),
    queryFn: () => resumeMatchApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useRunMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ResumeMatchRunInput) => resumeMatchApi.run(input),
    onSuccess: (analysis) => {
      // Seed the detail cache so reopening the just-run analysis needs no fetch.
      queryClient.setQueryData(resumeMatchKeys.detail(analysis.id), analysis);
      queryClient.invalidateQueries({ queryKey: resumeMatchKeys.lists() });
    },
  });
}

export function useDeleteMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => resumeMatchApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: resumeMatchKeys.lists() });
    },
  });
}
