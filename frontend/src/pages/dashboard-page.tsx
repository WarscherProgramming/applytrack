import {
  AlertTriangle,
  Bell,
  Briefcase,
  Building2,
  CalendarClock,
  TrendingUp,
} from 'lucide-react';

import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { DashboardCharts } from '@/features/dashboard/components/dashboard-charts';
import { StatCard } from '@/features/dashboard/components/stat-card';
import { useDashboardStats } from '@/features/dashboard/hooks/use-dashboard-stats';

export function DashboardPage() {
  const { stats, isLoading, isError, error, refetch } = useDashboardStats();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="An overview of your job search at a glance."
      />

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatCard
              label="Total Companies"
              value={stats.totalCompanies}
              icon={Building2}
              isLoading={isLoading}
            />
            <StatCard
              label="Total Applications"
              value={stats.totalApplications}
              icon={Briefcase}
              isLoading={isLoading}
              accentClassName="bg-secondary text-secondary-foreground"
            />
            <StatCard
              label="Active Applications"
              value={stats.activeApplications}
              icon={TrendingUp}
              isLoading={isLoading}
              accentClassName="bg-success/10 text-success"
              hint="Excludes closed applications"
            />
            <StatCard
              label="Interviews Scheduled"
              value={stats.interviewsScheduled}
              icon={CalendarClock}
              isLoading={isLoading}
              accentClassName="bg-primary/10 text-primary"
            />
            <StatCard
              label="Follow-ups Due Today"
              value={stats.followupsDueToday}
              icon={Bell}
              isLoading={isLoading}
              accentClassName="bg-warning/15 text-warning"
            />
            <StatCard
              label="Overdue Follow-ups"
              value={stats.overdueFollowups}
              icon={AlertTriangle}
              isLoading={isLoading}
              accentClassName="bg-destructive/10 text-destructive"
            />
          </div>

          <DashboardCharts />
        </>
      )}
    </div>
  );
}
