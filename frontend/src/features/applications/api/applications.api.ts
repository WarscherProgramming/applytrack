import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Application,
  ApplicationListParams,
} from '../types/application.types';

/** Typed wrappers around the /applications endpoints (read-only for now). */
export const applicationsApi = {
  list(
    params: ApplicationListParams = {},
  ): Promise<PaginatedResponse<Application>> {
    return apiClient
      .get<PaginatedResponse<Application>>('/applications/', { params })
      .then((res) => res.data);
  },
};
