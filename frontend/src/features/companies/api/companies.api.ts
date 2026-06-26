import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Company,
  CompanyCreateInput,
  CompanyListParams,
  CompanyUpdateInput,
} from '../types/company.types';

/**
 * Typed wrappers around the /companies endpoints. These are the ONLY place
 * company URLs are referenced — hooks and components call these functions, not
 * the apiClient directly.
 */
export const companiesApi = {
  list(params: CompanyListParams = {}): Promise<PaginatedResponse<Company>> {
    return apiClient
      .get<PaginatedResponse<Company>>('/companies/', { params })
      .then((res) => res.data);
  },

  get(id: string): Promise<Company> {
    return apiClient.get<Company>(`/companies/${id}`).then((res) => res.data);
  },

  create(input: CompanyCreateInput): Promise<Company> {
    return apiClient.post<Company>('/companies/', input).then((res) => res.data);
  },

  update(id: string, input: CompanyUpdateInput): Promise<Company> {
    return apiClient
      .patch<Company>(`/companies/${id}`, input)
      .then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/companies/${id}`).then(() => undefined);
  },
};
