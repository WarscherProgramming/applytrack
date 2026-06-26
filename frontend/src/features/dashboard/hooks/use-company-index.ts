import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { companiesApi } from '@/features/companies/api/companies.api';

const INDEX_LIMIT = 100;

/**
 * Cached id→name lookup for companies, used to label applications by their
 * company on the dashboard without an N+1 request per row.
 */
export function useCompanyIndex() {
  const query = useQuery({
    queryKey: ['dashboard', 'companies-index'],
    queryFn: () => companiesApi.list({ skip: 0, limit: INDEX_LIMIT }),
  });

  const byId = useMemo(() => {
    const map = new Map<string, string>();
    for (const company of query.data?.items ?? []) {
      map.set(company.id, company.name);
    }
    return map;
  }, [query.data]);

  return { ...query, byId };
}
