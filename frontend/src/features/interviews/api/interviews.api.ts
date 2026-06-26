import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Interview,
  InterviewCreateInput,
  InterviewListParams,
  InterviewUpdateInput,
} from '../types/interview.types';

/**
 * Typed wrappers around the /interviews endpoints. The only place interview
 * URLs are referenced — hooks and components call these, never apiClient directly.
 */
export const interviewsApi = {
  list(
    params: InterviewListParams = {},
  ): Promise<PaginatedResponse<Interview>> {
    return apiClient
      .get<PaginatedResponse<Interview>>('/interviews/', { params })
      .then((res) => res.data);
  },

  get(id: string): Promise<Interview> {
    return apiClient.get<Interview>(`/interviews/${id}`).then((res) => res.data);
  },

  create(input: InterviewCreateInput): Promise<Interview> {
    return apiClient
      .post<Interview>('/interviews/', input)
      .then((res) => res.data);
  },

  update(id: string, input: InterviewUpdateInput): Promise<Interview> {
    return apiClient
      .patch<Interview>(`/interviews/${id}`, input)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/interviews/${id}`).then(() => undefined);
  },
};
