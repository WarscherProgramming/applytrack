import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import type { Company } from '../types/company.types';
import { companiesApi } from '../api/companies.api';

const EMPTY: Company[] = [];

/**
 * Loads companies for selection + id→name lookup. Used by the application form's
 * company picker and the Kanban board to label cards by company without an N+1
 * request per card. Capped at 100 (the backend's max page size).
 */
export function useCompanyOptions() {
  const query = useQuery({
    queryKey: ['companies', 'options'],
    queryFn: () => companiesApi.list({ skip: 0, limit: 100 }),
  });

  const options = query.data?.items ?? EMPTY;

  const byId = useMemo(() => {
    const map = new Map<string, string>();
    for (const company of query.data?.items ?? []) {
      map.set(company.id, company.name);
    }
    return map;
  }, [query.data]);

  return { ...query, options, byId };
}
