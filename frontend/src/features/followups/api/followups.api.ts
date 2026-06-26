import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  FollowUp,
  FollowUpListParams,
} from '../types/followup.types';

/**
 * Typed wrappers around the /followups endpoints (read-only for now).
 * `today` and `overdue` are dedicated reminder endpoints on the backend.
 */
export const followupsApi = {
  list(params: FollowUpListParams = {}): Promise<PaginatedResponse<FollowUp>> {
    return apiClient
      .get<PaginatedResponse<FollowUp>>('/followups/', { params })
      .then((res) => res.data);
  },

  listToday(
    params: FollowUpListParams = {},
  ): Promise<PaginatedResponse<FollowUp>> {
    return apiClient
      .get<PaginatedResponse<FollowUp>>('/followups/today', { params })
      .then((res) => res.data);
  },

  listOverdue(
    params: FollowUpListParams = {},
  ): Promise<PaginatedResponse<FollowUp>> {
    return apiClient
      .get<PaginatedResponse<FollowUp>>('/followups/overdue', { params })
      .then((res) => res.data);
  },
};
