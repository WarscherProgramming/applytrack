import { useQueries } from '@tanstack/react-query';

import { dashboardApi } from '../api/dashboard.api';

// Application statuses considered "closed". Active = total − sum(these).
const TERMINAL_APPLICATION_STATUSES = [
  'accepted',
  'rejected',
  'withdrawn',
  'ghosted',
] as const;

export interface DashboardStats {
  totalCompanies: number;
  totalApplications: number;
  activeApplications: number;
  interviewsScheduled: number;
  followupsDueToday: number;
  overdueFollowups: number;
}

/**
 * Loads all dashboard metrics in parallel. Active applications is computed as
 * total minus the closed-status counts so it stays accurate without a bespoke
 * stats endpoint.
 */
export function useDashboardStats() {
  const results = useQueries({
    queries: [
      { queryKey: ['stats', 'companies'], queryFn: dashboardApi.countCompanies },
      {
        queryKey: ['stats', 'applications', 'total'],
        queryFn: () => dashboardApi.countApplications(),
      },
      {
        queryKey: ['stats', 'interviews', 'scheduled'],
        queryFn: () => dashboardApi.countInterviews('scheduled'),
      },
      {
        queryKey: ['stats', 'followups', 'today'],
        queryFn: dashboardApi.countFollowupsToday,
      },
      {
        queryKey: ['stats', 'followups', 'overdue'],
        queryFn: dashboardApi.countFollowupsOverdue,
      },
      ...TERMINAL_APPLICATION_STATUSES.map((status) => ({
        queryKey: ['stats', 'applications', status],
        queryFn: () => dashboardApi.countApplications(status),
      })),
    ],
  });

  const isLoading = results.some((r) => r.isLoading);
  const isError = results.some((r) => r.isError);
  const error = results.find((r) => r.error)?.error;

  const [
    companies,
    applicationsTotal,
    interviewsScheduled,
    followupsToday,
    followupsOverdue,
    ...terminalCounts
  ] = results.map((r) => r.data ?? 0);

  const closedApplications = terminalCounts.reduce((sum, n) => sum + n, 0);

  const stats: DashboardStats = {
    totalCompanies: companies,
    totalApplications: applicationsTotal,
    activeApplications: Math.max(0, applicationsTotal - closedApplications),
    interviewsScheduled,
    followupsDueToday: followupsToday,
    overdueFollowups: followupsOverdue,
  };

  return { stats, isLoading, isError, error, refetch: () => results.forEach((r) => r.refetch()) };
}
