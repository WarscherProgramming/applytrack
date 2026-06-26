import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { recruitersApi } from '../api/recruiters.api';
import type {
  RecruiterCreateInput,
  RecruiterListParams,
  RecruiterUpdateInput,
} from '../types/recruiter.types';

/** Query key factory — keeps cache keys consistent and invalidation precise. */
export const recruiterKeys = {
  all: ['recruiters'] as const,
  lists: () => [...recruiterKeys.all, 'list'] as const,
  list: (params: RecruiterListParams) =>
    [...recruiterKeys.lists(), params] as const,
  details: () => [...recruiterKeys.all, 'detail'] as const,
  detail: (id: string) => [...recruiterKeys.details(), id] as const,
};

export function useRecruiters(params: RecruiterListParams) {
  return useQuery({
    queryKey: recruiterKeys.list(params),
    queryFn: () => recruitersApi.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useCreateRecruiter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RecruiterCreateInput) => recruitersApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recruiterKeys.lists() });
    },
  });
}

export function useUpdateRecruiter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: RecruiterUpdateInput }) =>
      recruitersApi.update(id, input),
    onSuccess: (recruiter) => {
      queryClient.invalidateQueries({ queryKey: recruiterKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: recruiterKeys.detail(recruiter.id),
      });
    },
  });
}

export function useDeleteRecruiter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recruitersApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recruiterKeys.lists() });
    },
  });
}
