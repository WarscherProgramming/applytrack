import { CalendarClock } from 'lucide-react';

import { StatusBadge } from '@/components/common/status-badge';
import { formatDateTime, humanizeEnum } from '@/utils/format';

import { useApplicationsIndex } from '../hooks/use-applications-index';
import { useUpcomingInterviews } from '../hooks/use-dashboard-lists';
import { DashboardSection } from './dashboard-section';
import { SectionRow } from './section-row';

/** Next scheduled interviews, linked to their application's job title. */
export function UpcomingInterviews() {
  const { data, isLoading, isError, error, refetch } = useUpcomingInterviews();
  // Reuses the cached applications index to resolve the job title per interview.
  const apps = useApplicationsIndex();

  const interviews = data?.items ?? [];

  return (
    <DashboardSection
      title="Upcoming interviews"
      icon={CalendarClock}
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={refetch}
      isEmpty={interviews.length === 0}
      emptyTitle="No interviews scheduled"
      emptyDescription="Scheduled interviews will appear here."
    >
      {interviews.map((interview) => {
        const job = apps.byId.get(interview.application_id)?.job_title;
        return (
          <SectionRow
            key={interview.id}
            leading={
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                <CalendarClock className="h-4 w-4" />
              </span>
            }
            title={
              interview.interview_type
                ? humanizeEnum(interview.interview_type)
                : 'Interview'
            }
            subtitle={job ?? 'Application'}
            meta={
              <div className="flex flex-col items-end gap-1">
                <StatusBadge status={interview.status} />
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(interview.scheduled_at)}
                </span>
              </div>
            }
          />
        );
      })}
    </DashboardSection>
  );
}
