import { apiClient } from '@/services/api-client';

import type { CareerCopilotResponse } from './types';

export const careerCopilotApi = {
  daily(): Promise<CareerCopilotResponse> {
    return apiClient
      .get<CareerCopilotResponse>('/career-copilot/daily')
      .then((res) => res.data);
  },
};

