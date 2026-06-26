import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Application,
  ApplicationCreateInput,
  ApplicationListParams,
  ApplicationUpdateInput,
} from '../types/application.types';

/**
 * Typed wrappers around the /applications endpoints. The only place application
 * URLs are referenced — hooks and components call these, never apiClient directly.
 */
export const applicationsApi = {
  list(
    params: ApplicationListParams = {},
  ): Promise<PaginatedResponse<Application>> {
    return apiClient
      .get<PaginatedResponse<Application>>('/applications/', { params })
      .then((res) => res.data);
  },

  get(id: string): Promise<Application> {
    return apiClient
      .get<Application>(`/applications/${id}`)
      .then((res) => res.data);
  },

  create(input: ApplicationCreateInput): Promise<Application> {
    return apiClient
      .post<Application>('/applications/', input)
      .then((res) => res.data);
  },

  update(id: string, input: ApplicationUpdateInput): Promise<Application> {
    return apiClient
      .patch<Application>(`/applications/${id}`, input)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/applications/${id}`).then(() => undefined);
  },
};
