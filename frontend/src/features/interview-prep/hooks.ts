import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { interviewPrepApi } from './api';
import type { InterviewPrepListParams, InterviewPrepRequest } from './types';

export const interviewPrepKeys = {
  all: ['interview-prep'] as const,
  lists: () => [...interviewPrepKeys.all, 'list'] as const,
  list: (params: InterviewPrepListParams) =>
    [...interviewPrepKeys.lists(), params] as const,
  details: () => [...interviewPrepKeys.all, 'detail'] as const,
  detail: (id: string) => [...interviewPrepKeys.details(), id] as const,
};

export function usePrepHistory(params: InterviewPrepListParams = {}) {
  return useQuery({
    queryKey: interviewPrepKeys.list(params),
    queryFn: () => interviewPrepApi.list(params),
    placeholderData: keepPreviousData,
  });
}

export function usePrep(id: string | null) {
  return useQuery({
    queryKey: interviewPrepKeys.detail(id ?? 'none'),
    queryFn: () => interviewPrepApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useGeneratePrep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: InterviewPrepRequest) => interviewPrepApi.generate(input),
    onSuccess: (pkg) => {
      // Seed detail cache so reopening the just-generated package needs no fetch.
      queryClient.setQueryData(interviewPrepKeys.detail(pkg.id), pkg);
      queryClient.invalidateQueries({ queryKey: interviewPrepKeys.lists() });
    },
  });
}

export function useDeletePrep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => interviewPrepApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interviewPrepKeys.lists() });
    },
  });
}
