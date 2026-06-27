import { useQuery } from '@tanstack/react-query';

import { careerCopilotApi } from './api';

export const careerCopilotKeys = {
  all: ['career-copilot'] as const,
  daily: () => [...careerCopilotKeys.all, 'daily'] as const,
};

export function useCareerCopilot() {
  return useQuery({
    queryKey: careerCopilotKeys.daily(),
    queryFn: careerCopilotApi.daily,
  });
}

