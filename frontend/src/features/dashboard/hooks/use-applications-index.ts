import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { applicationsApi } from '@/features/applications/api/applications.api';
import type {
  Application,
  ApplicationStatus,
} from '@/features/applications/types/application.types';

// The backend caps page size at 100. For a single user's job search this
// comfortably covers the whole pipeline, so one request powers the Recent
// list, the pipeline chart, and the interview→job-title lookup. A dedicated
// aggregation endpoint would replace this if datasets ever exceed 100.
const INDEX_LIMIT = 100;
const RECENT_COUNT = 5;

/**
 * Single source of truth for application data on the dashboard. Fetched once
 * (shared via the React Query cache) and reshaped into the views each section
 * needs.
 */
export function useApplicationsIndex() {
  const query = useQuery({
    queryKey: ['dashboard', 'applications-index'],
    queryFn: () => applicationsApi.list({ skip: 0, limit: INDEX_LIMIT }),
  });

  const items = useMemo(() => query.data?.items ?? [], [query.data]);

  const recent = useMemo(() => items.slice(0, RECENT_COUNT), [items]);

  const statusCounts = useMemo(() => {
    const counts = new Map<ApplicationStatus, number>();
    for (const app of items) {
      counts.set(app.status, (counts.get(app.status) ?? 0) + 1);
    }
    return counts;
  }, [items]);

  const byId = useMemo(() => {
    const map = new Map<string, Application>();
    for (const app of items) map.set(app.id, app);
    return map;
  }, [items]);

  return {
    ...query,
    items,
    recent,
    statusCounts,
    byId,
    total: query.data?.total ?? 0,
  };
}
