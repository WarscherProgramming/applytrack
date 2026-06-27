import { apiClient } from '@/services/api-client';

import type {
  JobIntelligenceParams,
  JobIntelligenceResponse,
} from './types';

export const jobIntelligenceApi = {
  get(params: JobIntelligenceParams = {}): Promise<JobIntelligenceResponse> {
    return apiClient
      .get<JobIntelligenceResponse>('/job-intelligence/', { params })
      .then((res) => res.data);
  },
};

