import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { applicationsApi } from '../api/applications.api';
import type {
  ApplicationCreateInput,
  ApplicationListParams,
  ApplicationUpdateInput,
} from '../types/application.types';

/** Query key factory — keeps cache keys consistent and invalidation precise. */
export const applicationKeys = {
  all: ['applications'] as const,
  lists: () => [...applicationKeys.all, 'list'] as const,
  list: (params: ApplicationListParams) =>
    [...applicationKeys.lists(), params] as const,
  details: () => [...applicationKeys.all, 'detail'] as const,
  detail: (id: string) => [...applicationKeys.details(), id] as const,
};

export function useApplications(params: ApplicationListParams) {
  return useQuery({
    queryKey: applicationKeys.list(params),
    queryFn: () => applicationsApi.list(params),
    // Keep the current board visible while filters/refetches resolve.
    placeholderData: keepPreviousData,
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ApplicationCreateInput) => applicationsApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.lists() });
    },
  });
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ApplicationUpdateInput }) =>
      applicationsApi.update(id, input),
    onSuccess: (application) => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: applicationKeys.detail(application.id),
      });
    },
  });
}

export function useDeleteApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => applicationsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.lists() });
    },
  });
}
