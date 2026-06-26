import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import type { Application } from '../types/application.types';
import { applicationsApi } from '../api/applications.api';

const EMPTY: Application[] = [];

/**
 * Loads applications for selection + id→application lookup. Used by the
 * interview form's application picker and the calendar to resolve an
 * interview's job title and company. Capped at 100 (backend max page size).
 */
export function useApplicationOptions() {
  const query = useQuery({
    queryKey: ['applications', 'options'],
    queryFn: () => applicationsApi.list({ skip: 0, limit: 100 }),
  });

  const options = query.data?.items ?? EMPTY;

  const byId = useMemo(() => {
    const map = new Map<string, Application>();
    for (const application of query.data?.items ?? []) {
      map.set(application.id, application);
    }
    return map;
  }, [query.data]);

  return { ...query, options, byId };
}
