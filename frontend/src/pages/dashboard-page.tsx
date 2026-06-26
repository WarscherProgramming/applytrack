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
import { ActivityChart } from '@/features/dashboard/components/activity-chart';
import { ApplicationPipelineChart } from '@/features/dashboard/components/application-pipeline-chart';
import { FollowupsToday } from '@/features/dashboard/components/followups-today';
import { OverdueFollowups } from '@/features/dashboard/components/overdue-followups';
import { RecentApplications } from '@/features/dashboard/components/recent-applications';
import { StatCard } from '@/features/dashboard/components/stat-card';
import { UpcomingInterviews } from '@/features/dashboard/components/upcoming-interviews';
import { useDashboardStats } from '@/features/dashboard/hooks/use-dashboard-stats';

export function DashboardPage() {
  const { stats, isLoading, isError, error, refetch } = useDashboardStats();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="An overview of your job search at a glance."
      />

      {/* Metric tiles */}
      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
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
      )}

      {/* Charts: real pipeline + placeholder activity trend */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ApplicationPipelineChart />
        <ActivityChart />
      </div>

      {/* Activity lists */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecentApplications />
        <UpcomingInterviews />
        <FollowupsToday />
        <OverdueFollowups />
      </div>
    </div>
  );
}
