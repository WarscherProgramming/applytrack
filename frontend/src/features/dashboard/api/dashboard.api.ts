import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

/**
 * Reads just the `total` from a list endpoint by requesting a single row.
 * Cheap way to get a count without transferring the full collection.
 */
async function countFrom(
  path: string,
  params: Record<string, unknown> = {},
): Promise<number> {
  const res = await apiClient.get<PaginatedResponse<unknown>>(path, {
    params: { ...params, skip: 0, limit: 1 },
  });
  return res.data.total;
}

/**
 * Dashboard aggregation calls. Each maps to an existing list endpoint; there is
 * no dedicated stats endpoint on the backend yet, so counts are derived here.
 */
export const dashboardApi = {
  countCompanies: () => countFrom('/companies/'),
  countApplications: (status?: string) =>
    countFrom('/applications/', status ? { status } : {}),
  countInterviews: (status?: string) =>
    countFrom('/interviews/', status ? { status } : {}),
  countFollowupsToday: () => countFrom('/followups/today'),
  countFollowupsOverdue: () => countFrom('/followups/overdue'),
};
