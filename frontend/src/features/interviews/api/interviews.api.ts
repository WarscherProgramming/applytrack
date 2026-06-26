import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Interview,
  InterviewListParams,
} from '../types/interview.types';

/** Typed wrappers around the /interviews endpoints (read-only for now). */
export const interviewsApi = {
  list(
    params: InterviewListParams = {},
  ): Promise<PaginatedResponse<Interview>> {
    return apiClient
      .get<PaginatedResponse<Interview>>('/interviews/', { params })
      .then((res) => res.data);
  },
};
