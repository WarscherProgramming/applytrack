import { PageHeader } from '@/components/common/page-header';
import { CalendarIntegrationSettingsCard } from '@/features/calendar-integration/components/calendar-integration-settings-card';

export function CalendarIntegrationPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Calendar Integration"
        description="Connect external calendars and export ApplyTrack schedule data."
      />
      <CalendarIntegrationSettingsCard />
    </div>
  );
}
