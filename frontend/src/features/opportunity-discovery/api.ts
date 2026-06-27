import { apiClient } from '@/services/api-client';

import type {
  OpportunitySearchRequest,
  OpportunitySearchResponse,
  SaveOpportunityRequest,
  SaveOpportunityResponse,
} from './types';

export const opportunityDiscoveryApi = {
  search(input: OpportunitySearchRequest): Promise<OpportunitySearchResponse> {
    return apiClient
      .post<OpportunitySearchResponse>('/opportunity-discovery/search', input)
      .then((res) => res.data);
  },

  save(input: SaveOpportunityRequest): Promise<SaveOpportunityResponse> {
    return apiClient
      .post<SaveOpportunityResponse>('/opportunity-discovery/save', input)
      .then((res) => res.data);
  },
};
