import { apiClient } from '@/services/api-client';

import type {
  CareerIntelligenceParams,
  CareerIntelligenceResponse,
} from './types';

export const careerIntelligenceApi = {
  get(params: CareerIntelligenceParams = {}): Promise<CareerIntelligenceResponse> {
    return apiClient
      .get<CareerIntelligenceResponse>('/career-intelligence/', { params })
      .then((res) => res.data);
  },
};

