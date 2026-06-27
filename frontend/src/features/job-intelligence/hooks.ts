import { useQuery } from '@tanstack/react-query';

import { jobIntelligenceApi } from './api';
import type { JobIntelligenceParams } from './types';

export const jobIntelligenceKeys = {
  all: ['job-intelligence'] as const,
  report: (params: JobIntelligenceParams) =>
    [...jobIntelligenceKeys.all, 'report', params] as const,
};

export function useJobIntelligence(params: JobIntelligenceParams) {
  return useQuery({
    queryKey: jobIntelligenceKeys.report(params),
    queryFn: () => jobIntelligenceApi.get(params),
  });
}

