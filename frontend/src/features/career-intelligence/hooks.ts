import { useQuery } from '@tanstack/react-query';

import { careerIntelligenceApi } from './api';
import type { CareerIntelligenceParams } from './types';

export const careerIntelligenceKeys = {
  all: ['career-intelligence'] as const,
  dashboard: (params: CareerIntelligenceParams) =>
    [...careerIntelligenceKeys.all, 'dashboard', params] as const,
};

export function useCareerIntelligence(params: CareerIntelligenceParams) {
  return useQuery({
    queryKey: careerIntelligenceKeys.dashboard(params),
    queryFn: () => careerIntelligenceApi.get(params),
  });
}

