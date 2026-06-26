import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Recruiter,
  RecruiterCreateInput,
  RecruiterListParams,
  RecruiterUpdateInput,
} from '../types/recruiter.types';

/**
 * Typed wrappers around the /recruiters endpoints. The only place recruiter
 * URLs are referenced — hooks and components call these, never apiClient directly.
 */
export const recruitersApi = {
  list(
    params: RecruiterListParams = {},
  ): Promise<PaginatedResponse<Recruiter>> {
    return apiClient
      .get<PaginatedResponse<Recruiter>>('/recruiters/', { params })
      .then((res) => res.data);
  },

  get(id: string): Promise<Recruiter> {
    return apiClient.get<Recruiter>(`/recruiters/${id}`).then((res) => res.data);
  },

  create(input: RecruiterCreateInput): Promise<Recruiter> {
    return apiClient
      .post<Recruiter>('/recruiters/', input)
      .then((res) => res.data);
  },

  update(id: string, input: RecruiterUpdateInput): Promise<Recruiter> {
    return apiClient
      .patch<Recruiter>(`/recruiters/${id}`, input)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/recruiters/${id}`).then(() => undefined);
  },
};
