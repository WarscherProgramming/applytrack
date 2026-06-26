import { Briefcase } from 'lucide-react';

import { StatusBadge } from '@/components/common/status-badge';
import { formatDate } from '@/utils/format';

import { useApplicationsIndex } from '../hooks/use-applications-index';
import { useCompanyIndex } from '../hooks/use-company-index';
import { DashboardSection } from './dashboard-section';
import { SectionRow } from './section-row';

/** Most recently active applications, with their company and status. */
export function RecentApplications() {
  const apps = useApplicationsIndex();
  const companies = useCompanyIndex();

  return (
    <DashboardSection
      title="Recent applications"
      icon={Briefcase}
      isLoading={apps.isLoading}
      isError={apps.isError}
      error={apps.error}
      onRetry={apps.refetch}
      isEmpty={apps.recent.length === 0}
      emptyTitle="No applications yet"
      emptyDescription="Applications you add will show up here."
    >
      {apps.recent.map((app) => (
        <SectionRow
          key={app.id}
          leading={
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Briefcase className="h-4 w-4" />
            </span>
          }
          title={app.job_title}
          subtitle={companies.byId.get(app.company_id) ?? 'Unknown company'}
          meta={
            <div className="flex flex-col items-end gap-1">
              <StatusBadge status={app.status} />
              <span className="text-xs text-muted-foreground">
                {formatDate(app.date_applied)}
              </span>
            </div>
          }
        />
      ))}
    </DashboardSection>
  );
}
