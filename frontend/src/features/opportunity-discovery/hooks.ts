import { useMutation, useQueryClient } from '@tanstack/react-query';

import { opportunityDiscoveryApi } from './api';
import type { OpportunitySearchRequest, SaveOpportunityRequest } from './types';

export const opportunityDiscoveryKeys = {
  all: ['opportunity-discovery'] as const,
};

export function useOpportunitySearch() {
  return useMutation({
    mutationFn: (input: OpportunitySearchRequest) =>
      opportunityDiscoveryApi.search(input),
  });
}

export function useSaveOpportunity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveOpportunityRequest) =>
      opportunityDiscoveryApi.save(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['applications'] });
      void queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
}
