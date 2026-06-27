import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  InterviewPrepListItem,
  InterviewPrepListParams,
  InterviewPrepPackage,
  InterviewPrepRequest,
} from './types';

/** Typed wrappers around the /interview-prep endpoints. */
export const interviewPrepApi = {
  generate(input: InterviewPrepRequest): Promise<InterviewPrepPackage> {
    return apiClient
      .post<InterviewPrepPackage>('/interview-prep/', input)
      .then((res) => res.data);
  },

  list(
    params: InterviewPrepListParams = {},
  ): Promise<PaginatedResponse<InterviewPrepListItem>> {
    return apiClient
      .get<PaginatedResponse<InterviewPrepListItem>>('/interview-prep/', {
        params,
      })
      .then((res) => res.data);
  },

  get(id: string): Promise<InterviewPrepPackage> {
    return apiClient
      .get<InterviewPrepPackage>(`/interview-prep/${id}`)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/interview-prep/${id}`).then(() => undefined);
  },
};
