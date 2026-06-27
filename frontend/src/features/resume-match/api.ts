import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  ResumeMatchAnalysis,
  ResumeMatchListItem,
  ResumeMatchListParams,
  ResumeMatchRunInput,
} from './types';

/** Typed wrappers around the /resume-match endpoints. */
export const resumeMatchApi = {
  run(input: ResumeMatchRunInput): Promise<ResumeMatchAnalysis> {
    return apiClient
      .post<ResumeMatchAnalysis>('/resume-match/', input)
      .then((res) => res.data);
  },

  list(
    params: ResumeMatchListParams = {},
  ): Promise<PaginatedResponse<ResumeMatchListItem>> {
    return apiClient
      .get<PaginatedResponse<ResumeMatchListItem>>('/resume-match/', { params })
      .then((res) => res.data);
  },

  get(id: string): Promise<ResumeMatchAnalysis> {
    return apiClient
      .get<ResumeMatchAnalysis>(`/resume-match/${id}`)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/resume-match/${id}`).then(() => undefined);
  },
};
