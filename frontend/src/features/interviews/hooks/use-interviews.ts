import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { interviewsApi } from '../api/interviews.api';
import type {
  InterviewCreateInput,
  InterviewListParams,
  InterviewUpdateInput,
} from '../types/interview.types';

/** Query key factory — keeps cache keys consistent and invalidation precise. */
export const interviewKeys = {
  all: ['interviews'] as const,
  lists: () => [...interviewKeys.all, 'list'] as const,
  list: (params: InterviewListParams) =>
    [...interviewKeys.lists(), params] as const,
  details: () => [...interviewKeys.all, 'detail'] as const,
  detail: (id: string) => [...interviewKeys.details(), id] as const,
};

export function useInterviews(params: InterviewListParams) {
  return useQuery({
    queryKey: interviewKeys.list(params),
    queryFn: () => interviewsApi.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useCreateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: InterviewCreateInput) => interviewsApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
    },
  });
}

export function useUpdateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: InterviewUpdateInput }) =>
      interviewsApi.update(id, input),
    onSuccess: (interview) => {
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: interviewKeys.detail(interview.id),
      });
    },
  });
}

export function useDeleteInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => interviewsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
    },
  });
}
